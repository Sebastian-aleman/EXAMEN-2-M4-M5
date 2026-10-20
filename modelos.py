"""Entidades del modelo de calendarización: trabajos, máquinas y asignaciones."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trabajo:
    """Trabajo a procesar.

    `rates[j]` es la velocidad (unidades/hora) con la que la máquina j
    (índice base 0) procesa este trabajo.
    """

    id_trabajo: int
    elementos: int
    id_producto: str
    rates: list[int]

    def rate_en(self, id_maquina: int) -> int:
        """Devuelve el rate del trabajo en la máquina indicada (id base 1)."""
        return self.rates[id_maquina - 1]

    def duracion_en(self, id_maquina: int) -> float:
        """Duración en horas del trabajo en la máquina: elementos / rate."""
        return self.elementos / self.rate_en(id_maquina)


@dataclass
class Maquina:
    """Máquina con su cola de trabajos asignados."""

    id_maquina: int
    cola: list[Trabajo] = field(default_factory=list)

    @property
    def nombre(self) -> str:
        """Nombre legible de la máquina (M1, M2, ...)."""
        return f"M{self.id_maquina}"

    def agregar_trabajo(self, trabajo: Trabajo) -> None:
        """Añade un trabajo al final de la cola de la máquina."""
        self.cola.append(trabajo)

    def carga_total(self) -> float:
        """Suma de las duraciones (horas) de todos los trabajos asignados."""
        return sum(trabajo.duracion_en(self.id_maquina) for trabajo in self.cola)


@dataclass(frozen=True)
class AsignacionTrabajo:
    """Registro del calendario: qué trabajo se procesa, dónde, cuándo y en qué orden.

    Además de los campos solicitados se guardan elementos, rate y la duración
    en horas para facilitar la presentación de resultados.
    """

    maquina: int
    id_trabajo: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    orden_secuenciacion: int
    id_producto: str
    elementos: int
    rate: int
    duracion_horas: float
