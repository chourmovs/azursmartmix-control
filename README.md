# azursmartmix-control (v1 read-only)

Control plane UI for AzurSmartMix:
- Reads station runtime config (YAML) in read-only mode
- Shows containers status (engine + scheduler)
- Shows logs tail (no follow yet)
- Shows Now Playing / Upcoming by proxying scheduler API

## Run

```bash
docker compose up -d --build
```

Open:
- http://YOUR_HOST:8088

## Expected environment
- Engine container name: azursmartmix_engine
- Scheduler container name: azursmartmix_scheduler
- Scheduler API reachable at http://azursmartmix_scheduler:8001

Adjust `docker-compose.yml` env vars if needed.

## Security note
This v1 mounts `/var/run/docker.sock` read-only to read status/logs.
Do NOT expose this UI publicly without auth / reverse-proxy protection.
