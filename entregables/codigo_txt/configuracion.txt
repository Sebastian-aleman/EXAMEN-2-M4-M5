"""Parámetros configurables de la simulación de calendarización de trabajos."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConfiguracionSimulacion:
    """Agrupa todos los parámetros del modelo.

    Los valores por defecto corresponden al enunciado del examen. Cualquier
    parámetro puede modificarse al construir la instancia para experimentar
    con otros escenarios.
    """

    # Número de trabajos: entero uniforme en [min_trabajos, max_trabajos].
    min_trabajos: int = 20
    max_trabajos: int = 30

    # Cantidad de elementos posibles por trabajo (equiprobables).
    valores_elementos: tuple[int, ...] = (10, 20, 30)

    # Número de máquinas: entero uniforme en [min_maquinas, max_maquinas].
    min_maquinas: int = 3
    max_maquinas: int = 5

    # Rate (unidades/hora) posibles de un trabajo en una máquina (equiprobables).
    valores_rate: tuple[int, ...] = (5, 10, 15)

    # Identificador de producto según la cantidad de elementos del trabajo.
    producto_por_elementos: dict[int, str] = field(
        default_factory=lambda: {10: "P1", 20: "P2", 30: "P3"}
    )

    # Fecha y hora en que todas las máquinas comienzan a operar.
    fecha_hora_inicio: datetime = datetime(2026, 10, 20, 8, 0)

    # Semilla del generador pseudoaleatorio (None = no reproducible).
    semilla: int | None = None

    def __post_init__(self) -> None:
        """Valida la coherencia de los parámetros recibidos."""
        if not 1 <= self.min_trabajos <= self.max_trabajos:
            raise ValueError("Se requiere 1 <= min_trabajos <= max_trabajos.")
        if not 1 <= self.min_maquinas <= self.max_maquinas:
            raise ValueError("Se requiere 1 <= min_maquinas <= max_maquinas.")
        if not self.valores_elementos or any(v <= 0 for v in self.valores_elementos):
            raise ValueError("valores_elementos debe contener enteros positivos.")
        if not self.valores_rate or any(v <= 0 for v in self.valores_rate):
            raise ValueError("valores_rate debe contener valores positivos.")
        faltantes = set(self.valores_elementos) - set(self.producto_por_elementos)
        if faltantes:
            raise ValueError(
                f"Falta IdProducto para los elementos: {sorted(faltantes)}."
            )
