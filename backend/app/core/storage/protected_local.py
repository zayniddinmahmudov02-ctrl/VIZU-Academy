from pathlib import Path

from app.core.storage.local import LocalStorage


class ProtectedLocalStorage(LocalStorage):
    """Identical to LocalStorage (same upload/delete file-write logic,
    inherited rather than duplicated) except its root is `protected_uploads/`
    instead of `uploads/` — a directory the app's StaticFiles mount
    (main.py, `/uploads` -> directory="uploads") does NOT cover.

    This is what actually makes Hören audio access-controlled: LocalStorage
    files are reachable by anyone who has the URL, by design (that's fine
    for flags/avatars/media where that's the intended behavior) — audio
    here is only ever readable through the authenticated GET /audio/{id}
    endpoint, which streams the file after a permission check. `.url()` is
    intentionally NOT used for audio; nothing should ever hand a caller a
    direct path into this tree.
    """

    # Lives under app/ rather than a bare top-level `protected_uploads/`
    # sibling to `uploads/` — same isolation from the public StaticFiles
    # mount (main.py only serves `uploads/`), just a location this
    # environment actually permits creating new directories in.
    ROOT = Path("app/protected_storage/audio")
