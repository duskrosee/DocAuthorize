import os
import shutil
from datetime import datetime
from pathlib import Path


def find_database_file(start_dir: Path):
    """Scan the project directory and automatically find the database file (.db or .sqlite)."""
    for root, dirs, files in os.walk(start_dir):
        if any(
            ignored in root
            for ignored in [".venv", "backups", "__pycache__", ".git"]
        ):
            continue
        for file in files:
            if file.endswith(".db") or file.endswith(".sqlite"):
                return Path(root) / file
    return None


def create_database_backup(db_path=None, backup_dir="backups"):
    """Create a timestamped backup of the database file."""
    try:
        services_dir = Path(__file__).resolve().parent
        backend_dir = services_dir.parent
        project_root = (
            backend_dir.parent
            if backend_dir.name == "backend"
            else backend_dir
        )

        db_file = find_database_file(project_root)

        if not db_file or not db_file.exists():
            print(
                "[Backup Error] Database file not found. Add a record first to initialize the database!"
            )
            return

        target_backup_dir = project_root / backup_dir
        if not target_backup_dir.exists():
            target_backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = target_backup_dir / backup_filename

        shutil.copy2(db_file, backup_path)
        print(f"[Backup] Successfully created backup: {backup_path}")

        clean_old_backups(target_backup_dir, max_backups=10)

    except Exception as e:
        print(f"[Backup Error] Failed to create backup: {e}")


def clean_old_backups(backup_dir, max_backups=10):
    """Delete old backup files to keep only the specified maximum count."""
    try:
        backup_dir_path = Path(backup_dir)
        if not backup_dir_path.exists():
            return

        backups = list(backup_dir_path.glob("backup_*.db"))
        backups.sort(key=lambda p: p.stat().st_mtime)

        while len(backups) > max_backups:
            old_backup = backups.pop(0)
            old_backup.unlink()
            print(f"[Backup] Removed old backup: {old_backup}")
    except Exception as e:
        print(f"[Backup Clean Error] Failed to clean old backups: {e}")
        


#.