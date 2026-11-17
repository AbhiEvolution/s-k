import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password, verify_password


def test_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("correct horse")
    assert hashed != "correct horse"
    assert verify_password("correct horse", hashed)


def test_wrong_password_fails():
    assert not verify_password("wrong", hash_password("correct horse"))


def test_same_password_gets_different_hashes():
    # Random salt: two hashes of one password differ.
    assert hash_password("same") != hash_password("same")
