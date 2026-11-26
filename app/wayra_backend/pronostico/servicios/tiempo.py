"""Todo se guarda en UTC; solo se pasa a hora de Lima para mostrar (RNF005)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")


def a_lima(dt):
    return dt.astimezone(LIMA).strftime("%d/%m %H:%M")


def a_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def desde_iso(texto):
    """Acepta '2026-12-03T13:00:00Z' o '2026-12-03T13:00'."""
    dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
