"""Script para ejecutar el job de recomendaciones manualmente (uso en desarrollo)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.jobs.recommendation_job import generate_daily_recommendations

if __name__ == '__main__':
    print("Ejecutando job de recomendaciones...")
    generate_daily_recommendations()
    print("Listo.")
