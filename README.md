---
title: Snapwave
emoji: ⚡
colorFrom: red
colorTo: indigo
sdk: docker
app_port: 8080
pinned: false
---

# SnapWave – Video & Audio Fast Downloader

Production-ready media downloader engine powered by FastAPI & yt-dlp.

## Admin password

Set `ADMIN_PASSWORD` to a unique password of at least 16 characters before
starting the app. Docker Compose refuses to start without it, and the app
validates it at startup. The password initializes the admin account when no
password has been configured yet and replaces recognized legacy defaults
during a one-time migration. Do not commit real credentials to `.env.example`
or source control.
