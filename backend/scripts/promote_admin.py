"""
Asciende un usuario existente al rol admin.

Uso (desde backend/ con venv activo):
    python scripts/promote_admin.py <email>

Ejemplo:
    python scripts/promote_admin.py name@example.com
"""
import sys
from pathlib import Path

# Agrega backend/ al path para poder importar "app.*" corriendo desde cualquier cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import User, UserRole


def promote(email: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"Error: no existe ningún usuario con email '{email}'.")
            sys.exit(1)

        if user.role == UserRole.admin:
            print(f"El usuario {email} ya es admin. Nada que hacer.")
            return

        user.role = UserRole.admin
        db.commit()
        print(f"OK: {email} ahora es admin.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python scripts/promote_admin.py <email>")
        sys.exit(1)
    promote(sys.argv[1])
