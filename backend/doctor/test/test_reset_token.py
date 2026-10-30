import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.auth import Jwt


def test_password_reset_token_round_trip() -> None:
  token = Jwt.create_password_reset_token(doctor_id=1)
  assert Jwt.verify_password_reset_token(token) == 1


if __name__ == "__main__":
  test_password_reset_token_round_trip()