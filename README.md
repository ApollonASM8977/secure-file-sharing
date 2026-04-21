# ðŸ” SecureShare

> End-to-end encrypted file sharing over local network â€” built with Python, PyQt6 and real cryptography.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)
![License](https://img.shields.io/badge/License-Proprietary-red)
![Security](https://img.shields.io/badge/Crypto-AES256%20%2B%20RSA2048-red)

---

## What is SecureShare?

SecureShare is a desktop application for **securely sharing files across a local network (LAN)**.  
Every file is encrypted before transmission using industry-standard cryptography â€” no plaintext ever leaves your machine.

---

## Features

| Feature | Details |
|---|---|
| ðŸ”’ File Encryption | AES-256-CBC with PBKDF2-derived keys (260,000 iterations) |
| ðŸ”‘ Key Exchange | RSA-2048 (OAEP) â€” each user has a unique key pair |
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
Password  â”€â”€â–º PBKDF2-HMAC-SHA256 (260k iter) â”€â”€â–º AES-256 key
                                                        â”‚
File â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º AES-CBC encrypt â”€â”€â–º .enc file
                                                        â”‚
AES key â”€â”€â–º RSA-OAEP (recipient's public key) â”€â”€â–º embedded in .enc
```

- **No hardcoded keys** â€” all keys are derived from user passwords with a unique random salt
- **Salt stored per file** â€” each encrypted file has its own PBKDF2 salt
- **Integrity guaranteed** â€” SHA-256 hash verified on every decrypt
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
â”œâ”€â”€ main.py            # Entry point + main app window
â”œâ”€â”€ admin_panel.py     # Admin panel
â”œâ”€â”€ auth.py            # Login & Register dialogs
â”œâ”€â”€ network.py         # Flask server + LAN device discovery
â”œâ”€â”€ styles.py          # Dark theme stylesheet
â”œâ”€â”€ config.py          # App constants & security parameters
â”œâ”€â”€ utils.py           # Crypto helpers, user management, logging
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .gitignore
â”œâ”€â”€ users.json.example # Sample user DB structure
â”œâ”€â”€ keys/              # RSA key pairs (gitignored)
â””â”€â”€ shared_files/      # Received files (gitignored)
```

---

## Usage

1. **Register** â€” create an account (RSA key pair generated automatically)
2. **Scan** â€” discover other devices running SecureShare on your network
3. **Encrypt** â€” select a file, choose a password and recipients
4. **Send** â€” transfer the `.enc` file to a peer device
5. **Decrypt** â€” the recipient decrypts with their password + private key
6. **Verify** â€” check that the file hasn't been modified since encryption

---

## Tech Stack

- **GUI** â€” PyQt6
- **Cryptography** â€” PyCryptodome (AES-256, RSA-2048, PKCS1-OAEP)
- **Key Derivation** â€” PBKDF2-HMAC-SHA256 (hashlib)
- **Authentication** â€” bcrypt
- **Server** â€” Flask (embedded, LAN only)
- **Discovery** â€” concurrent socket scanning (ThreadPoolExecutor)

---

## Author

**Aboubacar Sidick Meite** â€” Cybersecurity Student  
[GitHub](https://github.com/ApollonASM8977)

---

## License

Â© 2025 Aboubacar Sidick Meite â€” All Rights Reserved.  
See [LICENSE](LICENSE) for details.

