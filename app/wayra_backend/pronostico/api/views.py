from functools import wraps

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from . import consultas as c


def _json(datos, status=200):
    return JsonResponse(datos, status=status, safe=False, json_dumps_params={"ensure_ascii": False})


def api(vista):
    """Solo GET, y los errores conocidos salen como {error} con su código."""
    @require_GET
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        try:
            return _json(vista(request, *args, **kwargs))
        except c.NoEncontrado as e:
            return _json({"error": str(e)}, 404)
        except c.DatoInvalido as e:
            return _json({"error": str(e)}, 400)
        except c.SinEjecucion as e:
            return _json({"error": str(e)}, 503)
    return envoltura


@api
def destinos(request):
    return c.lista_destinos()


@api
def destino(request, codigo):
    return c.detalle_destino(codigo)


@api
def pronostico(request, codigo):
    return c.pronostico_destino(codigo)


@api
def ventanas(request, codigo):
    duracion = request.GET.get("duracion_h")
    try:
        duracion = int(duracion) if duracion else None
    except ValueError:
        raise c.DatoInvalido("duracion_h debe ser un número")
    return c.ventanas_destino(codigo, duracion)


@api
def mapa(request):
    return c.mapa(
        request.GET.get("variable", "temperatura"),
        request.GET.get("valido_utc"),
        request.GET.get("fuente", "wayra"),
    )


@api
def comparador(request):
    return c.comparador(request.GET.get("valido_utc"), request.GET.get("punto_id"))


@api
def ejecucion(request):
    return c.datos_ejecucion(c.ultima_ejecucion())
