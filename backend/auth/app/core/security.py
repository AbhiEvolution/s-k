import bcrypt

# bcrypt only looks at the first 72 bytes of a password.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    # gensalt() creates a random salt; it is stored inside the hash itself.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# A real bcrypt hash of a random password. Used so that logging in with an
# unknown email takes as long as a wrong password (see AuthService.login).
DUMMY_HASH = hash_password("dummy-password-for-timing")
