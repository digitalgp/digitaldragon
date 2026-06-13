# Digital Dragon

Digital Dragon is a local digital pet that grows from SABnzbd network activity. It reads SABnzbd through its API, turns downloaded data into XP, and shows a friendly companion dashboard in your browser.

## Setup

1. Open `.env`.
2. Keep `SABNZBD_URL=http://192.168.10.20:8188`.
3. Replace `SABNZBD_API_KEY=replace-with-your-api-key` with your SABnzbd API key.
4. Set `DEMO_MODE=false` when you want live SABnzbd data.
5. Run:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:5055
```

## How Growth Works

- Every 1 GB downloaded gives the dragon 100 XP.
- Current download speed gently feeds the appetite meter.
- Milestones unlock at 1 GB, 10 GB, 50 GB, 100 GB, 250 GB, and 500 GB.
- `pet_state.json` stores the most recent lifetime total so the pet can keep growing over time.

## Data Refresh

- The dashboard fetches fresh data as soon as the page opens.
- It automatically refreshes every 30 seconds.
- You can also fetch new data manually with the **Refresh** button.

## SABnzbd Notes

The app calls SABnzbd's local API using:

- `mode=queue` for speed and queue size
- `mode=history` for completed download history

If SABnzbd cannot be reached, the app falls back to demo data and shows the connection state in the UI.

## Unraid

For Unraid/Docker installation, see [UNRAID_INSTALL.md](UNRAID_INSTALL.md).
