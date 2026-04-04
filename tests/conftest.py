import os
import sys

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set FERNET_KEY for tests that import email models (EncryptedTextField needs it at import time)
if "FERNET_KEY" not in os.environ:
    from cryptography.fernet import Fernet

    os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
