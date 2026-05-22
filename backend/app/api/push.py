"""Endpoint para registrar suscripciones Web Push."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.auth.dependencies import get_current_user
from app.services.push import send_push_to_user

router = APIRouter(prefix="/push", tags=["push"])


class PushSubscriptionPayload(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

class PushSubscriptionMigratePayload(BaseModel):
    old_endpoint: str
    endpoint: str
    p256dh: str
    auth: str

@router.post("/migrate", status_code=status.HTTP_200_OK)
def migrate(payload: PushSubscriptionMigratePayload, db: Session = Depends(get_db)):
    """Migra una suscripcion a un nuevo endpoint tras la rotacion del navegador.
    
    No requiere auth: el service worker no tiene el JWT del usuario. La posesion
    del endpoint viejo (string aleatorio) identifica la suscripcion a migrar."""
    old = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.old_endpoint)
        .first()
    )
    if old is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripcion no encontrada")
    
    existing_new = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if existing_new and existing_new.id != old.id:
        # El nuevo endpoint ya estaba registrado: descartar el viejo.
        db.delete(old)
    else:
        old.endpoint = payload.endpoint
        old.p256dh = payload.p256dh
        old.auth = payload.auth
    db.commit()
    return {"detail": "Suscripcion migrada"}

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: PushSubscriptionPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra o actualiza la suscripcion push del usuario actual."""
    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if existing:
        existing.p256dh = payload.p256dh
        existing.auth = payload.auth
    else:
        db.add(PushSubscription(
            user_id=current_user.id,
            endpoint=payload.endpoint,
            p256dh=payload.p256dh,
            auth=payload.auth
        ))
    db.commit()
    return {"detail": "Suscripcion registrada"}


@router.delete("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    payload: PushSubscriptionPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Elimina la suscripcion push del usuario actual."""
    sub = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.endpoint == payload.endpoint,
            PushSubscription.user_id == current_user.id,
        )
        .first()
    )
    if sub:
        db.delete(sub)
        db.commit()


@router.post("/test", status_code=status.HTTP_200_OK)
def test_push(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Envia una notificacion de prueba a todas las suscripciones del usuario actual.

    Devuelve cuantas la recibieron con exito. Util para diagnosticar si el
    problema es de entrega (sent=0 o no llega al device) o de longevidad
    (la suscripcion muere despues, entre el subscribe y el job de las 8am)."""
    sent = send_push_to_user(
        current_user.id,
        title="Prueba de notificacion",
        body="Si ves esto, las notificaciones funcionan correctamente.",
        db=db,
    )
    return {"sent": sent}