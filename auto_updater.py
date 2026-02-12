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

OWNER = "HeadTDev"
REPO = "dataprocessingtool"

VERSION_FILE = "version.json"
LOG_FILE = "update_log.txt"

CHECK_TIMEOUT = 8
USER_AGENT = f"ReleaseAutoUpdater/2.0 (+https://github.com/{OWNER}/{REPO})"

DEBUG = True
ALLOW_ZIP_FALLBACK = True
INCREMENTAL_DEFAULT = True   # ha van commit összehasonlítási alap
INITIALIZE_WITHOUT_FORCE_DOWNLOAD = True  # első futásnál (nincs version.json) ne töltsön, csak inicializáljon
ALLOW_PRERELEASES = False

MAX_BODY_SNIPPET = 400  # promptban ennyire vágjuk a release body-t

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if DEBUG:
        print(line)


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
                    log(f"Törlés hiba: {filename}: {e}")

        elif status == "renamed":
            if prev_name and os.path.exists(prev_name):
                try:
                    os.remove(prev_name)
                except Exception as e:
                    log(f"Rename előző törlés hiba: {prev_name}: {e}")
            try:
                content = download_file_raw(head_sha, filename)
            except Exception as e:
                raise RuntimeError(f"Nem sikerült (rename) letölteni: {filename}: {e}")
            target_dir = os.path.dirname(filename)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            with open(filename, "wb") as f:
                f.write(content)
        else:
            log(f"Ismeretlen státusz: {status} - {filename}")


def download_release_zip(zip_url: str):
    log("Release ZIP letöltése...")
    zip_bytes = http_get_bytes(zip_url)
    with tempfile.TemporaryDirectory() as td:
        zip_path = os.path.join(td, "rel.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
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
                if rel_path in (VERSION_FILE, LOG_FILE):
                    continue
                target_path = os.path.join(os.getcwd(), rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member, "r") as src, open(target_path + ".autoupdate_tmp", "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.replace(target_path + ".autoupdate_tmp", target_path)
    log("Release ZIP kibontva.")


# --- Alap (headless) UI callback-ek (felülírhatóak) ---
def _default_prompt(q: str) -> bool:
    log(f"[PROMPT] {q} -> auto: yes")
    return True

def _default_info(m: str):
    log(f"[INFO] {m}")

def _default_error(m: str):
    log(f"[ERROR] {m}")

def _default_set_version(v: str):
    log(f"[SET_VERSION_CALLBACK] {v}")


def perform_update_flow(
    incremental_preferred=True,
    ui_prompt=_default_prompt,
    ui_info=_default_info,
    ui_error=_default_error,
    ui_set_version=_default_set_version,
    run_in_thread=False,
    delay_seconds=1.0
):
    """
    Release tag alapú frissítés.
    """

    def _work():
        time.sleep(delay_seconds)
        local = read_local_version_info()
        local_tag = local.get("version") or ""
        local_commit = local.get("commit") or ""
        log(f"Helyi verzió tag='{local_tag}' commit='{local_commit}'")

        try:
            release = get_latest_release()
        except Exception as e:
            log(f"Nem sikerült lekérni a latest release-t: {e}")
            return

        remote_tag = release.get("tag_name") or ""
        release_name = release.get("name") or remote_tag
        release_body = release.get("body") or ""
        if len(release_body) > MAX_BODY_SNIPPET:
            release_body_snip = release_body[:MAX_BODY_SNIPPET].rstrip() + "..."
        else:
            release_body_snip = release_body

        if not remote_tag:
            log("A release-ben nincs tag_name, kilépés.")
            return

        try:
            remote_commit_sha = get_commit_sha_for_tag(remote_tag)
        except Exception as e:
            log(f"Nem sikerült commit SHA-t lekérni a tagez: {e}")
            return

        if local_tag == remote_tag:
            log("Nincs új release (azonos tag).")
            ui_set_version(remote_tag or "ismeretlen")
            return

        # Első inicializáció (nincs helyi tag) – opcionálisan csak beállítjuk és nem töltünk
        if not local_tag and INITIALIZE_WITHOUT_FORCE_DOWNLOAD:
            write_local_version(remote_tag, remote_commit_sha)
            ui_set_version(remote_tag)
            log("Inicializáció (version.json létrehozva).")
            return

        # Van új release
        prompt_msg = f"Új release érhető el: {remote_tag} ({release_name}). Frissíted most?"
        if release_body_snip:
            prompt_msg += f"\n\nVáltozások (részlet):\n{release_body_snip}"

        if not ui_prompt(prompt_msg):
            log("Felhasználó elutasította a release frissítést.")
            return

        # Próbálunk inkrementális diff-et, ha van lokális commit és engedélyezett
        did_incremental = False
        if incremental_preferred and local_commit:
            try:
                cmp_data = compare_commits(local_commit, remote_commit_sha)
                ahead_by = cmp_data.get("ahead_by")
                files = cmp_data.get("files", [])
                log(f"Compare: ahead_by={ahead_by}, files={len(files)}")
                if ahead_by and ahead_by > 0 and files:
                    apply_incremental_update(files, remote_commit_sha)
                    did_incremental = True
                    log("Inkrementális frissítés sikeres release-re.")
                else:
                    log("Nincs diff vagy üres diff -> inkrementális nem szükséges.")
                    did_incremental = True  # gyakorlatilag nincs változás
            except Exception as e:
                log(f"Inkrementális frissítés sikertelen: {e}")
                log(traceback.format_exc())

        # Ha nem sikerült inkrementális vagy nem preferált: teljes ZIP
        if not did_incremental:
            try:
                zip_url = release.get("zipball_url")
                if not zip_url:
                    raise RuntimeError("Hiányzik zipball_url a release-ben.")
                download_release_zip(zip_url)
            except Exception as e:
                ui_error(f"ZIP alapú frissítés sikertelen: {e}")
                return

        # Verzió mentése
        write_local_version(remote_tag, remote_commit_sha)
        ui_set_version(remote_tag)
        ui_info(f"Frissítés kész: {remote_tag}. Indítsd újra az alkalmazást a teljes érvényesüléshez.")

    if run_in_thread:
        t = threading.Thread(target=_work, name="ReleaseAutoUpdaterThread", daemon=True)
        t.start()
    else:
        _work()