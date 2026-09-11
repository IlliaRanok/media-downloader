#!/usr/bin/env python3
"""
Media Downloader (YouTube, TikTok, Instagram, Twitter/X etc.)
- 100% QuickTime Player compatibility on macOS (H.264 / AAC / MP3)
- First-run language setup (Default: English) with persistent config
- Audio dubbing language selector (Ukrainian, English, etc.)
- Classic high-visibility banner
"""

import sys
import os
import ast
import json
import subprocess
import shutil

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
        print("║          📥 МЕДІА-ЗАВАНТАЖУВАЧ (1-КЛІК)           ║")
        print("║    YouTube • TikTok • Instagram • Twitter • Web   ║")
    else:
        print("║            📥 MEDIA DOWNLOADER (1-CLICK)          ║")
        print("║    YouTube • TikTok • Instagram • Twitter • Web   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"{RESET}")


def get_initial_language():
    """Запитує мову лише один раз при першому вході, за замовчуванням англійська"""
    cfg = load_config()
    if "ui_lang" in cfg:
        return cfg["ui_lang"]

    clear_screen()
    print(f"{CYAN}{BOLD}")
    print("╔═══════════════════════════════════════════════════╗")
    print("║            📥 MEDIA DOWNLOADER (1-CLICK)          ║")
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


def get_clipboard_url():
    try:
        res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=1)
        text = res.stdout.strip()
        if text.startswith("http://") or text.startswith("https://"):
            return text
    except Exception:
        pass
    return None


def send_macos_notification(title, message):
    try:
        script = f'display notification "{message}" with title "{title}" sound name "Glass"'
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

    # QuickTime підтримує h264/avc1. Не підтримує vp9, av1/av01, hevc без hvc1 тега тощо.
    # Також QuickLook малює чорне прев'ю, якщо pix_fmt - це застарілий full-range yuvj420p або pc-range!
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


def download_media(url, mode, selected_lang, ui_lang="en"):
    import tempfile
    is_ua = (ui_lang == "ua")
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
            msg_ok = "✅ Відео успішно завантажено та готове до перегляду!" if is_ua else "✅ Download completed successfully!"
            print(f"\n{GREEN}{BOLD}{msg_ok}{RESET}")
            print(f"📁 {'Збережено в:' if is_ua else 'Saved to:'} {CYAN}{DOWNLOADS_DIR}{RESET}\n")
            send_macos_notification(
                "Медіа збережено! 🎉" if is_ua else "Media saved! 🎉",
                "Відео готове у папці Завантаження" if is_ua else "Video ready in your Downloads folder"
            )
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
                    msg_ok = "✅ Відео успішно завантажено та готове до перегляду!" if is_ua else "✅ Download completed successfully!"
                    print(f"\n{GREEN}{BOLD}{msg_ok}{RESET}")
                    print(f"📁 {'Збережено в:' if is_ua else 'Saved to:'} {CYAN}{DOWNLOADS_DIR}{RESET}\n")
                    send_macos_notification(
                        "Медіа збережено! 🎉" if is_ua else "Media saved! 🎉",
                        "Відео готове у папці Завантаження" if is_ua else "Video ready in your Downloads folder"
                    )
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


def main():
    ui_lang = get_initial_language()
    cfg = load_config()
    next_url = None

    while True:
        is_ua = (ui_lang == "ua")
        print_banner(ui_lang)

        url = ""
        if next_url:
            url = next_url
            next_url = None
            print(f"🔗 {BOLD}URL:{RESET}\n   {CYAN}{url}{RESET}\n")
        else:
            clip = get_clipboard_url()
            if clip:
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
                elif ans == "":
                    url = clip
                else:
                    url = ans
            else:
                prompt_text = "Вставте посилання на відео/аудіо (або [q] вихід): " if is_ua else "Paste video/audio link (or [q] quit): "
                ans = input(prompt_text).strip()
                if ans.lower() in ["q", "quit", "exit"]:
                    print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
                    break
                elif ans.lower() in ["l", "lang", "language", "мова", "5"]:
                    ui_lang = "en" if is_ua else "ua"
                    cfg["ui_lang"] = ui_lang
                    save_config(cfg)
                    continue
                url = ans

        if not url:
            continue

        selected_lang = None

        print(f"\n{BOLD}{'Оберіть бажаний формат:' if is_ua else 'Choose format:'}{RESET}")
        print(f" {GREEN}[1]{RESET} 🎬 {'Відео MP4 (Найвища якість 1080p, QuickTime)' if is_ua else 'Video MP4 (Highest quality 1080p, QuickTime)'}")
        print(f" {GREEN}[2]{RESET} 🎵 {'Лише музика / аудіо (MP3 320 kbps)' if is_ua else 'Audio only (MP3 320 kbps)'}")
        print(f" {GREEN}[3]{RESET} 🌐 {BOLD}{'Обрати мову дубляжу для YouTube' if is_ua else 'Choose audio dubbing language (YouTube)'}{RESET}")
        print(f" {GREEN}[4]{RESET} ⚡ {'Швидке відео MP4 (720p HD)' if is_ua else 'Fast video MP4 (720p HD)'}")
        print(f" {CYAN}[5]{RESET} 🌍 {'Змінити мову інтерфейсу на English' if is_ua else 'Switch interface language to Українська'}")
        print(f" {RED}[0]{RESET} ❌ {'Скасувати' if is_ua else 'Cancel'}")

        choice = input(f"\n{'Ваш вибір [1/2/3/4/5]' if is_ua else 'Your choice [1/2/3/4/5]'} (default 1): ").strip().lower()

        if choice == "0":
            continue
        elif choice in ["5", "l", "lang", "language", "мова"]:
            ui_lang = "en" if is_ua else "ua"
            cfg["ui_lang"] = ui_lang
            save_config(cfg)
            next_url = url
            continue
        elif choice == "3":
            print(f"\n{YELLOW}{'⏳ Отримую список доступних мов озвучки...' if is_ua else '⏳ Fetching available audio languages...'}{RESET}")
            available_langs = get_video_audio_languages(url)

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
                download_media(url, target_mode, selected_lang, ui_lang)
            else:
                print(f"\n{YELLOW}{'У цього відео стандартна єдина аудіодоріжка.' if is_ua else 'This video only has a single standard audio track.'}{RESET}")
                download_media(url, "1", None, ui_lang)
        elif choice == "2":
            download_media(url, "2", None, ui_lang)
        elif choice == "4":
            download_media(url, "3", None, ui_lang)
        else:
            download_media(url, "1", None, ui_lang)

        print(f"{CYAN}───────────────────────────────────────────────────{RESET}")
        next_prompt = "Вставте наступне посилання, або натисніть [Enter] (чи [q] вихід): " if is_ua else "Paste next link, or press [Enter] (or [q] quit): "
        nxt = input(next_prompt).strip()
        if nxt.lower() in ["q", "quit", "exit"]:
            print("\nДо зустрічі!" if is_ua else "\nGoodbye!")
            break
        elif nxt.lower() in ["l", "lang", "мова"]:
            ui_lang = "en" if is_ua else "ua"
            cfg["ui_lang"] = ui_lang
            save_config(cfg)
            next_url = None
        elif nxt.startswith("http://") or nxt.startswith("https://"):
            next_url = nxt
        else:
            next_url = None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
