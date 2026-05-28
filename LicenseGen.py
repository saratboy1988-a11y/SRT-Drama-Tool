# -*- coding: utf-8 -*-
import sys
import hashlib
import hmac
import base64
import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, QFormLayout)
from PyQt5.QtGui import QFont

# === SECRET KEY (ត្រូវតែដូចគ្នាជាមួយ RVC Tool.py) ===
# WARNING: Keep this file PRIVATE. Do not distribute it to customers.
# ហាមចែកចាយ file នេះទៅអតិថិជន ព្រោះវាមានលេខកូដសម្ងាត់សម្រាប់បង្កើត License
LICENSE_SECRET_PLAIN = "DRAMA_TOOL_RVC_SECRET_KEY_2024"
LICENSE_SECRET = hashlib.sha256(LICENSE_SECRET_PLAIN.encode()).hexdigest()

class LicenseGenerator(QWidget):
    txt_machine_id: QLineEdit
    txt_email: QLineEdit
    cb_duration: QComboBox
    txt_output: QLineEdit
    btn_gen: QPushButton
    btn_copy: QPushButton

    def __init__(self):
        super().__init__()
        self.setWindowTitle("License Generator (កម្មវិធីបង្កើតកូដ)")
        self.resize(400, 300)
        self.setFont(QFont("Segoe UI", 10))
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # Inputs
        self.txt_machine_id = QLineEdit()
        self.txt_machine_id.setPlaceholderText("Paste Machine ID here...")
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Customer Email...")
        
        self.cb_duration = QComboBox()
        self.cb_duration.addItems(["1 Month (១ ខែ)", "6 Months (៦ ខែ)", "1 Year (១ ឆ្នាំ)", "Lifetime (មួយជីវិត)"])
        
        form.addRow("Machine ID (លេខកូដម៉ាស៊ីន):", self.txt_machine_id)
        form.addRow("Email (អ៊ីមែល):", self.txt_email)
        form.addRow("Duration (រយះពេល):", self.cb_duration)
        
        layout.addLayout(form)
        
        # Generate Button
        self.btn_gen = QPushButton("Generate License (បង្កើតកូដ)")
        self.btn_gen.clicked.connect(self.generate_key)
        self.btn_gen.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(self.btn_gen)
        
        # Output
        layout.addWidget(QLabel("Generated License Key:"))
        self.txt_output = QLineEdit()
        self.txt_output.setReadOnly(True)
        layout.addWidget(self.txt_output)
        
        # Copy Button
        self.btn_copy = QPushButton("Copy (ចម្លង)")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.btn_copy)
        
        self.setLayout(layout)

    def generate_key(self):
        # Type guard for Pylance (ការពារកំហុស reportOptionalMemberAccess)
        if self.txt_machine_id is None or self.txt_email is None or self.cb_duration is None:
            return
            
        mid = self.txt_machine_id.text().strip().replace("|", "")
        email = self.txt_email.text().strip().replace("|", "")
        
        if not mid or not email:
            QMessageBox.warning(self, "Error", "Please fill Machine ID and Email!")
            return
            
        # Calculate Expiry
        duration_idx = self.cb_duration.currentIndex()
        if duration_idx == 3: # Lifetime
            expiry_str = "LIFETIME"
        else:
            days = 30
            if duration_idx == 1: days = 180
            elif duration_idx == 2: days = 365
            
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
            # Convert to int to remove decimals (ធ្វើអោយកូដខ្លីជាងមុនបន្តិចដោយកាត់កន្ទុយទសភាគ)
            expiry_str = str(int(expiry_date.timestamp()))
            
        # Create Payload: email|machine_id|expiry
        payload = f"{email}|{mid}|{expiry_str}"
        
        # Sign
        signature = hmac.new(LICENSE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        # Encode
        final_data = f"{payload}::{signature}"
        license_key = base64.b64encode(final_data.encode()).decode()
        
        if self.txt_output is not None:
            self.txt_output.setText(license_key)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        # Type guard for Pylance: Ensure both clipboard and widget exist
        if clipboard is not None and self.txt_output is not None:
            clipboard.setText(self.txt_output.text())
            QMessageBox.information(self, "Copied", "License key copied to clipboard!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LicenseGenerator()
    window.show()
    sys.exit(app.exec_())