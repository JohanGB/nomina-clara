import datetime as dt

from hypothesis import given, settings, strategies as st

from nomina_clara.costo_empleador import costo_mensual, total
from nomina_clara.reglas_motor import es_festivo, regla
from nomina_clara.turnos import Turno, liquidar_turnos, total_recargos

D = dt.datetime
SAL = 1750905


def test_reglas_por_vigencia():
    assert regla("inicio_nocturno", dt.date(2025, 12, 24)).valor == 21
    assert regla("inicio_nocturno", dt.date(2025, 12, 25)).valor == 19
    assert regla("recargo_dominical_festivo", dt.date(2026, 6, 30)).valor == 0.80
    assert regla("recargo_dominical_festivo", dt.date(2026, 7, 1)).valor == 0.90
    assert regla("recargo_dominical_festivo", dt.date(2027, 7, 1)).valor == 1.00
    assert regla("jornada_maxima_semanal", dt.date(2026, 7, 15)).valor == 42


def test_festivos_2026():
    assert es_festivo(dt.date(2026, 11, 16))       # Independencia de Cartagena (lunes)
    assert es_festivo(dt.date(2026, 7, 13))        # Virgen de Chiquinquirá (trasladado)
    assert not es_festivo(dt.date(2026, 11, 11))


def test_turno_diurno_entre_semana_sin_recargo():
    lineas = liquidar_turnos([Turno(D(2026, 11, 11, 8), D(2026, 11, 11, 16))], SAL)
    assert total_recargos(lineas) == 0


def test_nocturno_empieza_7pm_desde_reforma():
    # Martes 10-nov-2026, 18:00 a 22:00 -> 3 h nocturnas (19-22)
    lineas = liquidar_turnos([Turno(D(2026, 11, 10, 18), D(2026, 11, 10, 22))], SAL)
    noct = sum(l.minutos for l in lineas if "nocturna" in l.concepto)
    assert noct == 180
    vh = SAL / 210
    assert abs(total_recargos(lineas) - round(3 * vh * 0.35, 2)) < 0.05


def test_mismo_turno_antes_de_reforma_tenia_menos_nocturno():
    antes = liquidar_turnos([Turno(D(2025, 12, 23, 18), D(2025, 12, 23, 22))], SAL)
    assert sum(l.minutos for l in antes if "nocturna" in l.concepto) == 60  # solo 21-22


def test_cruce_a_domingo_y_festivo():
    # Sábado 14-nov 22:00 a domingo 15-nov 06:00 (nocturno; desde medianoche dominical)
    lineas = liquidar_turnos([Turno(D(2026, 11, 14, 22), D(2026, 11, 15, 6))], SAL)
    dom = sum(l.minutos for l in lineas if "dominical" in l.concepto)
    assert dom == 360
    vh = SAL / 210
    esperado = 2 * vh * 0.35 + 6 * vh * (0.35 + 0.90)
    assert abs(total_recargos(lineas) - esperado) < 0.1


def test_horas_extra_sobre_jornada_semanal():
    # 6 días x 8 h (lunes 9 a sábado 14 de nov-2026) = 48 h; jornada 42 -> 6 h extra
    turnos = [Turno(D(2026, 11, d, 8), D(2026, 11, d, 16)) for d in range(9, 15)]
    lineas = liquidar_turnos(turnos, SAL)
    extra = sum(l.minutos for l in lineas if l.concepto.startswith("extra"))
    assert extra == 6 * 60


@settings(max_examples=60, deadline=None)
@given(h=st.integers(1, 12), extra_min=st.integers(1, 240))
def test_propiedad_mas_tiempo_nunca_paga_menos(h, extra_min):
    ini = D(2026, 11, 12, 6)
    a = total_recargos(liquidar_turnos([Turno(ini, ini + dt.timedelta(hours=h))], SAL))
    b = total_recargos(liquidar_turnos(
        [Turno(ini, ini + dt.timedelta(hours=h, minutes=extra_min))], SAL))
    assert b >= a


def test_costo_empleador_minimo_exonerado():
    r = costo_mensual(dt.date(2026, 11, 1), SAL)
    nombres = {x.concepto: x for x in r}
    assert nombres["Salud (empleador)"].valor == 0
    assert nombres["Auxilio de transporte"].valor == 249095
    assert nombres["Pensión (empleador)"].valor == round(SAL * 0.12, 2)
    assert total(r) > SAL * 1.4


def test_alerta_exceso_horas_extra():
    from nomina_clara.turnos import alertas_legales
    turnos = [Turno(D(2026, 11, d, 6), D(2026, 11, d, 18)) for d in range(9, 15)]  # 72 h
    assert any("tope de 12 h" in a for a in alertas_legales(turnos))
