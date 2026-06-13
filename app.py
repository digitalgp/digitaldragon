from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
ENV_PATH = ROOT / ".env"
STATE_PATH = ROOT / "pet_state.json"


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


CONFIG = load_env()


def config_value(name: str, default: str = "") -> str:
    return os.environ.get(name) or CONFIG.get(name) or default


def bool_config(name: str, default: bool = False) -> bool:
    raw = config_value(name, str(default)).lower()
    return raw in {"1", "true", "yes", "on"}


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"last_total_gb": 0, "hatched_at": datetime.now().isoformat()}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"last_total_gb": 0, "hatched_at": datetime.now().isoformat()}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def sabnzbd_api(mode: str, **params: str) -> dict[str, Any]:
    base_url = config_value("SABNZBD_URL", "http://192.168.10.20:8188").rstrip("/")
    api_key = config_value("SABNZBD_API_KEY")
    query = {"mode": mode, "output": "json", "apikey": api_key, **params}
    url = f"{base_url}/api?{urlencode(query)}"

    with urlopen(url, timeout=6) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_size_to_gb(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) / (1024 ** 3)

    text = str(value).strip().replace(",", ".")
    parts = text.split()
    if not parts:
        return 0.0

    try:
        amount = float(parts[0])
    except ValueError:
        return 0.0

    unit = parts[1].lower() if len(parts) > 1 else "b"
    if unit.startswith("tb"):
        return amount * 1024
    if unit.startswith("gb") or unit == "g":
        return amount
    if unit.startswith("mb") or unit == "m":
        return amount / 1024
    if unit.startswith("kb") or unit == "k":
        return amount / (1024 * 1024)
    return amount / (1024 ** 3)


def parse_speed_to_mbs(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", ".")
    parts = text.split()
    if not parts:
        return 0.0
    try:
        amount = float(parts[0])
    except ValueError:
        return 0.0

    unit = parts[1].lower() if len(parts) > 1 else "b/s"
    if unit.startswith("gb"):
        return amount * 1024
    if unit.startswith("mb") or unit == "m":
        return amount
    if unit.startswith("kb") or unit == "k":
        return amount / 1024
    return amount / (1024 * 1024)


def history_total_gb(history: dict[str, Any]) -> tuple[float, float]:
    slots = history.get("history", {}).get("slots", [])
    today = datetime.now().date()
    total = 0.0
    today_total = 0.0

    for item in slots:
        size_gb = parse_size_to_gb(item.get("size") or item.get("bytes"))
        total += size_gb

        completed = item.get("completed") or item.get("completed_time") or item.get("finish")
        completed_date = None
        if isinstance(completed, (int, float)) and completed:
            completed_date = datetime.fromtimestamp(completed).date()
        elif isinstance(completed, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    completed_date = datetime.strptime(completed[:19], fmt).date()
                    break
                except ValueError:
                    pass
        if completed_date == today:
            today_total += size_gb

    return total, today_total


def demo_payload() -> dict[str, Any]:
    hour_wave = (datetime.now().hour % 8) / 8
    downloaded_total_gb = 86.4 + hour_wave * 9.0
    downloaded_today_gb = 8.2 + random.random() * 4.4
    speed_mbs = 7.5 + random.random() * 12
    queue_count = random.randint(2, 6)
    queue_gb = 1.2 + random.random() * 4
    return build_pet_payload(
        downloaded_total_gb=downloaded_total_gb,
        downloaded_today_gb=downloaded_today_gb,
        speed_mbs=speed_mbs,
        queue_count=queue_count,
        queue_gb=queue_gb,
        source="demo",
        connection_ok=False,
        message="Demo mode is active. Add your API key and set DEMO_MODE=false for live feeding.",
    )


def live_payload() -> dict[str, Any]:
    queue = sabnzbd_api("queue")
    history = sabnzbd_api("history", limit="80")

    queue_data = queue.get("queue", {})
    speed_mbs = parse_speed_to_mbs(queue_data.get("speed"))
    queue_count = int(queue_data.get("noofslots") or len(queue_data.get("slots", [])) or 0)
    mb_left = queue_data.get("mbleft")
    if isinstance(mb_left, (int, float)):
        queue_gb = float(mb_left) / 1024
    else:
        queue_gb = parse_size_to_gb(queue_data.get("sizeleft") or mb_left)
    downloaded_total_gb, downloaded_today_gb = history_total_gb(history)

    return build_pet_payload(
        downloaded_total_gb=downloaded_total_gb,
        downloaded_today_gb=downloaded_today_gb,
        speed_mbs=speed_mbs,
        queue_count=queue_count,
        queue_gb=queue_gb,
        source="live",
        connection_ok=True,
        message="Feeding successful. Dragon is happy.",
    )


def build_pet_payload(
    *,
    downloaded_total_gb: float,
    downloaded_today_gb: float,
    speed_mbs: float,
    queue_count: int,
    queue_gb: float,
    source: str,
    connection_ok: bool,
    message: str,
) -> dict[str, Any]:
    state = load_state()
    previous_total = float(state.get("last_total_gb") or 0)
    lifetime_total = max(previous_total, downloaded_total_gb)
    gained_gb = max(0.0, lifetime_total - previous_total)
    state["last_total_gb"] = lifetime_total
    state["last_seen_at"] = datetime.now().isoformat()
    save_state(state)

    xp = int(lifetime_total * 100)
    level = max(1, int(xp / 1000) + 1)
    stage = growth_stage(level)
    current_level_xp = xp % 1000
    appetite = min(100, int(35 + speed_mbs * 3.5 + min(queue_gb, 8) * 2))

    milestones = [
        ("Hatched", 1),
        ("First steps", 10),
        ("Wings unlocked", 50),
        ("Growth spurt", 100),
        ("Teenager", 250),
        ("Ancient friend", 500),
    ]

    return {
        "source": source,
        "connection_ok": connection_ok,
        "message": message,
        "checked_at": datetime.now().isoformat(),
        "config": {
            "sabnzbd_url": config_value("SABNZBD_URL", "http://192.168.10.20:8188"),
            "api_key_set": bool(config_value("SABNZBD_API_KEY")) and config_value("SABNZBD_API_KEY") != "replace-with-your-api-key",
            "demo_mode": bool_config("DEMO_MODE", True),
        },
        "stats": {
            "downloaded_today_gb": round(downloaded_today_gb, 2),
            "downloaded_total_gb": round(lifetime_total, 2),
            "gained_gb": round(gained_gb, 2),
            "speed_mbs": round(speed_mbs, 1),
            "queue_count": queue_count,
            "queue_gb": round(queue_gb, 2),
        },
        "pet": {
            "name": "Digital Dragon",
            "stage": stage,
            "level": level,
            "xp": xp,
            "current_level_xp": current_level_xp,
            "next_level_xp": 1000,
            "appetite": appetite,
            "mood": pet_mood(appetite, gained_gb),
            "scale": min(1.35, 0.82 + level * 0.025),
        },
        "milestones": [
            {
                "label": label,
                "gb": gb,
                "unlocked": lifetime_total >= gb,
                "remaining_gb": max(0, round(gb - lifetime_total, 1)),
            }
            for label, gb in milestones
        ],
    }


def growth_stage(level: int) -> str:
    if level >= 26:
        return "Ancient"
    if level >= 16:
        return "Elder"
    if level >= 9:
        return "Teenager"
    if level >= 4:
        return "Youngling"
    return "Hatchling"


def pet_mood(appetite: int, gained_gb: float) -> str:
    if gained_gb > 0.25:
        return "Growing"
    if appetite > 75:
        return "Well fed"
    if appetite > 45:
        return "Curious"
    return "Hungry"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/pet"):
            self.send_pet()
            return
        if self.path == "/health":
            self.send_json({"ok": True, "time": datetime.now().isoformat()})
            return
        super().do_GET()

    def send_pet(self) -> None:
        try:
            if bool_config("DEMO_MODE", True):
                payload = demo_payload()
            else:
                payload = live_payload()
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            payload = demo_payload()
            payload["message"] = f"Could not reach SABnzbd: {exc}"
            payload["source"] = "fallback"
        self.send_json(payload)

    def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host = config_value("HOST", "127.0.0.1")
    port = int(config_value("PORT", "5055"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Digital Dragon is running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
