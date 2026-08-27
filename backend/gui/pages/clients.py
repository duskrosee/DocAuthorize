import os
import platform
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt

from database.db import (
    get_clients_with_all_documents,
    delete_client,
    export_clients_to_excel,
)
from backend.services.exporter import send_client_history_report


class Clients(QWidget):
    def __init__(self):
        super().__init__()
        self.current_lang = None
        self.create_interface()

    def create_interface(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header_layout = QHBoxLayout()

        self.title = QLabel("👥 Clients")
        self.title.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.title)
        header_layout.addStretch()

        self.export_button = QPushButton("Export to Excel")
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.export_button.clicked.connect(self.export_to_excel)
        header_layout.addWidget(self.export_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
        """)
        self.refresh_button.clicked.connect(self.load_clients)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")

        self.clients_layout = QVBoxLayout()
        self.clients_layout.setSpacing(16)
        self.clients_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container.setLayout(self.clients_layout)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.setLayout(layout)
        self.load_clients()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_clients()

    def get_text(self, key, english_text):
        if self.current_lang:
            return self.current_lang.get(key, english_text)
        return english_text

    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.get_text("export_title", "Save Excel File"),
            "clients_export.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        try:
            export_clients_to_excel(file_path)
            QMessageBox.information(
                self,
                self.get_text("success", "Success"),
                self.get_text("export_success", f"Data successfully exported to:\n{file_path}")
            )
        except Exception as e:
            QMessageBox.critical(self,self.get_text("error", "Error"),
                f"Failed to export data:\n{str(e)}"
            )

    def open_document(self, path):
        if not path:
            QMessageBox.warning(
                self,
                self.get_text("file_missing_title", "File missing"),
                self.get_text("file_missing_text", "No document path saved."),
            )
            return

        if not os.path.exists(path):
            QMessageBox.warning(
                self,
                self.get_text("file_not_found_title", "File not found"),
                path,
            )
            return

        if platform.system() == "Darwin":
            subprocess.call(("open", path))
        elif platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.call(("xdg-open", path))

    def load_clients(self):
        while self.clients_layout.count():
            item = self.clients_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        clients = get_clients_with_all_documents()

        for item in clients:
            client = item["client"]
            documents = item["documents"]

            card = QFrame()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(12)

            card_header_layout = QHBoxLayout()

            company_name = (
                client["company_name"] or self.get_text("unknown", "Unknown")
            )
            title_label = QLabel(f"🏢 {company_name}")
            title_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; border: none; background: transparent;"
            )
            card_header_layout.addWidget(title_label)
            card_header_layout.addStretch()

            send_button = QPushButton(f"📩 {self.get_text('send_all', 'Send All')}")
            send_button.setCursor(Qt.CursorShape.PointingHandCursor)
            send_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #3b82f6;
                    border: 1px solid #3b82f6;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #3b82f6;
                    color: white;
                }
            """)
            send_button.clicked.connect(
                lambda checked=False, nip=client["nip"]: self.send_client_report(nip)
            )
            card_header_layout.addWidget(send_button)

            delete_button = QPushButton(
                f"🗑 {self.get_text('delete_client', 'Delete')}"
            )
            delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ef4444;
                    border: 1px solid #ef4444;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #ef4444;
                    color: white;
                }
            """)
            delete_button.clicked.connect(
                lambda checked=False, cid=client["id"]: self.remove_client(cid)
            )
            card_header_layout.addWidget(delete_button)

            card_layout.addLayout(card_header_layout)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)

            nip = client["nip"] or "---"
            company_phone = client["company_phone"] or "---"
            contact_person = client["contact_person"] or "---"
            contact_phone = client["contact_phone"] or "---"
            email = client["email"] or "---"
            manager_name = client["manager"] or "---"

            lbl_company_phone = self.get_text("company_phone", "Company phone")
            lbl_manager = self.get_text("manager", "Manager")
            lbl_contact_person = self.get_text("contact_person", "Contact person")
            
            info_text = f"""
            <div style="font-size: 13px; line-height: 1.4;">
                <b>NIP:</b> <span>{nip}</span> &nbsp;|&nbsp; 
                <b>{lbl_company_phone}:</b> <span>{company_phone}</span><br>
                <b>👤 {lbl_manager}:</b> <span>{manager_name}</span> &nbsp;|&nbsp; 
                <b>{lbl_contact_person}:</b> <span>{contact_person}</span> ({contact_phone})<br>
                <b>📧 Email:</b> <span>{email}</span>
            </div>
            """
            info_label = QLabel(info_text)
            info_label.setStyleSheet("border: none; background: transparent;")
            info_layout.addWidget(info_label)

            card_layout.addLayout(info_layout)

            if documents:
                contracts_title = QLabel(
                    f"📄 {self.get_text('contracts', 'Contracts')}:"
                )
                contracts_title.setStyleSheet(
                    "font-weight: bold; font-size: 14px; margin-top: 6px; border: none; background: transparent;"
                )
                card_layout.addWidget(contracts_title)

                lbl_contract_date = self.get_text("contract_date", "Contract date")
                lbl_validity = self.get_text("validity_period", "Valid until")
                lbl_price = self.get_text("price", "Price")

                for doc in documents:
                    contract_date = doc["contract_date"] or "---"
                    validity = doc["validity_period"] or "---"
                    price = doc["price"] or "---"
                    file_name = doc["file_name"] or "No file attached"

                    doc_html = f"""
                    <b style='color: #3b82f6; font-size: 14px;'>📎 {file_name}</b><br>
                    <span style='font-size: 13px;'>
                        <b>📅 {lbl_contract_date}:</b> {contract_date} &nbsp;|&nbsp; 
                        <b>⏳ {lbl_validity}:</b> {validity} &nbsp;|&nbsp; 
                        <b>💰 {lbl_price}:</b> {price}
                    </span>
                    """
                    contract_box = QLabel(doc_html)
                    contract_box.setCursor(Qt.CursorShape.PointingHandCursor)
                    contract_box.setStyleSheet("""
                        QLabel {
                            border-left: 3px solid #3b82f6;
                            border-radius: 6px;
                            padding: 10px;
                            margin-top: 4px;
                        }
                    """)
                    contract_box.mousePressEvent = (
                        lambda event, path=doc["file_path"]: self.open_document(
                            path
                        )
                    )
                    card_layout.addWidget(contract_box)

            self.clients_layout.addWidget(card)

    def send_client_report(self, nip):
        if not nip or nip == "---":
            QMessageBox.warning(self, "Warning", "NIP is missing. Cannot find documents for this client.")
            return

        reply = QMessageBox.question(
            self,
            "Send Full Report",
            f"Are you sure you want to send all historical documents for NIP {nip} to the manager?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            root_dir = Path(os.getcwd())
            success = send_client_history_report(nip, root_dir)
            if success:
                QMessageBox.information(self, "Success", f"Full report for NIP {nip} sent successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to send report. Please check settings and emails.")

    def remove_client(self, client_id):
        user_choice = QMessageBox.question(
            self,
            self.get_text("delete_client_title", "Delete client"),
            self.get_text(
                "delete_client_question",
                "Delete this client and all documents?",
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if user_choice == QMessageBox.StandardButton.Yes:
            delete_client(client_id)
            QMessageBox.information(
                self,
                self.get_text("deleted_title", "Deleted"),
                self.get_text("client_deleted", "Client removed successfully."),
            )
            self.load_clients()



    def set_language(self, lang):
        self.current_lang = lang
        self.title.setText("👥 " + self.get_text("clients", "Clients"))
        self.refresh_button.setText(self.get_text("refresh", "Refresh"))
        self.export_button.setText(self.get_text("export_excel", "Export to Excel"))
        self.load_clients()

#.