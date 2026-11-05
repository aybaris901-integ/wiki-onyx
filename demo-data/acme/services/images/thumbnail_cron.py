"""Nightly thumbnail cron.

Pre-renders the "thumb" and "card" renditions for every SKU touched in the
last day so the image server (server.py) serves them from cache.

History: on 2026-08-12 this job ran twice after a deploy restarted it mid-run,
and the second run deleted renditions the first one was still writing. Alex
Chen fixed it alone at 2am (PR "Make thumbnail cron idempotent", #images
thread 2026-08-12). The fix is the lock file plus writing to a temp name and
renaming. Nobody else has run this job by hand. If Alex leaves, read
docs/handoffs/alex-offboarding.md first.

Owner: @alex.
"""

from __future__ import annotations

import os
from pathlib import Path

from .server import ImageRequest, ImageServer

LOCK_FILE = Path("/var/run/acme-thumbnail-cron.lock")


class AlreadyRunning(RuntimeError):
    pass


def acquire_lock(lock: Path = LOCK_FILE) -> int:
    # O_EXCL makes this atomic: two cron starts cannot both win.
    try:
        return os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise AlreadyRunning(str(lock)) from exc


def release_lock(fd: int, lock: Path = LOCK_FILE) -> None:
    os.close(fd)
    lock.unlink(missing_ok=True)


def run(server: ImageServer, skus: list[str], lock: Path = LOCK_FILE) -> int:
    """Pre-render renditions for skus. Returns the count rendered. Safe to re-run."""
    fd = acquire_lock(lock)
    rendered = 0
    try:
        for sku in skus:
            for rendition in ("thumb", "card"):
                # path_for renders to a cache path; the server writes atomically
                # (temp file + rename), so a crash never leaves half a thumbnail.
                server.path_for(ImageRequest(sku, rendition))
                rendered += 1
    finally:
        release_lock(fd, lock)
    return rendered
