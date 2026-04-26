"""Servicio de envio de notificaciones Web Push via VAPID."""
import json
import logging
from pywebpush import webpush, WebPushException
from app.models.push_subscription import PushSubscription
from app.config import settings

logger = logging.getLogger(__name__)


def send_push_notification(endpoint: str, p256dh: str, auth: str, title: str, body: str) -> bool:
    """Envia notificacion push a una suscripcion.
    Args:
        endpoint: URL del endpoint del browser.
        p256dh: clave publica del cliente.
        auth: clave de autenticacion del cliente.
        title: titulo de la notificacion.
        body: cuerpo de la notificacion.

    Returns:
        True si se envio correctamente, False si fallo.
    """
    try:
        private_key = settings.vapid_private_key.replace("\\n", "\n")
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
                
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
        return True
    except WebPushException as e:
        logger.warning("Error al enviar push notification: %s", e)
        return False
    

def send_push_to_user(user_id: int, title: str, body:str, db) -> int:
    """Envia notificacion push a todas las suscripciones activas de un usuario.
    
    Returns:
        Cantidad de notificaciones enviadas exitosamente.
    """
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
            # Subscripcion invalida o expirada - eliminarla
            db.delete(sub)
    if sent > 0:
        db.commit()
    return sent
    