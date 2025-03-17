import sqlite3
import pytest
import time
from project2 import (
    init_db, generate_rsa_key, store_key, get_private_key, generate_jwt, public_key_to_jwk, app
)
from fastapi.testclient import TestClient

client = TestClient(app)

DB_FILE = "totally_not_my_privateKeys.db"

def test_init_db():
    """Ensure the database initializes correctly."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keys'")
    assert cursor.fetchone() is not None
    conn.close()

def test_generate_rsa_key():
    """Ensure RSA key generation works."""
    private_key = generate_rsa_key()
    assert private_key is not None
    assert private_key.key_size == 2048

def test_store_key():
    """Ensure keys are stored in the database."""
    private_key = generate_rsa_key()
    exp_time = int(time.time()) + 3600
    store_key(private_key, exp_time)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT key, exp FROM keys WHERE exp = ?", (exp_time,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None

def test_get_private_key():
    """Ensure private key retrieval works."""
    private_key = generate_rsa_key()
    exp_time = int(time.time()) + 3600
    store_key(private_key, exp_time)

    retrieved_key, kid = get_private_key(expired=False)
    assert retrieved_key is not None

def test_get_expired_private_key():
    """Ensure expired keys retrieval works."""
    private_key = generate_rsa_key()
    exp_time = int(time.time()) - 100
    store_key(private_key, exp_time)

    retrieved_key = get_private_key(expired=True)
    assert retrieved_key is not None

def test_generate_jwt():
    """Ensure JWT generation works."""
    private_key = generate_rsa_key()
    token = generate_jwt(private_key, kid=1)
    assert token is not None
    assert isinstance(token, str)

def test_auth_endpoint():
    """Test the /auth endpoint."""
    response = client.post("/auth")
    assert response.status_code == 200
    assert "token" in response.json()

def test_auth_with_expired_key():
    """Test the /auth endpoint with expired keys."""
    response = client.post("/auth", params={"expired": True})
    assert response.status_code == 200
    assert "error" in response.json() or "token" in response.json()

def test_jwks_endpoint():
    """Test the JWKS endpoint."""
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200
    assert "keys" in response.json()
    assert isinstance(response.json()["keys"], list)


