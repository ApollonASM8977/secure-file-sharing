APP_NAME = "SecureShare"
VERSION = "2.0.0"

FLASK_PORT = 5000
UPLOAD_FOLDER = "shared_files"
USER_DB = "users.json"
KEYS_DIR = "keys"
LOG_FILE = "logs.json"
DEVICE_NAMES_FILE = "device_names.json"
BACKUP_DIR = "backup"

# Security
PBKDF2_ITERATIONS = 260_000   # OWASP 2024 recommendation
RSA_KEY_SIZE = 2048
AES_KEY_SIZE = 32              # AES-256
