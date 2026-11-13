"""Liquidación del contrato de trabajo: cesantías, intereses, prima, vacaciones e indemnización.

Cada rubro se devuelve con su base, sus días y la cita de la regla vigente en la fecha de
retiro (``reglas/parametros.yaml``). Nada se calcula con valores escritos en el código.

Alcance (v0.3):
- Contrato laboral ordinario: término indefinido, término fijo y obra o labor.
- Motivos: renuncia, justa causa, mutuo acuerdo, vencimiento del plazo o fin de la obra (sin
  indemnización); despido sin justa causa y terminación por incumplimiento grave del
  empleador (con indemnización del CST art. 64; la segunda requiere que se pruebe).
- Salario fijo o variable (con historial mensual de lo devengado).
- Indemnización moratoria del art. 65, como cálculo aparte por días de retardo.

Fuera de alcance, con error explícito: salario integral (no causa cesantías ni prima) y el
régimen transitorio del art. 64 (10 o más años de servicio al 1-ene-1991).

Supuestos: año comercial de 360 días y meses de 30 (S20); la indemnización se calcula con el
último salario ordinario aunque haya extras variables (S21); las cesantías de años anteriores
ya se consignaron al fondo (Ley 50 de 1990, art. 99); la prima del semestre en curso no se
ha pagado; los días de vacaciones disfrutados los informa el usuario.
"""
from __future__ import annotations

import calendar
import datetime as dt
import statistics
from dataclasses import dataclass, field

from .costo_empleador import Rubro
from .reglas_motor import regla

TIPOS = {"indefinido", "fijo", "obra_labor"}
MOTIVOS_SIN_INDEMNIZACION = {"renuncia", "justa_causa", "mutuo_acuerdo", "vencimiento_plazo", "fin_obra"}
MOTIVOS_CON_INDEMNIZACION = {"sin_justa_causa", "incumplimiento_empleador"}


class FueraDeAlcance(NotImplementedError):
    """El caso existe en la ley pero Nómina Clara todavía no lo calcula."""


# ------------------------------------------------------------------ días

def dias_360(inicio: dt.date, fin: dt.date) -> int:
    """Días entre dos fechas, ambas incluidas, con meses de 30 días (año comercial).

    El inicio cuenta su día (máximo 30). Si el fin es el último día de su mes (28, 29, 30 o
    31), cuenta como el día 30, de modo que un mes completo suma 30 y un año completo 360.
    """
    if fin < inicio:
        return 0
    d1 = min(inicio.day, 30)
    d2 = 30 if fin.day == calendar.monthrange(fin.year, fin.month)[1] else min(fin.day, 30)
    return (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30 + (d2 - d1) + 1


# ------------------------------------------------------------------ datos de entrada

@dataclass
class Contrato:
    fecha_ingreso: dt.date
    fecha_retiro: dt.date                    # último día trabajado (incluido)
    tipo: str                                # indefinido | fijo | obra_labor
    motivo: str                              # ver MOTIVOS_*
    salario_mensual: float                   # último salario ordinario mensual
    fecha_fin_pactada: dt.date | None = None # término fijo: fin del plazo; obra: fin estimado de la obra
    devengado_mensual: dict[tuple[int, int], float] = field(default_factory=dict)
    # (año, mes) -> salario devengado en el mes (incluye recargos y extras), expresado como mes completo
    # (si el último mes fue parcial, informe su equivalente mensual). Solo si el salario es variable.
    devengado_vacaciones_mensual: dict[tuple[int, int], float] = field(default_factory=dict)
    # (año, mes) -> devengado sin dominicales ni horas extra (CST art. 192). Solo si es variable.
    dias_vacaciones_disfrutados: float = 0.0
    cesantias_pendientes_desde: dt.date | None = None   # por defecto, 1-ene del año de retiro
    prima_pendiente_desde: dt.date | None = None        # por defecto, inicio del semestre en curso
    salario_integral: bool = False

    def validar(self) -> None:
        if self.tipo not in TIPOS:
            raise ValueError(f"tipo debe ser uno de {sorted(TIPOS)}")
        if self.motivo not in MOTIVOS_SIN_INDEMNIZACION | MOTIVOS_CON_INDEMNIZACION:
            raise ValueError(f"motivo desconocido: {self.motivo!r}")
        if self.fecha_retiro < self.fecha_ingreso:
            raise ValueError("La fecha de retiro es anterior a la de ingreso")
        if self.salario_mensual <= 0:
            raise ValueError("El salario debe ser positivo")
        if self.dias_vacaciones_disfrutados < 0:
            raise ValueError("Los días de vacaciones disfrutados no pueden ser negativos")
        if self.salario_integral:
            raise FueraDeAlcance("Salario integral: no causa cesantías ni prima (CST art. 132); aún no se liquida aquí.")
        if self.motivo in MOTIVOS_CON_INDEMNIZACION and self.tipo in {"fijo", "obra_labor"} and not self.fecha_fin_pactada:
            raise ValueError("Para indemnizar un contrato a término fijo u obra se necesita fecha_fin_pactada")


@dataclass
class Liquidacion:
    rubros: list[Rubro]
    dias_servicio: int
    alertas: list[str]
    supuestos: list[str]

    @property
    def total(self) -> float:
        return round(sum(r.valor for r in self.rubros), 2)

    def tabla(self) -> str:
        filas = [f"{'Concepto':38} {'Base':>14} {'Valor':>14}"]
        for r in self.rubros:
            filas.append(f"{r.concepto:38} {r.base:>14,.0f} {r.valor:>14,.0f}".replace(",", "."))
        filas.append(f"{'TOTAL':38} {'':>14} {self.total:>14,.0f}".replace(",", "."))
        return "\n".join(filas)


# ------------------------------------------------------------------ bases

def _meses_hacia_atras(fin: dt.date, n: int, desde: dt.date) -> list[tuple[int, int]]:
    salida, a, m = [], fin.year, fin.month
    while len(salida) < n and (a, m) >= (desde.year, desde.month):
        salida.append((a, m))
        a, m = (a - 1, 12) if m == 1 else (a, m - 1)
    return salida


def _auxilio_vigente(c: Contrato) -> tuple[float, str]:
    smmlv = regla("salario_minimo", c.fecha_retiro)
    tope = regla("auxilio_transporte_tope_smmlv", c.fecha_retiro)
    aux = regla("auxilio_transporte", c.fecha_retiro)
    if c.salario_mensual <= tope.valor * smmlv.valor:
        return float(aux.valor), f"auxilio {aux.valor:,.0f} [{aux.cita()}]; tope {tope.valor} SMMLV [{tope.cita()}]".replace(",", ".")
    return 0.0, f"sin auxilio: salario mayor a {tope.valor} SMMLV [{tope.cita()}]"


def base_cesantias(c: Contrato) -> tuple[float, str]:
    """CST art. 253: último salario si no varió en 3 meses; si varió, promedio del último año."""
    r = regla("cesantias_base_salario", c.fecha_retiro)
    ult = _meses_hacia_atras(c.fecha_retiro, r.valor["meses_sin_variacion"], c.fecha_ingreso)
    valores = [c.devengado_mensual[k] for k in ult if k in c.devengado_mensual]
    if len(valores) < len(ult):
        return c.salario_mensual, f"último salario (sin historial de los últimos {len(ult)} meses) [{r.cita()}]"
    if len(set(round(v, 2) for v in valores)) == 1:
        return valores[0], f"último salario devengado (sin variación en {len(ult)} meses) [{r.cita()}]"
    meses = _meses_hacia_atras(c.fecha_retiro, r.valor["meses_promedio"], c.fecha_ingreso)
    datos = [c.devengado_mensual[k] for k in meses if k in c.devengado_mensual]
    falta = f"; ATENCIÓN: solo hay {len(datos)} de {len(meses)} meses en el historial" if len(datos) < len(meses) else ""
    return statistics.fmean(datos), f"promedio de {len(datos)} meses porque el salario varió{falta} [{r.cita()}]"


def base_prima(c: Contrato, desde: dt.date) -> tuple[float, str]:
    r = regla("prima_servicios", c.fecha_retiro)
    meses = [k for k in c.devengado_mensual if (desde.year, desde.month) <= k <= (c.fecha_retiro.year, c.fecha_retiro.month)]
    datos = [c.devengado_mensual[k] for k in sorted(meses)]
    if len(set(round(v, 2) for v in datos)) > 1:
        return statistics.fmean(datos), f"promedio del semestre ({len(datos)} meses; supuesto S19) [{r.cita()}]"
    return c.salario_mensual, f"salario mensual [{r.cita()}]"


def base_vacaciones(c: Contrato) -> tuple[float, str]:
    r = regla("vacaciones_base_excluye", c.fecha_retiro)
    meses = _meses_hacia_atras(c.fecha_retiro, 12, c.fecha_ingreso)
    datos = [c.devengado_vacaciones_mensual[k] for k in meses if k in c.devengado_vacaciones_mensual]
    if len(set(round(v, 2) for v in datos)) > 1:
        return statistics.fmean(datos), f"promedio del último año sin dominicales ni extras (CST 192) [{r.cita()}]"
    return c.salario_mensual, "último salario (CST art. 189, num. 3)"


# ------------------------------------------------------------------ liquidación

def liquidar(c: Contrato) -> Liquidacion:
    c.validar()
    f = c.fecha_retiro
    conv = regla("convencion_dias_comerciales", f)
    anio = conv.valor["dias_anio"]
    rubros: list[Rubro] = []
    alertas: list[str] = []
    supuestos = [f"Días contados con año de {anio} y meses de {conv.valor['dias_mes']} [{conv.cita()}]"]
    servicio = dias_360(c.fecha_ingreso, f)

    aux, cita_aux = _auxilio_vigente(c)
    en_base = regla("auxilio_transporte_en_base_prestaciones", f)

    # Cesantías (CST 249, 253) e intereses (Ley 52 de 1975)
    desde_ces = max(c.cesantias_pendientes_desde or dt.date(f.year, 1, 1), c.fecha_ingreso)
    if c.cesantias_pendientes_desde is None:
        supuestos.append("Cesantías de años anteriores ya consignadas al fondo (Ley 50 de 1990, art. 99)")
    dias_ces = dias_360(desde_ces, f)
    b_ces, cita_b = base_cesantias(c)
    if "ATENCIÓN" in cita_b:
        alertas.append("El promedio para cesantías se calculó con un historial incompleto: " + cita_b.split("ATENCIÓN: ")[1].split(" [")[0])
    aux_ces = aux if en_base.valor["cesantias"] else 0.0
    p = regla("prestaciones_dias_por_anio", f)
    ces = (b_ces + aux_ces) * p.valor["cesantias"] / 30 * dias_ces / anio
    rubros.append(Rubro(f"Cesantías ({dias_ces} días)", b_ces + aux_ces, dias_ces / anio, round(ces, 2),
                        f"{cita_b}; {cita_aux}; auxilio en base [{en_base.cita()}]; [{p.cita()}]"))
    i = regla("intereses_cesantias", f)
    rubros.append(Rubro(f"Intereses de cesantías ({dias_ces} días)", round(ces, 2), i.valor * dias_ces / anio,
                        round(ces * i.valor * dias_ces / anio, 2), f"12 % anual proporcional [{i.cita()}]"))

    # Prima (CST 306)
    sem = dt.date(f.year, 1, 1) if f.month <= 6 else dt.date(f.year, 7, 1)
    desde_pri = max(c.prima_pendiente_desde or sem, c.fecha_ingreso)
    if c.prima_pendiente_desde is None:
        supuestos.append("La prima del semestre en curso no se ha pagado")
    dias_pri = dias_360(desde_pri, f)
    b_pri, cita_p = base_prima(c, desde_pri)
    aux_pri = aux if en_base.valor["prima"] else 0.0
    pr = regla("prima_servicios", f)
    prima = (b_pri + aux_pri) * pr.valor["dias_por_anio"] / 30 * dias_pri / anio
    rubros.append(Rubro(f"Prima de servicios ({dias_pri} días)", b_pri + aux_pri, dias_pri / anio, round(prima, 2),
                        f"{cita_p}; {cita_aux}"))

    # Vacaciones (CST 186, 189; Ley 995 de 2005)
    vc = regla("vacaciones_compensacion_proporcional", f)
    causadas = p.valor["vacaciones"] * servicio / anio
    pendientes = causadas - c.dias_vacaciones_disfrutados
    if pendientes < -1e-9:
        alertas.append(f"Se reportan {c.dias_vacaciones_disfrutados} días disfrutados pero solo se causaron "
                       f"{causadas:.2f}: hubo vacaciones anticipadas. No se descuentan (CST art. 149 exige autorización escrita).")
        pendientes = 0.0
    b_vac, cita_v = base_vacaciones(c)
    vac = b_vac / 30 * pendientes
    rubros.append(Rubro(f"Vacaciones compensadas ({pendientes:.2f} días)", b_vac, pendientes / 30, round(vac, 2),
                        f"{p.valor['vacaciones']} días por {anio} trabajados; {cita_v}; [{vc.cita()}]"))

    # Indemnización por terminación sin justa causa (CST 64)
    if c.motivo in MOTIVOS_CON_INDEMNIZACION:
        rubros.append(_indemnizacion(c, servicio, anio))
        if c.devengado_mensual:
            supuestos.append("Indemnización con el último salario ordinario, sin promediar extras variables (S21)")
        if c.motivo == "incumplimiento_empleador":
            alertas.append("Terminación por incumplimiento grave del empleador: la indemnización procede si se prueba "
                           "(CST art. 47, parágrafo, mod. Ley 2466 de 2025). Se muestra el valor que correspondería.")

    for r in (regla("salario_minimo", f), regla("auxilio_transporte", f)):
        if not r.verificada:
            alertas.append(f"Regla sin verificar en el texto oficial: {r.cita()}")
    alertas.append("Pague la liquidación al terminar el contrato: el retardo genera la indemnización del CST art. 65 "
                   "(use indemnizacion_moratoria) y los intereses de cesantías no pagados se deben dobles (Decreto 116 de 1976, art. 5).")
    return Liquidacion(rubros, servicio, alertas, supuestos)


def _indemnizacion(c: Contrato, servicio: int, anio: int) -> Rubro:
    r = regla("indemnizacion_despido", c.fecha_retiro)
    v = r.valor
    diario = c.salario_mensual / 30
    if c.tipo == "fijo":
        dias = dias_360(c.fecha_retiro + dt.timedelta(days=1), c.fecha_fin_pactada)
        return Rubro(f"Indemnización art. 64 ({dias} días que faltaban del plazo)", c.salario_mensual, dias / 30,
                     round(diario * dias, 2), f"salarios del tiempo que faltaba [{r.cita()}]")
    if c.tipo == "obra_labor":
        faltan = dias_360(c.fecha_retiro + dt.timedelta(days=1), c.fecha_fin_pactada)
        dias = max(faltan, v["obra_labor_minimo_dias"])
        return Rubro(f"Indemnización art. 64 ({dias} días; mínimo {v['obra_labor_minimo_dias']})", c.salario_mensual,
                     dias / 30, round(diario * dias, 2), f"tiempo que faltaba de la obra [{r.cita()}]")
    if c.fecha_ingreso < v["regimen_transitorio_ingreso_antes_de"]:
        raise FueraDeAlcance("10 o más años de servicio al 1-ene-1991: aplica el régimen de la Ley 50 de 1990 "
                             "(parágrafo transitorio del art. 64), que Nómina Clara no calcula.")
    smmlv = regla("salario_minimo", c.fecha_retiro)
    tabla = v["umbral_o_mas"] if c.salario_mensual >= v["umbral_smmlv"] * smmlv.valor else v["menos_de_umbral"]
    adicionales = max(0, servicio - anio) / anio      # años después del primero, con fracción
    dias = tabla["primer_anio"] + tabla["por_anio_adicional"] * adicionales
    rango = "10 SMMLV o más" if tabla is v["umbral_o_mas"] else "menos de 10 SMMLV"
    return Rubro(f"Indemnización art. 64 ({dias:.2f} días)", c.salario_mensual, dias / 30, round(diario * dias, 2),
                 f"{tabla['primer_anio']} días el primer año + {tabla['por_anio_adicional']} por año adicional "
                 f"({adicionales:.4f}); salario de {rango} [{smmlv.cita()}] [{r.cita()}]")


def indemnizacion_moratoria(salario_mensual: float, fecha_retiro: dt.date, dias_retardo: int) -> tuple[Rubro, list[str]]:
    """CST art. 65: un día de salario por cada día de retardo en pagar la liquidación."""
    if dias_retardo < 0:
        raise ValueError("Los días de retardo no pueden ser negativos")
    r = regla("indemnizacion_moratoria", fecha_retiro)
    smmlv = regla("salario_minimo", fecha_retiro)
    alertas = []
    dias = dias_retardo
    if salario_mensual > r.valor["tope_aplica_si_salario_mayor_a_smmlv"] * smmlv.valor:
        tope = r.valor["tope_meses"] * 30
        if dias > tope:
            alertas.append(f"Pasados {r.valor['tope_meses']} meses se deben intereses moratorios a la tasa máxima "
                           "certificada por la Superintendencia Financiera; no se calculan aquí.")
            dias = tope
    else:
        alertas.append("Salario de 1 SMMLV o menos: rige el art. 65 anterior a la Ley 789 de 2002, sin tope de 24 meses.")
    return (Rubro(f"Indemnización moratoria art. 65 ({dias} días)", salario_mensual, dias / 30,
                  round(salario_mensual / 30 * dias, 2), r.cita()), alertas)
