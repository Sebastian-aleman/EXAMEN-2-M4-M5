"""Interfaz gráfica (Tkinter) para configurar, ejecutar y exportar el experimento."""

import os
import secrets
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from configuracion import ConfiguracionSimulacion
from experimento import Experimento
from exportador import ExportadorResultados

FORMATOS_FECHA = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def leer_entero(texto: str, nombre: str, minimo: int = 1) -> int:
    """Convierte `texto` a entero >= minimo o lanza ValueError con un mensaje claro."""
    try:
        valor = int(texto.strip())
    except ValueError:
        raise ValueError(f"'{nombre}' debe ser un número entero (se recibió '{texto}').") from None
    if valor < minimo:
        condicion = "positivo" if minimo == 1 else f"mayor o igual a {minimo}"
        raise ValueError(f"'{nombre}' debe ser un entero {condicion} (se recibió {valor}).")
    return valor


def leer_lista_enteros(texto: str, nombre: str) -> tuple[int, ...]:
    """Convierte '10, 20, 30' en (10, 20, 30); exige enteros positivos sin repetir."""
    partes = [p for p in texto.replace(" ", "").split(",") if p]
    if not partes:
        raise ValueError(f"'{nombre}' no puede estar vacío (ejemplo: 10, 20, 30).")
    valores = tuple(leer_entero(p, nombre) for p in partes)
    if len(set(valores)) != len(valores):
        raise ValueError(f"'{nombre}' tiene valores repetidos.")
    return valores


def leer_fecha(texto: str) -> datetime:
    """Convierte 'AAAA-MM-DD HH:MM' (segundos opcionales) en datetime."""
    for formato in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto.strip(), formato)
        except ValueError:
            pass
    raise ValueError(
        f"La fecha/hora de inicio '{texto}' no es válida. Use el formato AAAA-MM-DD HH:MM."
    )


class InterfazSimulacion:
    """Ventana principal: parámetros, botones, resultados y barra de estado."""

    VALORES_POR_DEFECTO = {
        "min_trabajos": "20",
        "max_trabajos": "30",
        "min_maquinas": "3",
        "max_maquinas": "5",
        "elementos": "10, 20, 30",
        "rates": "5, 10, 15",
        "replicas": "20",
        "semilla": "42",
        "fecha_inicio": "2026-10-20 08:00",
    }

    def __init__(self, raiz: tk.Tk) -> None:
        """Construye todos los componentes de la ventana."""
        self.raiz = raiz
        self.raiz.title("Simulación de calendarización de trabajos")
        self.raiz.minsize(760, 560)
        self.variables = {
            clave: tk.StringVar(value=valor) for clave, valor in self.VALORES_POR_DEFECTO.items()
        }
        self.carpeta_ultima_corrida: Path | None = None

        self.raiz.columnconfigure(0, weight=1)
        self.raiz.rowconfigure(2, weight=1)
        self._construir_parametros()
        self._construir_botones()
        self._construir_resultados()
        self._construir_estado()

    def _construir_parametros(self) -> None:
        """Crea la sección 'Parámetros' con los campos editables."""
        marco = ttk.LabelFrame(self.raiz, text="Parámetros", padding=10)
        marco.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        def campo(fila: int, columna: int, clave: str, ancho: int = 8) -> None:
            ttk.Entry(marco, textvariable=self.variables[clave], width=ancho).grid(
                row=fila, column=columna, sticky="w", padx=(0, 12), pady=2
            )

        def etiqueta(fila: int, columna: int, texto: str) -> None:
            ttk.Label(marco, text=texto).grid(row=fila, column=columna, sticky="w", padx=(0, 6), pady=2)

        etiqueta(0, 0, "Trabajos:")
        etiqueta(0, 1, "mínimo")
        campo(0, 2, "min_trabajos")
        etiqueta(0, 3, "máximo")
        campo(0, 4, "max_trabajos")

        etiqueta(1, 0, "Máquinas:")
        etiqueta(1, 1, "mínimo")
        campo(1, 2, "min_maquinas")
        etiqueta(1, 3, "máximo")
        campo(1, 4, "max_maquinas")

        etiqueta(2, 0, "Elementos posibles:")
        ttk.Entry(marco, textvariable=self.variables["elementos"], width=24).grid(
            row=2, column=1, columnspan=4, sticky="w", pady=2
        )
        etiqueta(2, 5, "(separados por coma)")

        etiqueta(3, 0, "Rates posibles (u/h):")
        ttk.Entry(marco, textvariable=self.variables["rates"], width=24).grid(
            row=3, column=1, columnspan=4, sticky="w", pady=2
        )
        etiqueta(3, 5, "(separados por coma)")

        etiqueta(4, 0, "Número de réplicas:")
        campo(4, 1, "replicas")
        etiqueta(4, 3, "Semilla:")
        campo(4, 4, "semilla")
        etiqueta(4, 5, "(vacía = aleatoria)")

        etiqueta(5, 0, "Fecha/hora de inicio:")
        ttk.Entry(marco, textvariable=self.variables["fecha_inicio"], width=24).grid(
            row=5, column=1, columnspan=4, sticky="w", pady=2
        )
        etiqueta(5, 5, "(AAAA-MM-DD HH:MM)")

    def _construir_botones(self) -> None:
        """Crea los botones de ejecutar y abrir carpeta."""
        marco = ttk.Frame(self.raiz, padding=(10, 0))
        marco.grid(row=1, column=0, sticky="w")
        ttk.Button(marco, text="Ejecutar simulación", command=self.ejecutar_simulacion).pack(
            side="left", padx=(0, 8), pady=5
        )
        self.boton_abrir = ttk.Button(
            marco,
            text="Abrir carpeta de resultados",
            command=self.abrir_carpeta_resultados,
            state="disabled",
        )
        self.boton_abrir.pack(side="left", pady=5)

    def _construir_resultados(self) -> None:
        """Crea el área de texto con scroll donde se muestra el reporte."""
        marco = ttk.LabelFrame(self.raiz, text="Resultados", padding=5)
        marco.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)
        self.texto_resultados = ScrolledText(
            marco, font=("Consolas", 10), wrap="none", width=84, height=20, state="disabled"
        )
        self.texto_resultados.grid(row=0, column=0, sticky="nsew")

    def _construir_estado(self) -> None:
        """Crea la etiqueta de estado en la parte inferior."""
        self.variable_estado = tk.StringVar(
            value="Listo. Ajuste los parámetros y presione 'Ejecutar simulación'."
        )
        ttk.Label(
            self.raiz, textvariable=self.variable_estado, relief="sunken", anchor="w", padding=(6, 3)
        ).grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def leer_configuracion(self) -> tuple[ConfiguracionSimulacion, int]:
        """Valida los campos y devuelve (configuración, número de réplicas).

        Lanza ValueError con un mensaje legible si algún dato es inválido.
        """
        v = {clave: variable.get() for clave, variable in self.variables.items()}

        min_trabajos = leer_entero(v["min_trabajos"], "Trabajos mínimo")
        max_trabajos = leer_entero(v["max_trabajos"], "Trabajos máximo")
        if min_trabajos > max_trabajos:
            raise ValueError("Trabajos: el mínimo no puede ser mayor que el máximo.")

        min_maquinas = leer_entero(v["min_maquinas"], "Máquinas mínimo")
        max_maquinas = leer_entero(v["max_maquinas"], "Máquinas máximo")
        if min_maquinas > max_maquinas:
            raise ValueError("Máquinas: el mínimo no puede ser mayor que el máximo.")

        elementos = leer_lista_enteros(v["elementos"], "Elementos posibles")
        rates = leer_lista_enteros(v["rates"], "Rates posibles")
        num_replicas = leer_entero(v["replicas"], "Número de réplicas")

        if v["semilla"].strip():
            semilla = leer_entero(v["semilla"], "Semilla", minimo=0)
        else:
            # Semilla aleatoria, pero registrada en el reporte para poder repetir la corrida.
            semilla = secrets.randbelow(1_000_000)

        fecha_inicio = leer_fecha(v["fecha_inicio"])

        # IdProducto: P1, P2, ... según el orden creciente de elementos.
        producto_por_elementos = {
            e: f"P{i}" for i, e in enumerate(sorted(elementos), start=1)
        }

        configuracion = ConfiguracionSimulacion(
            min_trabajos=min_trabajos,
            max_trabajos=max_trabajos,
            valores_elementos=elementos,
            min_maquinas=min_maquinas,
            max_maquinas=max_maquinas,
            valores_rate=rates,
            producto_por_elementos=producto_por_elementos,
            fecha_hora_inicio=fecha_inicio,
            semilla=semilla,
        )
        return configuracion, num_replicas

    def ejecutar_simulacion(self) -> None:
        """Valida, corre el experimento, exporta los archivos y muestra el reporte."""
        try:
            configuracion, num_replicas = self.leer_configuracion()
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error), parent=self.raiz)
            return

        self.raiz.config(cursor="watch")
        self.variable_estado.set("Ejecutando simulación...")
        self.raiz.update_idletasks()
        try:
            experimento = Experimento(configuracion, num_replicas=num_replicas)
            experimento.ejecutar()
            exportador = ExportadorResultados(experimento)
            carpeta = exportador.exportar()
        except OSError as error:
            self.variable_estado.set("Error al guardar los archivos.")
            messagebox.showerror("Error al exportar", f"No se pudieron escribir los archivos:\n{error}",
                                 parent=self.raiz)
            return
        finally:
            self.raiz.config(cursor="")

        self.mostrar_resultados(exportador.generar_texto_resultados())
        self.carpeta_ultima_corrida = carpeta
        self.boton_abrir.config(state="normal")
        self.variable_estado.set(f"Archivos guardados en: {carpeta}")

    def mostrar_resultados(self, texto: str) -> None:
        """Reemplaza el contenido del área de resultados."""
        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", "end")
        self.texto_resultados.insert("1.0", texto)
        self.texto_resultados.config(state="disabled")

    def abrir_carpeta_resultados(self) -> None:
        """Abre en el Explorador de Windows la carpeta de la última corrida."""
        if self.carpeta_ultima_corrida is None or not self.carpeta_ultima_corrida.exists():
            messagebox.showwarning("Sin resultados", "Aún no hay una carpeta de resultados.",
                                   parent=self.raiz)
            return
        try:
            os.startfile(self.carpeta_ultima_corrida)
        except OSError as error:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{error}", parent=self.raiz)


def activar_alta_resolucion() -> None:
    """En Windows, evita que la ventana se vea borrosa en pantallas con escalado."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass


def main() -> None:
    """Punto de entrada de la aplicación gráfica."""
    activar_alta_resolucion()
    raiz = tk.Tk()
    InterfazSimulacion(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
