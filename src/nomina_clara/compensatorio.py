"""Descanso compensatorio por trabajo en días de descanso obligatorio (domingos y festivos).

Reglas (parametros.yaml):
- Ocasional vs habitual: hasta 2 días de descanso obligatorio trabajados en el MES CALENDARIO
  es ocasional; 3 o más, habitual (CST art. 179 par. 1, Ley 2466 de 2025 art. 14; verificado).
- Ocasional: el trabajador ELIGE recargo en dinero o descanso compensatorio remunerado
  (CST art. 180, Ley 50 de 1990 art. 30; verificado).
- Habitual: descanso compensatorio remunerado SIN PERJUICIO del recargo en dinero
  (CST art. 181, Ley 50 de 1990 art. 31; verificado).
- Plazo: otro día laborable de la semana siguiente (CST art. 183; verificado, paráfrasis).

Supuestos (docs/supuestos.md): un día de descanso obligatorio "trabajado" es una fecha con al
menos un minuto de trabajo (S9); los festivos que no caen en domingo también generan
compensatorio en el caso habitual (S10, lectura literal del art. 181); el valor de un
compensatorio es un día de salario ordinario = salario mensual / 30 (S11).
"""
from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field

from .reglas_motor import es_dominical_o_festivo, es_festivo, regla
from .turnos import Turno, liquidar_turnos, validar_turnos


@dataclass
class ResultadoCompensatorio:
    anio: int
    mes: int
    caso: str                                  # "sin trabajo dominical" | "ocasional" | "habitual"
    dias_descanso_trabajados: list[dt.date]
    eleccion_ocasional: str | None             # "dinero" | "compensatorio" | None
    compensatorios_generados: int
    otorgados: dict[dt.date, dt.date]          # día trabajado -> día compensatorio
    faltantes: list[dt.date]                   # días trabajados sin compensatorio en plazo
    no_verificables: list[dt.date]             # la semana siguiente cae fuera del cuadro
    valor_dia: float
    costo_compensatorios: float                # días pagados sin trabajar (otorgados + debidos)
    pasivo_no_otorgados: float                 # faltantes × valor_dia (supuesto S12)
    recargo_dominical_no_causado: float        # ocasional con compensatorio: recargo que no se paga
    alertas: list[str] = field(default_factory=list)
    citas: list[str] = field(default_factory=list)


def _minutos_por_dia(turnos: list[Turno]) -> dict[dt.date, int]:
    por_dia: dict[dt.date, int] = defaultdict(int)
    for t in validar_turnos(turnos):
        m = t.inicio
        while m < t.fin:
            fin_dia = min(t.fin, dt.datetime.combine(m.date() + dt.timedelta(days=1), dt.time()))
            por_dia[m.date()] += int((fin_dia - m).total_seconds() // 60)
            m = fin_dia
    return por_dia


def dias_descanso_trabajados(turnos: list[Turno], anio: int, mes: int) -> list[dt.date]:
    """Domingos y festivos del mes calendario con al menos un minuto trabajado (S9)."""
    return sorted(d for d, mins in _minutos_por_dia(turnos).items()
                  if d.year == anio and d.month == mes and mins > 0 and es_dominical_o_festivo(d))


def clasificar(n_dias: int, fecha: dt.date) -> tuple[str, str]:
    r = regla("dominical_habitual_desde_dias", fecha)
    if n_dias == 0:
        caso = "sin trabajo dominical"
    elif n_dias >= r.valor:
        caso = "habitual"
    else:
        caso = "ocasional"
    return caso, r.cita()


def _lunes(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def descanso_compensatorio(
    turnos: list[Turno],
    anio: int,
    mes: int,
    salario_mensual: float,
    eleccion_ocasional: str = "dinero",
    descansos_otorgados: list[dt.date] | None = None,
    turnos_semana_siguiente_incluidos: bool = False,
) -> ResultadoCompensatorio:
    """Clasifica el trabajo en días de descanso obligatorio del mes y revisa compensatorios.

    `descansos_otorgados`: días que el cuadro marca como compensatorio. Si es None, se INFIERE:
    cuenta como compensatorio un día laborable (lunes a sábado, no festivo) de la semana
    siguiente sin ningún minuto trabajado (cada día libre cubre un solo compensatorio).
    `turnos_semana_siguiente_incluidos`: True si `turnos` trae también la semana siguiente al
    fin de mes; si no, los domingos de la última semana quedan como "no verificables".
    """
    if eleccion_ocasional not in ("dinero", "compensatorio"):
        raise ValueError("eleccion_ocasional debe ser 'dinero' o 'compensatorio'")
    if salario_mensual <= 0:
        raise ValueError("salario_mensual debe ser positivo")
    ultimo = dt.date(anio, mes, calendar.monthrange(anio, mes)[1])
    trabajados = dias_descanso_trabajados(turnos, anio, mes)
    caso, cita_caso = clasificar(len(trabajados), ultimo)
    derechos = regla("derechos_trabajo_dominical", ultimo)
    plazo = regla("compensatorio_plazo", ultimo)
    citas = [cita_caso, derechos.cita(), plazo.cita()]

    incl_fest = regla("compensatorio_incluye_festivos", ultimo)
    citas.append(incl_fest.cita())
    con_derecho = [d for d in trabajados if incl_fest.valor or d.weekday() == 6]
    if caso == "habitual":
        exigidos = con_derecho
        eleccion = None
    elif caso == "ocasional":
        eleccion = eleccion_ocasional
        exigidos = con_derecho if eleccion_ocasional == "compensatorio" else []
    else:
        exigidos, eleccion = [], None

    minutos = _minutos_por_dia(turnos)
    hasta_cuadro = max(minutos) if minutos else ultimo
    limite_cuadro = hasta_cuadro if turnos_semana_siguiente_incluidos else ultimo

    otorgados: dict[dt.date, dt.date] = {}
    faltantes: list[dt.date] = []
    no_verif: list[dt.date] = []
    alertas: list[str] = []
    usados: set[dt.date] = set()
    explicitos = set(descansos_otorgados or [])

    for d in exigidos:
        ini = _lunes(d) + dt.timedelta(days=7)
        semana_sig = [ini + dt.timedelta(days=i) for i in range(7)]
        candidatos = []
        for c in semana_sig:
            if c in usados or minutos.get(c, 0) > 0:
                continue
            if descansos_otorgados is not None:
                if c in explicitos:
                    candidatos.append(c)
            elif c.weekday() < 6 and not es_festivo(c):
                candidatos.append(c)
        if candidatos:
            otorgados[d] = candidatos[0]
            usados.add(candidatos[0])
        elif semana_sig[-1] > limite_cuadro:
            no_verif.append(d)
            alertas.append(f"{d}: el compensatorio vence la semana del {ini}; el cuadro no la incluye "
                           "(no verificable)")
        else:
            faltantes.append(d)
            alertas.append(f"{d}: trabajo en día de descanso obligatorio ({caso}) sin descanso compensatorio "
                           f"en la semana del {ini} [{derechos.cita()}; {plazo.cita()}]")

    if descansos_otorgados is not None:
        for c in sorted(explicitos):
            if minutos.get(c, 0) > 0:
                alertas.append(f"{c}: marcado como compensatorio pero tiene turnos asignados")

    valor_dia = salario_mensual / 30
    recargo_no_causado = 0.0
    if caso == "ocasional" and eleccion_ocasional == "compensatorio":
        # Con compensatorio no se paga el recargo dominical de esos días (art. 180: uno U otro).
        for d in exigidos:
            dia_turnos = [_recortar(t, d) for t in turnos]
            dia_turnos = [t for t in dia_turnos if t is not None]
            for lin in liquidar_turnos(dia_turnos, salario_mensual):
                recargo_no_causado += lin.componentes.get("dominical", 0.0)

    debidos = len(otorgados) + len(faltantes) + len(no_verif)
    return ResultadoCompensatorio(
        anio=anio, mes=mes, caso=caso, dias_descanso_trabajados=trabajados,
        eleccion_ocasional=eleccion, compensatorios_generados=len(exigidos),
        otorgados=otorgados, faltantes=faltantes, no_verificables=no_verif,
        valor_dia=round(valor_dia, 2),
        costo_compensatorios=round(debidos * valor_dia, 2),
        pasivo_no_otorgados=round(len(faltantes) * valor_dia, 2),
        recargo_dominical_no_causado=round(recargo_no_causado, 2),
        alertas=alertas, citas=citas,
    )


def _recortar(t: Turno, d: dt.date) -> Turno | None:
    ini = max(t.inicio, dt.datetime.combine(d, dt.time()))
    fin = min(t.fin, dt.datetime.combine(d + dt.timedelta(days=1), dt.time()))
    return Turno(ini, fin) if fin > ini else None
