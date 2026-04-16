"""SecureShare — Admin panel."""

import datetime
import hashlib
import os
import shutil

from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QFrame, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListWidget,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from config import (
    APP_NAME, BACKUP_DIR, DEVICE_NAMES_FILE,
    KEYS_DIR, LOG_FILE, UPLOAD_FOLDER, USER_DB,
)
from styles import DARK_THEME
from utils import generate_rsa_keys, hash_password, load_users, save_users


class AdminPanel(QWidget):
    def __init__(self, username: str, full_name: str):
        super().__init__()
        self.username = username
        self.full_name = full_name
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"{APP_NAME}  ·  Admin Panel")
        self.setMinimumSize(560, 480)
        self.setStyleSheet(DARK_THEME)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)

        lbl = QLabel(f"🔐  {APP_NAME}  ·  Admin")
        lbl.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #ffffff; background: transparent;"
        )
        hl.addWidget(lbl)
        hl.addStretch()

        badge = QLabel(f"🛡️  {self.full_name}")
        badge.setStyleSheet("color: #d29922; font-size: 13px; background: transparent;")
        hl.addWidget(badge)

        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet("padding: 0 14px; font-size: 12px;")
        logout_btn.clicked.connect(self._logout)
        hl.addWidget(logout_btn)
        root.addWidget(header)

        # Body
        body = QVBoxLayout()
        body.setContentsMargins(24, 24, 24, 24)
        body.setSpacing(12)

        section = QLabel("ADMINISTRATION")
        section.setObjectName("sectionLabel")
        body.addWidget(section)

        buttons = [
            ("👥   Manage Users",         None,         self._manage_users),
            ("➕   Create New User",       "primaryBtn", self._create_user),
            ("🔑   Regenerate User Keys", "warnBtn",    self._manage_keys),
            ("💾   Backup Data",          None,         self._backup_data),
            ("♻️   Restore Backup",       None,         self._restore_data),
        ]
        for text, obj, slot in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(44)
            if obj:
                btn.setObjectName(obj)
            btn.clicked.connect(slot)
            body.addWidget(btn)

        body.addStretch()
        root.addLayout(body)
        self.setLayout(root)

    # ── User management ───────────────────────────────────────────────────────

    def _manage_users(self):
        win = QWidget()
        win.setWindowTitle("Manage Users")
        win.setStyleSheet(DARK_THEME)
        win.resize(500, 400)
        layout = QVBoxLayout(win)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("All registered users:"))
        user_list = QListWidget()
        self._populate(user_list)
        layout.addWidget(user_list)

        btn_row = QHBoxLayout()
        suspend_btn = QPushButton("Suspend / Activate")
        suspend_btn.clicked.connect(lambda: self._toggle_suspend(user_list))
        btn_row.addWidget(suspend_btn)

        delete_btn = QPushButton("Delete User")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(lambda: self._delete_user(user_list))
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        win.show()
        self._user_win = win

    def _populate(self, lw: QListWidget):
        lw.clear()
        for uname, data in load_users().items():
            role = "Admin" if uname.lower() == "admin" else "User"
            status = data.get("status", "active")
            icon = "🟢" if status == "active" else "🔴"
            lw.addItem(f"{icon}  {data['full_name']}  ({uname})  [{role}]  — {status}")

    def _toggle_suspend(self, lw: QListWidget):
        item = lw.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a user first.")
            return
        uname = item.text().split("(")[1].split(")")[0].strip()
        users = load_users()
        current = users[uname].get("status", "active")
        users[uname]["status"] = "suspended" if current == "active" else "active"
        save_users(users)
        self._populate(lw)
        QMessageBox.information(self, "Done", f"'{uname}' is now {users[uname]['status']}.")

    def _delete_user(self, lw: QListWidget):
        item = lw.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a user first.")
            return
        uname = item.text().split("(")[1].split(")")[0].strip()
        if uname.lower() == "admin":
            QMessageBox.critical(self, "Forbidden", "Cannot delete the admin account.")
            return
        if QMessageBox.question(
            self, "Confirm", f"Permanently delete '{uname}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        users = load_users()
        users.pop(uname, None)
        save_users(users)
        for kt in ("private", "public"):
            p = os.path.join(KEYS_DIR, f"{uname}_{kt}.pem")
            if os.path.exists(p):
                os.remove(p)
        self._populate(lw)
        QMessageBox.information(self, "Deleted", f"User '{uname}' deleted.")

    # ── Create user ───────────────────────────────────────────────────────────

    def _create_user(self):
        win = QWidget()
        win.setWindowTitle("Create New User")
        win.setStyleSheet(DARK_THEME)
        win.resize(380, 320)
        layout = QVBoxLayout(win)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Full Name"))
        fn_input = QLineEdit()
        fn_input.setFixedHeight(40)
        layout.addWidget(fn_input)

        layout.addWidget(QLabel("Username"))
        un_input = QLineEdit()
        un_input.setFixedHeight(40)
        layout.addWidget(un_input)

        layout.addWidget(QLabel("Password"))
        pw_input = QLineEdit()
        pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        pw_input.setFixedHeight(40)
        layout.addWidget(pw_input)

        err = QLabel("")
        err.setStyleSheet("color: #f85149; font-size: 12px; background: transparent;")
        layout.addWidget(err)

        def _save():
            full = fn_input.text().strip()
            uname = un_input.text().strip()
            pwd = pw_input.text()
            if not all([full, uname, pwd]):
                err.setText("All fields are required.")
                return
            users = load_users()
            if uname in users:
                err.setText("Username already exists.")
                return
            users[uname] = {
                "full_name": full,
                "password": hash_password(pwd),
                "status": "active",
            }
            save_users(users)
            generate_rsa_keys(uname)
            QMessageBox.information(self, "Created", f"User '{uname}' created.")
            win.close()

        btn = QPushButton("Create User")
        btn.setObjectName("primaryBtn")
        btn.setFixedHeight(42)
        btn.clicked.connect(_save)
        layout.addWidget(btn)

        win.show()
        self._create_win = win

    # ── Key management ────────────────────────────────────────────────────────

    def _manage_keys(self):
        win = QWidget()
        win.setWindowTitle("Regenerate RSA Keys")
        win.setStyleSheet(DARK_THEME)
        win.resize(340, 300)
        layout = QVBoxLayout(win)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Select user to regenerate RSA key pair:"))
        lw = QListWidget()
        for uname in load_users():
            lw.addItem(uname)
        layout.addWidget(lw)

        def _regen():
            item = lw.currentItem()
            if not item:
                return
            generate_rsa_keys(item.text())
            QMessageBox.information(win, "Done", f"Keys regenerated for '{item.text()}'.")

        btn = QPushButton("Regenerate Keys")
        btn.setObjectName("warnBtn")
        btn.setFixedHeight(42)
        btn.clicked.connect(_regen)
        layout.addWidget(btn)

        win.show()
        self._keys_win = win

    # ── Backup / Restore ──────────────────────────────────────────────────────

    def _backup_data(self):
        password, ok = QInputDialog.getText(
            self, "Backup Password", "Password to encrypt backup:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not password:
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = os.path.join(BACKUP_DIR, f"backup_{ts}")
        os.makedirs(folder, exist_ok=True)

        for item in [USER_DB, LOG_FILE, DEVICE_NAMES_FILE, KEYS_DIR, UPLOAD_FOLDER]:
            if os.path.exists(item):
                dst = os.path.join(folder, os.path.basename(item))
                shutil.copytree(item, dst) if os.path.isdir(item) else shutil.copy2(item, dst)

        zip_path = folder + ".zip"
        shutil.make_archive(folder, "zip", folder)
        shutil.rmtree(folder)

        key = hashlib.sha256(password.encode()).digest()
        iv = os.urandom(16)
        with open(zip_path, "rb") as f:
            data = f.read()
        enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data, AES.block_size))
        enc_path = zip_path + ".enc"
        with open(enc_path, "wb") as f:
            f.write(iv + enc)
        os.remove(zip_path)

        QMessageBox.information(self, "Backup", f"Saved:\n{enc_path}")

    def _restore_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup", filter="Encrypted Backup (*.enc)"
        )
        if not path:
            return

        password, ok = QInputDialog.getText(
            self, "Restore Password", "Backup password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not password:
            return

        key = hashlib.sha256(password.encode()).digest()
        try:
            with open(path, "rb") as f:
                iv, encrypted = f.read(16), f.read()
            data = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(encrypted), AES.block_size)
        except (ValueError, KeyError):
            QMessageBox.critical(self, "Error", "Incorrect password or corrupted backup.")
            return

        zip_path = path.replace(".enc", "")
        restore_dir = os.path.join(BACKUP_DIR, "restore_temp")
        with open(zip_path, "wb") as f:
            f.write(data)
        shutil.unpack_archive(zip_path, restore_dir)
        os.remove(zip_path)

        for item in os.listdir(restore_dir):
            src = os.path.join(restore_dir, item)
            if os.path.exists(item):
                shutil.rmtree(item) if os.path.isdir(item) else os.remove(item)
            shutil.move(src, item)
        shutil.rmtree(restore_dir)

        QMessageBox.information(self, "Restored", "Backup restored successfully.")

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        from auth import LoginWindow
        from main import SecureShareApp
        self.close()
        login = LoginWindow()
        if login.exec() == QDialog.DialogCode.Accepted:
            if login.username and login.username.lower() == "admin":
                self._next = AdminPanel(login.username, login.full_name)
            else:
                self._next = SecureShareApp(login.username, login.full_name)
            self._next.show()
