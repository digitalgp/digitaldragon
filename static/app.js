const elements = {
  statusBanner: document.querySelector("#statusBanner"),
  statusTitle: document.querySelector("#statusTitle"),
  statusMessage: document.querySelector("#statusMessage"),
  refreshButton: document.querySelector("#refreshButton"),
  livePill: document.querySelector("#livePill"),
  demoPill: document.querySelector("#demoPill"),
  levelValue: document.querySelector("#levelValue"),
  growthTitle: document.querySelector("#growthTitle"),
  xpFill: document.querySelector("#xpFill"),
  xpValue: document.querySelector("#xpValue"),
  dragon: document.querySelector("#dragon"),
  todayValue: document.querySelector("#todayValue"),
  gainValue: document.querySelector("#gainValue"),
  queueValue: document.querySelector("#queueValue"),
  queueSizeValue: document.querySelector("#queueSizeValue"),
  speedValue: document.querySelector("#speedValue"),
  moodValue: document.querySelector("#moodValue"),
  appetiteCopy: document.querySelector("#appetiteCopy"),
  appetiteBars: document.querySelector("#appetiteBars"),
  onlineBadge: document.querySelector("#onlineBadge"),
  urlValue: document.querySelector("#urlValue"),
  keyValue: document.querySelector("#keyValue"),
  checkedValue: document.querySelector("#checkedValue"),
  milestoneRail: document.querySelector("#milestoneRail"),
};

function formatGb(value) {
  return `${Number(value || 0).toLocaleString(undefined, {
    maximumFractionDigits: value >= 10 ? 1 : 2,
  })} GB`;
}

function formatTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function setSourceState(data) {
  const isLive = data.source === "live";
  elements.livePill.classList.toggle("active", isLive);
  elements.demoPill.classList.toggle("active", !isLive);
  elements.statusBanner.classList.toggle("offline", !data.connection_ok);
  elements.statusTitle.textContent = isLive ? "Connected to SABnzbd" : "Demo feeding active";
  elements.statusMessage.textContent = data.message;
  elements.onlineBadge.textContent = isLive ? "Online" : data.source === "fallback" ? "Fallback" : "Demo";
  elements.onlineBadge.classList.toggle("offline", !isLive);
}

function renderAppetite(value) {
  elements.appetiteBars.innerHTML = "";
  const filled = Math.round((value / 100) * 14);
  for (let index = 0; index < 14; index += 1) {
    const bar = document.createElement("span");
    bar.className = index < filled ? "filled" : "";
    elements.appetiteBars.appendChild(bar);
  }
}

function renderMilestones(milestones) {
  elements.milestoneRail.innerHTML = "";
  milestones.forEach((milestone) => {
    const item = document.createElement("article");
    item.className = `milestone ${milestone.unlocked ? "" : "locked"}`;
    item.innerHTML = `
      <div class="milestone-dot">${milestone.unlocked ? "&check;" : milestone.gb}</div>
      <strong>${milestone.label}</strong>
      <small>${milestone.unlocked ? `${milestone.gb} GB` : `${milestone.remaining_gb} GB to go`}</small>
    `;
    elements.milestoneRail.appendChild(item);
  });
}

function render(data) {
  setSourceState(data);

  const { pet, stats, config } = data;
  const xpPercent = Math.min(100, (pet.current_level_xp / pet.next_level_xp) * 100);
  elements.levelValue.textContent = pet.level;
  elements.growthTitle.textContent = pet.stage;
  elements.xpFill.style.width = `${xpPercent}%`;
  elements.xpValue.textContent = `${pet.current_level_xp.toLocaleString()} / ${pet.next_level_xp.toLocaleString()} XP`;
  elements.dragon.style.setProperty("--dragon-scale", pet.scale);

  elements.todayValue.textContent = formatGb(stats.downloaded_today_gb);
  elements.gainValue.textContent = `+${formatGb(stats.gained_gb)}`;
  elements.queueValue.textContent = stats.queue_count;
  elements.queueSizeValue.textContent = formatGb(stats.queue_gb);
  elements.speedValue.textContent = `${stats.speed_mbs} MB/s`;

  elements.moodValue.textContent = pet.mood;
  elements.appetiteCopy.textContent =
    pet.appetite > 74 ? "Keep the downloads flowing." : "A few downloads would perk the dragon up.";
  renderAppetite(pet.appetite);

  elements.urlValue.textContent = config.sabnzbd_url;
  elements.keyValue.textContent = config.api_key_set ? "****************" : "not set";
  elements.checkedValue.textContent = formatTime(data.checked_at);
  renderMilestones(data.milestones);
}

async function refresh() {
  elements.refreshButton.disabled = true;
  elements.refreshButton.textContent = "Refreshing";
  try {
    const response = await fetch("/api/pet", { cache: "no-store" });
    const data = await response.json();
    render(data);
  } catch (error) {
    elements.statusBanner.classList.add("offline");
    elements.statusTitle.textContent = "Backend is not responding";
    elements.statusMessage.textContent = error.message;
  } finally {
    elements.refreshButton.disabled = false;
    elements.refreshButton.textContent = "Refresh";
  }
}

elements.refreshButton.addEventListener("click", refresh);
refresh();
setInterval(refresh, 30000);
