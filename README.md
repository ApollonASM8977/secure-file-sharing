# ðŸ” SecureShare

> End-to-end encrypted file sharing over local network — built with Python, PyQt6 and real cryptography.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)
![License](https://img.shields.io/badge/License-Proprietary-red)
![Security](https://img.shields.io/badge/Crypto-AES256%20%2B%20RSA2048-red)

---

## What is SecureShare?

SecureShare is a desktop application for **securely sharing files across a local network (LAN)**.  
Every file is encrypted before transmission using industry-standard cryptography — no plaintext ever leaves your machine.

---

## Features

| Feature | Details |
|---|---|
| 🔒 File Encryption | AES-256-CBC with PBKDF2-derived keys (260,000 iterations) |
| ðŸ”‘ Key Exchange | RSA-2048 (OAEP) — each user has a unique key pair |
| ðŸ“ Folder Encryption | Entire folders archived and encrypted as a single blob |
| âœ… Integrity Verification | SHA-256 hash stored alongside every encrypted file |
| ðŸŒ LAN Discovery | Automatic subnet scan to find peers running SecureShare |
| ðŸ“¤ File Transfer | Direct peer-to-peer transfer via embedded Flask server |
| ðŸ‘¥ Multi-Recipient | Encrypt one file for multiple users simultaneously |
| ðŸ›¡ï¸ Admin Panel | User management, key regeneration, encrypted backup/restore |
| ðŸ”„ Key Rotation | Regenerate your RSA key pair at any time |

---

## Security Model

```
Password  ──â–º PBKDF2-HMAC-SHA256 (260k iter) ──â–º AES-256 key
                                                        │
File ──────────────────────────────────────────â–º AES-CBC encrypt ──â–º .enc file
                                                        │
AES key ──â–º RSA-OAEP (recipient's public key) ──â–º embedded in .enc
```

- **No hardcoded keys** — all keys are derived from user passwords with a unique random salt
- **Salt stored per file** — each encrypted file has its own PBKDF2 salt
- **Integrity guaranteed** — SHA-256 hash verified on every decrypt
- **Passwords hashed with bcrypt** (cost factor 12)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/ApollonASM8977/secure-file-sharing.git
cd secure-file-sharing

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Requirements
- Python 3.11+
- Windows / Linux / macOS

---

## Project Structure

```
SecureFileSharing/
├── main.py            # Entry point + main app window
├── admin_panel.py     # Admin panel
├── auth.py            # Login & Register dialogs
├── network.py         # Flask server + LAN device discovery
├── styles.py          # Dark theme stylesheet
├── config.py          # App constants & security parameters
├── utils.py           # Crypto helpers, user management, logging
├── requirements.txt
├── .gitignore
├── users.json.example # Sample user DB structure
├── keys/              # RSA key pairs (gitignored)
└── shared_files/      # Received files (gitignored)
```

---

## Usage

1. **Register** — create an account (RSA key pair generated automatically)
2. **Scan** — discover other devices running SecureShare on your network
3. **Encrypt** — select a file, choose a password and recipients
4. **Send** — transfer the `.enc` file to a peer device
5. **Decrypt** — the recipient decrypts with their password + private key
6. **Verify** — check that the file hasn't been modified since encryption

---

## Tech Stack

- **GUI** — PyQt6
- **Cryptography** — PyCryptodome (AES-256, RSA-2048, PKCS1-OAEP)
- **Key Derivation** — PBKDF2-HMAC-SHA256 (hashlib)
- **Authentication** — bcrypt
- **Server** — Flask (embedded, LAN only)
- **Discovery** — concurrent socket scanning (ThreadPoolExecutor)

---

## Author

**Aboubacar Sidick Meite** — Cybersecurity Student  
[GitHub](https://github.com/ApollonASM8977)

---

## License

© 2025 Aboubacar Sidick Meite — All Rights Reserved.  
See [LICENSE](LICENSE) for details.

