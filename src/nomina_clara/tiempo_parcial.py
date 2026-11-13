"""Tiempo parcial, trabajo por días y por horas.

- Salario mínimo proporcional a las horas efectivamente trabajadas (CST art. 147; verificado).
- Valor hora = salario / (horas semanales pactadas × factor) (S1, por verificar).
- Auxilio de transporte proporcional a los días laborados (por verificar; decisión del autor).
- Prestaciones proporcionales: mismas fórmulas que a tiempo completo sobre el salario pactado.
- Cotización por semanas para quienes laboran menos de 30 días en el mes y ganan menos de
  1 SMMLV (Decreto 2616 de 2013 compilado en el Decreto 1072 de 2015; tabla verificada contra
  la guía de la UGPP): 1-7 días = 1 semana, 8-14 = 2, 15-21 = 3, 22-29 = 4; cada semana vale
  1/4 de SMMLV; se cotiza a pensión, ARL y caja; salud NO (régimen subsidiado o beneficiario).
- Si no se cumplen ambas condiciones, se cotiza el mes completo con IBC mínimo de 1 SMMLV
  (S13, por verificar; decisión del autor para quien trabaja todos los días pocas horas).
- El Piso de Protección Social (art. 193 Ley 1955 de 2019) es inexequible desde el 20-jun-2023
  (C-276 de 2021; verificado) y no se modela.
"""
from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass

from .costo_empleador import (Rubro, _validar_recargos, exonerado, redondear, rubros_aportes,
                              rubros_parafiscales_icbf_sena, rubros_provisiones)
from .reglas_motor import regla
from .turnos import Turno, valor_hora, validar_turnos


def salario_minimo_proporcional(fecha: dt.date, horas_semanales: float) -> tuple[float, list[str]]:
    """SMMLV × horas pactadas / jornada máxima legal (CST art. 147)."""
    if horas_semanales <= 0:
        raise ValueError("horas_semanales debe ser positivo")
    smmlv = regla("salario_minimo", fecha)
    j = regla("jornada_maxima_semanal", fecha)
    if horas_semanales > j.valor:
        raise ValueError(f"{horas_semanales} h/semana superan la jornada máxima legal de {j.valor} h")
    p = regla("salario_minimo_proporcional", fecha)
    return smmlv.valor * horas_semanales / j.valor, [smmlv.cita(), j.cita(), p.cita()]


def valor_hora_tiempo_parcial(salario: float, horas_semanales: float, fecha: dt.date) -> tuple[float, list[str]]:
    return valor_hora(salario, fecha, horas_semanales)


def semanas_cotizacion(dias_laborados: int, fecha: dt.date) -> tuple[int, str]:
    r = regla("cotizacion_por_semanas", fecha)
    for desde, hasta, semanas in r.valor["tabla"]:
        if desde <= dias_laborados <= hasta:
            return semanas, r.cita()
    raise ValueError(f"{dias_laborados} días no están en la tabla de cotización por semanas")


def aplica_cotizacion_por_semanas(fecha: dt.date, salario: float, dias_laborados: int) -> bool:
    r = regla("cotizacion_por_semanas", fecha).valor
    smmlv = regla("salario_minimo", fecha).valor
    return dias_laborados < r["dias_menos_de"] and salario < r["salario_menor_a_smmlv"] * smmlv


def dias_laborados_en_mes(turnos: list[Turno], anio: int, mes: int) -> int:
    """Días calendario del mes con al menos un minuto trabajado."""
    dias: set[dt.date] = set()
    for t in validar_turnos(turnos):
        m = t.inicio
        while m < t.fin:
            if m.year == anio and m.month == mes:
                dias.add(m.date())
            m = min(t.fin, dt.datetime.combine(m.date() + dt.timedelta(days=1), dt.time()))
    return len(dias)


@dataclass
class ResumenTiempoParcial:
    salario_minimo_proporcional: float
    valor_hora: float
    dias_laborados: int
    modalidad_cotizacion: str      # "por semanas (N)" | "mensual"
    ibc: float


def costo_mensual_tiempo_parcial(
    fecha: dt.date,
    salario: float,
    horas_semanales: float,
    dias_laborados: int,
    recargos_y_extras: float = 0.0,
    clase_riesgo_arl: str = "I",
    exonerado_art_114_1: bool = True,
    recargo_nocturno_ordinario: float = 0.0,
) -> tuple[list[Rubro], ResumenTiempoParcial]:
    """Costo mensual de un trabajador de tiempo parcial / por días / por horas.

    `salario`: salario mensual pactado (o lo devengado en el mes por las horas ordinarias).
    `dias_laborados`: días calendario del mes con trabajo (ver `dias_laborados_en_mes`).
    """
    _validar_recargos(recargos_y_extras, recargo_nocturno_ordinario)
    if not 1 <= dias_laborados <= 31:
        raise ValueError("dias_laborados debe estar entre 1 y 31")
    dias = min(dias_laborados, 30)
    minimo, citas_min = salario_minimo_proporcional(fecha, horas_semanales)
    if salario + 0.005 < minimo:
        raise ValueError(f"Salario {salario:,.0f} inferior al mínimo proporcional {minimo:,.0f} "
                         f"para {horas_semanales} h/semana (CST art. 147)")
    smmlv = regla("salario_minimo", fecha)
    aux = regla("auxilio_transporte", fecha)
    tope_aux = regla("auxilio_transporte_tope_smmlv", fecha)
    aux_tp = regla("auxilio_transporte_tiempo_parcial", fecha)
    ibc_max = regla("ibc_maximo_smmlv", fecha)

    devengado = salario + recargos_y_extras
    tiene_aux = salario <= tope_aux.valor * smmlv.valor
    factor_aux = dias / 30 if aux_tp.valor == "proporcional_dias_laborados" else 1.0
    auxilio = aux.valor * factor_aux if tiene_aux else 0.0
    exon, cita_exon = exonerado(fecha, devengado, exonerado_art_114_1)
    vh, _ = valor_hora_tiempo_parcial(salario, horas_semanales, fecha)

    r: list[Rubro] = [
        Rubro("Salario", salario, None, salario,
              f"Contrato a tiempo parcial ({horas_semanales} h/sem); mínimo proporcional "
              f"{minimo:,.0f} [{citas_min[-1]}]"),
        Rubro("Recargos y horas extra", recargos_y_extras, None, recargos_y_extras, "Ver detalle de turnos"),
        Rubro("Auxilio de transporte", aux.valor if tiene_aux else 0, factor_aux if tiene_aux else None, auxilio,
              aux.cita() + (f" × {dias}/30 [{aux_tp.cita()}]" if tiene_aux else " — no aplica")),
    ]

    if aplica_cotizacion_por_semanas(fecha, salario, dias):
        cps = regla("cotizacion_por_semanas", fecha)
        semanas, _ = semanas_cotizacion(dias, fecha)
        ibc = semanas * cps.valor["valor_semana_smmlv"] * smmlv.valor
        base_arl = smmlv.valor if cps.valor["arl_base"] == "smmlv_mensual" else ibc
        r += rubros_aportes(fecha, ibc, clase_riesgo_arl, exon, cita_exon, base_arl=base_arl,
                            salud_aplica=False,
                            nota_salud=f"No cotiza en la modalidad por semanas: el trabajador debe estar en el "
                                       f"régimen subsidiado o ser beneficiario [{cps.cita()}]")
        for x in r[-3:]:
            if x.concepto.startswith("ARL"):
                x.cita += f"; base ARL = {cps.valor['arl_base']} (supuesto S12b) [{cps.cita()}]"
            else:
                x.cita += f"; {semanas} semana(s) × 1/4 SMMLV [{cps.cita()}]"
        # ICBF y SENA no hacen parte de la cotización por semanas (pensión, ARL, caja); si el
        # empleador no está exonerado se liquidan sobre la nómina real (supuesto S14).
        r += rubros_parafiscales_icbf_sena(fecha, devengado, exon, cita_exon)
        modalidad = f"por semanas ({semanas})"
    else:
        ibc = min(max(devengado, smmlv.valor), ibc_max.valor * smmlv.valor)
        r += rubros_aportes(fecha, ibc, clase_riesgo_arl, exon, cita_exon)
        for x in r[-4:]:
            x.cita += "; mensual: IBC mínimo 1 SMMLV (supuesto S13)"
        r += rubros_parafiscales_icbf_sena(fecha, ibc, exon, cita_exon)
        modalidad = "mensual"

    r += rubros_provisiones(fecha, devengado, auxilio, salario + recargo_nocturno_ordinario)
    resumen = ResumenTiempoParcial(round(minimo, 2), round(vh, 2), dias, modalidad, round(ibc, 2))
    return redondear(r), resumen
