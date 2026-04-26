"""Endpoint para registrar suscripciones Web Push."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/push", tags=["push"])


class PushSubscriptionPayload(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


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