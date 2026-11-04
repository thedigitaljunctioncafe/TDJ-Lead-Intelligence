"""Create and verify a consistent SQLite backup; optionally copy it to rclone remote."""
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.getenv("TDJ_SQLITE_PATH", ROOT / "data" / "tdj_leads.db")).resolve()
BACKUP_DIR = Path(os.getenv("TDJ_BACKUP_DIR", ROOT / "backups" / "local")).resolve()
RETENTION_DAYS = int(os.getenv("TDJ_BACKUP_RETENTION_DAYS", "30"))
RCLONE_REMOTE = os.getenv("TDJ_RCLONE_REMOTE", "").strip()
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
if not SOURCE.exists():
    raise SystemExit(f"Database not found: {SOURCE}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target = BACKUP_DIR / f"tdj_leads_{stamp}.db"
try:
    with sqlite3.connect(SOURCE) as source_conn:
        with sqlite3.connect(target) as target_conn:
            source_conn.backup(target_conn)
            result = target_conn.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise RuntimeError(f"Backup integrity check failed: {result}")
except Exception:
    target.unlink(missing_ok=True)
    raise

print(f"LOCAL_BACKUP_OK={target}")

# Optional cloud copy: configure rclone and set TDJ_RCLONE_REMOTE, e.g.
# gdrive:TDJ-Lead-Intelligence/backups
if RCLONE_REMOTE:
    rclone = shutil.which("rclone")
    if not rclone:
        raise SystemExit("Local backup succeeded, but TDJ_RCLONE_REMOTE is set and rclone is not installed.")
    remote_file = f"{RCLONE_REMOTE.rstrip('/')}/{target.name}"
    subprocess.run([rclone, "copyto", str(target), remote_file], check=True)
    print(f"REMOTE_BACKUP_OK={remote_file}")
else:
    print("REMOTE_BACKUP_SKIPPED=Configure rclone and TDJ_RCLONE_REMOTE to enable online backup.")

cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
for old_file in BACKUP_DIR.glob("tdj_leads_*.db"):
    if datetime.fromtimestamp(old_file.stat().st_mtime) < cutoff:
        old_file.unlink(missing_ok=True)
print(f"LOCAL_RETENTION_DAYS={RETENTION_DAYS}")
