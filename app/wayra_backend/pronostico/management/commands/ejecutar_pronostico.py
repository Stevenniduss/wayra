from django.core.management.base import BaseCommand, CommandError

from pronostico.servicios.ejecucion import ejecutar


class Command(BaseCommand):
    help = "Descarga el GFS, corre el modelo y guarda el pronóstico."

    def add_arguments(self, parser):
        parser.add_argument("--gfs", help="Usar un .npz de GFS ya guardado (sin internet).")
        parser.add_argument("--respaldo", action="store_true", help="Marcar como ejecución de respaldo para la demo.")

    def handle(self, *args, **options):
        try:
            ejec = ejecutar(gfs_desde=options["gfs"], respaldo=options["respaldo"])
        except Exception as e:
            raise CommandError(f"La ejecución falló y quedó registrada: {e}")
        segundos = (ejec.fin_proceso_utc - ejec.inicio_proceso_utc).total_seconds()
        self.stdout.write(self.style.SUCCESS(
            f"Ejecución {ejec.pk} lista en {segundos:.0f} s (GFS {ejec.gfs_inicio_utc:%d/%m %H:%M} UTC)."
        ))
