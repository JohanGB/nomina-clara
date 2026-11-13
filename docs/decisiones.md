# Registro de decisiones

Cada decisión dice qué se hizo, por qué y qué tiene que decidir el autor (si aplica).

## Correcciones de errores (con prueba que las fija)

| # | Error en v0.1 | Corrección | Prueba |
|---|---|---|---|
| C1 | Provisiones con tasas redondeadas: cesantías y prima 0,0833, vacaciones 0,0417. Con base de 2.000.000, la cesantía quedaba en 166.600 en lugar de 166.666,67 (66,67 pesos menos al mes por trabajador) | Días por año / 360 (30, 30 y 15), tomados de los arts. 249, 306 y 186 CST | `test_costo_tiempo_completo_resuelto_a_mano`, `test_provisiones_exactas_no_redondeadas` |
| C2 | La base de vacaciones excluía **todos** los recargos | El art. 192 CST excluye solo el trabajo en días de descanso obligatorio y las horas extra; el recargo nocturno ordinario entra. Nuevo parámetro `recargo_nocturno_ordinario` y `recargos_por_componente()` | `test_vacaciones_incluyen_recargo_nocturno_ordinario_y_excluyen_extras` |
| C3 | `jornada_semanal_pactada=0` se convertía en silencio en la jornada máxima legal (`0 or ...`) | Error explícito (`ValueError`); `None` sigue significando "usar la máxima legal" | `test_jornada_pactada_cero_es_error_y_no_cae_a_la_legal` |
| C4 | Turnos solapados contaban dos veces los mismos minutos | `validar_turnos()` rechaza los solapes; los turnos contiguos son válidos | `test_turnos_solapados_se_rechazan_y_contiguos_se_aceptan` |
| C5 | En una semana con cambio de jornada (15-jul), las alertas usaban el límite del lunes y la liquidación el de cada minuto: eran incoherentes | Ambas usan `limite_semanal_legal()` (ver D2) | `test_semana_que_cruza_cambio_de_jornada_usa_el_menor_limite` |
| C6 | No había alerta del tope de **2 h extra diarias** ni excepción de los sectores de seguridad y salud (Ley 2466, art. 13) | Alerta diaria y parámetro `sector_exceptuado`. El vigilante del ejemplo pertenece al sector de seguridad y ya no recibe una alerta de tope que no le aplica | `test_alerta_tope_diario_y_excepcion_sector_seguridad` |
| C7 | El IBC no tenía tope | Tope de 25 SMMLV (regla `ibc_maximo_smmlv`, por verificar) | `test_ibc_tope_25_smmlv` |
| C8 | Las alertas asignaban todo un turno que cruza medianoche al día y la semana en que empieza (un turno de domingo 23:00 a lunes 07:00 sumaba 8 h a la semana anterior) | Se reparten por día calendario real | `test_alerta_reparte_turno_que_cruza_a_la_semana_siguiente` |
| C9 | El ejemplo no corría sin instalar el paquete, y el símbolo "⚠" falla en una consola cp1252 de Windows | `sys.path` con `pathlib` y `sys.stdout.reconfigure(encoding="utf-8")` | se ejecutó con `PYTHONIOENCODING=cp1252` |
| C10 | Fuentes vagas ("Decreto dic-2025") | Se identificaron los números de decreto (1469 y 1470 de 2025, 0159 de 2026). Siguen `por_verificar` porque no se leyó su texto | — |

Ningún valor legal **verificado** resultó distinto del que tenía v0.1: 19 h desde el 25-dic-2025,
80/90/100 % cada 1 de julio, 35/25/75 %, 2 h/12 h y SMMLV 2025 coinciden con el texto oficial.

## Decisiones de diseño

- **D1. Estados.** Solo hay dos estados: `verificado` y `por_verificar`. `verificado` exige `url` y
  `consultado` (el cargador lo valida). Cuando el valor se verificó pero la fecha de inicio de la
  serie es convencional (p. ej. 1990-01-01 para el 35 % nocturno), la `nota` lo dice. La Ley 2101
  queda `por_verificar` porque lo que falta es justamente la fecha.
- **D2. Semana con cambio de jornada máxima** (lunes 13 a domingo 19 de jul-2026, 44 → 42 h): se
  usa el **menor** límite vigente en algún día de la semana, que es lo más favorable al trabajador.
  *El autor decide.* Alternativas: el límite del lunes (44) o un límite proporcional por días.
  Ejemplo: con 55,5 h esa semana, la regla elegida da 13,5 h extra; con la del lunes, 11,5 h.
- **D3. Recargos.** Los del art. 168 se excluyen entre sí (verificado: la extra nocturna paga 75 %,
  no 35 % + 75 %). El dominical/festivo se **suma** (S3, por verificar).
- **D4. Descanso compensatorio.** Se cuenta un día de descanso obligatorio "trabajado" con al menos
  1 minuto de trabajo (S9). Los festivos cuentan para la habitualidad (verificado) y, por defecto,
  también generan compensatorio (S10, regla `compensatorio_incluye_festivos`). El valor de un
  compensatorio es un día de salario (salario / 30, S11). Si el cuadro no lo otorga, se reporta un
  pasivo igual a ese valor (S12). Si no se pasa la lista de compensatorios, se *infiere* que el
  primer día laborable libre de la semana siguiente lo es (S15). Esta inferencia es generosa para
  quien trabaja a tiempo parcial y ya tiene días libres: para auditar, use `descansos_otorgados`.
- **D5. Tiempo parcial.** El salario mínimo es proporcional a las horas pactadas (art. 147). El
  valor hora usa la jornada pactada: salario / (horas × 5). El auxilio de transporte es
  proporcional a los días laborados (S16, *decisión del autor*). La cotización es por semanas
  solo si se cumplen **las dos** condiciones: menos de 30 días laborados **y** salario menor a
  1 SMMLV. Si no, se cotiza el mes completo con IBC mínimo de 1 SMMLV (S13). La base de la ARL por
  semanas es 1 SMMLV (S12b), según el texto de la guía de la UGPP, cuyo ejemplo se contradice.
- **D6. Salto del auxilio.** Al pasar de 2 SMMLV se pierden el auxilio y su efecto en las
  prestaciones, así que el costo total **baja** aunque el salario suba un peso. No es un error del
  motor: la prueba `test_salto_del_auxilio_existe` lo documenta.
- **D7. Festivos.** Vienen de la librería `holidays` (≥ 0.108), que ya incluye la Virgen de
  Chiquinquirá desde 2026, trasladada a lunes. Si la Corte la tumba, basta con poner
  `valor: false` en `festivo_virgen_chiquinquira`, sin tocar el código.
- **D8. No modelado (se documenta):** el empleador que se acoge al 100 % dominical antes de 2027;
  la jornada de 36 h en turnos sucesivos (excepción en los arts. 168, 180 y 181); el día de
  descanso pactado distinto al domingo (art. 179, par. 3); la cotización a tiempo parcial de
  microempresas y hogares (Ley 2466, art. 34, pendiente de reglamentación); el Piso de Protección
  Social (inexequible desde el 20-jun-2023, C-276 de 2021); el redondeo del IBC al peso o al
  múltiplo que exija la planilla PILA.
- **D9. Rendimiento.** `regla()` usa caché; un mes de turnos de un trabajador se liquida en
  milisegundos y la suite completa corre en unos 1–2 s (cabe sin problema en 8 GB de RAM).

## v0.3 · Liquidación del contrato (11-nov-2026)

- **D-L1. Alcance.** Contrato ordinario (indefinido, fijo, obra o labor) y siete motivos de terminación.
  Lo que la ley prevé pero el motor no calcula falla con `FueraDeAlcance` y un mensaje claro, en vez de
  dar un número equivocado: salario integral y régimen transitorio del art. 64 (10 años al 1-ene-1991).
- **D-L2. Base de cesantías (art. 253).** Si hay historial y los 3 últimos meses son iguales, se usa ese
  valor; si varió, el promedio de 12 meses. Si al historial le faltan meses, se promedia lo que hay y se
  emite una alerta (no se rellena nada).
- **D-L3. Terminación por incumplimiento del empleador.** Se calcula la misma indemnización del art. 64,
  con alerta de que procede solo si se prueba (art. 47, parágrafo, Ley 2466 de 2025).
- **D-L4. Vacaciones anticipadas.** Si se disfrutaron más días de los causados, no se descuentan: el
  art. 149 del CST exige autorización escrita para cualquier descuento. Se alerta.
- **D-L5. Moratoria (art. 65).** Se calcula aparte, por días de retardo. Desde el mes 25 corren intereses
  a una tasa que cambia cada mes: no se calculan y se avisa.
- **D-L6. Verificación sin el Gestor Normativo para dos leyes.** La Ley 1 de 1963 y la Ley 995 de 2005 se
  leyeron en el normograma de Colpensiones (entidad pública) y quedan `verificado` con esa URL. Se pide al
  autor contrastarlas con Función Pública (`verificacion_reglas.md`, punto 8).
