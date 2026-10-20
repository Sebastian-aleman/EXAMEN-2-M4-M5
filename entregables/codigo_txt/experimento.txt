"""Experimento Monte Carlo: varias réplicas independientes de la simulación."""

from dataclasses import dataclass

from configuracion import ConfiguracionSimulacion
from simulador import ResultadoSimulacion, Simulador


@dataclass
class ResultadoReplica:
    """Indicadores de una réplica, más el resultado completo para exportar."""

    num_simulacion: int
    num_trabajos: int
    num_maquinas: int
    total_elementos: int
    makespan: float  # horas
    maquina_critica: str  # p. ej. "M3" (o "M1, M3" si hay empate)
    resultado: ResultadoSimulacion


@dataclass
class ResumenExperimento:
    """Estadísticos del makespan sobre todas las réplicas."""

    makespan_promedio: float
    makespan_maximo: float
    makespan_minimo: float
    simulacion_maximo: int  # réplica donde ocurrió el máximo
    simulacion_minimo: int  # réplica donde ocurrió el mínimo


class Experimento:
    """Corre `num_replicas` simulaciones con una sola instancia de Simulador.

    Cada réplica sortea factores nuevos porque el generador continúa su
    secuencia; con la misma semilla el experimento completo es reproducible.
    """

    def __init__(self, configuracion: ConfiguracionSimulacion, num_replicas: int = 20) -> None:
        """Guarda la configuración y el número de réplicas a ejecutar."""
        if num_replicas < 1:
            raise ValueError("num_replicas debe ser al menos 1.")
        self.configuracion = configuracion
        self.num_replicas = num_replicas
        self.replicas: list[ResultadoReplica] = []
        self.resumen: ResumenExperimento | None = None

    def ejecutar(self) -> list[ResultadoReplica]:
        """Ejecuta todas las réplicas y calcula el resumen del makespan."""
        simulador = Simulador(self.configuracion)
        self.replicas = []

        for num_simulacion in range(1, self.num_replicas + 1):
            resultado = simulador.ejecutar()
            factores = resultado.factores
            self.replicas.append(
                ResultadoReplica(
                    num_simulacion=num_simulacion,
                    num_trabajos=factores.num_trabajos,
                    num_maquinas=factores.num_maquinas,
                    total_elementos=sum(factores.elementos_por_trabajo),
                    makespan=resultado.makespan,
                    maquina_critica=", ".join(f"M{m}" for m in resultado.maquinas_criticas()),
                    resultado=resultado,
                )
            )

        self.resumen = self.calcular_resumen()
        return self.replicas

    def calcular_resumen(self) -> ResumenExperimento:
        """Calcula promedio, máximo y mínimo del makespan de las réplicas."""
        if not self.replicas:
            raise RuntimeError("Primero se debe ejecutar el experimento.")

        makespans = [r.makespan for r in self.replicas]
        replica_maxima = max(self.replicas, key=lambda r: r.makespan)
        replica_minima = min(self.replicas, key=lambda r: r.makespan)
        return ResumenExperimento(
            makespan_promedio=sum(makespans) / len(makespans),
            makespan_maximo=replica_maxima.makespan,
            makespan_minimo=replica_minima.makespan,
            simulacion_maximo=replica_maxima.num_simulacion,
            simulacion_minimo=replica_minima.num_simulacion,
        )
