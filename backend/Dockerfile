FROM python:3.14-slim

WORKDIR /app

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo de la app
COPY . .

EXPOSE 8000

# Aplica migraciones y levanta el servidor.
# Escucha en 8000 solo dentro de la red Docker (no se expone a internet).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
