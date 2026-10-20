"""Exportación de los resultados de un experimento a CSV y TXT."""

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

from experimento import Experimento

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def obtener_carpeta_base_salidas() -> Path:
    """Devuelve la carpeta raíz `salidas/`.

    Empaquetado con PyInstaller (sys.frozen) se ubica junto al .exe, porque
    __file__ apunta a una carpeta temporal que se borra al cerrar. En modo
    script se ubica junto a este archivo.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "salidas"
    return Path(__file__).resolve().parent / "salidas"


class ExportadorResultados:
    """Escribe secuenciacion.csv y resultados.txt en salidas/AAAAMMDD_HHMMSS/."""

    COLUMNAS_CSV = [
        "NumSimulacion",
        "Maquina",
        "idTrabajo",
        "fechaHoraInicio",
        "fechaHoraFin",
        "OrdenSecuenciacion",
        "IdProducto",
    ]

    def __init__(
        self,
        experimento: Experimento,
        carpeta_base: Path | str | None = None,
        delimitador: str = ",",
    ) -> None:
        """Recibe un experimento ya ejecutado y la carpeta raíz de salidas.

        Por defecto se usa `obtener_carpeta_base_salidas()`.
        """
        if not experimento.replicas or experimento.resumen is None:
            raise RuntimeError("El experimento debe ejecutarse antes de exportar.")
        self.experimento = experimento
        self.carpeta_base = Path(carpeta_base) if carpeta_base else obtener_carpeta_base_salidas()
        self.delimitador = delimitador
        self.momento_generacion = datetime.now()
        self.carpeta_salida: Path | None = None

    def crear_carpeta(self) -> Path:
        """Crea la carpeta salidas/AAAAMMDD_HHMMSS/ y la devuelve."""
        nombre = self.momento_generacion.strftime("%Y%m%d_%H%M%S")
        self.carpeta_salida = self.carpeta_base / nombre
        self.carpeta_salida.mkdir(parents=True, exist_ok=True)
        return self.carpeta_salida

    def exportar_secuenciacion_csv(self, carpeta: Path) -> Path:
        """Escribe una fila por trabajo programado, de todas las réplicas."""
        ruta = carpeta / "secuenciacion.csv"
        with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo, delimiter=self.delimitador)
            escritor.writerow(self.COLUMNAS_CSV)
            for replica in self.experimento.replicas:
                asignaciones = sorted(
                    replica.resultado.asignaciones,
                    key=lambda a: (a.maquina, a.orden_secuenciacion),
                )
                for a in asignaciones:
                    escritor.writerow([
                        replica.num_simulacion,
                        f"M{a.maquina}",
                        a.id_trabajo,
                        a.fecha_hora_inicio.strftime(FORMATO_FECHA),
                        a.fecha_hora_fin.strftime(FORMATO_FECHA),
                        a.orden_secuenciacion,
                        a.id_producto,
                    ])
        return ruta

    def generar_texto_resultados(self) -> str:
        """Arma el reporte legible: parámetros, tabla por réplica y resumen."""
        cfg = self.experimento.configuracion
        resumen = self.experimento.resumen
        productos = ", ".join(
            f"{e}->{cfg.producto_por_elementos[e]}" for e in cfg.valores_elementos
        )
        separador = "=" * 78
        lineas = [
            separador,
            "RESULTADOS DEL EXPERIMENTO DE CALENDARIZACIÓN (MONTE CARLO)",
            f"Generado: {self.momento_generacion.strftime(FORMATO_FECHA)}",
            separador,
            "",
            "PARÁMETROS",
            "-" * 78,
            f"Número de réplicas:         {self.experimento.num_replicas}",
            f"Semilla:                    {cfg.semilla}",
            f"Fecha/hora de inicio:       {cfg.fecha_hora_inicio.strftime(FORMATO_FECHA)}",
            f"Trabajos por réplica:       entero uniforme en [{cfg.min_trabajos}, {cfg.max_trabajos}]",
            f"Máquinas por réplica:       entero uniforme en [{cfg.min_maquinas}, {cfg.max_maquinas}]",
            f"Elementos por trabajo:      {list(cfg.valores_elementos)} (equiprobables)",
            f"IdProducto:                 {productos}",
            f"Rate (unidades/hora):       {list(cfg.valores_rate)} (equiprobables)",
            "Asignación / secuenciación: máquina uniforme por trabajo, cola FIFO",
            "",
            "RESULTADOS POR RÉPLICA",
            "-" * 78,
            f"{'Sim':>4} {'Trabajos':>9} {'Máquinas':>9} {'Elementos':>10} "
            f"{'Makespan(h)':>12}  {'Máq.crítica':<12} {'Fin makespan':<19}",
            "-" * 78,
        ]
        for r in self.experimento.replicas:
            fin = cfg.fecha_hora_inicio + timedelta(hours=r.makespan)
            lineas.append(
                f"{r.num_simulacion:>4} {r.num_trabajos:>9} {r.num_maquinas:>9} "
                f"{r.total_elementos:>10} {r.makespan:>12.2f}  {r.maquina_critica:<12} "
                f"{fin.strftime(FORMATO_FECHA):<19}"
            )
        lineas += [
            "",
            "RESUMEN DEL MAKESPAN",
            "-" * 78,
            f"Promedio: {resumen.makespan_promedio:8.2f} h",
            f"Máximo:   {resumen.makespan_maximo:8.2f} h  (simulación {resumen.simulacion_maximo})",
            f"Mínimo:   {resumen.makespan_minimo:8.2f} h  (simulación {resumen.simulacion_minimo})",
            separador,
        ]
        return "\n".join(lineas)

    def exportar_resultados_txt(self, carpeta: Path) -> Path:
        """Escribe resultados.txt con el reporte legible."""
        ruta = carpeta / "resultados.txt"
        ruta.write_text(self.generar_texto_resultados() + "\n", encoding="utf-8")
        return ruta

    def exportar(self) -> Path:
        """Crea la carpeta de salida, escribe ambos archivos y devuelve la carpeta."""
        carpeta = self.crear_carpeta()
        self.exportar_secuenciacion_csv(carpeta)
        self.exportar_resultados_txt(carpeta)
        return carpeta
