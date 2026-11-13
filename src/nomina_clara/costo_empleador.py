"""Costo mensual total de un trabajador para el empleador, con cada rubro citado.

Alcance: contrato laboral ordinario a tiempo completo (`costo_mensual`) y, desde v0.2,
tiempo parcial / por días / por horas (`nomina_clara.tiempo_parcial`), que reutiliza los
bloques de este módulo. Pendiente: salario integral, aprendices, trabajo doméstico.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .reglas_motor import regla


@dataclass
class Rubro:
    concepto: str
    base: float
    tasa: float | None
    valor: float
    cita: str


def _validar_recargos(recargos_y_extras: float, recargo_nocturno_ordinario: float) -> None:
    if recargos_y_extras < 0 or recargo_nocturno_ordinario < 0:
        raise ValueError("Recargos negativos")
    if recargo_nocturno_ordinario > recargos_y_extras + 0.005:
        raise ValueError("recargo_nocturno_ordinario es una parte de recargos_y_extras y no puede superarlo")


def exonerado(fecha: dt.date, devengado: float, exonerado_art_114_1: bool) -> tuple[bool, str]:
    """¿Aplica la exoneración del art. 114-1 ET? `exonerado_art_114_1` indica si el EMPLEADOR
    es sujeto (persona jurídica declarante, o persona natural con 2+ trabajadores)."""
    smmlv = regla("salario_minimo", fecha)
    ex = regla("exoneracion_art_114_1", fecha)
    aplica = exonerado_art_114_1 and devengado < ex.valor["tope_smmlv"] * smmlv.valor
    return aplica, ex.cita()


def rubros_aportes(fecha: dt.date, ibc: float, clase_riesgo_arl: str, exon: bool, cita_exon: str,
                   base_arl: float | None = None, base_caja: float | None = None,
                   salud_aplica: bool = True, nota_salud: str = "") -> list[Rubro]:
    ap = regla("aportes_empleador", fecha)
    t = ap.valor
    if clase_riesgo_arl not in t["arl"]:
        raise ValueError(f"Clase de riesgo ARL desconocida: {clase_riesgo_arl!r} (use I a V)")
    r: list[Rubro] = []

    def ap_(nombre: str, clave: str, base: float, exento: bool = False, nota_exento: str = ""):
        if exento:
            r.append(Rubro(nombre, base, 0.0, 0.0, nota_exento))
        else:
            tasa = t[clave]
            r.append(Rubro(nombre, base, tasa, base * tasa,
                           f"{clave}={tasa:.2%} sobre {base:,.0f}; {ap.fuente} ({ap.estado})"))

    if not salud_aplica:
        ap_("Salud (empleador)", "salud", 0.0, True, nota_salud)
    else:
        ap_("Salud (empleador)", "salud", ibc, exon, f"Exonerado [{cita_exon}]")
    ap_("Pensión (empleador)", "pension", ibc)
    b_arl = ibc if base_arl is None else base_arl
    tasa_arl = t["arl"][clase_riesgo_arl]
    r.append(Rubro(f"ARL clase {clase_riesgo_arl}", b_arl, tasa_arl, b_arl * tasa_arl,
                   f"arl={tasa_arl:.3%} sobre {b_arl:,.0f}; Decreto 1295 de 1994, art. 26 ({ap.estado})"))
    ap_("Caja de compensación", "caja_compensacion", ibc if base_caja is None else base_caja)
    return r


def rubros_parafiscales_icbf_sena(fecha: dt.date, base: float, exon: bool, cita_exon: str) -> list[Rubro]:
    ap = regla("aportes_empleador", fecha)
    out = []
    for nombre, clave in (("ICBF", "icbf"), ("SENA", "sena")):
        if exon:
            out.append(Rubro(nombre, base, 0.0, 0.0, f"Exonerado [{cita_exon}]"))
        else:
            tasa = ap.valor[clave]
            out.append(Rubro(nombre, base, tasa, base * tasa,
                             f"{clave}={tasa:.2%} sobre {base:,.0f}; {ap.fuente} ({ap.estado})"))
    return out


def rubros_provisiones(fecha: dt.date, devengado: float, auxilio: float, base_vacaciones: float) -> list[Rubro]:
    """Provisiones mensuales en días de salario por año sobre 360 (CST 249, 306, 186)."""
    p = regla("prestaciones_dias_por_anio", fecha)
    i = regla("intereses_cesantias", fecha)
    a = regla("auxilio_transporte_en_base_prestaciones", fecha)
    v = regla("vacaciones_base_excluye", fecha)
    d, n = p.valor, p.valor["base_dias_anio"]
    aux_ces = auxilio if a.valor["cesantias"] else 0.0
    aux_pri = auxilio if a.valor["prima"] else 0.0
    ces = (devengado + aux_ces) * d["cesantias"] / n
    return [
        Rubro("Provisión cesantías", devengado + aux_ces, d["cesantias"] / n, ces,
              f"{d['cesantias']}/{n} [{p.cita()}]; auxilio en base [{a.cita()}]"),
        Rubro("Provisión intereses cesantías", ces, i.valor, ces * i.valor, i.cita()),
        Rubro("Provisión prima", devengado + aux_pri, d["prima"] / n, (devengado + aux_pri) * d["prima"] / n,
              f"{d['prima']}/{n} [{p.cita()}]"),
        Rubro("Provisión vacaciones", base_vacaciones, d["vacaciones"] / n, base_vacaciones * d["vacaciones"] / n,
              f"{d['vacaciones']}/{n} [{p.cita()}]; base sin dominicales ni extras [{v.cita()}]"),
    ]


def redondear(rubros: list[Rubro]) -> list[Rubro]:
    for x in rubros:
        x.valor = round(x.valor, 2)
    return rubros


def costo_mensual(
    fecha: dt.date,
    salario: float,
    recargos_y_extras: float = 0.0,
    clase_riesgo_arl: str = "I",
    exonerado_art_114_1: bool = True,
    recargo_nocturno_ordinario: float = 0.0,
) -> list[Rubro]:
    """Costo mensual a tiempo completo.

    `recargos_y_extras`: total de recargos y horas extra del mes (salario, art. 127 CST).
    `recargo_nocturno_ordinario`: parte de lo anterior que es recargo nocturno ordinario; entra
    en la base de vacaciones (art. 192 CST excluye solo dominicales/festivos y horas extra).
    """
    _validar_recargos(recargos_y_extras, recargo_nocturno_ordinario)
    smmlv = regla("salario_minimo", fecha)
    aux = regla("auxilio_transporte", fecha)
    tope_aux = regla("auxilio_transporte_tope_smmlv", fecha)
    ibc_max = regla("ibc_maximo_smmlv", fecha)

    if salario < smmlv.valor:
        raise ValueError("Salario inferior al mínimo para jornada completa; "
                         "para tiempo parcial use nomina_clara.tiempo_parcial.costo_mensual_tiempo_parcial")

    devengado = salario + recargos_y_extras
    tiene_aux = salario <= tope_aux.valor * smmlv.valor
    auxilio = aux.valor if tiene_aux else 0.0
    ibc = min(max(devengado, smmlv.valor), ibc_max.valor * smmlv.valor)
    exon, cita_exon = exonerado(fecha, devengado, exonerado_art_114_1)

    r: list[Rubro] = [
        Rubro("Salario", salario, None, salario, "Contrato"),
        Rubro("Recargos y horas extra", recargos_y_extras, None, recargos_y_extras, "Ver detalle de turnos"),
        Rubro("Auxilio de transporte", 0, None, auxilio,
              aux.cita() + (f" — aplica: salario ≤ {tope_aux.valor} SMMLV" if tiene_aux else " — no aplica")),
    ]
    r += rubros_aportes(fecha, ibc, clase_riesgo_arl, exon, cita_exon)
    r += rubros_parafiscales_icbf_sena(fecha, ibc, exon, cita_exon)
    r += rubros_provisiones(fecha, devengado, auxilio, salario + recargo_nocturno_ordinario)
    return redondear(r)


def total(rubros: list[Rubro]) -> float:
    return round(sum(x.valor for x in rubros), 2)
