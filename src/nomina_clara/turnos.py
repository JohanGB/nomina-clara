"""Clasificación de turnos minuto a minuto y valoración con recargos.

Reglas y supuestos (ver docs/supuestos.md y docs/decisiones.md):
- Valor hora ordinaria = salario mensual / (jornada semanal × factor), factor = 5 (S1, por verificar).
- Horas extra: minutos que superan la jornada semanal pactada (o la máxima legal), contados en
  orden cronológico dentro de la semana lunes-domingo (S2); opcionalmente también los que
  superan un tope diario.
- En una semana que cruza un cambio de jornada máxima (p. ej. 15-jul-2026, 44 → 42 h) se usa
  el MENOR límite vigente en algún día de esa semana (D2, decisión del autor pendiente).
- Recargos del art. 168 CST excluyentes entre sí (num. 4, verificado): la extra nocturna (75 %)
  reemplaza al nocturno (35 %). El recargo dominical/festivo (art. 179) se suma (S3).
- Nocturno y dominical/festivo se evalúan minuto a minuto con la regla vigente ese día.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from .reglas_motor import es_dominical_o_festivo, regla

UN_MIN = dt.timedelta(minutes=1)


@dataclass(frozen=True)
class Turno:
    inicio: dt.datetime
    fin: dt.datetime

    def __post_init__(self):
        if self.fin <= self.inicio:
            raise ValueError("El turno debe terminar después de empezar")
        if self.inicio.second or self.inicio.microsecond or self.fin.second or self.fin.microsecond:
            raise ValueError("Los turnos se expresan en minutos exactos (sin segundos)")

    @property
    def minutos(self) -> int:
        return int((self.fin - self.inicio).total_seconds() // 60)


@dataclass
class Linea:
    concepto: str          # p. ej. "ordinaria nocturna dominical/festiva"
    minutos: int
    recargo: float         # fracción adicional sobre la hora ordinaria
    valor: float
    reglas: list[str] = field(default_factory=list)
    # Valor del recargo separado por componente: "nocturno", "extra", "dominical".
    componentes: dict[str, float] = field(default_factory=dict)


def validar_turnos(turnos: list[Turno]) -> list[Turno]:
    """Ordena y rechaza turnos solapados (contarían dos veces los mismos minutos).
    Turnos contiguos (uno termina cuando empieza el otro) son válidos."""
    orden = sorted(turnos, key=lambda x: x.inicio)
    for a, b in zip(orden, orden[1:]):
        if b.inicio < a.fin:
            raise ValueError(
                f"Turnos solapados: {a.inicio:%Y-%m-%d %H:%M}-{a.fin:%H:%M} y "
                f"{b.inicio:%Y-%m-%d %H:%M}-{b.fin:%H:%M}")
    return orden


def _validar_jornada(jornada_semanal_pactada: float | None) -> None:
    if jornada_semanal_pactada is not None and jornada_semanal_pactada <= 0:
        raise ValueError("jornada_semanal_pactada debe ser positiva (o None para usar la máxima legal)")


@lru_cache(maxsize=4096)
def _es_nocturno_hora(fecha: dt.date, hora: int) -> tuple[bool, str]:
    r = regla("inicio_nocturno", fecha)
    return (hora >= r.valor or hora < 6), r.cita()


def _es_nocturno(t: dt.datetime) -> tuple[bool, str]:
    return _es_nocturno_hora(t.date(), t.hour)


@lru_cache(maxsize=4096)
def valor_hora(salario: float, fecha: dt.date,
               jornada_semanal: float | None = None) -> tuple[float, list[str]]:
    """Valor de la hora ordinaria. Con `jornada_semanal` (tiempo parcial) el divisor es esa
    jornada × factor; si no, la jornada máxima legal vigente × factor."""
    f = regla("factor_divisor_hora_mensual", fecha)
    if jornada_semanal is None:
        j = regla("jornada_maxima_semanal", fecha)
        divisor = j.valor * f.valor
        citas = [j.cita(), f.cita(), f"divisor={divisor} h/mes"]
    else:
        _validar_jornada(jornada_semanal)
        divisor = jornada_semanal * f.valor
        citas = [f.cita(), f"divisor={divisor} h/mes (jornada pactada {jornada_semanal} h/sem)"]
    return salario / divisor, citas


def _lunes(fecha: dt.date) -> dt.date:
    return fecha - dt.timedelta(days=fecha.weekday())


@lru_cache(maxsize=1024)
def limite_semanal_legal(lunes: dt.date) -> float:
    """Menor jornada máxima legal vigente en algún día de la semana que empieza en `lunes`."""
    return min(regla("jornada_maxima_semanal", lunes + dt.timedelta(days=i)).valor for i in range(7))


def _limite_semana(lunes: dt.date, jornada_semanal_pactada: float | None) -> float:
    legal = limite_semanal_legal(lunes)
    return legal if jornada_semanal_pactada is None else min(jornada_semanal_pactada, legal)


def liquidar_turnos(
    turnos: list[Turno],
    salario_mensual: float,
    jornada_semanal_pactada: float | None = None,
    tope_diario_horas: float | None = None,
    valor_hora_jornada_pactada: bool = False,
) -> list[Linea]:
    """Valora cada minuto trabajado y agrupa por concepto con su cita legal.

    `valor_hora_jornada_pactada=True` calcula el valor hora con la jornada pactada (tiempo
    parcial: salario / (horas pactadas × factor)); por defecto usa la jornada máxima legal.
    """
    _validar_jornada(jornada_semanal_pactada)
    if tope_diario_horas is not None and tope_diario_horas <= 0:
        raise ValueError("tope_diario_horas debe ser positivo")
    orden = validar_turnos(turnos)
    jornada_vh = jornada_semanal_pactada if valor_hora_jornada_pactada else None

    usados_semana: dict[dt.date, int] = defaultdict(int)
    usados_dia: dict[dt.date, int] = defaultdict(int)
    agrupado: dict[str, Linea] = {}

    for t in orden:
        m = t.inicio
        while m < t.fin:
            f = m.date()
            lunes = _lunes(f)
            usados_semana[lunes] += 1
            usados_dia[f] += 1
            extra = usados_semana[lunes] > _limite_semana(lunes, jornada_semanal_pactada) * 60
            if tope_diario_horas is not None and usados_dia[f] > tope_diario_horas * 60:
                extra = True

            nocturno, cita_noc = _es_nocturno(m)
            dom = es_dominical_o_festivo(f)
            citas = [cita_noc]
            comp: dict[str, float] = {}

            if extra:
                r = regla("extra_nocturna" if nocturno else "extra_diurna", f)
                comp["extra"] = r.valor
                citas.append(r.cita())
                citas.append(regla("recargos_168_excluyentes", f).cita())
            elif nocturno:
                r = regla("recargo_nocturno", f)
                comp["nocturno"] = r.valor
                citas.append(r.cita())
            if dom:
                r = regla("recargo_dominical_festivo", f)
                comp["dominical"] = r.valor
                citas.append(r.cita())
            recargo = sum(comp.values())

            vh, citas_vh = valor_hora(salario_mensual, f, jornada_vh)
            concepto = " ".join(x for x in [
                "extra" if extra else "ordinaria",
                "nocturna" if nocturno else "diurna",
                "dominical/festiva" if dom else "",
            ] if x)
            clave = f"{concepto}|{recargo:.4f}|{vh:.6f}"
            if clave not in agrupado:
                agrupado[clave] = Linea(concepto, 0, recargo, 0.0, sorted(set(citas + citas_vh)), {})
            lin = agrupado[clave]
            lin.minutos += 1
            lin.valor += vh / 60 * recargo  # solo el recargo; la hora base va en el salario
            for k, v in comp.items():
                lin.componentes[k] = lin.componentes.get(k, 0.0) + vh / 60 * v
            m += UN_MIN

    return sorted(agrupado.values(), key=lambda l: (-l.valor, l.concepto))


def total_recargos(lineas: list[Linea]) -> float:
    return round(sum(l.valor for l in lineas), 2)


def recargos_por_componente(lineas: list[Linea]) -> dict[str, float]:
    """Suma del valor por componente. "nocturno" es el recargo nocturno ORDINARIO (entra en la
    base de vacaciones, art. 192 CST); "extra" y "dominical" no entran."""
    tot = {"nocturno": 0.0, "extra": 0.0, "dominical": 0.0}
    for l in lineas:
        for k, v in l.componentes.items():
            tot[k] += v
    return {k: round(v, 2) for k, v in tot.items()}


def alertas_legales(
    turnos: list[Turno],
    jornada_semanal_pactada: float | None = None,
    jornada_diaria_ordinaria: float | None = None,
    sector_exceptuado: str | None = None,
) -> list[str]:
    """Alertas de cumplimiento (no bloquean el cálculo).

    Topes de trabajo suplementario: 2 h diarias y 12 h semanales (Ley 50 de 1990, art. 22,
    modificado por la Ley 2466 de 2025, art. 13; verificado). Los sectores de seguridad y salud
    están exceptuados: con `sector_exceptuado="seguridad"` o `"salud"` la alerta de topes se
    reemplaza por una nota.
    """
    _validar_jornada(jornada_semanal_pactada)
    orden = validar_turnos(turnos)
    por_semana: dict[dt.date, int] = defaultdict(int)
    por_dia: dict[dt.date, int] = defaultdict(int)
    for t in orden:
        m = t.inicio
        while m < t.fin:  # reparte por día calendario real (turnos que cruzan medianoche)
            fin_dia = min(t.fin, dt.datetime.combine(m.date() + dt.timedelta(days=1), dt.time()))
            mins = int((fin_dia - m).total_seconds() // 60)
            por_dia[m.date()] += mins
            por_semana[_lunes(m.date())] += mins
            m = fin_dia

    alertas: list[str] = []
    for lunes, mins in sorted(por_semana.items()):
        tope = regla("tope_horas_extra", lunes)
        exceptuado = sector_exceptuado in tope.valor["sectores_exceptuados"]
        extra_h = max(0.0, mins / 60 - _limite_semana(lunes, jornada_semanal_pactada))
        if extra_h > tope.valor["semanal"]:
            anio, sem, _ = lunes.isocalendar()
            if exceptuado:
                alertas.append(f"Semana {anio}-S{sem}: {extra_h:.1f} h extra; sector {sector_exceptuado} "
                               f"exceptuado del tope de {tope.valor['semanal']} h [{tope.cita()}]")
            else:
                alertas.append(f"Semana {anio}-S{sem}: {extra_h:.1f} h extra superan el tope de "
                               f"{tope.valor['semanal']} h semanales [{tope.cita()}]")
    for dia, mins in sorted(por_dia.items()):
        tope = regla("tope_horas_extra", dia)
        if sector_exceptuado in tope.valor["sectores_exceptuados"]:
            continue
        diaria = jornada_diaria_ordinaria
        if diaria is None:
            diaria = regla("jornada_maxima_diaria", dia).valor["ordinaria"]
        extra_h = mins / 60 - diaria
        if extra_h > tope.valor["diario"]:
            alertas.append(f"Día {dia}: {extra_h:.1f} h por encima de la jornada diaria de {diaria} h "
                           f"superan el tope de {tope.valor['diario']} h extra diarias [{tope.cita()}]")
    for t in orden:
        h = t.minutos / 60
        if h > 12:
            alertas.append(f"Turno {t.inicio:%Y-%m-%d %H:%M} de {h:.1f} h: revisar jornada y descansos")
    return alertas
