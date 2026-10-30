"""Entorno de prueba: se ejecuta antes de importar cualquier módulo de `app`.

Fija variables de entorno falsas, que tienen prioridad sobre el `.env`, para
que las pruebas no dependan de él ni toquen la base real: SQLite en un
directorio temporal y una clave VAPID generada en el momento. No hay
credenciales reales de Earth Engine; los servicios externos se reemplazan
con dobles en cada prueba.
"""
import atexit
import os
import shutil
import tempfile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

_TMP_DIR = tempfile.mkdtemp(prefix="irrigation-tests-")

_VAPID_PEM = ec.generate_private_key(ec.SECP256R1()).private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()

os.environ.update({
    "DATABASE_URL": f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}",
    "SECRET_KEY": "clave-de-prueba",
    "FRONTEND_URL": "http://localhost:5173",
    "GEE_SERVICE_ACCOUNT": "prueba@example.com",
    "GEE_CREDENTIALS_JSON": "{}",
    "VAPID_PRIVATE_KEY": _VAPID_PEM,
    "VAPID_PUBLIC_KEY": "clave-publica-de-prueba",
    "VAPID_SUBJECT": "mailto:prueba@example.com",
})


def _cleanup() -> None:
    from app.database import engine
    engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


atexit.register(_cleanup)
