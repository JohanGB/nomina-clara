# Supuestos y pendientes (v0.2)

Estado al 2026-11-11. El detalle de cada verificación está en [verificacion_reglas.md](verificacion_reglas.md)
y las decisiones en [decisiones.md](decisiones.md).

## Supuestos de v0.1

| # | Supuesto | Estado v0.2 | Comentario |
|---|---|---|---|
| S1 | Valor hora = salario / (jornada semanal × 5); con 42 h → divisor 210 | por verificar | Ninguna ley fija un divisor; el factor está en el YAML (`factor_divisor_hora_mensual`) |
| S2 | Horas extra = minutos que superan la jornada semanal, en orden cronológico (semana lunes–domingo) | por verificar | |
| S3 | Recargo dominical/festivo se suma al nocturno o a la extra | parcialmente verificado | Los recargos del art. 168 se excluyen entre sí (verificado); la suma con el dominical sigue como supuesto |
| S4 | El recargo dominical cambia el 1 de julio | **verificado** | Ley 2466, art. 14 |
| S5 | SMMLV 2026 = $1.750.905; auxilio = $249.095 | por verificar | Decretos 1469 y 1470 de 2025 y 0159 de 2026 no leídos |
| S6 | Festivo de la Virgen de Chiquinquirá incluido | por verificar | Se puede apagar en el YAML |
| S7 | Exoneración de salud, ICBF y SENA para devengados < 10 SMMLV | por verificar | Concepto DIAN leído; el artículo no |
| S8 | Tope de horas extra | **verificado** | 2 h diarias y 12 h semanales; seguridad y salud exceptuados |

## Supuestos nuevos (v0.2)

| # | Supuesto | Dónde |
|---|---|---|
| S9 | Un día de descanso obligatorio cuenta como trabajado con 1 minuto de trabajo | `compensatorio.py` |
| S10 | Los festivos que no caen en domingo también generan compensatorio en el caso habitual | YAML `compensatorio_incluye_festivos` |
| S11 | Un compensatorio vale un día de salario = salario mensual / 30 | `compensatorio.py` |
| S12 | El compensatorio no otorgado se cuenta como pasivo de un día de salario | `compensatorio.py` |
| S12b | En la cotización por semanas, la ARL se liquida sobre 1 SMMLV | YAML `cotizacion_por_semanas.arl_base` |
| S13 | Tiempo parcial con 30 días laborados o salario ≥ 1 SMMLV: IBC mensual mínimo de 1 SMMLV | `tiempo_parcial.py` |
| S14 | En la cotización por semanas, ICBF y SENA (si no hay exoneración) se liquidan sobre la nómina real | `tiempo_parcial.py` |
| S15 | Sin lista de compensatorios, se infiere que el primer día laborable libre de la semana siguiente lo es | `compensatorio.py` |
| S16 | Auxilio de transporte a tiempo parcial proporcional a los días laborados | YAML `auxilio_transporte_tiempo_parcial` |
| S17 | Semana que cruza un cambio de jornada máxima: se usa el menor límite | `turnos.py` (D2) |
| S18 | El inicio nocturno a las 7 p. m. rige el 25-dic-2025 (sanción + 6 meses), no el 26 | YAML `inicio_nocturno` |

## Supuestos nuevos (v0.3, liquidación)
| # | Supuesto | Dónde |
|---|---|---|
| S19 | Si el salario es variable, la prima se liquida con el promedio de lo devengado en el semestre (el art. 306 dice "30 días de salario"; la ley no define la base variable) | `liquidacion.base_prima` |
| S20 | Los días se cuentan con meses de 30 y años de 360 (último día del mes = día 30). Es la práctica general; ninguna norma la fija | YAML `convencion_dias_comerciales` |
| S21 | La indemnización del art. 64 se calcula con el último salario ordinario, sin promediar horas extra ocasionales | `liquidacion._indemnizacion` |
| S22 | Las cesantías de años anteriores ya se consignaron al fondo, y la prima del semestre en curso no se ha pagado (se pueden cambiar con `cesantias_pendientes_desde` y `prima_pendiente_desde`) | `liquidacion.liquidar` |
| S23 | El salario del último periodo, los recargos pendientes y los descuentos se liquidan en la nómina, no aquí | alcance |

## Pendientes (orden previsto)
1. Verificar a mano las reglas `por_verificar` (lista en verificacion_reglas.md).
2. Trabajo doméstico, aprendices (contrato laboral desde la Ley 2466, art. 21), salario integral.
3. Jornada de 36 h en turnos sucesivos, día de descanso distinto al domingo (art. 179, par. 3) y empleador que se acoge al 100 % dominical.
4. Optimizador de turnos: cumplir la ley al menor costo (programación entera).
5. Lectura de cuadros de turnos desde Excel o foto.
6. Vista simple del trabajador ("¿me pagaron bien?").
