"""Carga de reglas versionadas por fecha de vigencia.

Cada consulta devuelve el valor y la regla completa (fuente, estado y campos de
trazabilidad: norma, artículo, URL del texto oficial, fecha de consulta y cita
textual), para que cada peso calculado pueda citar de dónde salió.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import holidays
import yaml

RUTA = Path(__file__).parent / "reglas" / "parametros.yaml"

ESTADOS_VALIDOS = {"verificado", "por_verificar"}


@dataclass(frozen=True)
class Regla:
    nombre: str
    valor: Any
    desde: dt.date
    fuente: str
    estado: str
    # Campos de trazabilidad (v0.2). Opcionales para no romper la API de v0.1.
    norma: str | None = None
    articulo: str | None = None
    url: str | None = None
    consultado: dt.date | None = None
    cita_textual: str | None = None
    nota: str | None = None

    @property
    def verificada(self) -> bool:
        return self.estado == "verificado"

    def cita(self) -> str:
        """Cita corta: valor, vigencia, fuente y estado (con fecha de consulta si se verificó)."""
        v = "tabla" if isinstance(self.valor, (dict, list)) else self.valor
        estado = self.estado
        if self.verificada and self.consultado:
            estado = f"verificado {self.consultado}"
        return f"{self.nombre}={v} (desde {self.desde}; {self.fuente}; {estado})"

    def cita_completa(self) -> str:
        """Cita larga con URL del texto oficial y fragmento literal, para informes."""
        partes = [self.cita()]
        if self.url:
            partes.append(f"texto oficial: {self.url}")
        if self.cita_textual:
            partes.append(f'"{self.cita_textual}"')
        return " | ".join(partes)


@lru_cache(maxsize=1)
def _cargar() -> dict:
    with open(RUTA, encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    for nombre, versiones in datos.items():
        for r in versiones:
            if r.get("estado") not in ESTADOS_VALIDOS:
                raise ValueError(f"Regla '{nombre}' desde {r.get('desde')}: estado inválido {r.get('estado')!r}")
            if r["estado"] == "verificado" and not (r.get("url") and r.get("consultado")):
                raise ValueError(f"Regla '{nombre}' desde {r['desde']}: 'verificado' exige url y consultado")
    return datos


def nombres_reglas() -> list[str]:
    return sorted(_cargar())


def versiones(nombre: str) -> list[Regla]:
    """Todas las versiones de una regla, ordenadas por fecha de vigencia."""
    return list(_versiones(nombre))


@lru_cache(maxsize=128)
def _versiones(nombre: str) -> tuple[Regla, ...]:
    if nombre not in _cargar():
        raise KeyError(f"No existe la regla '{nombre}' en {RUTA.name}")
    return tuple(_a_regla(nombre, r) for r in sorted(_cargar()[nombre], key=lambda r: r["desde"]))


def _a_regla(nombre: str, r: dict) -> Regla:
    return Regla(
        nombre, r["valor"], r["desde"], r["fuente"], r["estado"],
        norma=r.get("norma"), articulo=r.get("articulo"), url=r.get("url"),
        consultado=r.get("consultado"), cita_textual=r.get("cita_textual"), nota=r.get("nota"),
    )


def regla(nombre: str, fecha: dt.date) -> Regla:
    """Devuelve la regla vigente para `nombre` en `fecha`."""
    if isinstance(fecha, dt.datetime):
        fecha = fecha.date()
    return _regla(nombre, fecha)


@lru_cache(maxsize=8192)
def _regla(nombre: str, fecha: dt.date) -> Regla:
    vigente = None
    for r in _versiones(nombre):
        if r.desde <= fecha:
            vigente = r
    if vigente is None:
        raise ValueError(f"No hay regla '{nombre}' vigente en {fecha}")
    return vigente


@lru_cache(maxsize=32)
def _festivos(anio: int) -> dict[dt.date, str]:
    """Festivos de Colombia (Ley 51 de 1983, traslado a lunes) según la librería `holidays`,
    ajustados por las reglas del YAML (p. ej. excluir la Virgen de Chiquinquirá)."""
    base = dict(holidays.CO(years=anio).items())
    try:
        incluir_chiq = regla("festivo_virgen_chiquinquira", dt.date(anio, 12, 31)).valor
    except ValueError:
        incluir_chiq = True  # años anteriores a la regla: la librería no lo incluye
    if not incluir_chiq:
        base = {d: n for d, n in base.items() if "Chiquinquir" not in n}
    return base


def es_festivo(fecha: dt.date) -> bool:
    return fecha in _festivos(fecha.year)


def nombre_festivo(fecha: dt.date) -> str | None:
    return _festivos(fecha.year).get(fecha)


def es_dominical_o_festivo(fecha: dt.date) -> bool:
    return fecha.weekday() == 6 or es_festivo(fecha)
