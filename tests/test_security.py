import unittest

import bcrypt

from app.security import get_password_hash, verify_password


class PasswordTests(unittest.TestCase):
    def test_new_hash_accepts_correct_password_and_rejects_wrong_password(self):
        hashed = get_password_hash("short-password")
        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password("short-password", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_long_unicode_password_is_not_truncated(self):
        password = "\u00e9" * 80
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password(password + "different", hashed))

    def test_existing_bcrypt_hash_is_supported(self):
        hashed = bcrypt.hashpw(b"existing-password", bcrypt.gensalt(rounds=4)).decode()
        self.assertTrue(verify_password("existing-password", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))
        self.assertFalse(verify_password("\u00e9" * 80, hashed))
