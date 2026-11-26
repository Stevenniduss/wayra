from django.core.management.base import BaseCommand, CommandError

from pronostico.servicios.configuracion import ConfigError, cargar_config


class Command(BaseCommand):
    help = "Carga actividades, destinos y criterios desde datos/config."

    def handle(self, *args, **options):
        try:
            r = cargar_config()
        except ConfigError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(
            f"Listo: {r['actividades']} actividades, {r['destinos']} destinos, "
            f"{r['puntos']} puntos, {r['criterios']} criterios."
        ))
