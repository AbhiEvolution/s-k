"""Create the RSA key pair used to sign tokens.

Run once:  python scripts/generate_keys.py
The private key stays in keys/ (git-ignored) and is never shared with other
services. They fetch the public key from /.well-known/jwks.json instead.
"""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

out = Path("keys")
out.mkdir(exist_ok=True)
target = out / "private.pem"

if target.exists():
    raise SystemExit(f"{target} already exists; refusing to overwrite it")

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
target.write_bytes(
    key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
)
print(f"Wrote {target}")
