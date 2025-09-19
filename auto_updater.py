import os
import json
import threading
import time
import traceback
import urllib.request
import urllib.error
import shutil
import tempfile
from datetime import datetime, timezone

# --- Alap konfiguráció ---
OWNER = "HeadTDev"
REPO = "dataprocessingtool"
BRANCH = "main"

VERSION_FILE = "version.json"
LOG_FILE = "update_log.txt"

CHECK_TIMEOUT = 6
USER_AGENT = f"AutoUpdater/1.1 (+https://github.com/{OWNER}/{REPO})"
DEBUG = True

ALLOW_ZIP_FALLBACK = True
INCREMENTAL_DEFAULT = True

# Alapértelmezett (headless) UI callback-ek – ezek lecserélhetők PySide6 integrációnál
def _default_prompt(question: str) -> bool:
    log(f"[PROMPT] {question} (auto: yes)")
    return True

def _default_info(msg: str):
    log(f"[INFO] {msg}")

def _default_error(msg: str):
    log(f"[ERROR] {msg}")

def log(msg: str):
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"[{timestamp}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if DEBUG:
        print(line)


def read_local_version():
    if not os.path.exists(VERSION_FILE):
        return None
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("commit")
    except Exception:
        return None


def write_local_version(commit_sha: str):
    data = {
        "commit": commit_sha,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    tmp = VERSION_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, VERSION_FILE)


def _build_request(url: str):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json"
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def http_get_json(url: str):
    req = _build_request(url)
    with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return json.loads(text)


def http_get_bytes(url: str):
    req = _build_request(url)
    with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
        return resp.read()


def get_remote_latest_commit():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{BRANCH}"
    data = http_get_json(url)
    sha = data.get("sha")
    if not sha:
        raise RuntimeError("Nem talált SHA-t a commit lekérdezésben.")
    return sha


def compare_commits(base_sha: str, head_sha: str):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/compare/{base_sha}...{head_sha}"
    data = http_get_json(url)
    if "files" not in data:
        raise RuntimeError("Nincs 'files' kulcs a compare válaszban.")
    return data


def download_file_raw(commit_sha: str, path: str) -> bytes:
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{path}"
    return http_get_bytes(raw_url)


def apply_incremental_update(changed_files: list, head_sha: str):
    for fentry in changed_files:
        status = fentry.get("status")
        filename = fentry.get("filename")
        prev_name = fentry.get("previous_filename")
        log(f"Fájl: {filename} (status={status})")

        if status in ("added", "modified"):
            try:
                content = download_file_raw(head_sha, filename)
            except Exception as e:
                raise RuntimeError(f"Nem sikerült letölteni: {filename}: {e}")

            target_dir = os.path.dirname(filename)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            tmp_path = filename + ".autoupdate_tmp"
            with open(tmp_path, "wb") as f:
                f.write(content)
            if os.path.exists(filename):
                os.remove(filename)
            os.replace(tmp_path, filename)

        elif status == "removed":
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    log(f"Nem sikerült törölni: {filename}: {e}")

        elif status == "renamed":
            if prev_name and os.path.exists(prev_name):
                try:
                    os.remove(prev_name)
                except Exception as e:
                    log(f"Nem sikerült törölni (rename előző): {prev_name}: {e}")
            try:
                content = download_file_raw(head_sha, filename)
            except Exception as e:
                raise RuntimeError(f"Nem sikerült letölteni (rename): {filename}: {e}")
            target_dir = os.path.dirname(filename)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            with open(filename, "wb") as f:
                f.write(content)
        else:
            log(f"Ismeretlen státusz (kihagyva): {status} - {filename}")


def download_full_zip_and_extract():
    zip_url = f"https://codeload.github.com/{OWNER}/{REPO}/zip/refs/heads/{BRANCH}"
    log("Teljes ZIP letöltése...")
    zip_bytes = http_get_bytes(zip_url)

    with tempfile.TemporaryDirectory() as td:
        zip_path = os.path.join(td, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            root_dir_prefix = f"{REPO}-{BRANCH}/"
            for member in zf.namelist():
                if not member.startswith(root_dir_prefix):
                    continue
                rel_path = member[len(root_dir_prefix):]
                if not rel_path:
                    continue
                if rel_path in (VERSION_FILE, LOG_FILE):
                    # Ezeket nem írjuk felül
                    pass
                target_path = os.path.join(os.getcwd(), rel_path)
                if member.endswith("/"):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(member, "r") as src, open(target_path + ".autoupdate_tmp", "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.replace(target_path + ".autoupdate_tmp", target_path)
    log("Teljes ZIP frissítés kész.")


def perform_update_flow(
    incremental_preferred=True,
    ui_prompt=_default_prompt,
    ui_info=_default_info,
    ui_error=_default_error,
    run_in_thread=False,
    delay_seconds=1.5
):
    """
    ui_prompt(question)->bool
    ui_info(msg)
    ui_error(msg)
    run_in_thread: ha True, háttérszálban fut (a UI callback-eket ilyenkor thread-safe módon kell biztosítanod).
    """
    def _work():
        time.sleep(delay_seconds)
        local_sha = read_local_version()
        log(f"Helyi verzió: {local_sha}")
        try:
            remote_sha = get_remote_latest_commit()
            log(f"Távoli (main) legújabb: {remote_sha}")
        except Exception as e:
            log(f"Nem sikerült lekérdezni a távoli commitot: {e}")
            return

        if local_sha == remote_sha:
            log("Nincs új frissítés (azonos SHA).")
            return

        need_full = False
        if not local_sha:
            log("Nincs helyi verzió (version.json üres). Inicializálás...")
            try:
                # Ellenőrzés: remote_sha vs remote_sha -> 0 diff
                compare_commits(remote_sha, remote_sha)
                write_local_version(remote_sha)
                log("Verzió inicializálva.")
                return
            except Exception:
                need_full = True

        if not need_full and incremental_preferred and local_sha:
            try:
                compare_data = compare_commits(local_sha, remote_sha)
                ahead_by = compare_data.get("ahead_by")
                files = compare_data.get("files", [])
                log(f"Compare ahead_by={ahead_by}, módosult={len(files)}")

                if ahead_by == 0:
                    write_local_version(remote_sha)
                    log("Verzió meta frissítve (no diff).")
                    return

                if ui_prompt(f"Új verzió érhető el ({ahead_by} commit). Frissíted most?"):
                    try:
                        apply_incremental_update(files, remote_sha)
                        write_local_version(remote_sha)
                        ui_info("Frissítés sikeres (inkrementális). Indítsd újra az alkalmazást a teljes érvényesüléshez.")
                    except Exception as e:
                        log(f"Inkrementális frissítés hiba: {e}")
                        log(traceback.format_exc())
                        if ALLOW_ZIP_FALLBACK and ui_prompt("Inkrementális frissítés nem sikerült. Teljes ZIP frissítés?"):
                            try:
                                download_full_zip_and_extract()
                                write_local_version(remote_sha)
                                ui_info("Teljes frissítés sikeres. Indítsd újra az alkalmazást.")
                            except Exception as ee:
                                ui_error(f"Teljes frissítés hibás: {ee}")
                        else:
                            ui_error(f"Frissítés nem sikerült: {e}")
                else:
                    log("Felhasználó elutasította a frissítést.")
                return
            except urllib.error.HTTPError as he:
                log(f"Compare HTTP hiba: {he}")
                need_full = True
            except Exception as e:
                log(f"Compare hiba: {e}")
                need_full = True

        if need_full or not incremental_preferred:
            if ui_prompt("Differenciális frissítés nem elérhető. Letöltöd a teljes új verziót?"):
                try:
                    download_full_zip_and_extract()
                    write_local_version(remote_sha)
                    ui_info("Teljes frissítés kész. Indítsd újra az alkalmazást.")
                except Exception as e:
                    ui_error(f"Teljes frissítés hiba: {e}")
            else:
                log("Felhasználó elutasította a teljes frissítést.")

    if run_in_thread:
        t = threading.Thread(target=_work, name="AutoUpdaterThread", daemon=True)
        t.start()
    else:
        _work()