# Digital Dragon: Unraid Installation Guide

This guide installs Digital Dragon on an Unraid server as a small Docker container. The app reads SABnzbd stats from your LAN, stores pet growth in `pet_state.json`, and serves the dashboard on port `5055`.

## Requirements

- Unraid with Docker enabled.
- SABnzbd reachable from the Unraid server at `http://192.168.10.20:8188`.
- Your SABnzbd API key.
- Either the Unraid **Compose Manager** plugin or access to the Unraid terminal.

## 1. Copy the Project to Unraid

Create an app folder on your Unraid server:

```bash
mkdir -p /mnt/user/appdata/digital-dragon
```

Copy these project files into that folder:

```text
app.py
Dockerfile
docker-compose.yml
.env.unraid.example
static/
```

If you are copying from another machine, use SMB, SFTP, or the Unraid web terminal.

## 2. Create the Environment File

On Unraid, go to the app folder:

```bash
cd /mnt/user/appdata/digital-dragon
cp .env.unraid.example .env
```

Edit `.env`:

```bash
nano .env
```

Use this shape:

```env
SABNZBD_URL=http://192.168.10.20:8188
SABNZBD_API_KEY=your-real-sabnzbd-api-key
DEMO_MODE=false
HOST=0.0.0.0
PORT=5055
```

Important: `HOST=0.0.0.0` is required inside Docker so the dashboard can be reached from other devices on your network.

## 3. Create the Pet State File

Create an empty state file so Docker can mount it as a file:

```bash
touch /mnt/user/appdata/digital-dragon/pet_state.json
echo '{"last_total_gb":0}' > /mnt/user/appdata/digital-dragon/pet_state.json
```

This file keeps the dragon's growth between container restarts.

## 4. Install with Compose Manager

If you use the Unraid Compose Manager plugin:

1. Open the Unraid web UI.
2. Go to **Docker**.
3. Open **Compose Manager**.
4. Add a new stack named `digital-dragon`.
5. Set the stack path to:

```text
/mnt/user/appdata/digital-dragon
```

6. Use the included `docker-compose.yml`.
7. Click **Compose Up**.

After it starts, open:

```text
http://YOUR-UNRAID-IP:5055
```

Example:

```text
http://192.168.10.10:5055
```

## 5. Install from the Unraid Terminal

If you prefer the terminal:

```bash
cd /mnt/user/appdata/digital-dragon
docker compose up -d --build
```

Check logs:

```bash
docker logs -f digital-dragon
```

Open the dashboard:

```text
http://YOUR-UNRAID-IP:5055
```

## 6. Updating the App

Copy the new files into `/mnt/user/appdata/digital-dragon`, then rebuild:

```bash
cd /mnt/user/appdata/digital-dragon
docker compose up -d --build
```

The `pet_state.json` file should remain in place so the dragon keeps its progress.

## 7. Troubleshooting

If the dashboard opens but says demo or fallback mode:

- Confirm `.env` has `DEMO_MODE=false`.
- Confirm `SABNZBD_API_KEY` is set.
- Confirm the Unraid server can reach SABnzbd:

```bash
curl "http://192.168.10.20:8188/api?mode=version&output=json&apikey=YOUR_API_KEY"
```

If the dashboard does not open:

- Confirm the container is running:

```bash
docker ps | grep digital-dragon
```

- Confirm port `5055` is not already used by another container.
- Confirm `HOST=0.0.0.0` in `.env`.
- Check logs:

```bash
docker logs digital-dragon
```

If SABnzbd is running in another Docker container on the same Unraid host, using the LAN IP address is usually the simplest option:

```env
SABNZBD_URL=http://192.168.10.20:8188
```

## 8. Optional: Run in Demo Mode

To test the UI without SABnzbd:

```env
DEMO_MODE=true
```

Restart the container:

```bash
docker restart digital-dragon
```

## 9. Optional: Unraid XML Template

This project includes a suggested Unraid Docker XML template:

```text
unraid-template-digital-dragon.xml
```

You can copy it into Unraid's Docker template folder:

```bash
cp /mnt/user/appdata/digital-dragon/unraid-template-digital-dragon.xml /boot/config/plugins/dockerMan/templates-user/my-digital-dragon.xml
```

Then open the Unraid web UI:

1. Go to **Docker**.
2. Click **Add Container**.
3. Choose `digital-dragon` from the template dropdown.
4. Set the SABnzbd API key.
5. Apply the template.

The XML template points directly to this Docker image:

```text
ghcr.io/digitalgp/digitaldragon:latest
```

The template also points back to the GitHub project, issue tracker, and raw template URL. If the image has not been published yet, build it locally as a temporary workaround:

```bash
cd /mnt/user/appdata/digital-dragon
docker build -t ghcr.io/digitalgp/digitaldragon:latest .
```
