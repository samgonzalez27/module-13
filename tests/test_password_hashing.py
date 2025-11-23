"""TDD tests for password hashing and verification."""

from app.security import PasswordHasher, hash_password, verify_password


def test_hashing_and_verify_module_helpers():
    raw = "mysecretpassword"
    hashed = hash_password(raw)
    # hashed should not equal raw
    assert hashed != raw
    # correct password verifies
    assert verify_password(raw, hashed) is True
    # incorrect password does not verify
    assert verify_password("wrongpass", hashed) is False


def test_passwordhasher_instance_methods():
    hasher = PasswordHasher()
    raw = "anothersecret"
    hashed = hasher.hash(raw)
    assert hashed != raw
    assert hasher.verify(raw, hashed) is True
    assert hasher.verify("nope", hashed) is False


def test_passwordhasher_with_deprecated_option():
    # ensure the code path that passes a non-None `deprecated` value is exercised
    hasher = PasswordHasher(deprecated="auto")
    raw = "shortpass"
    hashed = hasher.hash(raw)
    assert hasher.verify(raw, hashed) is True
