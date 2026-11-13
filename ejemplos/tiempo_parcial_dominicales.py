"""Ejemplo: trabajadora por horas en una cafetería, noviembre de 2026.

Pacta 20 h a la semana: jueves a domingo de 4:00 p. m. a 9:00 p. m. (5 h por turno).
Desde el 25-dic-2025 el trabajo nocturno empieza a las 7:00 p. m., así que cada turno tiene
2 h nocturnas. Trabaja todos los domingos del mes → trabajo dominical HABITUAL → además del
recargo, debe recibir un descanso compensatorio remunerado la semana siguiente.
El cuadro de turnos solo marca dos compensatorios.

Ejecutar desde la raíz del proyecto:  python ejemplos/tiempo_parcial_dominicales.py
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

from nomina_clara.compensatorio import descanso_compensatorio  # noqa: E402
from nomina_clara.costo_empleador import total  # noqa: E402
from nomina_clara.tiempo_parcial import (costo_mensual_tiempo_parcial,  # noqa: E402
                                         dias_laborados_en_mes, salario_minimo_proporcional)
from nomina_clara.turnos import (Turno, liquidar_turnos, recargos_por_componente,  # noqa: E402
                                 total_recargos)

ANIO, MES, HORAS_SEM = 2026, 11, 20
FECHA = dt.date(ANIO, MES, 1)
turnos = [Turno(dt.datetime(ANIO, MES, d, 16), dt.datetime(ANIO, MES, d, 21))
          for d in range(1, 31) if dt.date(ANIO, MES, d).weekday() in (3, 4, 5, 6)]
compensatorios_en_cuadro = [dt.date(2026, 11, 3), dt.date(2026, 11, 10)]

salario, citas = salario_minimo_proporcional(FECHA, HORAS_SEM)
print(f"SALARIO MÍNIMO PROPORCIONAL ({HORAS_SEM} h/sem): ${salario:,.2f}")
for c in citas:
    print(f"   - {c}")

lineas = liquidar_turnos(turnos, salario, jornada_semanal_pactada=HORAS_SEM, valor_hora_jornada_pactada=True)
print("\nRECARGOS DEL MES")
for l in lineas:
    print(f"  {l.concepto:38s} {l.minutos/60:5.1f} h  +{l.recargo*100:5.1f}%  ${l.valor:>10,.0f}")
rec = total_recargos(lineas)
comp = recargos_por_componente(lineas)
print(f"  TOTAL: ${rec:,.0f}")

c = descanso_compensatorio(turnos, ANIO, MES, salario, descansos_otorgados=compensatorios_en_cuadro)
print(f"\nDESCANSO COMPENSATORIO: caso {c.caso.upper()} "
      f"({len(c.dias_descanso_trabajados)} días de descanso obligatorio trabajados)")
print(f"  Compensatorios generados: {c.compensatorios_generados}; otorgados en el cuadro: {len(c.otorgados)}")
for d, o in c.otorgados.items():
    print(f"    {d} -> descansa el {o}")
print(f"  Valor de un día de salario: ${c.valor_dia:,.2f}")
print(f"  Pasivo por compensatorios no otorgados: ${c.pasivo_no_otorgados:,.2f}")
for a in c.alertas:
    print("  !", a)
for x in c.citas:
    print(f"   - {x}")

dias = dias_laborados_en_mes(turnos, ANIO, MES)
r, res = costo_mensual_tiempo_parcial(FECHA, salario, HORAS_SEM, dias, recargos_y_extras=rec,
                                      recargo_nocturno_ordinario=comp["nocturno"])
print(f"\nCOSTO MENSUAL EMPLEADOR — {dias} días laborados, cotización {res.modalidad_cotizacion}, "
      f"IBC ${res.ibc:,.2f}, valor hora ${res.valor_hora:,.2f}")
for x in r:
    print(f"  {x.concepto:32s} ${x.valor:>12,.0f}   [{x.cita}]")
print(f"  TOTAL: ${total(r):,.0f}")
print("\nNo es asesoría jurídica. Reglas 'por_verificar': ver docs/verificacion_reglas.md")
