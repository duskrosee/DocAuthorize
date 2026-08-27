import random
import smtplib
from email.message import EmailMessage

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Settings(QWidget):

    def __init__(self):
        super().__init__()
        self.settings = QSettings("DocAuthorize", "ContractManager")
        self.password_visible = False
        self.current_lang = None
        self.create_interface()
        self.load_settings()

    def create_interface(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.title = QLabel("⚙️ Settings")
        self.title.setStyleSheet(
            "QLabel { font-size: 26px; font-weight: bold; border: none; background: transparent; }"
        )

        self.description = QLabel(
            "Enter the corporate email, its password, and the manager's email to receive reports. "
            "Changing credentials requires mandatory verification via the corporate email."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet(
            "QLabel { font-size: 13px; border: none; background: transparent; opacity: 0.8; }"
        )

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        active_input_style = """
            QLineEdit {
                background-color: rgba(130, 130, 130, 0.15);
                border: 1px solid rgba(130, 130, 130, 0.5);
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: rgba(130, 130, 130, 0.25);
            }
        """

        self.sender_email_input = QLineEdit()
        self.sender_email_input.setPlaceholderText("e.g. biuro@pmdigital.pl")
        self.sender_email_input.setStyleSheet(active_input_style)

        self.sender_password_input = QLineEdit()
        self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sender_password_input.setPlaceholderText("Password for corporate email")
        self.sender_password_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                font-size: 14px;
            }
        """)

        self.eye_button = QPushButton("👁")
        self.eye_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_button.setFixedSize(28, 28)
        self.eye_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(130, 130, 130, 0.2);
                border-radius: 4px;
            }
        """)
        self.eye_button.clicked.connect(self.toggle_password_visibility)

        pwd_container = QWidget()
        pwd_container.setObjectName("pwd_container")
        pwd_container.setStyleSheet("""
            QWidget#pwd_container {
                background-color: rgba(130, 130, 130, 0.15);
                border: 1px solid rgba(130, 130, 130, 0.5);
                border-radius: 8px;
            }
        """)

        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(10, 4, 8, 4)
        pwd_layout.setSpacing(6)
        pwd_layout.addWidget(self.sender_password_input)
        pwd_layout.addWidget(self.eye_button)

    
        self.boss_email_input = QLineEdit()
        self.boss_email_input.setPlaceholderText("e.g. boss@company.com")
        self.boss_email_input.setStyleSheet(active_input_style)
        
        label_style = "QLabel { font-size: 14px; font-weight: bold; border: none; background: transparent; padding: 0px; margin: 0px; }"

        self.lbl_corp = QLabel("Corporate Email:")
        self.lbl_pwd = QLabel("Password:")
        self.lbl_boss = QLabel("Manager Email (Boss):")

        self.lbl_corp.setStyleSheet(label_style)
        self.lbl_pwd.setStyleSheet(label_style)
        self.lbl_boss.setStyleSheet(label_style)

        form_layout.addRow(self.lbl_corp, self.sender_email_input)
        form_layout.addRow(self.lbl_pwd, pwd_container)
        form_layout.addRow(self.lbl_boss, self.boss_email_input)

        self.save_button = QPushButton("Send Verification Code & Save")
        self.save_button.setMinimumHeight(42)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)

        layout.addWidget(self.title)
        layout.addWidget(self.description)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def toggle_password_visibility(self):
        if self.password_visible:
            self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_button.setText("👁")
            self.password_visible = False
        else:
            self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_button.setText("🙈")
            self.password_visible = True

    def load_settings(self):
        self.sender_email_input.setText(self.settings.value("corp_email", "biuro@pmdigital.pl"))
        self.sender_password_input.setText(self.settings.value("corp_password", ""))
        self.boss_email_input.setText(self.settings.value("boss_email", ""))

    def get_text(self, key, english_text):
        if self.current_lang:
            return self.current_lang.get(key, english_text)
        return english_text

    def send_real_verification_code(self, sender_email: str, recipient_email: str, code: str, password: str) -> bool:
        """Sends a 6-digit verification code from the specified corporate email."""
        try:
            msg = EmailMessage()
            msg["Subject"] = "DocAuthorize: Authorization Code"
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg.set_content(
                f"Dzień dobry,\n\n"
                f"Twój kod weryfikacyjny do zatwierdzenia ustawień w aplikacji DocAuthorize to: {code}\n\n"
                f"Jeśli ta zmiana nie była inicjowana przez Ciebie, zignoruj tę wiadomość."
            )

            with smtplib.SMTP("smtp.office365.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[Verification Email Error]: {e}")
            return False

    def save_settings(self):
        sender_email = self.sender_email_input.text().strip()
        password = self.sender_password_input.text().strip()
        boss = self.boss_email_input.text().strip()

        if not sender_email or not password or not boss:
            QMessageBox.warning(
                self, 
                self.get_text("warning_title", "Warning"), 
                self.get_text("settings_empty_warning", "Please fill in all fields (Email, Password and Boss Email)!")
            )
            return

        verification_code = str(random.randint(100000, 999999))
        self.save_button.setEnabled(False)
        sending_code_text = self.get_text("sending_code_text", "Sending Verification Code...")
        self.save_button.setText(sending_code_text)
        QApplication.processEvents()

        sent_success = self.send_real_verification_code(sender_email, sender_email, verification_code, password)

        self.save_button.setEnabled(True)
        self.save_button.setText(self.get_text("save_verification", "Send Verification Code & Save"))

        if not sent_success:
            QMessageBox.critical(
                self,
                self.get_text("auth_failed_title", "Authentication Failed"),
                self.get_text("auth_failed_msg", "Could not send verification email. Please make sure the entered email and password are correct.")
            )
            return

        user_input, ok = QInputDialog.getText(
            self,
            self.get_text("security_ver_title", "Security Verification"),
            self.get_text("security_ver_prompt", f"A 6-digit confirmation code has been sent to {sender_email}.\nEnter code:")
        )

        if ok and user_input.strip() == verification_code:
            self.settings.setValue("corp_email", sender_email)
            self.settings.setValue("corp_password", password)
            self.settings.setValue("boss_email", boss)
            QMessageBox.information(
                self, 
                self.get_text("success_title", "Success"), 
                self.get_text("success_settings_msg", "Verification passed! Settings saved securely.")
            )
        else:
            QMessageBox.critical(
                self, 
                self.get_text("access_denied_title", "Access Denied"), 
                self.get_text("access_denied_msg", "Invalid confirmation code. Settings were NOT saved.")
            )

    def set_language(self, lang: dict):
        """Updates all texts on the settings page when changing the language"""        
        self.current_lang = lang

        if hasattr(self, "title"):
            self.title.setText("⚙️ " + lang.get("settings", "Settings"))

        if hasattr(self, "description"):
            self.description.setText(
                lang.get(
                    "settings_description", 
                    "Enter the corporate email, its password, and the manager's email to receive reports. Changing credentials requires mandatory verification via the corporate email."
                )
            )
            
        if hasattr(self, "lbl_corp"):
            self.lbl_corp.setText(lang.get("corporate_email", "Corporate Email:"))
        if hasattr(self, "lbl_pwd"):
            self.lbl_pwd.setText(lang.get("password", "Password:"))
        if hasattr(self, "lbl_boss"):
            self.lbl_boss.setText(lang.get("manager_email", "Manager Email (Boss):"))
            
        if hasattr(self, "sender_password_input"):
            self.sender_password_input.setPlaceholderText(
                lang.get("password_placeholder", "Password for corporate email")
            )
            
        if hasattr(self, "save_button"):
            self.save_button.setText(lang.get("save_verification", "Send Verification Code & Save"))

            #.