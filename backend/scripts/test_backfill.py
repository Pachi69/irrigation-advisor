"""Verificacion manual del backfill batch (no persiste: hace rollback al final)."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date, timedelta
from app.database import SessionLocal
from app.models.field import Field
from app.models.daily_water_balance import DailyWaterBalance
from app.services.recommendation import run_backfill

FIELD_ID = 21  # 'Prueba88' — campo de prueba con poligono

db = SessionLocal()
try:
    field = db.get(Field, FIELD_ID)
    if field is None:
        print(f"No existe el campo {FIELD_ID}")
        sys.exit(1)

    today = date.today()
    start = today - timedelta(days=20)
    end = today - timedelta(days=1)
    print(f"Campo {field.id} ({field.name}) - backfill {start}..{end}")
    print(f"Deficit inicial (field.last_deficit_mm): {field.last_deficit_mm}\n")

    t0 = time.perf_counter()
    run_backfill(field, start, end, db)
    elapsed = time.perf_counter() - t0
    print(f"\nrun_backfill termino en {elapsed:.2f}s\n")

    rows = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.field_id == field.id,
            DailyWaterBalance.date >= start,
            DailyWaterBalance.date <= end,
        )
        .order_by(DailyWaterBalance.date)
        .all()
    )
    print(f"{'fecha':<12}{'lluvia':>8}{'ETc':>7}{'deficit':>9}{'kc':>7}  kc_source")
    for r in rows:
        print(f"{str(r.date):<12}{r.precipitation_mm:>8.1f}{r.etc_mm:>7.2f}"
              f"{r.water_deficit_mm:>9.2f}{r.kc:>7.3f}  {r.kc_source}")
    print(f"\nTotal dias backfilleados: {len(rows)} (esperado ~20)")
finally:
    db.rollback()
    db.close()
    print("Rollback hecho - la DB no se modifico.")
