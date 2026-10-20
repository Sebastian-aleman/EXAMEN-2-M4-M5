"""Generación de variables aleatorias discretas por el método de Monte Carlo."""

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class GeneradorMonteCarlo:
    """Genera variables aleatorias discretas a partir de una uniforme U(0,1).

    Se usa el método de la transformada inversa: se obtiene u ~ U(0,1) y se
    recorre la función de distribución acumulada F de la variable discreta;
    el valor elegido es el primero x_i tal que u < F(x_i).

    Ejemplo con tres valores equiprobables (a, b, c):
        u < 1/3        -> a
        1/3 <= u < 2/3 -> b
        2/3 <= u < 1   -> c
    """

    def __init__(self, semilla: int | None = None) -> None:
        """Inicializa un generador propio (independiente del módulo random global)."""
        self.semilla = semilla
        self._rng = random.Random(semilla)

    def generar_uniforme(self) -> float:
        """Devuelve un número pseudoaleatorio u ~ U(0,1), con 0 <= u < 1."""
        return self._rng.random()

    @staticmethod
    def mapear_a_discreto(
        u: float,
        valores: Sequence[T],
        probabilidades: Sequence[float] | None = None,
    ) -> T:
        """Transforma un u en [0,1) en uno de los `valores` por transformada inversa.

        Si no se indican `probabilidades`, todos los valores son equiprobables
        (1/n cada uno). Las probabilidades deben sumar 1.
        """
        if not valores:
            raise ValueError("La lista de valores no puede estar vacía.")
        if not 0.0 <= u < 1.0:
            raise ValueError("u debe estar en el intervalo [0, 1).")

        n = len(valores)
        if probabilidades is None:
            probabilidades = [1.0 / n] * n
        elif len(probabilidades) != n:
            raise ValueError("valores y probabilidades deben tener la misma longitud.")
        elif abs(sum(probabilidades) - 1.0) > 1e-9:
            raise ValueError("Las probabilidades deben sumar 1.")

        acumulada = 0.0
        for valor, probabilidad in zip(valores, probabilidades):
            acumulada += probabilidad
            if u < acumulada:
                return valor
        # Solo se llega aquí por redondeo cuando u está muy cerca de 1.
        return valores[-1]

    def muestrear_discreto(
        self,
        valores: Sequence[T],
        probabilidades: Sequence[float] | None = None,
    ) -> T:
        """Genera u ~ U(0,1) y lo mapea a uno de los `valores` del conjunto discreto."""
        return self.mapear_a_discreto(self.generar_uniforme(), valores, probabilidades)

    def muestrear_entero(self, minimo: int, maximo: int) -> int:
        """Genera un entero uniforme en [minimo, maximo] (ambos extremos incluidos).

        Es el caso particular de `muestrear_discreto` con los valores
        minimo, minimo+1, ..., maximo, todos equiprobables.
        """
        if minimo > maximo:
            raise ValueError("minimo no puede ser mayor que maximo.")
        return self.muestrear_discreto(range(minimo, maximo + 1))
