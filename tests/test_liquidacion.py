"""Liquidación del contrato: casos resueltos a mano y pruebas por propiedades.

Valores de 2026 usados en los cálculos a mano (reglas/parametros.yaml):
SMMLV 1.750.905 · auxilio de transporte 249.095 · tope del auxilio 2 SMMLV = 3.501.810 · 10 SMMLV = 17.509.050.
"""
from __future__ import annotations

import datetime as dt

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from nomina_clara.liquidacion import (Contrato, FueraDeAlcance, dias_360, indemnizacion_moratoria,
                                      liquidar)

D = dt.date


def valor(liq, prefijo):
    return next(r.valor for r in liq.rubros if r.concepto.startswith(prefijo))


# ------------------------------------------------------------------ días comerciales

@pytest.mark.parametrize("a, b, esperado", [
    (D(2026, 1, 1), D(2026, 12, 31), 360),      # año completo
    (D(2026, 2, 1), D(2026, 2, 28), 30),        # febrero completo cuenta 30
    (D(2024, 2, 1), D(2024, 2, 29), 30),        # bisiesto también
    (D(2026, 1, 1), D(2026, 1, 31), 30),        # el 31 cierra el mes en 30
    (D(2026, 3, 10), D(2026, 3, 10), 1),        # un solo día
    (D(2026, 1, 15), D(2026, 1, 14), 0),        # fin antes del inicio
    (D(2024, 3, 1), D(2026, 11, 20), 980),      # 2×360 + 8×30 + 20
])
def test_dias_360(a, b, esperado):
    assert dias_360(a, b) == esperado


@settings(max_examples=200, deadline=None)
@given(st.dates(D(2000, 1, 1), D(2030, 12, 31)), st.integers(0, 40), st.integers(1, 40))
def test_dias_360_se_suman_al_partir_en_fin_de_mes(inicio, meses1, meses2):
    """Partir un periodo en un fin de mes no cambia el total."""
    a, m = divmod(inicio.month - 1 + meses1, 12)
    corte = D(inicio.year + a, m + 1, 1) - dt.timedelta(days=1) if meses1 else None
    if corte is None or corte < inicio:
        return
    a2, m2 = divmod(corte.month - 1 + meses2, 12)
    fin = D(corte.year + a2, m2 + 1, 28)
    assert dias_360(inicio, corte) + dias_360(corte + dt.timedelta(days=1), fin) == dias_360(inicio, fin)


# ------------------------------------------------------------------ casos resueltos a mano

def test_indefinido_despido_sin_justa_causa_con_auxilio():
    """Ingreso 1-mar-2024, retiro 20-nov-2026, salario 2.000.000 (≤ 2 SMMLV: lleva auxilio).

    Servicio: 980 días.  Base con auxilio: 2.000.000 + 249.095 = 2.249.095.
    Cesantías 1-ene a 20-nov-2026 = 320 días: 2.249.095 × 320/360 = 1.999.195,56
    Intereses: 1.999.195,56 × 12 % × 320/360 = 213.247,53
    Prima 1-jul a 20-nov = 140 días: 2.249.095 × 140/360 = 874.648,06
    Vacaciones: 15 × 980/360 = 40,8333 días × 2.000.000/30 = 2.722.222,22
    Indemnización (< 10 SMMLV): 30 + 20 × (620/360) = 64,4444 días × 66.666,67 = 4.296.296,30
    """
    liq = liquidar(Contrato(D(2024, 3, 1), D(2026, 11, 20), "indefinido", "sin_justa_causa", 2_000_000))
    assert liq.dias_servicio == 980
    assert valor(liq, "Cesantías") == pytest.approx(1_999_195.56, abs=0.01)
    assert valor(liq, "Intereses") == pytest.approx(213_247.53, abs=0.01)
    assert valor(liq, "Prima") == pytest.approx(874_648.06, abs=0.01)
    assert valor(liq, "Vacaciones") == pytest.approx(2_722_222.22, abs=0.01)
    assert valor(liq, "Indemnización") == pytest.approx(4_296_296.30, abs=0.01)
    assert liq.total == pytest.approx(10_105_609.67, abs=0.05)


def test_termino_fijo_despedido_antes_del_plazo_sin_auxilio():
    """Ingreso 1-feb-2026, plazo hasta 31-ene-2027, retiro 15-ago-2026, salario 4.000.000 (> 2 SMMLV).

    Servicio 1-feb a 15-ago = 195 días.
    Cesantías: 4.000.000 × 195/360 = 2.166.666,67 · Intereses: × 12 % × 195/360 = 140.833,33
    Prima 1-jul a 15-ago = 45 días: 500.000 · Vacaciones: 15 × 195/360 = 8,125 días → 1.083.333,33
    Indemnización: 16-ago-2026 a 31-ene-2027 = 165 días × 133.333,33 = 22.000.000
    """
    liq = liquidar(Contrato(D(2026, 2, 1), D(2026, 8, 15), "fijo", "sin_justa_causa", 4_000_000,
                            fecha_fin_pactada=D(2027, 1, 31)))
    assert valor(liq, "Cesantías") == pytest.approx(2_166_666.67, abs=0.01)
    assert valor(liq, "Intereses") == pytest.approx(140_833.33, abs=0.01)
    assert valor(liq, "Prima") == pytest.approx(500_000.00, abs=0.01)
    assert valor(liq, "Vacaciones") == pytest.approx(1_083_333.33, abs=0.01)
    assert valor(liq, "Indemnización") == pytest.approx(22_000_000.00, abs=0.01)


def test_obra_labor_paga_minimo_quince_dias():
    """La obra terminaba 5 días después del despido: se pagan 15 (mínimo del art. 64). 3.000.000/30 × 15."""
    liq = liquidar(Contrato(D(2026, 6, 1), D(2026, 9, 10), "obra_labor", "sin_justa_causa", 3_000_000,
                            fecha_fin_pactada=D(2026, 9, 15)))
    assert valor(liq, "Indemnización") == pytest.approx(1_500_000.00, abs=0.01)


def test_salario_de_diez_smmlv_o_mas_usa_tabla_de_20_y_15():
    """Salario 20.000.000 (≥ 17.509.050), 2 años y medio: 20 + 15 × 1,5 = 42,5 días × 666.666,67 = 28.333.333,33."""
    liq = liquidar(Contrato(D(2024, 1, 1), D(2026, 6, 30), "indefinido", "sin_justa_causa", 20_000_000))
    assert liq.dias_servicio == 900
    assert valor(liq, "Indemnización") == pytest.approx(28_333_333.33, abs=0.01)


def test_menos_de_un_anio_paga_los_treinta_dias_completos():
    liq = liquidar(Contrato(D(2026, 9, 1), D(2026, 10, 31), "indefinido", "sin_justa_causa", 3_000_000))
    assert valor(liq, "Indemnización") == pytest.approx(3_000_000.00, abs=0.01)


def test_salario_variable_usa_promedio_para_cesantias():
    """El devengado varió en los últimos 3 meses: base = promedio del último año (CST 253).
    Historial nov-2025 a oct-2026: 2.500.000 × 9 (nov–jul), 3.100.000 (ago), 2.800.000 (sep), 3.100.000 (oct)
    → promedio = (22.500.000 + 9.000.000) / 12 = 2.625.000. Salario ordinario 2.500.000 ≤ 2 SMMLV: lleva auxilio.
    Cesantías 1-ene a 31-oct-2026 = 300 días: (2.625.000 + 249.095) × 300/360 = 2.395.079,17
    """
    dev = {(2025, 11): 2_500_000.0, (2025, 12): 2_500_000.0} | {(2026, m): 2_500_000.0 for m in range(1, 8)}
    dev |= {(2026, 8): 3_100_000.0, (2026, 9): 2_800_000.0, (2026, 10): 3_100_000.0}
    liq = liquidar(Contrato(D(2025, 1, 1), D(2026, 10, 31), "indefinido", "renuncia", 2_500_000, devengado_mensual=dev))
    assert valor(liq, "Cesantías") == pytest.approx(2_395_079.17, abs=0.01)
    assert not any(r.concepto.startswith("Indemnización") for r in liq.rubros)
    assert not any("incompleto" in a for a in liq.alertas)


def test_salario_variable_con_historial_incompleto_avisa():
    dev = {(2026, 8): 3_100_000.0, (2026, 9): 2_800_000.0, (2026, 10): 3_100_000.0}
    liq = liquidar(Contrato(D(2025, 1, 1), D(2026, 10, 31), "indefinido", "renuncia", 2_500_000, devengado_mensual=dev))
    assert any("incompleto" in a and "3 de 12" in a for a in liq.alertas)


def test_salario_estable_en_tres_meses_usa_el_ultimo_devengado():
    dev = {(2026, m): 3_200_000.0 for m in (8, 9, 10)}
    liq = liquidar(Contrato(D(2026, 1, 1), D(2026, 10, 31), "indefinido", "renuncia", 3_200_000, devengado_mensual=dev))
    assert valor(liq, "Cesantías") == pytest.approx((3_200_000 + 249_095) * 300 / 360, abs=0.01)


def test_vacaciones_descuentan_las_disfrutadas_y_avisan_si_hubo_anticipo():
    base = dict(fecha_ingreso=D(2025, 1, 1), fecha_retiro=D(2026, 12, 31), tipo="indefinido",
                motivo="renuncia", salario_mensual=3_000_000)
    assert valor(liquidar(Contrato(**base, dias_vacaciones_disfrutados=15)), "Vacaciones") == pytest.approx(1_500_000)
    liq = liquidar(Contrato(**base, dias_vacaciones_disfrutados=40))
    assert valor(liq, "Vacaciones") == 0
    assert any("anticipadas" in a for a in liq.alertas)


def test_casos_fuera_de_alcance_fallan_con_mensaje():
    with pytest.raises(FueraDeAlcance, match="integral"):
        liquidar(Contrato(D(2024, 1, 1), D(2026, 1, 1), "indefinido", "renuncia", 30_000_000, salario_integral=True))
    with pytest.raises(FueraDeAlcance, match="1991"):
        liquidar(Contrato(D(1980, 1, 1), D(2026, 1, 1), "indefinido", "sin_justa_causa", 3_000_000))
    with pytest.raises(ValueError, match="fecha_fin_pactada"):
        liquidar(Contrato(D(2026, 1, 1), D(2026, 5, 1), "fijo", "sin_justa_causa", 3_000_000))


def test_moratoria_tope_de_24_meses_solo_sobre_un_smmlv():
    r, avisos = indemnizacion_moratoria(3_000_000, D(2026, 11, 1), 800)
    assert r.valor == pytest.approx(100_000 * 720) and avisos
    r, avisos = indemnizacion_moratoria(1_750_905, D(2026, 11, 1), 800)
    assert r.valor == pytest.approx(1_750_905 / 30 * 800) and "sin tope" in avisos[0]


def test_cada_rubro_cita_su_regla():
    liq = liquidar(Contrato(D(2024, 3, 1), D(2026, 11, 20), "indefinido", "sin_justa_causa", 2_000_000))
    for r in liq.rubros:
        assert "desde" in r.cita and ("verificado" in r.cita or "por_verificar" in r.cita)


# ------------------------------------------------------------------ propiedades

retiros = st.dates(D(2025, 1, 1), D(2026, 12, 31))   # años con SMMLV en las reglas


@settings(max_examples=150, deadline=None)
@given(retiros, st.integers(0, 4000), st.floats(3_600_000, 8_700_000))
def test_sin_auxilio_todo_es_proporcional_al_salario(retiro, dias, salario):
    """Entre 2 y 10 SMMLV no hay auxilio ni cambio de tabla: duplicar el salario duplica cada rubro."""
    ingreso = retiro - dt.timedelta(days=dias)
    if retiro.year < 2026:            # en 2025 el tope del auxilio es otro: se prueba solo 2026
        return
    a = liquidar(Contrato(ingreso, retiro, "indefinido", "sin_justa_causa", salario))
    b = liquidar(Contrato(ingreso, retiro, "indefinido", "sin_justa_causa", salario * 2))
    for x, y in zip(a.rubros, b.rubros):
        assert y.valor == pytest.approx(2 * x.valor, rel=1e-6, abs=0.05)


@settings(max_examples=150, deadline=None)
@given(retiros, st.integers(0, 4000), st.floats(1_000_000, 15_000_000))
def test_despido_nunca_paga_menos_que_renuncia(retiro, dias, salario):
    ingreso = retiro - dt.timedelta(days=dias)
    r = liquidar(Contrato(ingreso, retiro, "indefinido", "renuncia", salario))
    d = liquidar(Contrato(ingreso, retiro, "indefinido", "sin_justa_causa", salario))
    assert d.total >= r.total
    assert sum(1 for x in d.rubros if x.concepto.startswith("Indemnización")) == 1


@settings(max_examples=150, deadline=None)
@given(retiros, st.integers(0, 3000), st.integers(1, 400), st.floats(1_000_000, 15_000_000))
def test_mas_tiempo_nunca_reduce_vacaciones_ni_indemnizacion(r1, dias, extra, salario):
    ingreso = r1 - dt.timedelta(days=dias)
    r2 = min(r1 + dt.timedelta(days=extra), D(2026, 12, 31))
    if r1.year != r2.year:            # el SMMLV y el auxilio cambian de año a año
        return
    a = liquidar(Contrato(ingreso, r1, "indefinido", "sin_justa_causa", salario))
    b = liquidar(Contrato(ingreso, r2, "indefinido", "sin_justa_causa", salario))
    assert valor(b, "Vacaciones") >= valor(a, "Vacaciones") - 1e-6
    assert valor(b, "Indemnización") >= valor(a, "Indemnización") - 1e-6
