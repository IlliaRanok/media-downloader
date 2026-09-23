#!/usr/bin/env python3
"""
Media Downloader (YouTube, TikTok, Instagram, Twitter/X etc.)
- 100% QuickTime Player compatibility on macOS (H.264 / AAC / MP3)
- First-run language setup (Default: English) with persistent config
- Audio dubbing language selector (Ukrainian, English, etc.)
- Batch & Playlist downloads with queue progress [X/N] and summary
- In-app automatic self-updater (GitHub / Firebase)
- Classic high-visibility banner
"""

import sys
import os
import re
import ast
import json
import subprocess
import shutil
import tempfile
import time

APP_VERSION = "3.1.0"
VERSION_URLS = [
    "https://media-downloader-web.web.app/version.json",
    "https://raw.githubusercontent.com/IlliaRanok/media-downloader/main/version.json",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_BIN = os.path.join(SCRIPT_DIR, ".venv", "bin")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

# Пошук yt-dlp у поточній папці, у .venv або в системі
YT_DLP_BIN = None
for candidate in [
    os.path.join(SCRIPT_DIR, "yt-dlp-standalone"),
    os.path.join(SCRIPT_DIR, "yt-dlp"),
    os.path.join(VENV_BIN, "yt-dlp-standalone"),
    os.path.join(VENV_BIN, "yt-dlp"),
    shutil.which("yt-dlp"),
]:
    if candidate and os.path.exists(candidate):
        YT_DLP_BIN = candidate
        break
if not YT_DLP_BIN:
    YT_DLP_BIN = "yt-dlp"

# Пошук ffmpeg
FFMPEG_BIN = None
for candidate in [
    os.path.join(SCRIPT_DIR, "ffmpeg"),
    os.path.join(SCRIPT_DIR, "Media_Downloader.app", "Contents", "Resources", "ffmpeg"),
    os.path.join(SCRIPT_DIR, "Завантажувач_Відео.app", "Contents", "Resources", "ffmpeg"),
    os.path.join(VENV_BIN, "ffmpeg"),
    shutil.which("ffmpeg"),
]:
    if candidate and os.path.exists(candidate):
        FFMPEG_BIN = candidate
        break

FFMPEG_BIN_DIR = os.path.dirname(FFMPEG_BIN) if FFMPEG_BIN else SCRIPT_DIR
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
NODE_BIN = shutil.which("node") or "/opt/homebrew/bin/node"
QJS_BIN = None
for candidate in [
    os.path.join(SCRIPT_DIR, "qjs"),
    os.path.join(VENV_BIN, "qjs"),
    shutil.which("qjs"),
]:
    if candidate and os.path.exists(candidate):
        QJS_BIN = os.path.abspath(candidate)
        break

# ANSI Colors
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

USER_CONFIG_FILE = os.path.expanduser("~/.media_downloader_config.json")
LOCAL_CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")


def load_config():
    for path in [USER_CONFIG_FILE, LOCAL_CONFIG_FILE]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "ui_lang" in data:
                        return data
            except Exception:
                pass
    return {}


def save_config(cfg):
    for path in [USER_CONFIG_FILE, LOCAL_CONFIG_FILE]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def clear_screen():
    print("\033[H\033[J", end="")


def print_banner(ui_lang="en"):
    clear_screen()
    print(f"{CYAN}{BOLD}")
    print("╔═══════════════════════════════════════════════════╗")
    if ui_lang == "ua":
        print(f"║          📥 МЕДІА-ЗАВАНТАЖУВАЧ (v{APP_VERSION})           ║")
        print("║    YouTube • TikTok • Instagram • Twitter • Web   ║")
    else:
        print(f"║            📥 MEDIA DOWNLOADER (v{APP_VERSION})           ║")
        print("║    YouTube • TikTok • Instagram • Twitter • Web   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"{RESET}")


def parse_version(v_str):
    parts = re.findall(r"\d+", str(v_str))
    return tuple(int(p) for p in parts) if parts else (0,)


def is_newer_version(remote_v, local_v):
    return parse_version(remote_v) > parse_version(local_v)


def check_for_updates(ui_lang="en", silent=True):
    """
    Перевіряє наявність оновлень на GitHub / Firebase.
    silent=True: показує сповіщення лише якщо оновлення знайдено.
    silent=False: показує статус пошуку та результат користувачу.
    """
    import urllib.request
    import ssl

    is_ua = (ui_lang == "ua")
    if not silent:
        print(f"\n{YELLOW}{'⏳ Перевіряю наявність оновлень...' if is_ua else '⏳ Checking for updates...'}{RESET}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    remote_data = None
    for u in VERSION_URLS:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "MediaDownloaderUpdater/3.0"})
            with urllib.request.urlopen(req, timeout=2.5, context=ctx) as response:
                if response.status == 200:
                    remote_data = json.loads(response.read().decode("utf-8"))
                    break
        except Exception:
            continue

    if not remote_data:
        if not silent:
            print(f"{RED}{'❌ Не вдалося з’єднатися із сервером оновлень. Перевірте інтернет.' if is_ua else '❌ Could not reach update server. Check your connection.'}{RESET}\n")
        return False

    remote_ver = remote_data.get("version", "0.0.0")
    if is_newer_version(remote_ver, APP_VERSION):
        notes = remote_data.get("notes_ua" if is_ua else "notes_en", "")
        print(f"\n{CYAN}{BOLD}╔════════════════════════════════════════════════════════════════╗{RESET}")
        title_str = f"  ✨ Доступна нова версія: v{remote_ver} (поточна: v{APP_VERSION})" if is_ua else f"  ✨ New version available: v{remote_ver} (current: v{APP_VERSION})"
        pad = max(1, 62 - len(title_str))
        print(f"{CYAN}{BOLD}║{GREEN}{title_str}{' ' * pad}{CYAN}║{RESET}")
        if notes:
            note_line = f"  📢 Що нового: {notes[:46]}" if is_ua else f"  📢 What's new: {notes[:45]}"
            note_pad = max(1, 62 - len(note_line))
            print(f"{CYAN}{BOLD}║{WHITE}{note_line}{' ' * note_pad}{CYAN}║{RESET}")
        print(f"{CYAN}{BOLD}╚════════════════════════════════════════════════════════════════╝{RESET}\n")

        prompt = "Оновити програму зараз? [Y/n] (Enter = Так): " if is_ua else "Update program now? [Y/n] (Enter = Yes): "
        ans = input(prompt).strip().lower()
        if ans in ["", "y", "yes", "так", "д", "да"]:
            return perform_self_update(remote_data, ui_lang)
        else:
            print(f"{GRAY}{'Оновлення відкладено.' if is_ua else 'Update postponed.'}{RESET}\n")
            return False
    else:
        if not silent:
            print(f"{GREEN}{BOLD}{f'✅ У вас встановлена найновіша версія (v{APP_VERSION})!' if is_ua else f'✅ You are running the latest version (v{APP_VERSION})!'}{RESET}\n")
        return False


def perform_self_update(remote_data, ui_lang="en"):
    """
    Завантажує новий код, валідує синтаксис та безпечно замінює поточний файл.
    Також оновлює yt-dlp і перезапускає програму.
    """
    import urllib.request
    import ssl
    import py_compile

    is_ua = (ui_lang == "ua")
    print(f"\n{YELLOW}{'⏳ Завантажую оновлений скрипт...' if is_ua else '⏳ Downloading updated script...'}{RESET}")

    candidate_urls = [
        remote_data.get("script_url"),
        remote_data.get("script_url_fallback"),
        "https://media-downloader-web.web.app/media_downloader_app.py",
        "https://raw.githubusercontent.com/IlliaRanok/media-downloader/main/media_downloader_app.py",
    ]
    candidate_urls = [u for u in candidate_urls if u]

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    script_content = None
    for u in candidate_urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "MediaDownloaderUpdater/3.0"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                if resp.status == 200:
                    raw = resp.read().decode("utf-8")
                    if "Media Downloader" in raw and len(raw) > 5000:
                        script_content = raw
                        break
        except Exception:
            continue

    if not script_content:
        print(f"{RED}{'❌ Помилка: не вдалося завантажити файл оновлення.' if is_ua else '❌ Error: Failed to download update file.'}{RESET}\n")
        return False

    current_script_path = os.path.abspath(__file__)
    dir_name = os.path.dirname(current_script_path)
    temp_target = os.path.join(dir_name, ".temp_update_app.py")

    try:
        with open(temp_target, "w", encoding="utf-8") as f:
            f.write(script_content)

        try:
            py_compile.compile(temp_target, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"{RED}{'❌ Помилка синтаксису оновленого файлу:' if is_ua else '❌ Update file syntax error:'} {e}{RESET}")
            if os.path.exists(temp_target):
                os.remove(temp_target)
            return False

        if os.path.exists(current_script_path):
            try:
                os.chmod(temp_target, 0o755)
            except Exception:
                pass
            shutil.move(temp_target, current_script_path)

        # Оновлення рушія yt-dlp
        print(f"{YELLOW}{'⏳ Оновлюю медіа-рушій yt-dlp...' if is_ua else '⏳ Updating media engine yt-dlp...'}{RESET}")
        try:
            ytdlp_cmd = [YT_DLP_BIN, "-U"] if (YT_DLP_BIN and YT_DLP_BIN != "yt-dlp") else [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
            subprocess.run(ytdlp_cmd, capture_output=True, timeout=15)
        except Exception:
            pass

        print(f"\n{GREEN}{BOLD}{'🎉 Програму успішно оновлено! Перезапускаю...' if is_ua else '🎉 Program updated successfully! Restarting...'}{RESET}\n")
        restart_application()
        return True

    except Exception as e:
        print(f"{RED}{'❌ Помилка при застосуванні оновлення:' if is_ua else '❌ Error applying update:'} {e}{RESET}\n")
        if os.path.exists(temp_target):
            try:
                os.remove(temp_target)
            except Exception:
                pass
        return False


def restart_application():
    """Перезапускає поточний скрипт без необхідності відкривати термінал заново"""
    time.sleep(1)
    if os.name == "nt":
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv)


def get_initial_language():
    """Запитує мову лише один раз при першому вході, за замовчуванням англійська"""
    cfg = load_config()
    if "ui_lang" in cfg:
        return cfg["ui_lang"]

    clear_screen()
    print(f"{CYAN}{BOLD}")
    print("╔═══════════════════════════════════════════════════╗")
    print(f"║            📥 MEDIA DOWNLOADER (v{APP_VERSION})           ║")
    print("║    YouTube • TikTok • Instagram • Twitter • Web   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"{RESET}")
    print(f"{BOLD}Welcome! Please select your interface language / Оберіть мову:{RESET}\n")
    print(f"  {GREEN}[1]{RESET} English {BOLD}(Default){RESET}")
    print(f"  {GREEN}[2]{RESET} Українська")

    ans = input(f"\nYour choice {BOLD}[1/2]{RESET} (press Enter for English): ").strip()
    if ans in ["2", "ua", "uk", "ukr", "україна"]:
        lang = "ua"
    else:
        lang = "en"

    cfg["ui_lang"] = lang
    save_config(cfg)
    return lang


def extract_urls(text):
    """Витягує всі валідні URL із тексту чи списку"""
    if not text:
        return []
    matches = re.findall(r"https?://[^\s<>\"']+", text)
    cleaned = []
    for u in matches:
        u = u.rstrip(".,;:)\"'>]")
        if u and u not in cleaned:
            cleaned.append(u)
    return cleaned


def get_clipboard_text():
    try:
        res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=1)
        return res.stdout.strip()
    except Exception:
        return ""


def get_clipboard_urls():
    text = get_clipboard_text()
    return extract_urls(text)


def get_clipboard_url():
    urls = get_clipboard_urls()
    return urls[0] if urls else None


def is_playlist_url(url):
    """Визначає, чи є посилання плейлистом або колекцією відео"""
    if not url:
        return False
    u = url.lower()
    if ("youtube.com" in u or "youtu.be" in u) and ("list=" in u or "/playlist" in u):
        return True
    if "soundcloud.com" in u and "/sets/" in u:
        return True
    if "tiktok.com" in u and ("/collection/" in u or "/playlist/" in u):
        return True
    return False


def get_playlist_urls(url, ui_lang="en"):
    """Отримує список посилань на окремі відео з плейлиста без завантаження самих файлів"""
    is_ua = (ui_lang == "ua")
    print(f"\n{YELLOW}{'⏳ Отримую список відео з плейлиста...' if is_ua else '⏳ Fetching playlist video list...'}{RESET}")
    cmd = [
        YT_DLP_BIN,
        "--ffmpeg-location", FFMPEG_BIN_DIR,
        "--flat-playlist",
        "--print", "%(url)s",
        "--no-warnings",
        "--extractor-args", "youtube:player_client=ios,mweb,web;formats=missing_pot",
    ]
    if NODE_BIN and os.path.exists(NODE_BIN):
        cmd.extend(["--js-runtimes", f"node:{NODE_BIN}"])
    elif QJS_BIN and os.path.exists(QJS_BIN):
        cmd.extend(["--js-runtimes", f"quickjs:{QJS_BIN}"])
    cmd.append(url)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if proc.returncode == 0 and proc.stdout.strip():
            urls = []
            for line in proc.stdout.strip().splitlines():
                u = line.strip()
                if not u:
                    continue
                if u.startswith("http://") or u.startswith("https://"):
                    urls.append(u)
                elif "youtube.com" in url or "youtu.be" in url:
                    urls.append(f"https://www.youtube.com/watch?v={u}")
                else:
                    urls.append(u)
            return urls
    except Exception:
        pass
    return []


def send_macos_notification(title, message):
    try:
        t = str(title).replace('"', '\\"').replace('\n', ' ')
        m = str(message).replace('"', '\\"').replace('\n', ' ')
        script = f'display notification "{m}" with title "{t}" sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def get_video_audio_languages(url):
    """Швидке отримання списку доступних мов аудіодоріжок"""
    cmd = [
        YT_DLP_BIN,
        "--ffmpeg-location", FFMPEG_BIN_DIR,
        "--print", "%(formats.:.language)s",
        "--no-warnings",
        "--extractor-args", "youtube:player_client=ios,mweb,web;formats=missing_pot",
    ]
    if NODE_BIN and os.path.exists(NODE_BIN):
        cmd.extend(["--js-runtimes", f"node:{NODE_BIN}"])
    elif QJS_BIN and os.path.exists(QJS_BIN):
        cmd.extend(["--js-runtimes", f"quickjs:{QJS_BIN}"])
    cmd.append(url)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if proc.returncode == 0 and proc.stdout.strip():
            raw_list = ast.literal_eval(proc.stdout.strip())
            langs = sorted(list(set([l for l in raw_list if l and isinstance(l, str)])))
            return langs
    except Exception:
        pass
    return []


def format_lang_name(code):
    names = {
        "uk": "🇺🇦 Українська (Ukrainian)",
        "en": "🇬🇧 English (Original)",
        "en-US": "🇬🇧 English (US)",
        "en-GB": "🇬🇧 English (UK)",
        "de": "🇩🇪 Deutsch (German)",
        "de-DE": "🇩🇪 Deutsch (German)",
        "fr": "🇫🇷 Français (French)",
        "fr-FR": "🇫🇷 Français (French)",
        "es": "🇪🇸 Español (Spanish)",
        "es-US": "🇪🇸 Español (US)",
        "pl": "🇵🇱 Polski (Polish)",
        "it": "🇮🇹 Italiano (Italian)",
        "ja": "🇯🇵 日本語 (Japanese)",
        "ko": "🇰🇷 한국어 (Korean)",
        "pt-BR": "🇧🇷 Português (BR)",
        "ru": "Русский",
    }
    return names.get(code, f"🌐 {code}")


def probe_media(filepath):
    """Отримує детальну інформацію про відео (кодек, pix_fmt, color_range) та аудіо через ffmpeg"""
    if not FFMPEG_BIN or not os.path.exists(FFMPEG_BIN):
        return {"vcodec": None, "acodec": None, "pix_fmt": None, "color_range": "tv"}

    try:
        proc = subprocess.run(
            [FFMPEG_BIN, "-i", filepath],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        output = proc.stderr or ""
        vcodec = None
        acodec = None
        pix_fmt = None
        color_range = "tv"

        for line in output.splitlines():
            line_str = line.strip()
            if "Stream #" in line_str:
                if "Video:" in line_str and not vcodec:
                    parts = [p.strip() for p in line_str.split("Video:")[1].split(",")]
                    if parts:
                        vcodec = parts[0].split()[0].lower()
                    if len(parts) > 1:
                        p1 = parts[1]
                        raw_fmt = p1.split("(")[0].strip().lower()
                        pix_fmt = raw_fmt
                        if "(pc" in p1.lower() or "pc," in p1.lower() or "full" in p1.lower() or "yuvj" in raw_fmt:
                            color_range = "pc"
                        elif "(tv" in p1.lower() or "tv," in p1.lower() or "limited" in p1.lower():
                            color_range = "tv"
                elif "Audio:" in line_str and not acodec:
                    parts = line_str.split("Audio:")[1].strip().split(",")
                    if parts:
                        acodec = parts[0].strip().split()[0].lower()

        return {"vcodec": vcodec, "acodec": acodec, "pix_fmt": pix_fmt, "color_range": color_range}
    except Exception:
        return {"vcodec": None, "acodec": None, "pix_fmt": None, "color_range": "tv"}


def standardize_video_for_quicktime(filepath, ui_lang="en"):
    """
    Гарантує 100% сумісність відеофайлу з Apple QuickTime Player / QuickLook на macOS:
    - Відео: H.264 (yuv420p, Limited/TV range 16-235, BT.709)
    - Очищення застарілого full-range yuvj420p (який викликає чорний екран у QuickLook)
    - Аудіо: AAC (stereo 192k 44.1kHz)
    - Контейнер: MP4 з moov атомом на початку (+faststart)
    - Безпечні параметри без застарілого -vsync (сумісність з FFmpeg 7/8/9)
    """
    if not filepath or not os.path.exists(filepath):
        return filepath

    if not FFMPEG_BIN or not os.path.exists(FFMPEG_BIN):
        return filepath

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in [".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"]:
        return filepath

    is_ua = (ui_lang == "ua")
    probe = probe_media(filepath)
    vcodec = probe.get("vcodec")
    acodec = probe.get("acodec")
    pix_fmt = probe.get("pix_fmt")
    color_range = probe.get("color_range", "tv")

    needs_reencode = False
    if vcodec not in ["h264", "avc1"]:
        needs_reencode = True
    if pix_fmt and (pix_fmt != "yuv420p" or "yuvj" in str(pix_fmt) or color_range == "pc"):
        needs_reencode = True
    if acodec and acodec not in ["aac", "mp3"]:
        needs_reencode = True

    dir_name = os.path.dirname(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    final_path = os.path.join(dir_name, f"{base_name}.mp4")
    temp_path = os.path.join(dir_name, f".temp_qt_{os.path.basename(filepath)}.mp4")

    if needs_reencode:
        msg = "⚡ Оптимізую відео для Apple QuickTime (H.264 / AAC / TV-range)..." if is_ua else "⚡ Optimizing video for Apple QuickTime (H.264 / AAC / TV-range)..."
        print(f"{YELLOW}{msg}{RESET}")
        conv_cmd = [
            FFMPEG_BIN, "-y",
            "-i", filepath,
            "-vf", "scale=in_range=auto:out_range=limited,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-profile:v", "high",
            "-level", "4.1",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            temp_path
        ]
    else:
        msg = "⚡ Фіналізую MP4 контейнер для миттєвого перегляду..." if is_ua else "⚡ Finalizing MP4 container for instant preview..."
        print(f"{YELLOW}{msg}{RESET}")
        conv_cmd = [
            FFMPEG_BIN, "-y",
            "-i", filepath,
            "-c", "copy",
            "-movflags", "+faststart",
            temp_path
        ]

    try:
        res = subprocess.run(conv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            if os.path.exists(final_path) and final_path != filepath:
                try:
                    os.remove(final_path)
                except Exception:
                    pass
            os.rename(temp_path, final_path)
            return final_path
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    return filepath


def download_media(url, mode, selected_lang=None, ui_lang="en", is_batch=False, yes_playlist=False):
    is_ua = (ui_lang == "ua")
    if not is_batch:
        msg_dl = "⏳ Завантажую та оптимізую для Mac (QuickTime H.264/AAC)..." if is_ua else "⏳ Downloading and optimizing for Mac (QuickTime H.264/AAC)..."
        print(f"\n{YELLOW}{msg_dl}{RESET}\n")

    out_template = os.path.join(DOWNLOADS_DIR, "%(title).100s [%(id)s].%(ext)s")

    track_fd, track_path = tempfile.mkstemp(prefix="md_track_", suffix=".txt")
    os.close(track_fd)
    if os.path.exists(track_path):
        os.remove(track_path)

    cmd = [
        YT_DLP_BIN,
        "--ffmpeg-location", FFMPEG_BIN_DIR,
        "--output", out_template,
        "--print-to-file", "after_move:filepath", track_path,
        "--no-warnings",
        "--progress",
        "--extractor-args", "youtube:player_client=ios,mweb,web;formats=missing_pot",
    ]

    if yes_playlist:
        cmd.append("--yes-playlist")
    else:
        cmd.append("--no-playlist")

    if NODE_BIN and os.path.exists(NODE_BIN):
        cmd.extend(["--js-runtimes", f"node:{NODE_BIN}"])
    elif QJS_BIN and os.path.exists(QJS_BIN):
        cmd.extend(["--js-runtimes", f"quickjs:{QJS_BIN}"])

    audio_filter = f"[language={selected_lang}]" if selected_lang else ""

    if mode in ["1", "3"]:
        res_limit = "res:1080" if mode == "1" else "res:720"
        height_filter = "" if mode == "1" else "[height<=720]"
        format_str = f"bestvideo{height_filter}[vcodec^=avc]+bestaudio{audio_filter}[acodec^=mp4a]/bestvideo{height_filter}[vcodec^=avc]+bestaudio{audio_filter}/best[vcodec^=avc]/bestvideo+bestaudio/best"
        cmd.extend([
            "-S", f"vcodec:h264,{res_limit},acodec:m4a,ext:mp4",
            "-f", format_str,
            "--recode-video", "mp4",
        ])
    elif mode == "2":
        format_str = f"bestaudio{audio_filter}/bestaudio/best"
        cmd.extend([
            "-f", format_str,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--embed-metadata",
        ])

    cmd.append(url)

    def process_downloaded_files():
        d_files = []
        if os.path.exists(track_path):
            try:
                with open(track_path, "r", encoding="utf-8") as f:
                    d_files = [line.strip() for line in f if line.strip()]
                os.remove(track_path)
            except Exception:
                pass

        if not d_files:
            try:
                candidates = [
                    os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR)
                    if not f.startswith(".") and os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
                ]
                if candidates:
                    candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    d_files = [candidates[0]]
            except Exception:
                pass

        if mode in ["1", "3"]:
            for df in d_files:
                standardize_video_for_quicktime(df, ui_lang=ui_lang)

    try:
        proc = subprocess.run(cmd)
        if proc.returncode == 0:
            process_downloaded_files()
            if not is_batch:
                msg_ok = "✅ Відео успішно завантажено та готове до перегляду!" if is_ua else "✅ Download completed successfully!"
                print(f"\n{GREEN}{BOLD}{msg_ok}{RESET}")
                print(f"📁 {'Збережено в:' if is_ua else 'Saved to:'} {CYAN}{DOWNLOADS_DIR}{RESET}\n")
                send_macos_notification(
                    "Медіа збережено! 🎉" if is_ua else "Media saved! 🎉",
                    "Відео готове у папці Завантаження" if is_ua else "Video ready in your Downloads folder"
                )
            else:
                msg_ok = "✅ Успішно завантажено та оптимізовано!" if is_ua else "✅ Downloaded and optimized!"
                print(f"{GREEN}{msg_ok}{RESET}")
            return True
        else:
            print(f"\n{YELLOW}{'⚠️ Спроба обходу блокування YouTube через сесію браузера...' if is_ua else '⚠️ Retrying with browser session to bypass YouTube restriction...'}{RESET}")
            browsers = ["chrome", "firefox", "brave", "edge"]
            for b in browsers:
                retry_cmd = list(cmd)
                retry_cmd.insert(-1, "--cookies-from-browser")
                retry_cmd.insert(-1, b)
                proc_retry = subprocess.run(retry_cmd)
                if proc_retry.returncode == 0:
                    process_downloaded_files()
                    if not is_batch:
                        msg_ok = "✅ Відео успішно завантажено та готове до перегляду!" if is_ua else "✅ Download completed successfully!"
                        print(f"\n{GREEN}{BOLD}{msg_ok}{RESET}")
                        print(f"📁 {'Збережено в:' if is_ua else 'Saved to:'} {CYAN}{DOWNLOADS_DIR}{RESET}\n")
                        send_macos_notification(
                            "Медіа збережено! 🎉" if is_ua else "Media saved! 🎉",
                            "Відео готове у папці Завантаження" if is_ua else "Video ready in your Downloads folder"
                        )
                    else:
                        msg_ok = "✅ Успішно завантажено та оптимізовано!" if is_ua else "✅ Downloaded and optimized!"
                        print(f"{GREEN}{msg_ok}{RESET}")
                    return True

            print(f"\n{RED}{BOLD}{'❌ Не вдалося завершити завантаження.' if is_ua else '❌ Download failed.'}{RESET}\n")
            return False
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}\n")
        return False
    finally:
        if os.path.exists(track_path):
            try:
                os.remove(track_path)
            except Exception:
                pass


def download_batch(urls, mode, selected_lang=None, ui_lang="en"):
    """Пакетне послідовне завантаження списку посилань із загальним прогресом"""
    is_ua = (ui_lang == "ua")
    total = len(urls)
    success_count = 0
    failed_urls = []

    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════╗{RESET}")
    if is_ua:
        print(f"{CYAN}{BOLD}║      📦 ПАКЕТНЕ ЗАВАНТАЖЕННЯ ({total} файл.)              ║{RESET}")
    else:
        print(f"{CYAN}{BOLD}║       📦 BATCH DOWNLOAD ({total} files)                  ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════╝{RESET}\n")

    for idx, u in enumerate(urls, 1):
        print(f"\n{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}[{idx}/{total}]{RESET} ⏳ {u}")
        print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

        ok = download_media(u, mode, selected_lang, ui_lang=ui_lang, is_batch=True, yes_playlist=False)
        if ok:
            success_count += 1
            print(f"{GREEN}{BOLD}✔ [{idx}/{total}] {'Готово!' if is_ua else 'Done!'}{RESET}\n")
        else:
            failed_urls.append(u)
            print(f"{RED}{BOLD}✖ [{idx}/{total}] {'Помилка завантаження (пропускаємо)' if is_ua else 'Download failed (skipping)'}{RESET}\n")

    print(f"\n{CYAN}{BOLD}═══════════════════════════════════════════════════{RESET}")
    if is_ua:
        print(f"{GREEN}{BOLD}🎉 Пакетне завантаження завершено!{RESET}")
        print(f"   ✅ Успішно збережено: {BOLD}{success_count} із {total}{RESET}")
        if failed_urls:
            print(f"   ⚠️ Помилок / не вдалося: {BOLD}{len(failed_urls)}{RESET}")
        print(f"   📁 Збережено в: {CYAN}{DOWNLOADS_DIR}{RESET}")
        send_macos_notification(
            "Пакетне завантаження завершено! 🎉",
            f"Успішно збережено {success_count} із {total} файлів"
        )
    else:
        print(f"{GREEN}{BOLD}🎉 Batch download completed!{RESET}")
        print(f"   ✅ Successfully saved: {BOLD}{success_count} of {total}{RESET}")
        if failed_urls:
            print(f"   ⚠️ Failed / skipped: {BOLD}{len(failed_urls)}{RESET}")
        print(f"   📁 Saved to: {CYAN}{DOWNLOADS_DIR}{RESET}")
        send_macos_notification(
            "Batch download finished! 🎉",
            f"Successfully saved {success_count} of {total} files"
        )
    print(f"{CYAN}{BOLD}═══════════════════════════════════════════════════{RESET}\n")
    return success_count


def main():
    ui_lang = get_initial_language()
    cfg = load_config()

    # Автоматична перевірка наявності оновлень при запуску (тихий режим)
    try:
        updated = check_for_updates(ui_lang=ui_lang, silent=True)
        if updated:
            return
    except Exception:
        pass

    next_batch = None
    next_single = None

    while True:
        is_ua = (ui_lang == "ua")
        print_banner(ui_lang)

        current_batch = None
        single_url = None

        if next_batch:
            current_batch = next_batch
            next_batch = None
        elif next_single:
            single_url = next_single
            next_single = None
        else:
            clip_urls = get_clipboard_urls()
            if len(clip_urls) > 1:
                print(f"📋 {BOLD}{f'Виявлено список із {len(clip_urls)} посилань у буфері обміну:' if is_ua else f'Detected list of {len(clip_urls)} links in clipboard:'}{RESET}")
                for i, u in enumerate(clip_urls[:3], 1):
                    print(f"   {i}. {CYAN}{u}{RESET}")
                if len(clip_urls) > 3:
                    print(f"   {GRAY}... {'та ще' if is_ua else 'and'} {len(clip_urls)-3} {'посилань' if is_ua else 'more links'}{RESET}")
                print()
                prompt_text = f"Натисніть [Enter], щоб завантажити всі {len(clip_urls)} файлів пакетно, або вставте інше: " if is_ua else f"Press [Enter] to download all {len(clip_urls)} files in batch, or paste another: "
                ans = input(prompt_text).strip()
                if ans.lower() in ["q", "quit", "exit"]:
                    print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                    break
                elif ans.lower() in ["l", "lang", "language", "мова"]:
                    ui_lang = "en" if is_ua else "ua"
                    cfg["ui_lang"] = ui_lang
                    save_config(cfg)
                    continue
                elif ans.lower() in ["u", "update", "оновлення", "7"]:
                    check_for_updates(ui_lang=ui_lang, silent=False)
                    input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
                    continue
                elif ans == "":
                    current_batch = clip_urls
                else:
                    ext = extract_urls(ans)
                    if len(ext) > 1:
                        current_batch = ext
                    elif len(ext) == 1:
                        single_url = ext[0]
                    else:
                        single_url = ans
            elif len(clip_urls) == 1:
                clip = clip_urls[0]
                print(f"📋 {BOLD}{'Виявлено посилання в буфері обміну:' if is_ua else 'Link detected in clipboard:'}{RESET}")
                print(f"   {CYAN}{clip}{RESET}\n")
                prompt_text = "Натисніть [Enter], щоб використати його, або вставте інше: " if is_ua else "Press [Enter] to use it, or paste another: "
                ans = input(prompt_text).strip()
                if ans.lower() in ["q", "quit", "exit"]:
                    print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                    break
                elif ans.lower() in ["l", "lang", "language", "мова"]:
                    ui_lang = "en" if is_ua else "ua"
                    cfg["ui_lang"] = ui_lang
                    save_config(cfg)
                    continue
                elif ans.lower() in ["u", "update", "оновлення", "7"]:
                    check_for_updates(ui_lang=ui_lang, silent=False)
                    input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
                    continue
                elif ans == "":
                    single_url = clip
                else:
                    ext = extract_urls(ans)
                    if len(ext) > 1:
                        current_batch = ext
                    elif len(ext) == 1:
                        single_url = ext[0]
                    else:
                        single_url = ans
            else:
                prompt_text = "Вставте посилання на відео/плейлист або список (чи [q] вихід): " if is_ua else "Paste video/playlist link or URL list (or [q] quit): "
                ans = input(prompt_text).strip()
                if ans.lower() in ["q", "quit", "exit"]:
                    print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                    break
                elif ans.lower() in ["l", "lang", "language", "мова"]:
                    ui_lang = "en" if is_ua else "ua"
                    cfg["ui_lang"] = ui_lang
                    save_config(cfg)
                    continue
                elif ans.lower() in ["u", "update", "оновлення", "7"]:
                    check_for_updates(ui_lang=ui_lang, silent=False)
                    input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
                    continue
                ext = extract_urls(ans)
                if len(ext) > 1:
                    current_batch = ext
                elif len(ext) == 1:
                    single_url = ext[0]
                else:
                    single_url = ans

        if not current_batch and not single_url:
            continue

        # Пакетний режим для списку посилань
        if current_batch:
            print(f"\n{BOLD}{f'Оберіть формат для пакетного завантаження ({len(current_batch)} файлів):' if is_ua else f'Choose format for batch download ({len(current_batch)} files):'}{RESET}")
            print(f" {GREEN}[1]{RESET} 🎬 {'Відео MP4 (Найвища якість 1080p, QuickTime)' if is_ua else 'Video MP4 (Highest quality 1080p, QuickTime)'}")
            print(f" {GREEN}[2]{RESET} 🎵 {'Лише музика / аудіо (MP3 320 kbps)' if is_ua else 'Audio only (MP3 320 kbps)'}")
            print(f" {GREEN}[3]{RESET} ⚡ {'Швидке відео MP4 (720p HD)' if is_ua else 'Fast video MP4 (720p HD)'}")
            print(f" {RED}[0]{RESET} ❌ {'Скасувати' if is_ua else 'Cancel'}")

            bchoice = input(f"\n{'Ваш вибір [1/2/3]' if is_ua else 'Your choice [1/2/3]'} (default 1): ").strip().lower()
            if bchoice == "0":
                continue
            elif bchoice == "2":
                target_mode = "2"
            elif bchoice == "3":
                target_mode = "3"
            else:
                target_mode = "1"

            download_batch(current_batch, target_mode, None, ui_lang)

            print(f"{CYAN}───────────────────────────────────────────────────{RESET}")
            next_prompt = "Вставте наступне посилання або список, або натисніть [Enter] (чи [q] вихід): " if is_ua else "Paste next link or list, or press [Enter] (or [q] quit): "
            nxt = input(next_prompt).strip()
            if nxt.lower() in ["q", "quit", "exit"]:
                print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                break
            elif nxt.lower() in ["l", "lang", "мова"]:
                ui_lang = "en" if is_ua else "ua"
                cfg["ui_lang"] = ui_lang
                save_config(cfg)
            elif nxt.lower() in ["u", "update", "7"]:
                check_for_updates(ui_lang=ui_lang, silent=False)
                input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
            else:
                ext_nxt = extract_urls(nxt)
                if len(ext_nxt) > 1:
                    next_batch = ext_nxt
                elif len(ext_nxt) == 1:
                    next_single = ext_nxt[0]
            continue

        # Якщо одне посилання — перевіряємо, чи це плейлист
        if is_playlist_url(single_url):
            print(f"\n{BOLD}{'📋 Виявлено посилання на плейлист!' if is_ua else '📋 Playlist link detected!'}{RESET}")
            print(f"   {CYAN}{single_url}{RESET}\n")
            print(f" {GREEN}[1]{RESET} 📦 {'Завантажити весь плейлист (усі відео по черзі)' if is_ua else 'Download entire playlist (all videos sequentially)'}")
            print(f" {GREEN}[2]{RESET} 🎬 {'Завантажити лише одне поточне відео' if is_ua else 'Download only single current video'}")
            print(f" {RED}[0]{RESET} ❌ {'Скасувати' if is_ua else 'Cancel'}")

            pl_choice = input(f"\n{'Ваш вибір [1/2]' if is_ua else 'Your choice [1/2]'} (default 1): ").strip().lower()
            if pl_choice == "0":
                continue
            elif pl_choice in ["", "1"]:
                pl_urls = get_playlist_urls(single_url, ui_lang=ui_lang)
                if pl_urls:
                    print(f"\n{BOLD}{f'Оберіть формат для плейлиста ({len(pl_urls)} відео):' if is_ua else f'Choose format for playlist ({len(pl_urls)} videos):'}{RESET}")
                    print(f" {GREEN}[1]{RESET} 🎬 {'Відео MP4 (Найвища якість 1080p, QuickTime)' if is_ua else 'Video MP4 (Highest quality 1080p, QuickTime)'}")
                    print(f" {GREEN}[2]{RESET} 🎵 {'Лише музика / аудіо (MP3 320 kbps)' if is_ua else 'Audio only (MP3 320 kbps)'}")
                    print(f" {GREEN}[3]{RESET} ⚡ {'Швидке відео MP4 (720p HD)' if is_ua else 'Fast video MP4 (720p HD)'}")
                    print(f" {RED}[0]{RESET} ❌ {'Скасувати' if is_ua else 'Cancel'}")

                    bchoice = input(f"\n{'Ваш вибір [1/2/3]' if is_ua else 'Your choice [1/2/3]'} (default 1): ").strip().lower()
                    if bchoice == "0":
                        continue
                    elif bchoice == "2":
                        target_mode = "2"
                    elif bchoice == "3":
                        target_mode = "3"
                    else:
                        target_mode = "1"

                    download_batch(pl_urls, target_mode, None, ui_lang)
                else:
                    print(f"\n{YELLOW}{'Завантажую весь плейлист напряму...' if is_ua else 'Downloading playlist directly...'}{RESET}")
                    download_media(single_url, "1", None, ui_lang, is_batch=False, yes_playlist=True)

                print(f"{CYAN}───────────────────────────────────────────────────{RESET}")
                next_prompt = "Вставте наступне посилання або список, або натисніть [Enter] (чи [q] вихід): " if is_ua else "Paste next link or list, or press [Enter] (or [q] quit): "
                nxt = input(next_prompt).strip()
                if nxt.lower() in ["q", "quit", "exit"]:
                    print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                    break
                elif nxt.lower() in ["l", "lang", "мова"]:
                    ui_lang = "en" if is_ua else "ua"
                    cfg["ui_lang"] = ui_lang
                    save_config(cfg)
                elif nxt.lower() in ["u", "update", "7"]:
                    check_for_updates(ui_lang=ui_lang, silent=False)
                    input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
                else:
                    ext_nxt = extract_urls(nxt)
                    if len(ext_nxt) > 1:
                        next_batch = ext_nxt
                    elif len(ext_nxt) == 1:
                        next_single = ext_nxt[0]
                continue

        # Звичайне одиночне завантаження
        selected_lang = None
        print(f"🔗 {BOLD}URL:{RESET}\n   {CYAN}{single_url}{RESET}\n")
        print(f"{BOLD}{'Оберіть бажаний формат:' if is_ua else 'Choose format:'}{RESET}")
        print(f" {GREEN}[1]{RESET} 🎬 {'Відео MP4 (Найвища якість 1080p, QuickTime)' if is_ua else 'Video MP4 (Highest quality 1080p, QuickTime)'}")
        print(f" {GREEN}[2]{RESET} 🎵 {'Лише музика / аудіо (MP3 320 kbps)' if is_ua else 'Audio only (MP3 320 kbps)'}")
        print(f" {GREEN}[3]{RESET} 🌐 {BOLD}{'Обрати мову дубляжу для YouTube' if is_ua else 'Choose audio dubbing language (YouTube)'}{RESET}")
        print(f" {GREEN}[4]{RESET} ⚡ {'Швидке відео MP4 (720p HD)' if is_ua else 'Fast video MP4 (720p HD)'}")
        print(f" {CYAN}[5]{RESET} 📦 {'Пакетне завантаження (вставити кілька посилань)' if is_ua else 'Batch download (paste multiple links)'}")
        print(f" {CYAN}[6]{RESET} 🌍 {'Змінити мову інтерфейсу на English' if is_ua else 'Switch interface language to Українська'}")
        print(f" {CYAN}[7]{RESET} 🔄 {'Перевірити наявність оновлень' if is_ua else 'Check for updates'}")
        print(f" {RED}[0]{RESET} ❌ {'Скасувати' if is_ua else 'Cancel'}")

        choice = input(f"\n{'Ваш вибір [1/2/3/4/5/6/7]' if is_ua else 'Your choice [1/2/3/4/5/6/7]'} (default 1): ").strip().lower()

        if choice == "0":
            continue
        elif choice in ["6", "l", "lang", "language", "мова"]:
            ui_lang = "en" if is_ua else "ua"
            cfg["ui_lang"] = ui_lang
            save_config(cfg)
            next_single = single_url
            continue
        elif choice in ["7", "u", "update", "оновлення"]:
            check_for_updates(ui_lang=ui_lang, silent=False)
            input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
            next_single = single_url
            continue
        elif choice in ["5", "b", "batch"]:
            p_text = "Вставте кілька посилань через пробіл або новий рядок (або натисніть [Enter] для посилань з буфера): " if is_ua else "Paste multiple links separated by space or newline (or press [Enter] to use clipboard): "
            b_in = input(p_text).strip()
            if not b_in:
                clip_b = get_clipboard_urls()
                if clip_b:
                    next_batch = clip_b
                else:
                    print(f"{YELLOW}{'У буфері обміну немає посилань.' if is_ua else 'No links found in clipboard.'}{RESET}")
            else:
                ext_b = extract_urls(b_in)
                if ext_b:
                    next_batch = ext_b
                else:
                    print(f"{RED}{'Не знайдено валідних посилань.' if is_ua else 'No valid URLs found.'}{RESET}")
            continue
        elif choice == "3":
            print(f"\n{YELLOW}{'⏳ Отримую список доступних мов озвучки...' if is_ua else '⏳ Fetching available audio languages...'}{RESET}")
            available_langs = get_video_audio_languages(single_url)

            if available_langs:
                print(f"\n{BOLD}{'Знайдено такі мови аудіо:' if is_ua else 'Available audio tracks:'}{RESET}")
                priority = ["en-US", "en", "uk"] if not is_ua else ["uk", "en-US", "en"]
                sorted_langs = [k for k in priority if k in available_langs] + [k for k in available_langs if k not in priority]

                for idx, lk in enumerate(sorted_langs, 1):
                    star = " ★" if lk in ["uk", "en-US", "en"] else ""
                    print(f"  [{idx}] {format_lang_name(lk)}{star}")

                lang_ans = input(f"\n{'Оберіть номер мови' if is_ua else 'Choose language number'} (1-{len(sorted_langs)}): ").strip()
                if lang_ans.isdigit() and 1 <= int(lang_ans) <= len(sorted_langs):
                    selected_lang = sorted_langs[int(lang_ans) - 1]
                else:
                    selected_lang = sorted_langs[0]
                print(f"👉 {'Обрано' if is_ua else 'Selected'}: {BOLD}{format_lang_name(selected_lang)}{RESET}\n")

                fmt_sub = input(f"{'Зберегти як: [1] Відео MP4 чи [2] Музику MP3? (за замовчуванням 1): ' if is_ua else 'Save as: [1] Video MP4 or [2] Audio MP3? (default 1): '}").strip()
                target_mode = "2" if fmt_sub == "2" else "1"
                download_media(single_url, target_mode, selected_lang, ui_lang, is_batch=False, yes_playlist=False)
            else:
                print(f"\n{YELLOW}{'У цього відео стандартна єдина аудіодоріжка.' if is_ua else 'This video only has a single standard audio track.'}{RESET}")
                download_media(single_url, "1", None, ui_lang, is_batch=False, yes_playlist=False)
        elif choice == "2":
            download_media(single_url, "2", None, ui_lang, is_batch=False, yes_playlist=False)
        elif choice == "4":
            download_media(single_url, "3", None, ui_lang, is_batch=False, yes_playlist=False)
        else:
            download_media(single_url, "1", None, ui_lang, is_batch=False, yes_playlist=False)

        print(f"{CYAN}───────────────────────────────────────────────────{RESET}")
        next_prompt = "Вставте наступне посилання або список, або натисніть [Enter] (чи [q] вихід): " if is_ua else "Paste next link or list, or press [Enter] (or [q] quit): "
        nxt = input(next_prompt).strip()
        if nxt.lower() in ["q", "quit", "exit"]:
            print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
            break
        elif nxt.lower() in ["l", "lang", "мова"]:
            ui_lang = "en" if is_ua else "ua"
            cfg["ui_lang"] = ui_lang
            save_config(cfg)
        elif nxt.lower() in ["u", "update", "7"]:
            check_for_updates(ui_lang=ui_lang, silent=False)
            input(f"\n{'Натисніть [Enter], щоб продовжити...' if is_ua else 'Press [Enter] to continue...'}")
        else:
            ext_nxt = extract_urls(nxt)
            if len(ext_nxt) > 1:
                next_batch = ext_nxt
            elif len(ext_nxt) == 1:
                next_single = ext_nxt[0]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
