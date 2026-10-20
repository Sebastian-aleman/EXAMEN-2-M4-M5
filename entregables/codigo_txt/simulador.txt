"""Simulación Monte Carlo de la calendarización de trabajos en máquinas paralelas."""

from dataclasses import dataclass
from datetime import timedelta

from configuracion import ConfiguracionSimulacion
from generador_montecarlo import GeneradorMonteCarlo
from modelos import AsignacionTrabajo, Maquina, Trabajo


@dataclass
class FactoresSimulacion:
    """Factores aleatorios generados en una corrida de la simulación."""

    num_trabajos: int
    num_maquinas: int
    elementos_por_trabajo: list[int]
    matriz_rates: list[list[int]]  # filas = trabajos, columnas = máquinas
    maquina_por_trabajo: list[int]  # máquina (base 1) elegida para cada trabajo


@dataclass
class ResultadoSimulacion:
    """Salida de una corrida: factores, calendario, carga por máquina y makespan."""

    factores: FactoresSimulacion
    asignaciones: list[AsignacionTrabajo]
    carga_por_maquina: dict[int, float]  # id_maquina -> horas de trabajo
    makespan: float  # horas

    def asignaciones_de_maquina(self, id_maquina: int) -> list[AsignacionTrabajo]:
        """Devuelve la secuencia de trabajos de una máquina en orden de proceso."""
        return sorted(
            (a for a in self.asignaciones if a.maquina == id_maquina),
            key=lambda a: a.orden_secuenciacion,
        )

    def maquinas_criticas(self) -> list[int]:
        """Máquinas cuyo tiempo de finalización es igual al makespan."""
        return [
            id_maquina
            for id_maquina, carga in sorted(self.carga_por_maquina.items())
            if abs(carga - self.makespan) < 1e-9
        ]


class Simulador:
    """Ejecuta el modelo de calendarización.

    Pasos de una corrida (método `ejecutar`):
      1. generar_factores: nº de trabajos, nº de máquinas, elementos y rates.
      2. asignar_trabajos: cada trabajo va a UNA máquina elegida al azar.
      3. secuenciar_fifo: cada máquina procesa su cola por orden de llegada.
      4. calcular_makespan: máximo tiempo de finalización entre máquinas.

    Todas las variables aleatorias se obtienen con GeneradorMonteCarlo
    (U(0,1) + transformada inversa). Con la misma semilla, una instancia
    nueva reproduce exactamente la misma secuencia de corridas.
    """

    def __init__(self, configuracion: ConfiguracionSimulacion | None = None) -> None:
        """Crea el simulador con la configuración dada (o la del enunciado)."""
        self.configuracion = configuracion or ConfiguracionSimulacion()
        self.generador = GeneradorMonteCarlo(self.configuracion.semilla)
        self._reiniciar_estado()

    def _reiniciar_estado(self) -> None:
        """Limpia los datos de la corrida anterior."""
        self.factores: FactoresSimulacion | None = None
        self.trabajos: list[Trabajo] = []
        self.maquinas: list[Maquina] = []
        self.asignaciones: list[AsignacionTrabajo] = []

    def generar_factores(self) -> FactoresSimulacion:
        """Genera por Monte Carlo los factores del sistema y crea trabajos y máquinas.

        Orden de generación: nº de trabajos, nº de máquinas, elementos de cada
        trabajo y, por cada trabajo, su rate en cada máquina.
        """
        cfg = self.configuracion
        num_trabajos = self.generador.muestrear_entero(cfg.min_trabajos, cfg.max_trabajos)
        num_maquinas = self.generador.muestrear_entero(cfg.min_maquinas, cfg.max_maquinas)

        elementos_por_trabajo = [
            self.generador.muestrear_discreto(cfg.valores_elementos)
            for _ in range(num_trabajos)
        ]
        matriz_rates = [
            [self.generador.muestrear_discreto(cfg.valores_rate) for _ in range(num_maquinas)]
            for _ in range(num_trabajos)
        ]

        self.trabajos = [
            Trabajo(
                id_trabajo=i + 1,
                elementos=elementos,
                id_producto=cfg.producto_por_elementos[elementos],
                rates=matriz_rates[i],
            )
            for i, elementos in enumerate(elementos_por_trabajo)
        ]
        self.maquinas = [Maquina(id_maquina=j + 1) for j in range(num_maquinas)]

        self.factores = FactoresSimulacion(
            num_trabajos=num_trabajos,
            num_maquinas=num_maquinas,
            elementos_por_trabajo=elementos_por_trabajo,
            matriz_rates=matriz_rates,
            maquina_por_trabajo=[],
        )
        return self.factores

    def asignar_trabajos(self) -> list[int]:
        """Asigna cada trabajo a una máquina elegida con U(0,1) (equiprobable).

        Los trabajos se recorren por id, por lo que cada cola queda en orden
        de llegada. Devuelve la máquina (base 1) elegida para cada trabajo.
        """
        if self.factores is None:
            raise RuntimeError("Primero se deben generar los factores.")

        maquina_por_trabajo = []
        for trabajo in self.trabajos:
            id_maquina = self.generador.muestrear_entero(1, len(self.maquinas))
            self.maquinas[id_maquina - 1].agregar_trabajo(trabajo)
            maquina_por_trabajo.append(id_maquina)

        self.factores.maquina_por_trabajo = maquina_por_trabajo
        return maquina_por_trabajo

    def secuenciar_fifo(self) -> list[AsignacionTrabajo]:
        """Calcula el calendario de cada máquina con la regla FIFO.

        Cada máquina arranca en la fecha base y procesa su cola por id de
        trabajo (orden de llegada) sin tiempos muertos:
            inicio_k = fin_(k-1),   fin_k = inicio_k + elementos / rate.
        """
        fecha_base = self.configuracion.fecha_hora_inicio
        self.asignaciones = []

        for maquina in self.maquinas:
            reloj_horas = 0.0
            cola_fifo = sorted(maquina.cola, key=lambda t: t.id_trabajo)
            for orden, trabajo in enumerate(cola_fifo, start=1):
                duracion = trabajo.duracion_en(maquina.id_maquina)
                inicio_horas = reloj_horas
                reloj_horas += duracion
                self.asignaciones.append(
                    AsignacionTrabajo(
                        maquina=maquina.id_maquina,
                        id_trabajo=trabajo.id_trabajo,
                        fecha_hora_inicio=fecha_base + timedelta(hours=inicio_horas),
                        fecha_hora_fin=fecha_base + timedelta(hours=reloj_horas),
                        orden_secuenciacion=orden,
                        id_producto=trabajo.id_producto,
                        elementos=trabajo.elementos,
                        rate=trabajo.rate_en(maquina.id_maquina),
                        duracion_horas=duracion,
                    )
                )
        return self.asignaciones

    def calcular_carga_por_maquina(self) -> dict[int, float]:
        """Tiempo total (horas) que cada máquina pasa procesando trabajos."""
        return {maquina.id_maquina: maquina.carga_total() for maquina in self.maquinas}

    def calcular_makespan(self) -> float:
        """Makespan = max_j C_j, el mayor tiempo de finalización entre las máquinas.

        Como cada máquina trabaja sin interrupciones desde t = 0, su tiempo de
        finalización coincide con su carga total.
        """
        return max(self.calcular_carga_por_maquina().values(), default=0.0)

    def ejecutar(self) -> ResultadoSimulacion:
        """Ejecuta una corrida completa y devuelve su resultado.

        Llamadas sucesivas sobre la misma instancia producen réplicas
        independientes (el generador continúa su secuencia).
        """
        self._reiniciar_estado()
        factores = self.generar_factores()
        self.asignar_trabajos()
        asignaciones = self.secuenciar_fifo()
        return ResultadoSimulacion(
            factores=factores,
            asignaciones=asignaciones,
            carga_por_maquina=self.calcular_carga_por_maquina(),
            makespan=self.calcular_makespan(),
        )
