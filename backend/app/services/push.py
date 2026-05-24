"""Servicio de envio de notificaciones Web Push via VAPID."""
import json
import logging
from py_vapid import Vapid01
from pywebpush import webpush, WebPushException
from app.models.push_subscription import PushSubscription
from app.config import settings

logger = logging.getLogger(__name__)

# HTTP codes que confirman que la suscripcion ya no existe.
_DEAD_SUBSCRIPTION_CODES = {404, 410}


def _load_vapid() -> Vapid01:
    """Carga el VAPID Vapid01 desde la PEM en settings (una sola vez por proceso)."""
    pem = settings.vapid_private_key.replace("\\n", "\n").encode()
    return Vapid01.from_pem(pem)


_vapid = _load_vapid()


def send_push_notification(endpoint: str, p256dh: str, auth: str, title: str, body: str) -> bool | None:
    """Envia una notificacion push.

    Returns:
        True  -> enviada con exito
        False -> suscripcion muerta (404/410): debe eliminarse
        None  -> error transitorio (5xx, red, timeout): NO eliminar, reintentar luego
    """
    try:
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=_vapid,  # objeto Vapid01, NO string
            vapid_claims={"sub": settings.vapid_subject},
            ttl=86400,  # 1 dia
            headers={"Urgency": "high"},
        )
        return True
    except WebPushException as e:
        status = e.response.status_code if e.response is not None else None
        body = e.response.text[:200] if e.response is not None else "(sin response)"
        endpoint_tail = endpoint[-40:]
        if status in _DEAD_SUBSCRIPTION_CODES:
            logger.info(
                "PUSH_DEAD endpoint=...%s status=%s body=%s",
                endpoint_tail, status, body,
            )
            return False
        logger.warning(
            "PUSH_TRANSIENT endpoint=...%s status=%s body=%s err=%s",
            endpoint_tail, status, body, e,
        )
        return None


def send_push_to_user(user_id: int, title: str, body: str, db) -> int:
    """Envia notificacion push a todas las suscripciones activas de un usuario.

    Solo elimina suscripciones confirmadas como muertas (404/410). Ante errores
    transitorios mantiene la suscripcion para reintentar en la proxima corrida.
    """
    subscriptions = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id)
        .all()
    )
    sent = 0
    removed = 0
    for sub in subscriptions:
        result = send_push_notification(sub.endpoint, sub.p256dh, sub.auth, title, body)
        if result is True:
            sent += 1
        elif result is False:
            logger.info(
                "PUSH_DELETE user_id=%s sub_id=%s endpoint=...%s created_at=%s",
                sub.user_id, sub.id, sub.endpoint[-40:], sub.created_at,
            )
            db.delete(sub)
            removed += 1
        # result is None -> transitorio: se mantiene
    logger.info(
        "PUSH_BATCH user_id=%s total=%s sent=%s removed=%s",
        user_id, len(subscriptions), sent, removed,
    )
    if sent > 0 or removed > 0:
        db.commit()
    return sent