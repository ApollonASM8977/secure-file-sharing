"""SecureShare — Main application window and entry point."""

import atexit
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import threading

import requests as req_lib
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFileDialog,
    QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad

from config import (
    APP_NAME, DEVICE_NAMES_FILE, FLASK_PORT,
    KEYS_DIR, UPLOAD_FOLDER,
)
from network import start_server, get_local_ip, discover_devices
from styles import DARK_THEME
from utils import (
    derive_key, generate_rsa_keys, load_rsa_key,
    load_users, log_activity,
)
from auth import LoginWindow


# ── Firewall helpers ──────────────────────────────────────────────────────────

def _firewall(action: str) -> None:
    if platform.system() != "Windows":
        return
    rule_name = f"SecureShare {FLASK_PORT}"
    try:
        if action == "open":
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}", "dir=in", "action=allow",
                 "protocol=TCP", f"localport={FLASK_PORT}"],
                check=True, capture_output=True,
            )
        else:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule",
                 f"name={rule_name}"],
                check=True, capture_output=True,
            )
    except subprocess.CalledProcessError:
        pass


# ── Background scanner ────────────────────────────────────────────────────────

class DeviceScanner(QThread):
    finished = pyqtSignal(list)

    def run(self):
        self.finished.emit(discover_devices())


# ── Welcome screen ────────────────────────────────────────────────────────────

class WelcomeScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(480, 340)
        self.setStyleSheet(DARK_THEME)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(56, 56, 56, 56)

        icon = QLabel("🔐")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 56px; background: transparent;")
        layout.addWidget(icon)

        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("End-to-end encrypted file sharing over LAN")
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacerItem(
            QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        btn = QPushButton("Get Started →")
        btn.setObjectName("primaryBtn")
        btn.setFixedHeight(44)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        self.setLayout(layout)


# ── Main application window ───────────────────────────────────────────────────

class SecureShareApp(QWidget):
    def __init__(self, username: str, full_name: str):
        super().__init__()
        self.current_user = username
        self.full_name = full_name
        self.device_names: dict = self._load_device_names()
        self._build_ui()
        self._scan_devices()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle(f"{APP_NAME}  ·  {self.full_name}")
        self.setMinimumSize(780, 580)
        self.setStyleSheet(DARK_THEME)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addLayout(self._build_body(), stretch=1)
        root.addWidget(self._build_statusbar())
        self.setLayout(root)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(12)

        lbl = QLabel(f"🔐  {APP_NAME}")
        lbl.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #ffffff; background: transparent;"
        )
        hl.addWidget(lbl)
        hl.addStretch()

        self.user_badge = QLabel(f"👤  {self.full_name}")
        self.user_badge.setStyleSheet(
            "color: #8b949e; font-size: 13px; background: transparent;"
        )
        hl.addWidget(self.user_badge)

        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet("padding: 0 14px; font-size: 12px;")
        logout_btn.clicked.connect(self._logout)
        hl.addWidget(logout_btn)
        return header

    def _build_body(self) -> QHBoxLayout:
        body = QHBoxLayout()
        body.setContentsMargins(24, 20, 24, 20)
        body.setSpacing(20)

        # Left panel — actions
        left = QVBoxLayout()
        left.setSpacing(8)

        sec_lbl = QLabel("FILE OPERATIONS")
        sec_lbl.setObjectName("sectionLabel")
        left.addWidget(sec_lbl)

        actions = [
            ("🔒   Encrypt File",     "primaryBtn", self.encrypt_file),
            ("🔓   Decrypt File",     "primaryBtn", self.decrypt_file),
            ("📁   Encrypt Folder",   None,         self.encrypt_folder),
            ("📂   Decrypt Folder",   None,         self.decrypt_folder),
            ("✅   Verify Integrity", None,         self.verify_integrity),
            ("🔑   Rotate RSA Keys",  "warnBtn",    self.rotate_keys),
        ]
        for text, obj, slot in actions:
            btn = QPushButton(text)
            btn.setFixedHeight(42)
            if obj:
                btn.setObjectName(obj)
            btn.clicked.connect(slot)
            left.addWidget(btn)

        left.addStretch()
        body.addLayout(left, stretch=1)

        # Right panel — devices
        right = QVBoxLayout()
        right.setSpacing(8)

        dev_row = QHBoxLayout()
        dev_lbl = QLabel("NETWORK DEVICES")
        dev_lbl.setObjectName("sectionLabel")
        dev_row.addWidget(dev_lbl)
        dev_row.addStretch()

        self.scan_btn = QPushButton("🔄  Scan")
        self.scan_btn.setFixedHeight(28)
        self.scan_btn.setStyleSheet("font-size: 12px; padding: 0 12px;")
        self.scan_btn.clicked.connect(self._scan_devices)
        dev_row.addWidget(self.scan_btn)
        right.addLayout(dev_row)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        lists = QHBoxLayout()
        lists.setSpacing(8)

        ip_col = QVBoxLayout()
        ip_col.addWidget(QLabel("IP Address"))
        self.ip_list = QListWidget()
        self.ip_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.ip_list.setStyleSheet(
            "font-family: 'Courier New', monospace; font-size: 12px;"
        )
        ip_col.addWidget(self.ip_list)
        lists.addLayout(ip_col)

        name_col = QVBoxLayout()
        name_col.addWidget(QLabel("Device Name"))
        self.name_list = QListWidget()
        self.name_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.name_list.itemChanged.connect(self._rename_device)
        name_col.addWidget(self.name_list)
        lists.addLayout(name_col)

        card_layout.addLayout(lists)

        send_btn = QPushButton("📤   Send File(s) to Selected Devices")
        send_btn.setObjectName("primaryBtn")
        send_btn.setFixedHeight(42)
        send_btn.clicked.connect(self.send_files)
        card_layout.addWidget(send_btn)

        right.addWidget(card)
        body.addLayout(right, stretch=2)
        return body

    def _build_statusbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(36)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0)
        bl.setSpacing(12)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "color: #8b949e; font-size: 12px; background: transparent;"
        )
        bl.addWidget(self.status_label)
        bl.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(200, 8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        bl.addWidget(self.progress_bar)
        return bar

    # ── Status helpers ────────────────────────────────────────────────────────

    def _status(self, msg: str, color: str = "#8b949e"):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; background: transparent;"
        )
        QTimer.singleShot(6000, lambda: (
            self.status_label.setText("Ready"),
            self.status_label.setStyleSheet(
                "color: #8b949e; font-size: 12px; background: transparent;"
            ),
        ))

    def _progress(self, value: int):
        self.progress_bar.setValue(value)
        if value >= 100:
            QTimer.singleShot(2000, lambda: self.progress_bar.setValue(0))

    # ── Device scanning ───────────────────────────────────────────────────────

    def _scan_devices(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("⏳  Scanning...")
        self._status("Scanning local network...", "#58a6ff")
        self._scanner = DeviceScanner()
        self._scanner.finished.connect(self._on_scan_done)
        self._scanner.start()

    def _on_scan_done(self, peers: list):
        self.ip_list.clear()
        self.name_list.clear()
        local_ip = get_local_ip()
        all_ips = [local_ip] + peers

        for ip in all_ips:
            self.ip_list.addItem(ip)
            if ip == local_ip:
                item = QListWidgetItem("💻  This Device")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            else:
                name = self.device_names.get(ip, "Unknown Device")
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.device_names.setdefault(ip, name)
            self.name_list.addItem(item)

        self._save_device_names()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔄  Scan")
        self._status(f"Found {len(peers)} peer(s) on network.", "#3fb950")

    def _load_device_names(self) -> dict:
        if os.path.exists(DEVICE_NAMES_FILE):
            with open(DEVICE_NAMES_FILE, "r") as f:
                return json.load(f)
        return {}

    def _save_device_names(self):
        with open(DEVICE_NAMES_FILE, "w") as f:
            json.dump(self.device_names, f, indent=2)

    def _rename_device(self, item: QListWidgetItem):
        row = self.name_list.row(item)
        ip_item = self.ip_list.item(row)
        if ip_item:
            self.device_names[ip_item.text()] = item.text()
            self._save_device_names()

    # ── Crypto helpers ────────────────────────────────────────────────────────

    def _get_rsa_key(self, username: str, key_type: str = "private"):
        key = load_rsa_key(username, key_type)
        if key is None:
            QMessageBox.critical(
                self, "Key Error",
                f"Missing {key_type} key for '{username}'.",
            )
        return key

    def _ask_password(self, action: str = "encryption"):
        pwd, ok = QInputDialog.getText(
            self, f"{action.title()} Password",
            f"Enter the {action} password:",
            QLineEdit.EchoMode.Password,
        )
        return pwd if ok and pwd else None

    # ── Encrypt file ──────────────────────────────────────────────────────────

    def encrypt_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Encrypt")
        if not path:
            return

        password = self._ask_password("encryption")
        if not password:
            return

        users = load_users()
        candidates = [u for u in users if u != self.current_user]
        if not candidates:
            QMessageBox.warning(self, "No Recipients", "No other registered users found.")
            return

        # Recipient picker
        dlg = QDialog(self)
        dlg.setWindowTitle("Select Recipients")
        dlg.setStyleSheet(DARK_THEME)
        dlg.resize(300, 360)
        dl = QVBoxLayout(dlg)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.addWidget(QLabel("Select one or more recipients:"))
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for u in candidates:
            lw.addItem(u)
        dl.addWidget(lw)
        ok_btn = QPushButton("Encrypt for Selected")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.clicked.connect(dlg.accept)
        dl.addWidget(ok_btn)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        recipients = [i.text() for i in lw.selectedItems()]
        if not recipients:
            QMessageBox.warning(self, "No Selection", "Select at least one recipient.")
            return

        try:
            self._progress(10)
            self._status("Reading file...", "#58a6ff")
            with open(path, "rb") as f:
                plaintext = f.read()

            with open(path + ".hash", "w") as f:
                f.write(hashlib.sha256(plaintext).hexdigest())

            self._progress(25)
            self._status("Deriving key (PBKDF2)...", "#58a6ff")
            salt = os.urandom(16)
            iv = os.urandom(16)
            aes_key = derive_key(password, salt)

            self._progress(50)
            self._status("Encrypting (AES-256-CBC)...", "#58a6ff")
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

            self._progress(75)
            self._status("Wrapping keys (RSA-2048)...", "#58a6ff")
            enc_path = path + ".enc"
            with open(enc_path, "wb") as f:
                f.write(iv)
                f.write(salt)
                f.write(len(recipients).to_bytes(1, "big"))
                for recipient in recipients:
                    pub = self._get_rsa_key(recipient, "public")
                    if pub:
                        f.write(PKCS1_OAEP.new(pub).encrypt(aes_key))
                f.write(ciphertext)

            self._progress(100)
            log_activity("encrypt", os.path.basename(path), self.current_user)
            self._status(f"Encrypted for {', '.join(recipients)}", "#3fb950")
            QMessageBox.information(
                self, "Success",
                f"File encrypted successfully.\n\nSaved as: {os.path.basename(enc_path)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Encryption Error", str(e))
            self._status("Encryption failed.", "#f85149")

    # ── Decrypt file ──────────────────────────────────────────────────────────

    def decrypt_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Encrypted File",
            filter="Encrypted Files (*.enc);;All Files (*)",
        )
        if not path:
            return

        password = self._ask_password("decryption")
        if not password:
            return

        try:
            self._progress(10)
            self._status("Loading private key...", "#58a6ff")
            private_key = self._get_rsa_key(self.current_user, "private")
            if not private_key:
                return

            with open(path, "rb") as f:
                iv = f.read(16)
                salt = f.read(16)
                num_keys = int.from_bytes(f.read(1), "big")
                enc_keys = [f.read(256) for _ in range(num_keys)]
                ciphertext = f.read()

            self._progress(30)
            self._status("Deriving key (PBKDF2)...", "#58a6ff")
            aes_key = derive_key(password, salt)
            rsa = PKCS1_OAEP.new(private_key)

            self._progress(50)
            found = None
            for enc_key in enc_keys:
                try:
                    candidate = rsa.decrypt(enc_key)
                    if candidate == aes_key:
                        found = candidate
                        break
                except ValueError:
                    continue

            if found is None:
                QMessageBox.critical(
                    self, "Access Denied",
                    "You are not an authorized recipient, or the password is incorrect.",
                )
                self._status("Decryption failed — unauthorized.", "#f85149")
                self._progress(0)
                return

            self._progress(70)
            self._status("Decrypting (AES-256-CBC)...", "#58a6ff")
            cipher = AES.new(found, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

            out_path = path.replace(".enc", "")
            with open(out_path, "wb") as f:
                f.write(plaintext)

            self._progress(90)
            hash_file = out_path + ".hash"
            if os.path.exists(hash_file):
                with open(hash_file, "r") as f:
                    stored = f.read().strip()
                if hashlib.sha256(plaintext).hexdigest() != stored:
                    QMessageBox.critical(
                        self, "Integrity Failure",
                        "Hash mismatch — this file may have been tampered with!",
                    )
                    self._status("Integrity check FAILED.", "#f85149")
                    self._progress(0)
                    return

            self._progress(100)
            log_activity("decrypt", os.path.basename(path), self.current_user)
            self._status(f"Decrypted: {os.path.basename(out_path)}", "#3fb950")
            QMessageBox.information(
                self, "Success",
                f"File decrypted and integrity verified.\n\nSaved as: {os.path.basename(out_path)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Decryption Error", str(e))
            self._status("Decryption failed.", "#f85149")

    # ── Encrypt folder ────────────────────────────────────────────────────────

    def encrypt_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Encrypt")
        if not folder:
            return
        password = self._ask_password("encryption")
        if not password:
            return
        recipient, ok = QInputDialog.getText(self, "Recipient", "Recipient username:")
        if not ok or not recipient:
            return

        pub = self._get_rsa_key(recipient, "public")
        if not pub:
            return

        try:
            self._status("Archiving folder...", "#58a6ff")
            self._progress(20)
            salt = os.urandom(16)
            iv = os.urandom(16)
            aes_key = derive_key(password, salt)
            temp_tar = folder + ".tar"
            enc_path = folder + ".fold.enc"

            with tarfile.open(temp_tar, "w") as tar:
                tar.add(folder, arcname=os.path.basename(folder))

            self._progress(50)
            with open(temp_tar, "rb") as f:
                data = f.read()

            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(data, AES.block_size))
            enc_aes_key = PKCS1_OAEP.new(pub).encrypt(aes_key)

            with open(enc_path, "wb") as f:
                f.write(iv + salt + enc_aes_key + ciphertext)

            os.remove(temp_tar)
            self._progress(100)
            log_activity("encrypt_folder", os.path.basename(folder), self.current_user)
            self._status("Folder encrypted.", "#3fb950")
            QMessageBox.information(self, "Success", f"Folder encrypted:\n{enc_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── Decrypt folder ────────────────────────────────────────────────────────

    def decrypt_folder(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Encrypted Folder",
            filter="Encrypted Folder (*.fold.enc)",
        )
        if not path:
            return
        password = self._ask_password("decryption")
        if not password:
            return

        private_key = self._get_rsa_key(self.current_user, "private")
        if not private_key:
            return

        try:
            self._progress(20)
            with open(path, "rb") as f:
                iv = f.read(16)
                salt = f.read(16)
                enc_aes_key = f.read(256)
                ciphertext = f.read()

            try:
                aes_key = PKCS1_OAEP.new(private_key).decrypt(enc_aes_key)
            except ValueError:
                QMessageBox.critical(self, "Access Denied",
                                     "You are not authorized to decrypt this folder.")
                return

            if aes_key != derive_key(password, salt):
                QMessageBox.critical(self, "Wrong Password", "Incorrect password.")
                return

            self._progress(60)
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            data = unpad(cipher.decrypt(ciphertext), AES.block_size)

            out_dir = path.replace(".fold.enc", "_decrypted")
            temp_tar = path.replace(".fold.enc", ".tar")
            with open(temp_tar, "wb") as f:
                f.write(data)
            os.makedirs(out_dir, exist_ok=True)
            with tarfile.open(temp_tar, "r") as tar:
                tar.extractall(path=out_dir)
            os.remove(temp_tar)

            self._progress(100)
            log_activity("decrypt_folder", os.path.basename(path), self.current_user)
            self._status("Folder decrypted.", "#3fb950")
            QMessageBox.information(self, "Success", f"Folder decrypted:\n{out_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── Integrity verification ────────────────────────────────────────────────

    def verify_integrity(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Verify")
        if not path:
            return
        hash_file = path + ".hash"
        if not os.path.exists(hash_file):
            QMessageBox.warning(self, "No Hash", "No .hash file found for this file.")
            return
        try:
            with open(hash_file, "r") as f:
                stored = f.read().strip()
            with open(path, "rb") as f:
                current = hashlib.sha256(f.read()).hexdigest()

            if stored == current:
                self._status("Integrity verified ✓", "#3fb950")
                QMessageBox.information(self, "OK", "File has not been tampered with.")
            else:
                self._status("Integrity FAILED ✗", "#f85149")
                QMessageBox.critical(self, "Tampered",
                                     "Hash mismatch — the file has been modified!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── Rotate RSA keys ───────────────────────────────────────────────────────

    def rotate_keys(self):
        if QMessageBox.question(
            self, "Rotate Keys",
            "Regenerate your RSA key pair?\n\n"
            "Files encrypted for you with the old key will no longer be decryptable.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            generate_rsa_keys(self.current_user)
            self._status("RSA keys rotated.", "#3fb950")
            QMessageBox.information(self, "Done", "New RSA-2048 key pair generated.")

    # ── Send files ────────────────────────────────────────────────────────────

    def send_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Send")
        if not files:
            return

        local_ip = get_local_ip()
        target_ips = [
            item.text() for item in self.ip_list.selectedItems()
            if item.text() != local_ip
        ]
        if not target_ips:
            QMessageBox.warning(self, "No Target", "Select at least one remote device.")
            return

        success, failed = 0, []
        for ip in target_ips:
            for fp in files:
                try:
                    with open(fp, "rb") as f:
                        r = req_lib.post(
                            f"http://{ip}:{FLASK_PORT}/upload",
                            files={"file": f},
                            timeout=5,
                        )
                    if r.status_code == 200:
                        success += 1
                    else:
                        failed.append(f"{os.path.basename(fp)} → {ip}")
                except Exception:
                    failed.append(f"{os.path.basename(fp)} → {ip}")

        if success and not failed:
            self._status(f"Sent {success} file(s) successfully.", "#3fb950")
            QMessageBox.information(self, "Done", f"{success} file(s) sent.")
        elif failed:
            QMessageBox.warning(
                self, "Partial",
                f"{success} sent, {len(failed)} failed:\n" + "\n".join(failed),
            )

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        from admin_panel import AdminPanel
        self.close()
        login = LoginWindow()
        if login.exec() == QDialog.DialogCode.Accepted:
            if login.username and login.username.lower() == "admin":
                self._next = AdminPanel(login.username, login.full_name)
            else:
                self._next = SecureShareApp(login.username, login.full_name)
            self._next.show()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    from admin_panel import AdminPanel

    _firewall("open")
    atexit.register(_firewall, "close")

    flask_thread = threading.Thread(target=start_server, daemon=True)
    flask_thread.start()

    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")

    if WelcomeScreen().exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    login = LoginWindow()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    if login.username and login.username.lower() == "admin":
        window = AdminPanel(login.username, login.full_name)
    else:
        window = SecureShareApp(login.username, login.full_name)

    window.show()
    try:
        sys.exit(qt_app.exec())
    finally:
        _firewall("close")


if __name__ == "__main__":
    main()
