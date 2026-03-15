"""
Tests for Backend/Utility/security.py

Covers: password hashing, JWT creation/decoding, and SSN encryption.
These are pure-unit tests with no database dependency.
"""
import pytest
from Backend.Utility.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    encrypt_ssn,
    decrypt_ssn,
)


class TestPasswordHashing:
    def test_hash_returns_string(self):
        assert isinstance(hash_password("secret"), str)

    def test_hash_is_not_plaintext(self):
        pw = "MyPassword123"
        assert hash_password(pw) != pw

    def test_argon2_different_hashes_for_same_password(self):
        # Argon2 uses a random salt per hash
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_verify_correct_password_returns_true(self):
        pw = "CorrectHorseBattery"
        assert verify_password(pw, hash_password(pw)) is True

    def test_verify_wrong_password_returns_false(self):
        assert verify_password("wrong", hash_password("right")) is False

    def test_verify_empty_vs_nonempty(self):
        assert verify_password("", hash_password("nonempty")) is False


class TestJWT:
    def test_create_returns_string(self):
        token = create_access_token({"sub": "1", "role": "admin"})
        assert isinstance(token, str)

    def test_decode_recovers_payload(self):
        data = {"sub": "42", "role": "manager", "username": "alice"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "manager"
        assert payload["username"] == "alice"

    def test_decode_invalid_token_returns_none(self):
        assert decode_access_token("this.is.not.valid") is None

    def test_decode_empty_string_returns_none(self):
        assert decode_access_token("") is None

    def test_decode_tampered_signature_returns_none(self):
        token = create_access_token({"sub": "1"})
        # Corrupt the last few characters of the signature
        tampered = token[:-6] + "aaaaaa"
        assert decode_access_token(tampered) is None

    def test_token_contains_exp_claim(self):
        token = create_access_token({"sub": "5"})
        payload = decode_access_token(token)
        assert "exp" in payload


class TestSSNEncryption:
    def test_encrypt_returns_string(self):
        assert isinstance(encrypt_ssn("123-45-6789"), str)

    def test_encrypted_differs_from_plaintext(self):
        ssn = "123-45-6789"
        assert encrypt_ssn(ssn) != ssn

    def test_decrypt_recovers_original(self):
        ssn = "987-65-4321"
        assert decrypt_ssn(encrypt_ssn(ssn)) == ssn

    def test_two_encryptions_of_same_ssn_differ(self):
        # Fernet uses a random IV, so ciphertexts should differ
        ssn = "111-22-3333"
        assert encrypt_ssn(ssn) != encrypt_ssn(ssn)

    def test_round_trip_various_ssns(self):
        ssns = ["234-56-7890", "456-78-9012", "789-01-2345"]
        for ssn in ssns:
            assert decrypt_ssn(encrypt_ssn(ssn)) == ssn
