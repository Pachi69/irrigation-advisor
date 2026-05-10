"""Servicio de envio de notificaciones Web Push via VAPID."""
import json
import logging
from py_vapid import Vapid01
from pywebpush import webpush, WebPushException
from app.models.push_subscription import PushSubscription
from app.config import settings

logger = logging.getLogger(__name__)


def _load_vapid() -> Vapid01:
    """Carga el VAPID Vapid01 desde la PEM en settings (una sola vez por proceso)."""
    pem = settings.vapid_private_key.replace("\\n", "\n").encode()
    return Vapid01.from_pem(pem)


_vapid = _load_vapid()


def send_push_notification(endpoint: str, p256dh: str, auth: str, title: str, body: str) -> bool:
    try:
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=_vapid,  # objeto Vapid01, NO string
            vapid_claims={"sub": settings.vapid_subject},
        )
        return True
    except WebPushException as e:
        logger.warning("Error al enviar push notification: %s", e)
        return False


def send_push_to_user(user_id: int, title: str, body: str, db) -> int:
    """Envia notificacion push a todas las suscripciones activas de un usuario."""
    subscriptions = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id)
        .all()
    )
    sent = 0
    for sub in subscriptions:
        if send_push_notification(sub.endpoint, sub.p256dh, sub.auth, title, body):
            sent += 1
        else:
            db.delete(sub)
    if sent > 0:
        db.commit()
    return sent