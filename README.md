# 📥 Media Downloader

> **Clean, fast, and ascetic media downloader for macOS and Windows.**  
> Downloads 1080p Full HD video and crystal-clear audio from **YouTube, TikTok, Instagram Reels, Twitter/X, SoundCloud** without ads, watermarks, or malware.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Website](https://img.shields.io/badge/Website-media--downloader--web.web.app-brightgreen)](https://media-downloader-web.web.app)
[![Zero Ads](https://img.shields.io/badge/Ads-0%25%20Zero-success)](#)

---

## 🇺🇦 Українська версія

**Media Downloader** — це відкрита та прозора утиліта для швидкого збереження медіафайлів прямо на ваш комп'ютер у найвищій доступній якості.

### ✨ Головні можливості
- **100% без реклами та спаму:** ніяких спливаючих вікон, підроблених кнопок чи платних підписок.
- **📦 Пакетне завантаження та підтримка плейлистів:** вставляйте кілька посилань одночасно або посилання на цілий плейлист — програма по черзі завантажить усі файли з відображенням прогресу `[X/N]` та єдиним підсумковим сповіщенням.
- **Повна сумісність з Apple QuickTime:** кожне відео автоматично зводиться в кодеки H.264 (AVC) + AAC і стандартний телевізійний діапазон (BT.709), тому воно бездоганно відкривається по натисканню **Пробілу (QuickLook)** у macOS Finder та на iOS.
- **Підтримка TikTok без водяних знаків.**
- **Вибір мови дубляжу / аудіодоріжки:** збереження потрібної мови для багатомовних роликів YouTube (UA, EN тощо).
- **Підтримка нативного MP3:** конвертація у високоякісне аудіо 320 kbps.
- **1-клік лаунчери:** готові подвійні кліки для Mac (`.app`) та Windows (`.bat` з автоматичним створенням ярлика на Робочому столі).
- **🔄 Вбудоване самооновлення (Self-Update):** програма автоматично перевіряє наявність нових версій і оновлюється в 1 клік без ручного перекачування архівів.

### 🚀 Як запустити з коду
```bash
# 1. Клонувати репозиторій
git clone https://github.com/IlliaRanok/media-downloader.git
cd media-downloader

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Запустити програму
python3 media_downloader_app.py
```
*(Примітка: для конвертації та зведення аудіо рекомендується мати встановлений `ffmpeg`)*

---

## 🇬🇧 English Version

**Media Downloader** is an open-source, lightweight tool for downloading video and audio streams directly to your local computer in maximum available fidelity.

### ✨ Key Features
- **100% Ad-Free:** Zero third-party trackers, zero popups, zero premium walls.
- **📦 Batch & Playlist Downloading:** Paste multiple links at once or feed full playlist URLs — download entire queues with progress indicator `[X/N]` and consolidated notifications.
- **Native Apple QuickTime & QuickLook Support:** Streams are finalized as Apple-compliant H.264 / AAC MP4 with BT.709 colorimetry and +faststart flags.
- **Watermark-Free TikTok & Reels:** Direct progressive clean media capture.
- **Multi-Language Audio Track Selector:** Pick your preferred dubbing track for international YouTube videos.
- **Audio Extraction:** High-bitrate stereo MP3 extraction in one tap.
- **🔄 In-App Self-Update:** Automatically checks for new releases and updates in 1-click without re-downloading archives.

### 🚀 Quick Start
```bash
git clone https://github.com/IlliaRanok/media-downloader.git
cd media-downloader
pip install -r requirements.txt
python3 media_downloader_app.py
```

---

## 🌐 Official Web App & Ready-to-use Binaries
Ready-to-run portable packages for macOS (Apple Silicon / Intel) and Windows (10 / 11) are available on the official website:  
👉 **[https://media-downloader-web.web.app](https://media-downloader-web.web.app)**

## 📜 License
Distributed under the **MIT License**. See `LICENSE` for details.
