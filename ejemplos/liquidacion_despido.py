"""Ejemplo: liquidación de un despido sin justa causa, noviembre de 2026.

Auxiliar de bodega con contrato a término indefinido desde el 1-mar-2024 y salario de
$2.000.000. Su salario varió en los últimos meses por horas extra, así que las cesantías se
liquidan con el promedio del último año (CST art. 253). Disfrutó 15 días de vacaciones.
El empleador lo despide sin justa causa el 20-nov-2026.

Ejecutar desde la raíz del proyecto:  python ejemplos/liquidacion_despido.py
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

from nomina_clara.liquidacion import Contrato, indemnizacion_moratoria, liquidar  # noqa: E402

# Devengado de dic-2025 a nov-2026 (salario + horas extra). Los meses de 2026 con extras varían.
devengado = {(2025, 12): 2_000_000.0}
devengado |= {(2026, m): 2_000_000.0 for m in range(1, 9)}
devengado |= {(2026, 9): 2_310_000.0, (2026, 10): 2_190_000.0, (2026, 11): 2_250_000.0}

contrato = Contrato(
    fecha_ingreso=dt.date(2024, 3, 1),
    fecha_retiro=dt.date(2026, 11, 20),
    tipo="indefinido",
    motivo="sin_justa_causa",
    salario_mensual=2_000_000,
    devengado_mensual=devengado,
    dias_vacaciones_disfrutados=15,
)
liq = liquidar(contrato)

print("LIQUIDACIÓN DEL CONTRATO")
print(f"Tiempo de servicio: {liq.dias_servicio} días (año de 360)\n")
print(liq.tabla())
print("\nDe dónde sale cada valor:")
for r in liq.rubros:
    print(f"- {r.concepto}: {r.cita}")
print("\nSupuestos:")
for s in liq.supuestos:
    print(f"- {s}")
print("\nAlertas:")
for a in liq.alertas:
    print(f"- {a}")

mora, avisos = indemnizacion_moratoria(contrato.salario_mensual, contrato.fecha_retiro, 30)
monto = f"{mora.valor:,.0f}".replace(",", ".")
print(f"\nSi la paga con 30 días de retraso, debe además ${monto} (CST art. 65).")
print("\nNo es asesoría jurídica. Revise las fuentes citadas antes de usarlo en un caso real.")
