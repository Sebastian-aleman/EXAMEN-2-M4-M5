"""Prueba del núcleo: ejecuta UNA simulación con semilla 42 e imprime los resultados."""

from datetime import timedelta

from configuracion import ConfiguracionSimulacion
from simulador import ResultadoSimulacion, Simulador

FORMATO_FECHA = "%Y-%m-%d %H:%M"


def imprimir_titulo(texto: str) -> None:
    """Imprime un encabezado de sección."""
    print()
    print("=" * 78)
    print(texto)
    print("=" * 78)


def imprimir_factores(resultado: ResultadoSimulacion, configuracion: ConfiguracionSimulacion) -> None:
    """Muestra los factores generados por Monte Carlo."""
    f = resultado.factores
    imprimir_titulo("FACTORES GENERADOS (Monte Carlo)")
    print(f"Número de trabajos: {f.num_trabajos}")
    print(f"Número de máquinas: {f.num_maquinas}")
    print()

    encabezado_rates = "".join(f"{'R_M' + str(j + 1):>6}" for j in range(f.num_maquinas))
    print(f"{'Trabajo':>7} {'Elementos':>9} {'Producto':>8}{encabezado_rates} {'Máquina':>8}")
    print("-" * (34 + 6 * f.num_maquinas))
    for i in range(f.num_trabajos):
        elementos = f.elementos_por_trabajo[i]
        producto = configuracion.producto_por_elementos[elementos]
        rates = "".join(f"{r:>6}" for r in f.matriz_rates[i])
        print(f"{i + 1:>7} {elementos:>9} {producto:>8}{rates} {'M' + str(f.maquina_por_trabajo[i]):>8}")
    print("(R_Mj = rate en unidades/hora del trabajo en la máquina j)")


def imprimir_secuencias(resultado: ResultadoSimulacion) -> None:
    """Muestra el calendario FIFO de cada máquina."""
    imprimir_titulo("SECUENCIA POR MÁQUINA (FIFO)")
    for id_maquina in sorted(resultado.carga_por_maquina):
        secuencia = resultado.asignaciones_de_maquina(id_maquina)
        print(f"\nMáquina M{id_maquina} ({len(secuencia)} trabajos)")
        print(f"{'Orden':>5} {'Trabajo':>7} {'Producto':>8} {'Elem':>5} {'Rate':>5} "
              f"{'Duración(h)':>11}  {'Inicio':<16}  {'Fin':<16}")
        print("-" * 82)
        for a in secuencia:
            print(f"{a.orden_secuenciacion:>5} {a.id_trabajo:>7} {a.id_producto:>8} "
                  f"{a.elementos:>5} {a.rate:>5} {a.duracion_horas:>11.2f}  "
                  f"{a.fecha_hora_inicio.strftime(FORMATO_FECHA):<16}  "
                  f"{a.fecha_hora_fin.strftime(FORMATO_FECHA):<16}")


def imprimir_resumen(resultado: ResultadoSimulacion, configuracion: ConfiguracionSimulacion) -> None:
    """Muestra el tiempo total de cada máquina y el makespan."""
    imprimir_titulo("TIEMPO TOTAL POR MÁQUINA Y MAKESPAN")
    inicio = configuracion.fecha_hora_inicio
    for id_maquina, carga in sorted(resultado.carga_por_maquina.items()):
        fin = inicio + timedelta(hours=carga)
        print(f"M{id_maquina}: {carga:7.2f} h   (termina {fin.strftime(FORMATO_FECHA)})")

    fin_makespan = inicio + timedelta(hours=resultado.makespan)
    maquinas_criticas = [f"M{m}" for m in resultado.maquinas_criticas()]
    print("-" * 50)
    print(f"Makespan: {resultado.makespan:.2f} h  "
          f"(máquina crítica: {', '.join(maquinas_criticas)}; "
          f"fin {fin_makespan.strftime(FORMATO_FECHA)})")


def main() -> None:
    """Corre una simulación reproducible e imprime los resultados."""
    configuracion = ConfiguracionSimulacion(semilla=42)
    simulador = Simulador(configuracion)
    resultado = simulador.ejecutar()

    print(f"Simulación de calendarización - semilla {configuracion.semilla}, "
          f"inicio {configuracion.fecha_hora_inicio.strftime(FORMATO_FECHA)}")
    imprimir_factores(resultado, configuracion)
    imprimir_secuencias(resultado)
    imprimir_resumen(resultado, configuracion)


if __name__ == "__main__":
    main()
