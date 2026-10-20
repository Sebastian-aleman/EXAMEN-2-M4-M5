"""Corre el experimento por defecto (semilla 42), exporta los archivos e imprime el reporte."""

from configuracion import ConfiguracionSimulacion
from experimento import Experimento
from exportador import ExportadorResultados


def main() -> None:
    """Ejecuta 20 réplicas, exporta CSV/TXT y muestra el reporte en consola."""
    configuracion = ConfiguracionSimulacion(semilla=42)
    experimento = Experimento(configuracion, num_replicas=20)
    experimento.ejecutar()

    exportador = ExportadorResultados(experimento)
    carpeta = exportador.exportar()

    print(exportador.generar_texto_resultados())
    print(f"\nArchivos generados en: {carpeta}")


if __name__ == "__main__":
    main()
