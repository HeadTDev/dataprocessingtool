import os
import json
import urllib.request
import urllib.error
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.config.constants import GITHUB_OWNER, GITHUB_REPO, UPDATE_LOG_FILE, VERSION_FILE as VERSION_FILE_NAME
from app.config.paths import PROJECT_ROOT
from app.config.settings import ALLOW_PRERELEASES, USER_AGENT
from app.backend.services.logging_service import get_logger

OWNER = GITHUB_OWNER
REPO = GITHUB_REPO
VERSION_FILE = str(PROJECT_ROOT / VERSION_FILE_NAME)
PROTECTED_UPDATE_PATHS = {VERSION_FILE_NAME, "update_log.txt", f"logs/update/{UPDATE_LOG_FILE}"}

CHECK_TIMEOUT = 8

_logger = get_logger("update")


def log(msg: str):
    _logger.info(msg)


def safe_json_load(path: str):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def read_local_version_info():
    data = safe_json_load(VERSION_FILE)
    # Régi formátum kompatibilitás (ha csak commit volt)
    version = data.get("version") or data.get("tag") or ""
    commit = data.get("commit") or data.get("sha") or ""
    return {
        "version": version,
        "commit": commit,
        "last_updated": data.get("last_updated", "")
    }


def write_local_version(version_tag: str, commit_sha: str):
    data = {
        "version": version_tag,
        "commit": commit_sha,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    tmp = VERSION_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, VERSION_FILE)


def _build_request(url: str, accept_json=True):
    headers = {
        "User-Agent": USER_AGENT,
    }
    if accept_json:
        headers["Accept"] = "application/vnd.github+json"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def http_get_json(url: str):
    req = _build_request(url, accept_json=True)
    with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return json.loads(text)


def http_get_bytes(url: str):
    req = _build_request(url, accept_json=False)
    with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
        return resp.read()


def get_latest_release():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases?per_page=10"
    data = http_get_json(url)
    if isinstance(data, list):
        for rel in data:
            if rel.get("draft"):
                continue
            if rel.get("prerelease") and not ALLOW_PRERELEASES:
                continue
            return rel
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
    return http_get_json(url)  # tartalmaz: tag_name, name, body, zipball_url, target_commitish, etc.


def get_commit_sha_for_tag(tag_name: str):
    # A /commits/{ref} endpoint a ref alapján commit objektumot ad (tag/branch/sha)
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{tag_name}"
    data = http_get_json(url)
    sha = data.get("sha")
    if not sha:
        raise RuntimeError("Nem talált commit SHA-t a tag-hez.")
    return sha


def compare_commits(base_sha: str, head_sha: str):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/compare/{base_sha}...{head_sha}"
    data = http_get_json(url)
    if "files" not in data:
        raise RuntimeError("Compare válaszban nincs 'files'.")
    return data


def download_file_raw(commit_sha: str, path: str) -> bytes:
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{path}"
    return http_get_bytes(raw_url)


def apply_incremental_update(
    changed_files: list[dict[str, Any]],
    head_sha: str,
    progress_cb: Callable[[str, int, int, bool], None] | None = None,
):
    total = len(changed_files)
    for idx, fentry in enumerate(changed_files, start=1):
        if progress_cb:
            progress_cb("Fajlok frissitese...", idx, total, False)
        status = fentry.get("status")
        filename = fentry.get("filename")
        prev_name = fentry.get("previous_filename")
        log(f"File: {filename} (status={status})")
        if not isinstance(filename, str) or not filename:
            log("Missing or invalid filename, skipping.")
            continue

        if filename.replace("\\", "/") in PROTECTED_UPDATE_PATHS:
            log(f"Protected file skipped: {filename}")
            continue

        target_path = PROJECT_ROOT / filename

        if status in ("added", "modified"):
            try:
                content = download_file_raw(head_sha, filename)
            except Exception as e:
                raise RuntimeError(f"Nem sikerült letölteni: {filename}: {e}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = Path(str(target_path) + ".autoupdate_tmp")
            with open(tmp_path, "wb") as f:
                f.write(content)
            if target_path.exists():
                target_path.unlink()
            os.replace(tmp_path, target_path)

        elif status == "removed":
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception as e:
                    log(f"Delete error: {filename}: {e}")

        elif status == "renamed":
            if isinstance(prev_name, str) and prev_name.replace("\\", "/") not in PROTECTED_UPDATE_PATHS:
                prev_path = PROJECT_ROOT / prev_name
                if prev_path.exists():
                    try:
                        prev_path.unlink()
                    except Exception as e:
                        log(f"Rename previous-file delete error: {prev_name}: {e}")
            try:
                content = download_file_raw(head_sha, filename)
            except Exception as e:
                raise RuntimeError(f"Nem sikerült (rename) letölteni: {filename}: {e}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
        else:
            log(f"Unknown status: {status} - {filename}")


def download_release_zip(
    zip_url: str,
    progress_cb: Callable[[str, int, int, bool], None] | None = None,
):
    log("Downloading release ZIP...")
    with tempfile.TemporaryDirectory() as td:
        zip_path = os.path.join(td, "rel.zip")
        req = _build_request(zip_url, accept_json=False)
        with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp, open(zip_path, "wb") as f:
            total = resp.headers.get("Content-Length")
            try:
                total = int(total) if total else -1
            except ValueError:
                total = -1
            downloaded = 0
            chunk_size = 1024 * 64
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb("Letoltes...", downloaded, total, False)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            # A zipball_url általában <owner>-<repo>-<sha> / vagy hasonló root mappa
            # Nem tudjuk pontos prefixet, ezért az első szintet eltávolítjuk.
            names = zf.namelist()
            if not names:
                raise RuntimeError("Üres ZIP.")
            root_prefix = os.path.commonprefix(names)
            # Ha a root_prefix nem könyvtár, próbáljuk első elem alapján.
            if not root_prefix.endswith("/"):
                # keresünk egy '/' első előfordulást az első névben
                first = names[0]
                if "/" in first:
                    root_prefix = first.split("/")[0] + "/"
                else:
                    root_prefix = ""
            for member in names:
                if member.endswith("/"):
                    continue
                rel_path = member
                if root_prefix and rel_path.startswith(root_prefix):
                    rel_path = rel_path[len(root_prefix):]
                if not rel_path:  # gyökér
                    continue
                rel_path = rel_path.replace("\\", "/")
                if rel_path in PROTECTED_UPDATE_PATHS:
                    continue
                target_path = PROJECT_ROOT / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = Path(str(target_path) + ".autoupdate_tmp")
                with zf.open(member, "r") as src, open(tmp_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target_path.exists():
                    target_path.unlink()
                os.replace(tmp_path, target_path)
    log("Release ZIP extracted.")


def check_update_available():
    """Checks GitHub for a newer release than what's recorded in version.json.

    Runs on every app startup - no local caching/rate-limit gate. A GitHub
    API call on each launch is cheap and well within anonymous rate limits
    for normal desktop-app usage; a gate here previously lived in version.json
    itself, which made it possible to silently break the update check by
    editing/deleting that file (see git history).

    If there's no local version recorded at all (missing/corrupted
    version.json), this reports an update as available rather than silently
    initializing the file - always going through the real, verified download
    path instead of ever guessing that the install is already current.
    """
    local = read_local_version_info()
    local_tag = local.get("version") or ""

    try:
        release = get_latest_release()
    except Exception as e:
        log(f"Update check error: {e}")
        return False, None

    remote_tag = release.get("tag_name") or ""
    if not remote_tag:
        return False, None

    if local_tag != remote_tag:
        return True, release

    return False, None


def do_update(release, progress_cb=None):
    local = read_local_version_info()
    local_commit = local.get("commit") or ""
    remote_tag = release.get("tag_name")
    remote_commit_sha = get_commit_sha_for_tag(remote_tag)
    
    did_incremental = False
    if local_commit:
        try:
            cmp_data = compare_commits(local_commit, remote_commit_sha)
            ahead_by = cmp_data.get("ahead_by")
            files = cmp_data.get("files", [])
            if ahead_by and ahead_by > 0 and files:
                apply_incremental_update(files, remote_commit_sha, progress_cb=progress_cb)
                did_incremental = True
        except Exception as e:
            log(f"Incremental update failed: {e}")
            
    if not did_incremental:
        zip_url = release.get("zipball_url")
        if not zip_url:
            raise RuntimeError("Nincs zipball_url")
        download_release_zip(zip_url, progress_cb=progress_cb)
        
    write_local_version(remote_tag, remote_commit_sha)