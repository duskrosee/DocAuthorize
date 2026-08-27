import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.db import DB_PATH, BACKUP_DIR, create_tables
from services.backup import create_database_backup

create_database_backup(db_path=str(DB_PATH), backup_dir=str(BACKUP_DIR))
create_tables()

from gui.window import MainWindow
from gui.splash import SplashScreen
from gui.styles.dark_theme import DARK_THEME
from gui.styles.light_theme import LIGHT_THEME
from translations import LANGUAGES

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    settings = QSettings("DocAuthorize", "ContractManager")
    is_dark = settings.value("theme_is_dark", True, type=bool)
    if is_dark:
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

    window = MainWindow()

    saved_lang_key = settings.value("app_language", "ENG")
    current_lang_dict = LANGUAGES.get(saved_lang_key, LANGUAGES["ENG"])
    
    if hasattr(window, "set_language"):
        window.set_language(current_lang_dict)

    def start_main_window():
        window.show()

    splash = SplashScreen(on_finish_callback=start_main_window)
    splash.show()

    sys.exit(app.exec())



#.