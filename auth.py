"""Login and Registration dialogs."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt

from styles import DARK_THEME
from config import APP_NAME
from utils import (
    load_users, save_users, hash_password, verify_password,
    is_strong_password, generate_rsa_keys,
)


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setFixedSize(420, 400)
        self.setStyleSheet(DARK_THEME)
        self.username: str | None = None
        self.full_name: str | None = None
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(44, 44, 44, 44)

        icon = QLabel("🔐")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 40px; background: transparent; padding-bottom: 4px;")
        layout.addWidget(icon)

        title = QLabel("Welcome back")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Sign in to SecureShare")
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacerItem(QSpacerItem(0, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(42)
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(42)
        self.password_input.returnPressed.connect(self._login)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("badgeRed")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #f85149; font-size: 12px; background: transparent;")
        layout.addWidget(self.error_label)

        layout.addSpacerItem(QSpacerItem(0, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("primaryBtn")
        login_btn.setFixedHeight(42)
        login_btn.clicked.connect(self._login)
        layout.addWidget(login_btn)

        reg_btn = QPushButton("Create an account")
        reg_btn.setFixedHeight(38)
        reg_btn.clicked.connect(self._open_register)
        layout.addWidget(reg_btn)

        self.setLayout(layout)

    def _login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText("Please fill in all fields.")
            return

        users = load_users()
        user = users.get(username)

        if not user or not verify_password(password, user["password"]):
            self.error_label.setText("Invalid username or password.")
            return

        if user.get("status") == "suspended":
            self.error_label.setText("This account has been suspended.")
            return

        self.username = username
        self.full_name = user.get("full_name", username).title()
        self.accept()

    def _open_register(self):
        reg = RegisterWindow(self)
        if reg.exec() == QDialog.DialogCode.Accepted:
            self.username = reg.username
            self.full_name = reg.full_name
            self.accept()


class RegisterWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Create Account")
        self.setFixedSize(420, 480)
        self.setStyleSheet(DARK_THEME)
        self.username: str | None = None
        self.full_name: str | None = None
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(44, 36, 44, 36)

        title = QLabel("Create account")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        sub = QLabel("Fill in your details below")
        sub.setObjectName("subtitleLabel")
        layout.addWidget(sub)

        layout.addSpacerItem(QSpacerItem(0, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        fields = [
            ("Full Name", "full_name_input", False, "Your full name"),
            ("Username", "username_input", False, "Choose a unique username"),
            ("Password", "password_input", True, "≥8 chars, A-Z, a-z, 0-9, symbol"),
            ("Confirm Password", "confirm_input", True, "Repeat your password"),
        ]
        for label_text, attr, is_pwd, placeholder in fields:
            layout.addWidget(QLabel(label_text))
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setFixedHeight(42)
            if is_pwd:
                field.setEchoMode(QLineEdit.EchoMode.Password)
            setattr(self, attr, field)
            layout.addWidget(field)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f85149; font-size: 12px; background: transparent;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        layout.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        reg_btn = QPushButton("Create Account")
        reg_btn.setObjectName("primaryBtn")
        reg_btn.setFixedHeight(42)
        reg_btn.clicked.connect(self._register)
        layout.addWidget(reg_btn)

        back_btn = QPushButton("Back to Login")
        back_btn.setFixedHeight(38)
        back_btn.clicked.connect(self.reject)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def _register(self):
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not all([full_name, username, password, confirm]):
            self.error_label.setText("All fields are required.")
            return
        if not is_strong_password(password):
            self.error_label.setText(
                "Password must be ≥8 chars with uppercase, lowercase, digit, and special character."
            )
            return
        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        users = load_users()
        if username in users:
            self.error_label.setText("Username already taken.")
            return

        users[username] = {
            "full_name": full_name,
            "password": hash_password(password),
            "status": "active",
        }
        save_users(users)
        generate_rsa_keys(username)

        self.username = username
        self.full_name = full_name.title()
        self.accept()
