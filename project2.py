import time
import jwt
import base64
import logging
import sqlite3
from fastapi import FastAPI, Query
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Database file name
DB_FILE = "totally_not_my_privateKeys.db"


# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS keys (
        kid INTEGER PRIMARY KEY AUTOINCREMENT,
        key BLOB NOT NULL,
        exp INTEGER NOT NULL
    )
    """
    )
    conn.commit()
    conn.close()


# Call database
init_db()


# RSA Key Handling
def generate_rsa_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key


# Convert public key to JWK format
def public_key_to_jwk(public_key, kid):
    numbers = public_key.public_numbers()
    return {
        "kid": str(kid),
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": base64.urlsafe_b64encode(
            numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
        )
        .decode("utf-8")
        .rstrip("="),
        "e": base64.urlsafe_b64encode(
            numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
        )
        .decode("utf-8")
        .rstrip("="),
    }


# Store key in DB
def store_key(private_key, exp):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keys (key, exp) VALUES (?, ?)", (pem, exp))
    conn.commit()
    conn.close()


# Generate and store an active and expired key
store_key(generate_rsa_key(), int(time.time()) + 3600)  # Active key
store_key(generate_rsa_key(), int(time.time()) - 100)  # Expired key


# Retrieve private key from DB
def get_private_key(expired=False):
    now = int(time.time())
    query = (
        "SELECT kid, key FROM keys WHERE exp < ?"
        if expired
        else "SELECT kid, key FROM keys WHERE exp > ?"
    )

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, (now,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        logging.error("No private key found in database.")
        return None

    try:
        private_key = serialization.load_pem_private_key(row[1], password=None)
        logging.debug("Private key loaded successfully.")
        return private_key, row[0]  # Return private key and kid
    except Exception as e:
        logging.error(f"Failed to load private key: {e}")
        return None


# JWT Generation using key
def generate_jwt(private_key, kid):
    payload = {
        "sub": "test_user",
        "iat": int(time.time()),
        "exp": int(time.time() + 500),
    }

    try:
        token = jwt.encode(
            payload, private_key, algorithm="RS256", headers={"kid": str(kid)}
        )
        logging.debug(f"Successfully generated JWT: {token}")
        return token
    except Exception as e:
        logging.error(f"Error signing JWT: {e}")
        return None


# API Endpoints
@app.post("/auth")
def auth(expired: bool = Query(False)):
    logging.debug("Received request to /auth endpoint.")

    private_key, kid = get_private_key(
        expired
    )  # Retrieve both private key and kid from DB
    if not private_key:
        logging.error("Failed to retrieve a private key for JWT signing.")
        return {"error": "No key available"}

    try:
        token = generate_jwt(
            private_key, kid
        )  # Pass the kid along with the private key
        if not token:
            logging.error("Failed to generate JWT.")
            return {"error": "JWT generation failed"}

        logging.debug(f"Generated JWT: {token}")
        return {"token": token}  # Return the token in the response
    except Exception as e:
        logging.error(f"JWT generation failed: {e}")
        return {"error": "JWT generation failed"}


@app.get("/.well-known/jwks.json")
def get_jwks():
    now = int(time.time())

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT kid, key FROM keys WHERE exp > ?", (now,))
    rows = cursor.fetchall()
    conn.close()

    jwks_keys = []
    for row in rows:
        private_key = serialization.load_pem_private_key(row[1], password=None)
        public_key = private_key.public_key()
        jwks_keys.append(public_key_to_jwk(public_key, row[0]))

    logging.debug(f"JWKS generated: {jwks_keys}")
    return {"keys": jwks_keys}


# Testing
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
