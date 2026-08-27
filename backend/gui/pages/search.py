import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt

from database.db import (
    search_client_by_nip,
    get_documents_by_client,
)


class Search(QWidget):

    def __init__(self):
        super().__init__()
        self.current_lang = None
        self.create_interface()

    def create_interface(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        self.title = QLabel("🔎 Search client by NIP")
        self.title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(self.title)

        search_row_layout = QHBoxLayout()
        search_row_layout.setSpacing(10)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter NIP...")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(130, 130, 130, 0.15);
                border: 1px solid rgba(130, 130, 130, 0.5);
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: rgba(130, 130, 130, 0.25);
            }
        """)
        search_row_layout.addWidget(self.input)

        self.search_button = QPushButton("🔍 Search")
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 11px 24px;
                font-weight: bold;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
        """)
        self.search_button.clicked.connect(self.search)
        search_row_layout.addWidget(self.search_button)

        layout.addLayout(search_row_layout)

        self.result = QVBoxLayout()
        self.result.setSpacing(10)
        self.result.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.result_widget = QWidget()
        self.result_widget.setStyleSheet("background-color: transparent;")
        self.result_widget.setLayout(self.result)

        layout.addWidget(self.result_widget)
        layout.addStretch()

        self.setLayout(layout)

    def search(self):
        while self.result.count():
            item = self.result.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        nip = self.input.text().strip()
        search_results = search_client_by_nip(nip)

        if not search_results:
            QMessageBox.warning(
                self,
                self.get_text("not_found_title", "Not found"),
                self.get_text("not_found_text", "Client with this NIP does not exist.")
            )
            return

        for item in search_results:
            client = item["client"]
            documents = item["documents"]

            card = QFrame()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(12)

            company_name = client['company_name'] or "Unknown"
            client_nip = client['nip'] or "---"
            manager_name = client['manager'] or self.get_text("not_found", "Not found")

            info = QLabel(
                f"<h2 style='margin-top: 0; margin-bottom: 8px;'>🏢 {company_name}</h2>"
                f"<span style='font-size: 14px;'><b>NIP:</b> <span>{client_nip}</span></span><br>"
                f"<span style='font-size: 14px;'><b>👤 {self.get_text('manager', 'Manager')}:</b> <span>{manager_name}</span></span>"
            )
            info.setStyleSheet("border: none; background: transparent;")
            card_layout.addWidget(info)

            if documents:
                documents_title = QLabel(f"📄 {self.get_text('contracts', 'Contracts')}:")
                documents_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px; border: none; background: transparent;")
                card_layout.addWidget(documents_title)

                for doc in documents:
                    contract_date = doc['contract_date'] or self.get_text("date_not_found", "Date not found")
                    file_name = doc['file_name'] or self.get_text("no_file", "No file")

                    file = QLabel(f"<b>📎 {contract_date}</b><br><span style='font-size: 13px;'>{file_name}</span>")
                    file.setCursor(Qt.CursorShape.PointingHandCursor)
                    # Добавлена легкая заливка для карточек документов, чтобы они читались в любой теме
                    file.setStyleSheet("""
                        QLabel {
                            background-color: rgba(130, 130, 130, 0.1);
                            border-left: 3px solid #3b82f6;
                            border-radius: 6px;
                            padding: 12px;
                            margin-top: 4px;
                        }
                        QLabel:hover {
                            background-color: rgba(130, 130, 130, 0.2);
                        }
                    """)
                    file.mousePressEvent = lambda event, path=doc['file_path']: self.open_file(path)
                    card_layout.addWidget(file)

            card.setLayout(card_layout)
            self.result.addWidget(card)

    def open_file(self, path):
        if not path:
            return
        if os.path.exists(path):
            os.system(f'open "{path}"')
        else:
            QMessageBox.warning(self, "Error", f"File not found: {path}")

    def get_text(self, key, english_text):
        if self.current_lang:
            return self.current_lang.get(key, english_text)
        return english_text

    def set_language(self, lang):
        self.current_lang = lang
        self.title.setText("🔎 " + self.get_text("search_title", "Search client by NIP"))
        self.search_button.setText("🔍 " + self.get_text("search_button", "Search"))
        self.input.setPlaceholderText(self.get_text("enter_nip", "Enter NIP..."))


        #.