"""Ejemplo: vigilante en turno rotativo, semana del 9 al 15 de noviembre de 2026.

Ejecutar desde la raíz del proyecto:  python ejemplos/rotativo_noviembre.py
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

from nomina_clara.costo_empleador import costo_mensual, total  # noqa: E402
from nomina_clara.turnos import (Turno, alertas_legales, liquidar_turnos,  # noqa: E402
                                 recargos_por_componente, total_recargos)

D = dt.datetime
SAL = 1_750_905
turnos = [
    Turno(D(2026, 11, 9, 6), D(2026, 11, 9, 18)),     # lun día 12 h
    Turno(D(2026, 11, 10, 6), D(2026, 11, 10, 18)),   # mar día 12 h
    Turno(D(2026, 11, 11, 18), D(2026, 11, 12, 6)),   # mié-jue noche 12 h
    Turno(D(2026, 11, 14, 18), D(2026, 11, 15, 6)),   # sáb-dom noche 12 h
    Turno(D(2026, 11, 15, 18), D(2026, 11, 16, 6)),   # dom-lun festivo noche 12 h
]
lineas = liquidar_turnos(turnos, SAL)
print("DETALLE DE RECARGOS (semana)")
for l in lineas:
    print(f"  {l.concepto:38s} {l.minutos/60:5.1f} h  +{l.recargo*100:5.1f}%  ${l.valor:>12,.0f}")
    for c in l.reglas:
        print(f"      - {c}")
rec = total_recargos(lineas)
comp = recargos_por_componente(lineas)
print(f"  TOTAL RECARGOS SEMANA: ${rec:,.0f}  (nocturno ordinario ${comp['nocturno']:,.0f}; "
      f"extra ${comp['extra']:,.0f}; dominical ${comp['dominical']:,.0f})")
print("ALERTAS (vigilancia = sector de seguridad, exceptuado de los topes de horas extra)")
for a in alertas_legales(turnos, sector_exceptuado="seguridad"):
    print("  !", a)
print()
print("COSTO MENSUAL EMPLEADOR (supone 4,33 semanas iguales)")
r = costo_mensual(dt.date(2026, 11, 1), SAL, recargos_y_extras=rec * 4.33, clase_riesgo_arl="IV",
                  recargo_nocturno_ordinario=comp["nocturno"] * 4.33)
for x in r:
    print(f"  {x.concepto:32s} ${x.valor:>12,.0f}   [{x.cita}]")
print(f"  TOTAL: ${total(r):,.0f}")
