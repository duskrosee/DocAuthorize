import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from services.analyzer import NOT_FOUND, analyze_document
from services.pdf_reader import (
    OCRHint,
    OCRPolicy,
    ProcessedPDF,
    process_pdf,
)
from database.db import save_analyzed_document

from services.exporter import save_contracts_only, send_new_documents_report


class Documents(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_files = [] 
        self.current_processed_data = []  # Данные, готовые к отправке шефу
        self.current_lang = None
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.create_interface()

    def create_interface(self):
        layout = QVBoxLayout()

        self.title = QLabel("📑 Documents")
        self.title.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; border: none; background: transparent; }")

        self.description = QLabel(
            "Upload PDF documents. DocAuthorize will read the text, save clients to the DB, "
            "sort files (Signed/Pending). Then you can send a full report to the manager."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet("QLabel { font-size: 14px; border: none; background: transparent; opacity: 0.8; }")

        self.file_label = QLabel("No documents selected")
        self.file_label.setStyleSheet("QLabel { font-size: 14px; border: none; background: transparent; margin-top: 5px; margin-bottom: 5px; }")

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("The document analysis will appear here.")
        self.result_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(130, 130, 130, 0.1);
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)

        self.upload_button = QPushButton("📄 Upload PDFs")
        self.upload_button.setMinimumHeight(35)
        self.upload_button.clicked.connect(self.upload_pdfs)

        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Process and save to DB")
        self.save_button.setMinimumHeight(35)
        self.save_button.setStyleSheet("background-color: #2E8B57; color: white; font-weight: bold; border: none; border-radius: 6px;")
        self.save_button.clicked.connect(self.process_and_save)

        self.send_button = QPushButton("Send report to boss")
        self.send_button.setMinimumHeight(35)
        self.send_button.setStyleSheet("background-color: #00a8ff; color: white; font-weight: bold; border: none; border-radius: 6px;")
        self.send_button.setEnabled(False) 
        self.send_button.clicked.connect(self.send_report)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.send_button)

        layout.addWidget(self.title)
        layout.addWidget(self.description)
        layout.addWidget(self.upload_button)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.file_label)
        layout.addWidget(self.result_box)

        self.setLayout(layout)

    def get_text(self, key, english_text):
        if self.current_lang:
            return self.current_lang.get(key, english_text)
        return english_text

    def upload_pdfs(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.get_text("select_pdf_title", "Select PDF documents"),
            "",
            "PDF Files (*.pdf)",
        )

        if not file_paths:
            return
        self.selected_files = file_paths
        self.current_processed_data = [] 
        self.send_button.setEnabled(False)
        
        selected_text = self.get_text("selected_prefix", "Selected:")
        self.file_label.setText(
            f"<span>{selected_text}</span> <b>{len(self.selected_files)} {self.get_text('files_suffix', 'file(s)')}</b>"
        )
        
        ready_text = self.get_text("files_ready_text", "Files ready for processing:")
        names_html = "<br>".join([f"• {os.path.basename(p)}" for p in self.selected_files])
        self.result_box.setHtml(f"<div>{ready_text}<br><b>{names_html}</b></div>")

    def process_and_save(self):
        if not self.selected_files:
            QMessageBox.warning(
                self,
                self.get_text("warning_title", "Warning"),
                self.get_text("no_doc_warning", "No documents to process. Please upload PDFs first.")
            )
            return

        self.save_button.setEnabled(False)
        processing_text = self.get_text("processing_text", "Processing... Please wait")
        self.save_button.setText(processing_text)
        QApplication.processEvents()

        all_html_results = ""
        flat_data = []

        for file_path in self.selected_files:
            file_name = os.path.basename(file_path)
            file_title_label = self.get_text("file_title_label", "File:")
            all_html_results += f"<h3 style='border-bottom: 1px solid rgba(130, 130, 130, 0.3); padding-bottom: 5px;'>{file_title_label} {file_name}</h3>"
            
            try:
                processed_document = process_pdf(
                    file_path,
                    ocr_policy=OCRPolicy.FALLBACK,
                    ocr_hints=(OCRHint.TEXT,),
                )
                complex_data = analyze_document(processed_document)

                
                save_analyzed_document(data=complex_data, file_path=file_path, file_name=file_name)

                all_html_results += self.format_results(complex_data, processed_document)
                success_db_text = self.get_text("success_db_text", "✅ Client saved to DB & Files moved!")
                all_html_results += f"<div style='color: #27ae60; font-size: 14px;'>{success_db_text}</div><br><br>"

                def get_val(key):
                    val = complex_data.get(key, {}).get("value", "N/A")
                    return "N/A" if val == NOT_FOUND else str(val)

                flat_data.append({
                    "file_name": file_name,
                    "file_path": file_path,
                    "nip": get_val("NIP"),
                    "price": get_val("Price"),
                    "contract_date": get_val("Contract date"),
                    "manager": get_val("Manager"),
                    "status": get_val("Status") or "Pending Signature",
                })

            except Exception as error:
                err_title = self.get_text("analysis_error_title", "❌ Could not analyze this PDF.")
                all_html_results += f"<p style='color: #e84118;'><b>{err_title}</b><br>{error}</p><br><br>"

        self.result_box.setHtml(all_html_results)
        QApplication.processEvents()

        if flat_data:
            save_contracts_only(flat_data, self.root_dir)
            self.current_processed_data = flat_data
            self.send_button.setEnabled(True) 
            success_box_title = self.get_text("success_title", "Success")
            success_box_msg = self.get_text("success_process_msg", "All documents processed and saved to DB! You can now send the report.")
            QMessageBox.information(self, success_box_title, success_box_msg)

        self.save_button.setEnabled(True)
        self.save_button.setText(self.get_text("process_save_db", "Process and save to DB"))

    def send_report(self):
        if not self.current_processed_data:
            err_title = self.get_text("error_title", "Error")
            err_msg = self.get_text("no_data_send_msg", "No processed data to send.")
            QMessageBox.warning(self, err_title, err_msg)
            return
            
        self.send_button.setEnabled(False)
        sending_text = self.get_text("sending_email_text", "Sending Email...")
        self.send_button.setText(sending_text)
        QApplication.processEvents()
        
        success = send_new_documents_report(self.current_processed_data, self.root_dir)
        
        if success:
            email_sent_title = self.get_text("email_sent_title", "Email Sent")
            email_sent_msg = self.get_text("email_sent_msg", "Excel report with new and historical contracts sent to the manager!")
            QMessageBox.information(self, email_sent_title, email_sent_msg)
            self.selected_files.clear()
            self.current_processed_data = []
            self.file_label.setText(self.get_text("no_documents_selected", "No documents selected"))
        else:
            QMessageBox.warning(
                self, 
                self.get_text("email_error_title", "Email Error"), 
                self.get_text("email_error_msg", "Could not send email. Please check your internet connection or email settings in the 'Settings' tab.")
            )

        self.send_button.setEnabled(True)
        self.send_button.setText(self.get_text("send_report_to_boss", "✉️ Send Report to Boss"))
        
    @staticmethod
    def format_results(data, processed_document: ProcessedPDF):
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; margin-bottom: 10px;">
            <div style="margin-bottom: 10px; font-size: 12px; opacity: 0.7;">Pages analyzed: {processed_document.page_count}</div>
            <table width="100%" cellspacing="0" cellpadding="6" style="font-size: 14px; border-collapse: collapse;">
        """
        for field_name, field in data.items():
            value = str(field["value"])
            if "Not found" in value or value == str(NOT_FOUND):
                value_html = f"<i style='color: #e1b12c;'>{value}</i>"
            elif field_name == "Price":
                value_html = f"<b style='color: #27ae60; font-size: 15px;'>{value}</b>"
            elif field_name in ["Company", "NIP", "Status"]:
                value_html = f"<b>{value}</b>"
            else:
                value_html = f"<span>{value}</span>"

            html += f"""
                <tr>
                    <td width="35%" style="border-bottom: 1px solid rgba(130, 130, 130, 0.3); opacity: 0.8;"><b>{field_name}</b></td>
                    <td style="border-bottom: 1px solid rgba(130, 130, 130, 0.3);">{value_html}</td>
                </tr>
            """
        html += "</table></div>"
        return html

    def set_language(self, lang: dict):
        """Обновляет все тексты на странице документов при смене языка"""
        self.current_lang = lang

        if hasattr(self, "title"):
            self.title.setText(lang.get("documents", "📑 Documents"))

        if hasattr(self, "description"):
            self.description.setText(
                lang.get(
                    "documents_description", 
                    "Upload PDF documents. DocAuthorize will read the text, save clients to the DB, sort files (Signed/Pending). Then you can send a full report to the manager."
                )
            )

        if hasattr(self, "file_label") and not self.selected_files:
            self.file_label.setText(lang.get("no_documents_selected", "No documents selected"))

        if hasattr(self, "result_box"):
            self.result_box.setPlaceholderText(
                lang.get("document_analysis_placeholder", "The document analysis will appear here."))

        if hasattr(self, "upload_button"):
            self.upload_button.setText(lang.get("upload_pdfs", "📄 Upload PDFs"))

        if hasattr(self, "save_button"):
            self.save_button.setText(lang.get("process_save_db", "Process and save to DB"))

        if hasattr(self, "send_button"):
            self.send_button.setText(lang.get("send_report_to_boss", "Send report to boss"))

#.
            