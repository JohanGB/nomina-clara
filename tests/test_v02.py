"""Pruebas de v0.2: trazabilidad, correcciones, compensatorio, tiempo parcial y propiedades.

Convención: cada caso resuelto a mano muestra el cálculo esperado en el comentario.
SMMLV 2026 = 1.750.905 (por verificar); jornada desde 15-jul-2026 = 42 h; divisor = 210.
"""
import datetime as dt
import random

import pytest
from hypothesis import assume, given, settings, strategies as st

from nomina_clara.compensatorio import descanso_compensatorio
from nomina_clara.costo_empleador import costo_mensual, total
from nomina_clara.reglas_motor import nombres_reglas, regla, versiones
from nomina_clara.tiempo_parcial import (aplica_cotizacion_por_semanas, costo_mensual_tiempo_parcial,
                                         dias_laborados_en_mes, salario_minimo_proporcional,
                                         semanas_cotizacion)
from nomina_clara.turnos import (Turno, alertas_legales, liquidar_turnos, recargos_por_componente,
                                 total_recargos, valor_hora)

D = dt.datetime
SAL = 1_750_905
VH = SAL / 210          # 8.337,642857 por hora (42 h × 5)
NOV = dt.date(2026, 11, 1)


def por_concepto(rubros):
    return {x.concepto: x.valor for x in rubros}


# ---------------------------------------------------------------- trazabilidad de reglas
def test_toda_regla_verificada_tiene_url_y_fecha_de_consulta():
    for n in nombres_reglas():
        for r in versiones(n):
            assert r.estado in ("verificado", "por_verificar")
            if r.verificada:
                assert r.url and r.url.startswith("http") and r.consultado == dt.date(2026, 11, 11)


def test_cita_expone_estado_y_fecha_de_consulta():
    c = regla("recargo_dominical_festivo", dt.date(2026, 7, 1)).cita()
    assert "verificado 2026-11-11" in c and "Ley 2466 de 2025" in c
    assert "funcionpublica.gov.co" in regla("inicio_nocturno", dt.date(2026, 1, 1)).cita_completa()


def test_valores_verificados_en_texto_oficial():
    assert regla("salario_minimo", dt.date(2025, 6, 1)).valor == 1_423_500          # Decreto 1572/2024
    assert regla("inicio_nocturno", dt.date(2025, 12, 25)).valor == 19              # Ley 2466 art. 10
    assert regla("tope_horas_extra", NOV).valor["diario"] == 2                      # Ley 2466 art. 13
    assert regla("tope_horas_extra", NOV).valor["semanal"] == 12
    assert regla("dominical_habitual_desde_dias", NOV).valor == 3                   # Ley 2466 art. 14 par. 1
    assert regla("extra_nocturna", NOV).valor == 0.75 and regla("recargos_168_excluyentes", NOV).valor
    assert regla("recargo_dominical_festivo", dt.date(2025, 6, 30)).valor == 0.75
    assert regla("recargo_dominical_festivo", dt.date(2025, 7, 1)).valor == 0.80


# ---------------------------------------------------------------- correcciones (regresión)
def test_jornada_pactada_cero_es_error_y_no_cae_a_la_legal():
    t = [Turno(D(2026, 11, 11, 8), D(2026, 11, 11, 16))]
    with pytest.raises(ValueError):
        liquidar_turnos(t, SAL, jornada_semanal_pactada=0)
    with pytest.raises(ValueError):
        alertas_legales(t, jornada_semanal_pactada=0)


def test_turnos_solapados_se_rechazan_y_contiguos_se_aceptan():
    with pytest.raises(ValueError, match="solapados"):
        liquidar_turnos([Turno(D(2026, 11, 11, 8), D(2026, 11, 11, 16)),
                         Turno(D(2026, 11, 11, 15), D(2026, 11, 11, 18))], SAL)
    liquidar_turnos([Turno(D(2026, 11, 11, 8), D(2026, 11, 11, 16)),
                     Turno(D(2026, 11, 11, 16), D(2026, 11, 11, 18))], SAL)


def test_semana_que_cruza_cambio_de_jornada_usa_el_menor_limite():
    # Semana lun 13 – dom 19 jul 2026; el 15-jul la jornada pasa de 44 a 42 h.
    # Mar 14 a dom 19: 6 turnos de 9 h 15 min = 55,5 h. Límite de la semana = min(44, 42) = 42.
    # Extra = 55,5 − 42 = 13,5 h > 12 → alerta. (v0.1 usaba 44 en alertas: 11,5 h, sin alerta,
    # y 42 en la liquidación: incoherente.)
    t = [Turno(D(2026, 7, d, 6), D(2026, 7, d, 15, 15)) for d in range(14, 20)]
    assert any("13.5 h extra" in a for a in alertas_legales(t))
    extra = sum(l.minutos for l in liquidar_turnos(t, SAL) if l.concepto.startswith("extra"))
    assert extra == 810  # 13,5 h


def test_alerta_tope_diario_y_excepcion_sector_seguridad():
    # Miércoles 11-nov-2026, 7:00 a 18:00 = 11 h; jornada diaria 8 h → 3 h extra > 2.
    t = [Turno(D(2026, 11, 11, 7), D(2026, 11, 11, 18))]
    assert any("tope de 2 h extra diarias" in a for a in alertas_legales(t))
    assert not any("diarias" in a for a in alertas_legales(t, sector_exceptuado="seguridad"))


def test_alerta_reparte_turno_que_cruza_a_la_semana_siguiente():
    # Lun 9 a vie 13 de nov-2026: 5 × 9 h = 45 h; sáb 14: 8 h → 53 h. Dom 15 23:00 a lun 16 07:00:
    # solo 1 h cae en esa semana → 54 h − 42 = 12 h extra, que NO supera el tope de 12.
    # (v0.1 sumaba las 8 h del turno: 61 h → 19 h extra y alerta falsa.)
    t = [Turno(D(2026, 11, d, 6), D(2026, 11, d, 15)) for d in range(9, 14)]
    t += [Turno(D(2026, 11, 14, 6), D(2026, 11, 14, 14)), Turno(D(2026, 11, 15, 23), D(2026, 11, 16, 7))]
    assert not any("semanales" in a for a in alertas_legales(t))


def test_extra_nocturna_reemplaza_al_nocturno_no_se_suma():
    # Martes 10-nov-2026 19:00–21:00 con tope diario 1 h:
    #   19–20 ordinaria nocturna 35 %; 20–21 extra nocturna 75 % (no 35 % + 75 %).
    #   Esperado = 8.337,64 × (0,35 + 0,75) = 9.171,41
    l = liquidar_turnos([Turno(D(2026, 11, 10, 19), D(2026, 11, 10, 21))], SAL, tope_diario_horas=1)
    assert total_recargos(l) == pytest.approx(VH * 1.10, abs=0.01)
    assert {x.recargo for x in l} == {0.35, 0.75}


def test_festivo_trasladado_se_paga_el_lunes_no_en_la_fecha_original():
    # Ley 51 de 1983: Independencia de Cartagena (11-nov) se traslada al lunes 16-nov-2026.
    assert total_recargos(liquidar_turnos([Turno(D(2026, 11, 11, 8), D(2026, 11, 11, 16))], SAL)) == 0
    l = liquidar_turnos([Turno(D(2026, 11, 16, 8), D(2026, 11, 16, 16))], SAL)
    assert total_recargos(l) == pytest.approx(8 * VH * 0.90, abs=0.01)   # 60.031,03


def test_costo_tiempo_completo_resuelto_a_mano():
    # Noviembre 2026, salario mínimo, exonerado, ARL I.
    #   Auxilio 249.095 | IBC 1.750.905
    #   Pensión 12 % = 210.108,60 | ARL 0,522 % = 9.139,72 | Caja 4 % = 70.036,20
    #   Salud, ICBF, SENA = 0 (exonerado)
    #   Base prestaciones = 1.750.905 + 249.095 = 2.000.000
    #   Cesantías 30/360 = 166.666,67 | Intereses 12 % = 20.000,00 | Prima = 166.666,67
    #   Vacaciones 15/360 × 1.750.905 = 72.954,38
    r = por_concepto(costo_mensual(NOV, SAL))
    esperado = {"Auxilio de transporte": 249_095, "Pensión (empleador)": 210_108.60,
                "ARL clase I": 9_139.72, "Caja de compensación": 70_036.20, "Salud (empleador)": 0,
                "ICBF": 0, "SENA": 0, "Provisión cesantías": 166_666.67,
                "Provisión intereses cesantías": 20_000.00, "Provisión prima": 166_666.67,
                "Provisión vacaciones": 72_954.38}
    for k, v in esperado.items():
        assert r[k] == pytest.approx(v, abs=0.011), k
    assert total(costo_mensual(NOV, SAL)) == pytest.approx(SAL + sum(esperado.values()), abs=0.05)


def test_provisiones_exactas_no_redondeadas():
    # v0.1 usaba 0,0833: 2.000.000 × 0,0833 = 166.600 (66,67 menos por mes). Ahora 30/360.
    assert por_concepto(costo_mensual(NOV, SAL))["Provisión cesantías"] != 166_600


def test_vacaciones_incluyen_recargo_nocturno_ordinario_y_excluyen_extras():
    # Recargos 100.000, de los cuales 60.000 son nocturno ordinario (art. 192 CST).
    # Vacaciones = (1.750.905 + 60.000) × 15/360 = 75.454,38
    r = por_concepto(costo_mensual(NOV, SAL, recargos_y_extras=100_000, recargo_nocturno_ordinario=60_000))
    assert r["Provisión vacaciones"] == pytest.approx(75_454.38, abs=0.011)
    with pytest.raises(ValueError):
        costo_mensual(NOV, SAL, recargos_y_extras=10, recargo_nocturno_ordinario=20)


def test_ibc_tope_25_smmlv():
    r = costo_mensual(NOV, 30 * SAL, exonerado_art_114_1=False)
    pension = next(x for x in r if x.concepto == "Pensión (empleador)")
    assert pension.base == 25 * SAL


def test_componentes_separan_nocturno_extra_y_dominical():
    # Sábado 14 22:00 a domingo 15 06:00 (nov-2026): 2 h nocturnas + 6 h nocturnas dominicales.
    #   nocturno = 8 h × 0,35 × VH = 23.345,40 ; dominical = 6 h × 0,90 × VH = 45.023,27
    c = recargos_por_componente(liquidar_turnos([Turno(D(2026, 11, 14, 22), D(2026, 11, 15, 6))], SAL))
    assert c["nocturno"] == pytest.approx(8 * 0.35 * VH, abs=0.01)
    assert c["dominical"] == pytest.approx(6 * 0.90 * VH, abs=0.01)
    assert c["extra"] == 0


# ---------------------------------------------------------------- descanso compensatorio
def _domingos(*dias, mes=11):
    return [Turno(D(2026, mes, d, 8), D(2026, mes, d, 16)) for d in dias]


def test_ocasional_eleccion_dinero_no_exige_compensatorio():
    r = descanso_compensatorio(_domingos(8, 22), 2026, 11, SAL)
    assert r.caso == "ocasional" and r.compensatorios_generados == 0 and not r.alertas


def test_ocasional_eleccion_compensatorio_no_causa_recargo():
    # 2 domingos × 8 h × 0,90 × VH = 2 × 60.031,03 = 120.062,06 que no se pagan en dinero.
    r = descanso_compensatorio(_domingos(8, 22), 2026, 11, SAL, eleccion_ocasional="compensatorio")
    assert r.compensatorios_generados == 2
    assert r.recargo_dominical_no_causado == pytest.approx(2 * 8 * 0.90 * VH, abs=0.02)


def test_festivo_cuenta_para_habitualidad():
    # Dom 1, lun 2 (Todos los Santos, trasladado) y dom 8 de nov-2026 = 3 días → habitual.
    r = descanso_compensatorio(_domingos(1, 2, 8), 2026, 11, SAL)
    assert r.caso == "habitual" and r.compensatorios_generados == 3


def test_habitual_con_compensatorio_faltante_genera_alerta_y_pasivo():
    # Habitual: domingos 1, 8 y 15. El cuadro marca compensatorio el mar 3 (por el dom 1) y el
    # mié 11 (por el dom 8). Del mar 17 al sáb 21 hay turnos y el lun 16 (festivo) no está
    # marcado → el dom 15 queda sin compensatorio en la semana 16-22.
    # Pasivo = 1.750.905 / 30 = 58.363,50.
    t = _domingos(1, 8, 15)
    for d in range(17, 22):
        t.append(Turno(D(2026, 11, d, 8), D(2026, 11, d, 14)))
    r = descanso_compensatorio(t, 2026, 11, SAL,
                               descansos_otorgados=[dt.date(2026, 11, 3), dt.date(2026, 11, 11)])
    assert r.caso == "habitual"
    assert r.otorgados == {dt.date(2026, 11, 1): dt.date(2026, 11, 3),
                           dt.date(2026, 11, 8): dt.date(2026, 11, 11)}
    assert r.faltantes == [dt.date(2026, 11, 15)]
    assert r.pasivo_no_otorgados == pytest.approx(58_363.50, abs=0.01)
    assert any("sin descanso compensatorio" in a for a in r.alertas)


def test_ultimo_domingo_del_mes_no_verificable_sin_cuadro_siguiente():
    r = descanso_compensatorio(_domingos(1, 8, 15, 29), 2026, 11, SAL,
                               descansos_otorgados=[dt.date(2026, 11, 3), dt.date(2026, 11, 10),
                                                    dt.date(2026, 11, 17)])
    assert r.no_verificables == [dt.date(2026, 11, 29)] and not r.faltantes


# ---------------------------------------------------------------- tiempo parcial
def test_minimo_proporcional_y_valor_hora():
    # 20 h/sem en nov-2026: 1.750.905 × 20/42 = 833.764,29 ; valor hora = 833.764,29 / (20 × 5) = 8.337,64
    m, _ = salario_minimo_proporcional(NOV, 20)
    assert m == pytest.approx(833_764.29, abs=0.01)
    assert valor_hora(m, NOV, 20)[0] == pytest.approx(VH, abs=0.01)
    with pytest.raises(ValueError):
        costo_mensual_tiempo_parcial(NOV, 800_000, 20, 17)
    with pytest.raises(ValueError):
        salario_minimo_proporcional(NOV, 43)


@pytest.mark.parametrize("dias,semanas", [(1, 1), (7, 1), (8, 2), (14, 2), (15, 3), (21, 3), (22, 4), (29, 4)])
def test_tabla_semanas_de_cotizacion(dias, semanas):
    assert semanas_cotizacion(dias, NOV)[0] == semanas


def test_tiempo_parcial_por_semanas_resuelto_a_mano():
    # 20 h/sem, 17 días en el mes, salario 833.764,29 (< 1 SMMLV) → 3 semanas.
    #   IBC = 3 × 1.750.905 / 4 = 1.313.178,75
    #   Pensión 12 % = 157.581,45 | Caja 4 % = 52.527,15 | ARL I sobre 1 SMMLV = 9.139,72
    #   Salud = 0 (no cotiza) | Auxilio = 249.095 × 17/30 = 141.153,83
    r, res = costo_mensual_tiempo_parcial(NOV, 833_764.29, 20, 17)
    c = por_concepto(r)
    assert res.modalidad_cotizacion == "por semanas (3)" and res.ibc == pytest.approx(1_313_178.75)
    assert c["Pensión (empleador)"] == pytest.approx(157_581.45, abs=0.01)
    assert c["Caja de compensación"] == pytest.approx(52_527.15, abs=0.01)
    assert c["ARL clase I"] == pytest.approx(9_139.72, abs=0.01)
    assert c["Salud (empleador)"] == 0
    assert c["Auxilio de transporte"] == pytest.approx(141_153.83, abs=0.01)


def test_tiempo_parcial_todo_el_mes_cotiza_mensual_sobre_un_smmlv():
    r, res = costo_mensual_tiempo_parcial(NOV, 833_764.29, 20, 30)
    assert res.modalidad_cotizacion == "mensual" and res.ibc == SAL
    assert not aplica_cotizacion_por_semanas(NOV, SAL, 10)   # salario ≥ 1 SMMLV → mensual


def test_dias_laborados_cuenta_turnos_que_cruzan_medianoche_y_fin_de_mes():
    t = [Turno(D(2026, 11, 29, 22), D(2026, 11, 30, 2)), Turno(D(2026, 11, 30, 22), D(2026, 12, 1, 2))]
    assert dias_laborados_en_mes(t, 2026, 11) == 2


# ---------------------------------------------------------------- propiedades
inicio = st.datetimes(min_value=D(2025, 6, 1), max_value=D(2027, 12, 31)).map(
    lambda x: x.replace(second=0, microsecond=0))


@settings(max_examples=40, deadline=None)
@given(ini=inicio, dur=st.integers(2, 16 * 60), corte=st.integers(1, 16 * 60 - 1))
def test_propiedad_partir_un_turno_no_cambia_el_pago(ini, dur, corte):
    assume(corte < dur)
    a = Turno(ini, ini + dt.timedelta(minutes=dur))
    m = ini + dt.timedelta(minutes=corte)
    b = [Turno(ini, m), Turno(m, a.fin)]
    assert total_recargos(liquidar_turnos([a], SAL)) == pytest.approx(total_recargos(liquidar_turnos(b, SAL)), abs=0.02)


@settings(max_examples=30, deadline=None)
@given(ini=inicio, dur=st.integers(1, 14 * 60), k=st.integers(2, 5))
def test_propiedad_recargos_proporcionales_al_salario(ini, dur, k):
    t = [Turno(ini, ini + dt.timedelta(minutes=dur))]
    a = sum(l.valor for l in liquidar_turnos(t, SAL))
    b = sum(l.valor for l in liquidar_turnos(t, k * SAL))
    assert b == pytest.approx(k * a, rel=1e-9, abs=1e-6)


@settings(max_examples=30, deadline=None)
@given(ini=inicio, durs=st.lists(st.integers(30, 12 * 60), min_size=1, max_size=6))
def test_propiedad_suma_de_partes_igual_total(ini, durs):
    turnos, m = [], ini
    for d in durs:
        turnos.append(Turno(m, m + dt.timedelta(minutes=d)))
        m += dt.timedelta(minutes=d + 600)
    lineas = liquidar_turnos(turnos, SAL)
    assert sum(l.minutos for l in lineas) == sum(t.minutos for t in turnos)
    for l in lineas:
        assert sum(l.componentes.values()) == pytest.approx(l.valor, abs=1e-6)
    shuffled = turnos[:]
    random.Random(0).shuffle(shuffled)
    assert total_recargos(liquidar_turnos(shuffled, SAL)) == total_recargos(lineas)


@settings(max_examples=40, deadline=None)
@given(s1=st.floats(1.0, 9.9), s2=st.floats(1.0, 9.9))
def test_propiedad_costo_monotono_fuera_del_salto_del_auxilio(s1, s2):
    # El costo total crece con el salario dentro de cada tramo; al pasar de 2 SMMLV se pierde el
    # auxilio y el costo puede BAJAR (salto legal, ver docs/decisiones.md), por eso se compara
    # solo dentro del mismo tramo.
    assume((s1 <= 2) == (s2 <= 2))
    lo, hi = sorted((s1, s2))
    assert total(costo_mensual(NOV, lo * SAL)) <= total(costo_mensual(NOV, hi * SAL)) + 0.05


def test_salto_del_auxilio_existe():
    assert total(costo_mensual(NOV, 2 * SAL)) > total(costo_mensual(NOV, 2 * SAL + 1))


@settings(max_examples=30, deadline=None)
@given(d1=st.integers(1, 29), d2=st.integers(1, 29))
def test_propiedad_cotizacion_por_semanas_monotona_en_dias(d1, d2):
    lo, hi = sorted((d1, d2))
    a, _ = costo_mensual_tiempo_parcial(NOV, 833_764.29, 20, lo)
    b, _ = costo_mensual_tiempo_parcial(NOV, 833_764.29, 20, hi)
    assert total(a) <= total(b) + 0.05


@settings(max_examples=30, deadline=None)
@given(h=st.integers(1, 42))
def test_propiedad_minimo_proporcional_lineal_en_horas(h):
    m, _ = salario_minimo_proporcional(NOV, h)
    assert m == pytest.approx(SAL * h / 42)
