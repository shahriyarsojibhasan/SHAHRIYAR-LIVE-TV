<p align="center">
  <img src="https://i.ibb.co.com/TFSssmW/image.png" alt="SHAHRIYAR LIVE TV Logo" width="180">
</p>

<h1 align="center">📺 SHAHRIYAR LIVE TV</h1>

<p align="center">
  <b>High-Performance, Policy-Compliant, 100% Verified Live TV Streaming Ecosystem</b><br>
  Featuring Auto-Updating Playlists, Edge CORS Proxy, and Ultra-Fast Plyr Web Player.
</p>

<p align="center">
  <a href="https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/actions/workflows/shahriyar.yml">
    <img src="https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/actions/workflows/shahriyar.yml/badge.svg" alt="TV Update Status">
  </a>
  <a href="https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/actions/workflows/shahriyarapp.yml">
    <img src="https://github.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/actions/workflows/shahriyarapp.yml/badge.svg" alt="App Update Status">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python Version">
  </a>
  <a href="https://workers.cloudflare.com/">
    <img src="https://img.shields.io/badge/Edge%20Proxy-Cloudflare%20Workers-orange?logo=cloudflare&logoColor=white" alt="Cloudflare Workers">
  </a>
  <img src="https://img.shields.io/badge/Status-100%25%20Verified%20Playable-success?style=flat-square" alt="Status">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg?style=flat-square" alt="License">
  </a>
  <img src="https://img.shields.io/badge/Made%20in-Bangladesh%20%F0%9F%87%A7%F0%9F%87%A9-green?style=flat-square" alt="Made in Bangladesh">
</p>

<p align="center">
  <a href="https://t.me/shahriyartvbot">
    <img src="https://img.shields.io/badge/Telegram-Join%20Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  </a>
  <a href="https://discord.gg/shahriyarsojibhasan">
    <img src="https://img.shields.io/badge/Discord-Community-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
  </a>
</p>

---

## 🌟 Highlights & Features

- ⚡ **Ultra-Fast & Lightweight Web Player:** Custom-tuned Plyr.js player with GPU-accelerated video rendering, instant category filters, and zero-lag channel switching.
- 🛡️ **Edge CORS & Referer Bypass Proxy:** Built-in Cloudflare Worker (`worker.js`) and Node.js proxy (`server.js`) that automatically rewrites HLS segments and injects proper headers for seamless playback in any web browser.
- 🤖 **Automated GitHub Actions Verification:** The `SSHBOT` runs scheduled checks every 30 minutes, concurrently testing hundreds of streams with multi-threading to discard dead links, VODs, and error responses.
- 🎯 **100% Policy-Compliant & Verified FTA:** Strict curation of authentic public Free-To-Air (FTA) broadcasts, eliminating illegal/pirated restreams and DMCA concerns.
- 🌀 **Infinity Spring Progress & Animated HUD:** Includes real-time viewer tracking, smooth loading animations, and automatic stream health badges (`HLS`, `TS`, `DASH`, `EDGE_PROXY`).
- 📱 **Universal Cross-Platform Playback:** Optimized for PC browsers, mobile screens, smart TV remotes, VLC Media Player, and Android IPTV apps (OTT Navigator, Tivimate).

---

## 📡 Live Playlist Links

Copy and paste these direct raw links into your favorite video player or IPTV app:

### 1. 🌐 Web & Browser Optimized Playlist
*Best for Web Player, VLC Media Player on PC, and lightweight players:*
```bash
https://raw.githubusercontent.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/main/SHAHRIYAR-LIVE-TV.m3u
```

### 2. 📱 Android App & Advanced Metadata Playlist
*Full metadata support (`#EXTVLCOPT:`, `#EXTHTTP:`, `#KODIPROP:`, pipe tokens) for **OTT Navigator**, **Tivimate**, and **Android TV**:*
```bash
https://raw.githubusercontent.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/main/SHAHRIYAR-LIVE-TV-APP.m3u
```

---

## 📺 Channel Categories

All channels are automatically sorted and organized into clean categories:

| Category | Description | Channels Sample |
| :--- | :--- | :--- |
| **🇧🇩 BANGLADESH** | Leading Bangladeshi and Bengali FTA channels | BTV, Bangla Vision, Boishakhi, Ananda TV, Channel S, DBC, Deshi TV |
| **⚽ SPORTS** | Global Public Sports, Highlights & Extreme Action | Red Bull TV, Racing, Cricket, Football Public Feeds |
| **📰 NEWS** | 24/7 International & Regional Live News | Al Jazeera HD, DW News, France 24, BBC FTA, Euronews, CNA |
| **🎬 MOVIES** | Public Classic Cinema & Entertainment | B4U Movies FTA, Star/Enterr FTA, Classic Cinemas |
| **🎵 MUSIC** | Non-stop Music & Youth Culture | Music Broadcasts, Pop, Rock, Cultural Tracks |
| **👶 KIDS** | Animation, Cartoons & Family Programs | Duronto TV, Cartoon feeds, Kids Learning |
| **🌍 DOCUMENTARY**| Science, Space, Nature & Technology | NASA TV HD, Wildlife, Science Feeds |

---

## 🚀 How to Run & Play

### Option 1: Live Web Player (Browser)
1. Run locally with Node.js:
   ```bash
   npm install
   npm start
   ```
2. Open your browser at `http://localhost:3000`.
3. Or deploy `worker.js` directly to **Cloudflare Workers** with `wrangler deploy`.

### Option 2: VLC Media Player (PC / Mac)
1. Open **VLC Media Player**.
2. Press `Ctrl + N` (or `Media` ➔ `Open Network Stream`).
3. Paste the Web M3U URL and click **Play**.

### Option 3: OTT Navigator / Tivimate (Android TV & Phone)
1. Install **OTT Navigator** or **Tivimate**.
2. Go to `Settings` ➔ `Playlists` ➔ `Add Playlist` ➔ `M3U Playlist`.
3. Paste the **App M3U URL** (`SHAHRIYAR-LIVE-TV-APP.m3u`).

---

## ⚙️ Automated GitHub Actions Workflow

The repository includes GitHub Actions workflows (`.github/workflows/`):

```
GitHub Actions (Every 30 Mins)
   │
   ├── 1. Read Environment Secrets (Priority 1..10, Sources 1..20)
   ├── 2. Merge with Public Verified FTA Repositories
   ├── 3. Multi-Threaded Live Stream Verification (HTTP 200, Content-Type, Headers)
   ├── 4. Categorize & Deduplicate Streams
   ├── 5. Commit & Push SHAHRIYAR-LIVE-TV.m3u & APP.m3u
   └── 6. Send Telegram Notification
```

### Environment Secrets (Optional)
If you fork this repository, you can configure the following optional repository secrets in `Settings ➔ Secrets and variables ➔ Actions`:

| Secret Name | Purpose |
| :--- | :--- |
| `PRIORITY_PLAYLIST_URL_1` .. `10` | High-priority custom M3U sources |
| `PLAYLIST_SOURCE_URL_1` .. `20` | Secondary custom M3U sources |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token for update notifications |
| `TELEGRAM_TO` | Telegram chat/channel ID for notifications |

---

## 🛡️ Legal Notice & Policy Disclaimer

> [!NOTE]
> **SHAHRIYAR LIVE TV** does not host, store, or re-broadcast any proprietary copyrighted media files on its servers. All streams indexed within this repository are collected from publicly available, Free-To-Air (FTA) web transmissions broadcasted by their respective content owners.
> 
> If you believe any channel stream infringes upon your copyright, please open an issue or contact us via Telegram, and we will promptly review and remove the link.

---

## 👨‍💻 Author & Maintainer

Developed with ❤️ by **[Shahriyar Sojib Hasan](https://github.com/shahriyarsojibhasan)**.

- 🌐 GitHub: [@shahriyarsojibhasan](https://github.com/shahriyarsojibhasan)
- 💬 Telegram: [@shahriyartvbot](https://t.me/shahriyartvbot)
- 🎮 Discord: [SHAHRIYAR Community](https://discord.gg/shahriyarsojibhasan)

---

## 📜 License

This project is licensed under the terms of the **GNU Affero General Public License v3.0 (AGPLv3)**. See [LICENSE](LICENSE) for more details.
