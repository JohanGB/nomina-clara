# Verificación de reglas contra el texto oficial

Fechas de consulta: **2026-11-11** (primera verificación) y **2026-11-16** (revisión, ver abajo). Método: lectura del texto oficial en la web (Gestor Normativo de
Función Pública, Corte Constitucional, UGPP) con una herramienta de consulta automática. Una regla
queda `verificado` solo si el valor y la vigencia se leyeron en una fuente primaria de la lista
aceptada y coinciden. Si no se pudo abrir el texto oficial, queda `por_verificar` con el enlace exacto.

## Revisión del 16-nov-2026

Se releyeron las reglas que habían quedado `por_verificar` el 11-nov. Esto es lo que cambió en
`src/nomina_clara/reglas/parametros.yaml`; **ningún valor del motor se modificó**.

| | 11-nov | 16-nov |
|---|---|---|
| Entradas `verificado` (de 47) | 27 | **39** |
| Entradas `por_verificar` | 20 | **8** |
| Reglas con todas sus entradas verificadas (de 36) | 21 | **28** |

**Pasaron a `verificado` (12 entradas):** salario mínimo de 2026; auxilio de transporte 2025 y 2026 y su tope en SMMLV;
jornada máxima semanal (las 5 entradas: 1990 y los escalones de 2023 a 2026, con la fecha de publicación de la Ley 2101);
tasas de aportes del empleador; exoneración del art. 114-1 del ET; y el tope del IBC (25 SMMLV).

**Siguen `por_verificar` (8 entradas):**

| Regla | Motivo |
|---|---|
| `inicio_nocturno` (21 h, 2017-07-13) | **Discrepante**: el valor coincide, pero la Ley 1846 es del 18-jul-2017 |
| `recargo_dominical_festivo` (75 %, 2003-01-01) | **Discrepante**: el valor coincide, pero la Ley 789 rige desde el 27-dic-2002 (contratos anteriores: 1-abr-2003) |
| `tope_horas_extra` (1990-12-28) | **Discrepante**: los valores coinciden, pero la Ley 50 se publicó el 1-ene-1991 |
| `festivo_virgen_chiquinquira` (2026-01-01) | **Discrepante**: el valor coincide, pero la Ley 2578 es del 1-jun-2026 (rige desde el 2-jun-2026); sin efecto en el cálculo. Además hay una demanda cuyo estado no se pudo confirmar |
| `factor_divisor_hora_mensual` | Convención de liquidación sin norma que la fije; el concepto del Ministerio del Trabajo no menciona el divisor |
| `compensatorio_incluye_festivos` | Los arts. 179 a 183 del CST no resuelven la duda; decisión del autor |
| `auxilio_transporte_tiempo_parcial` | Sin fuente oficial; decisión del autor |
| `convencion_dias_comerciales` | Convención (supuesto S20), sin norma |

Las **4 discrepancias son solo de fecha de vigencia**. Se dejaron `por_verificar`, con `revision: discrepante` y la
fecha que dice la fuente en `fuente_dice`, hasta que el autor confirme si se corrige el YAML.

**Fuentes de esta revisión.** Se leyeron en compilaciones de entidades públicas, no en el Gestor Normativo de Función
Pública: el normograma de Colpensiones (Decretos 1469 de 2025, 1573 de 2024 y 1470 de 2025; Ley 50 de 1990) y las
compilaciones del Senado (Leyes 2101, 1846, 789, 2578, 100 y el Estatuto Tributario). Cada URL y cita textual está en el YAML.
El auxilio de 2026 tuvo además una segunda lectura coincidente en SISJUR (Alcaldía de Bogotá). **Conviene que el autor
decida si acepta estas compilaciones como fuente primaria**; la tabla de abajo conserva las fuentes del 11-nov y marca
con «(16-nov)» lo que cambió.

**Qué NO se pudo abrir el 11-nov** (para que se sepa por qué hubo reglas pendientes; varias se leyeron después en otra fuente):

| Sitio | Qué pasó |
|---|---|
| suin-juriscol.gov.co | Bloqueado: el proxy de la sesión rechaza la conexión y el `robots.txt` del sitio prohíbe la lectura automática |
| secretariasenado.gov.co | Redirección en bucle https → http (no se pudo leer) |
| mintrabajo.gov.co (conceptos y comunicados) | Su `robots.txt` prohíbe la lectura automática |
| funcionpublica.gov.co, `norma.php` | Bloqueado por `robots.txt`; **sí** se pudo leer `norma_pdf.php`, la versión imprimible del mismo texto |
| Decreto 2616 de 2013 en Función Pública | Bloqueado (`robots.txt`); una segunda URL devolvió otra norma |
| dapre.presidencia.gov.co, Decreto 1469 de 2025 | El PDF llegó vacío (es un escaneo sin texto) |

Fuentes leídas (URL exactas):

- [L2466] Ley 2466 de 2025: https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=260676
- [L2101] Ley 2101 de 2021: https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=166506
- [L50] Ley 50 de 1990, con notas de vigencia: https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=281
- [CST] Código Sustantivo del Trabajo (Decreto 2663 de 1950): https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=199983
- [D1572] Decreto 1572 de 2024: https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=257156
- [C276] Sentencia C-276 de 2021: https://www.corteconstitucional.gov.co/relatoria/2021/c-276-21.htm
- [UGPP] UGPP, *ABC Trabajadores a Tiempo Parcial* (2026): https://www.ugpp.gov.co/wp-content/uploads/2026/02/ABC-Trabajadores-a-Tiempo-Parcial.pdf
- [DIAN] Concepto DIAN 7196 de 2025 (antecedente del art. 114-1 ET): https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_7196_2025.htm
- [D116] Decreto 116 de 1976 (reglamenta la Ley 52 de 1975): https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=3285
- [L1-63] Ley 1 de 1963, normograma de Colpensiones: https://normativa.colpensiones.gov.co/compilacion/docs/ley_0001_1963.htm
- [L995] Ley 995 de 2005, normograma de Colpensiones: https://normativa.colpensiones.gov.co/colpens/compilacion/docs/ley_0995_2005.htm
- [L2466-RJ] Ley 2466 de 2025, texto completo en la Rama Judicial (para confirmar qué artículos del CST NO modifica): https://sidn.ramajudicial.gov.co/SIDN//NORMATIVA/TEXTOS_COMPLETOS/7_LEYES/LEYES%202025/Ley%202466%20de%202025.pdf

## Tabla por regla

| Regla (YAML) | Valor | Vigencia | Norma y artículo | URL | Consulta | Resultado | Nota |
|---|---|---|---|---|---|---|---|
| `salario_minimo` | 1.423.500 | 2025-01-01 | Decreto 1572 de 2024, art. 1 | [D1572] | 2026-11-11 | **verificado** | "Fijar a partir del primero (1) de enero de 2025 ... ($1.423.500)" |
| `salario_minimo` | 1.750.905 | 2026-01-01 | Decreto 1469 de 2025 (suspendido) y Decreto 0159 de 2026 (transitorio) | — | 2026-11-16 | **verificado** (16-nov) | Texto no leído. La guía de la UGPP de 2026 usa 437.726 por semana (= 1.750.905 / 4), lo que es coherente con el valor pero no es el decreto Texto leído el 16-nov en el normograma de Colpensiones: Decreto 1469 de 2025, art. 1 ($1.750.905), vigencia art. 2; suspendido provisionalmente por el Consejo de Estado (12-feb-2026) y reemplazado por el Decreto 0159 de 2026 con el mismo valor; la nota de vigencia dice que la suspensión se levantó el 9-jul-2026. No se leyó la providencia. |
| `auxilio_transporte` | 200.000 | 2025-01-01 | Decreto 1573 de 2024 | — | 2026-11-16 | **verificado** (16-nov) | No leído Decreto 1573 de 2024, art. 1; derogado por el Decreto 1470 de 2025. |
| `auxilio_transporte` | 249.095 | 2026-01-01 | Decreto 1470 de 2025 | — | 2026-11-16 | **verificado** (16-nov) | No leído; falta confirmar si la suspensión del 1469 lo afectó Decreto 1470 de 2025, art. 1. La suspensión del Consejo de Estado recayó sobre el 1469, no sobre el 1470. |
| `auxilio_transporte_tope_smmlv` | 2 | — | decretos anuales | — | 2026-11-16 | **verificado** (16-nov) | Decretos 1573 de 2024 y 1470 de 2025. La fecha 1990-01-01 es convencional. |
| `jornada_maxima_semanal` | 47 / 46 / 44 / 42 | 15-jul 2023/24/25/26 | Ley 2101 de 2021, art. 3 | [L2101] | 2026-11-16 | **verificado** (16-nov) | **Valores y escalonamiento coinciden.** La ley rige "a partir de la fecha de su publicación" (art. 8) y fue expedida el 15-jul-2021, pero el texto no muestra la fecha del Diario Oficial Fecha confirmada: Ley 2101 publicada en el Diario Oficial 51.736 de 15-jul-2021 y rige desde su publicación (art. 8). Los valores históricos (Ley 50 de 1990, art. 20) también se leyeron. |
| `jornada_maxima_diaria` | 8 h; flexible 4–9 h | 2025-06-25 | Ley 2466 de 2025, art. 11 (art. 161 CST) | [L2466] | 2026-11-11 | **verificado** | Fecha = sanción; la ley rige desde su promulgación (art. 70) |
| `factor_divisor_hora_mensual` | 5 (42 h → 210) | — | Ninguna norma lo fija | [L2101], [L2466] | 2026-11-16 | por verificar | Se confirmó que ni la Ley 2101 ni la 2466 fijan un divisor. El concepto del Ministerio del Trabajo no se pudo abrir El concepto del Ministerio del Trabajo se leyó el 16-nov: trata la reducción de jornada y turnos y no menciona divisor. |
| `inicio_nocturno` | 21 h | 2017-07-13 | Ley 1846 de 2017 | — | 2026-11-16 | por verificar: **discrepante** (16-nov) | No leído (solo afecta fechas anteriores al 25-dic-2025) El valor (21 h) coincide, pero la Ley 1846 es del 18-jul-2017 y el YAML dice 2017-07-13. YAML sin cambiar. |
| `inicio_nocturno` | 19 h | 2025-12-25 | Ley 2466 de 2025, art. 10, par. 2 (art. 160 CST) | [L2466] | 2026-11-11 | **verificado** | "entrará en vigencia seis (6) meses después de la sanción"; sanción 25-jun-2025 → 25-dic-2025 |
| `recargo_nocturno` | 35 % | — | CST art. 168 num. 1 (Ley 50, art. 24) | [L50] | 2026-11-11 | **verificado** | La Ley 2466 no cambia el porcentaje |
| `extra_diurna` | 25 % | — | CST art. 168 num. 2 | [L50] | 2026-11-11 | **verificado** | |
| `extra_nocturna` | 75 % | — | CST art. 168 num. 3 | [L50] | 2026-11-11 | **verificado** | |
| `recargos_168_excluyentes` | sí | — | CST art. 168 num. 4 | [L50] | 2026-11-11 | **verificado** | "Cada uno de los recargos antedichos se produce de manera exclusiva, es decir, sin acumularlo con alguno otro." La extra nocturna **reemplaza** el 35 % nocturno |
| `recargo_dominical_festivo` | 75 % | 2003 | Ley 789 de 2002, art. 26 | — | 2026-11-16 | por verificar: **discrepante** (16-nov) | Solo afecta fechas anteriores al 1-jul-2025 El valor (75 %) coincide, pero la Ley 789 rige desde el 27-dic-2002 (contratos anteriores: 1-abr-2003); ninguna es 2003-01-01. YAML sin cambiar. |
| `recargo_dominical_festivo` | 80 % / 90 % / 100 % | 1-jul 2025 / 2026 / 2027 | Ley 2466 de 2025, art. 14, par. transitorio | [L2466] | 2026-11-11 | **verificado** | Fechas exactas: "A partir del primero de julio de 2025 / 2026 / 2027". El empleador puede acogerse al 100 % desde la entrada en vigencia |
| `dominical_habitual_desde_dias` | 3 | 2025-06-25 | Ley 2466 de 2025, art. 14, par. 1 | [L2466] | 2026-11-11 | **verificado** | Ocasional: "hasta dos (2) días de descanso obligatorio, durante el mes calendario"; habitual: 3 o más. Cuenta **días de descanso obligatorio** (domingos y festivos), no solo domingos |
| `derechos_trabajo_dominical` | ocasional: elegir; habitual: recargo y compensatorio | — | CST arts. 180 y 181 (Ley 50, arts. 30 y 31) | [L50] | 2026-11-11 | **verificado** | La Ley 2466 no modificó los arts. 180–185 (revisado en su texto completo) |
| `compensatorio_plazo` | semana siguiente | — | CST art. 183 | [CST] | 2026-11-11 | **verificado** (paráfrasis) | Otro día laborable de la semana siguiente, o del mediodía o la 1 p. m. del domingo al mediodía o la 1 p. m. del lunes |
| `compensatorio_incluye_festivos` | sí | — | lectura de los arts. 180–181 | — | 2026-11-16 | por verificar | Supuesto S10: decisión del autor Leídos los arts. 179 a 183 del CST el 16-nov: no resuelven la duda; decisión del autor. |
| `tope_horas_extra` | 2 diarias / 12 semanales; seguridad y salud exceptuados | 2025-06-25 | Ley 50, art. 22, mod. Ley 2466, art. 13 | [L2466], [L50] | 2026-11-16 | **verificado** (vigencia 2025); la entrada original de 1990 es **discrepante** (16-nov) | Mismo tope que antes; la Ley 2466 agrega las excepciones La entrada de 1990-12-28 queda `por_verificar`: los valores (2 h y 12 h) coinciden, pero la Ley 50 se publicó el 1-ene-1991 (art. 117). YAML sin cambiar. |
| `festivo_virgen_chiquinquira` | incluido | 2026 | Ley 2578 de 2026 (según prensa) | — | 2026-11-16 | por verificar: **discrepante** (16-nov) | No se pudo abrir el texto (Senado). Hay demanda ante la Corte Se leyó la Ley 2578 de 2026: el valor coincide (festivo; en 2026 se trasladó al lunes 13-jul), pero la ley es del 1-jun-2026 (rige desde el 2-jun-2026) y el YAML dice 2026-01-01; sin efecto en el cálculo. Hay una demanda cuyo estado no se pudo confirmar. YAML sin cambiar. |
| `aportes_empleador` | salud 8,5 %, pensión 12 %, caja 4 %, ICBF 3 %, SENA 2 %, ARL I–V | — | Ley 100, Ley 1122, Ley 21 de 1982, Ley 89 de 1988, Decreto 1295 de 1994 | — | 2026-11-16 | **verificado** (16-nov) | Ningún texto legal leído. La guía de la UGPP coincide en pensión, caja y ARL (no es el texto legal) Seis tasas leídas en la Ley 100, la Ley 1122, el Decreto 4982 de 2007, la Ley 21 de 1982, la Ley 89 de 1988 y el Decreto 1772 de 1994; la fuente de las tarifas de ARL se corrigió (no el valor). |
| `exoneracion_art_114_1` | < 10 SMMLV; salud, ICBF, SENA | — | ET art. 114-1 | [DIAN] | 2026-11-16 | **verificado** (16-nov) | Se leyó el concepto DIAN, no el artículo Se leyó el art. 114-1 del ET (Ley 1819 de 2016, art. 65), no solo el concepto DIAN. |
| `ibc_maximo_smmlv` | 25 | — | Ley 100, art. 18 | — | 2026-11-16 | **verificado** (16-nov) | Regla nueva Ley 100, art. 18, modificado por la Ley 797 de 2003, art. 5. |
| `prestaciones_dias_por_anio` | cesantías 30, prima 30, vacaciones 15 (base 360) | — | CST arts. 249, 306, 186 | [CST] | 2026-11-11 | **verificado y corregido** | Reemplaza 0,0833 / 0,0417 redondeados |
| `vacaciones_base_excluye` | dominicales y horas extra | — | CST art. 192 | [CST] | 2026-11-11 | **verificado y corregido** | El recargo nocturno ordinario sí entra en la base |
| `intereses_cesantias` | 12 % | — | Ley 52 de 1975; Decreto 116 de 1976, arts. 1, 2 y 5 | [D116] | 2026-11-11 | **verificado** (v0.3) | "12% anual sobre los saldos"; proporcional al tiempo en el retiro; si no se pagan, suma adicional igual |
| `auxilio_transporte_en_base_prestaciones` | cesantías y prima sí | — | Ley 1 de 1963, art. 7 | [L1-63] | 2026-11-11 | **verificado** (v0.3) | "Considérase incorporado al salario, para todos los efectos de liquidación de prestaciones sociales, el auxilio de transporte". Vacaciones no: no son prestación social (interpretación) |
| `salario_minimo_proporcional` | por horas trabajadas | — | CST art. 147 | [CST] | 2026-11-11 | **verificado** | "en proporción al número de horas efectivamente trabajadas" |
| `dominical_proporcional_jornada_incompleta` | sí | — | CST art. 173 num. 5 (Ley 50, art. 26) | [L50] | 2026-11-11 | **verificado** | |
| `auxilio_transporte_tiempo_parcial` | proporcional a días | — | — | — | 2026-11-16 | por verificar | Decisión del autor No se encontró fuente oficial: los decretos fijan el auxilio mensual sin distinguir por jornada ni por días. |
| `cotizacion_por_semanas` | 1–7 → 1; 8–14 → 2; 15–21 → 3; 22–29 → 4; semana = 1/4 SMMLV; pensión, ARL, caja; salud no | — | Decreto 2616 de 2013 / Decreto 1072 de 2015, según la UGPP | [UGPP] | 2026-11-11 | **verificado (contra la guía de la UGPP, no contra el decreto)** | La guía se contradice en la base de la ARL y trae un error en la fila de 4 semanas |
| `piso_proteccion_social` | inexequible | 2023-06-20 | C-276 de 2021, resuelve 2.º y 3.º | [C276] | 2026-11-11 | **verificado** | "surtirá efectos a partir del 20 de junio de 2023". No se modela |

### Reglas nuevas de v0.3: liquidación del contrato

Se confirmó en el texto completo de la Ley 2466 de 2025 [L2466-RJ] que **no modifica** los artículos
64, 65, 186, 189, 249, 253 ni 306 del CST, ni la tasa de la Ley 52 de 1975 (su art. 64 solo permite
pactar el pago mensual de los intereses y aportes anticipados al fondo).

| Regla (YAML) | Valor | Vigencia | Norma y artículo | URL | Consulta | Resultado | Nota |
|---|---|---|---|---|---|---|---|
| `cesantias_base_salario` | último salario si no varió en 3 meses; si no, promedio de 12 | 1965 | CST art. 253 (Decreto 2351 de 1965, art. 17) | [CST] | 2026-11-11 | **verificado** | "el último salario mensual devengado por el trabajador, siempre que no haya tenido variación" |
| `prima_servicios` | 30 días por año; mitades al 30-jun y 20-dic | 2016-07-07 | CST art. 306 (Ley 1788 de 2016) | [CST] | 2026-11-11 | **verificado** | "por todo el semestre trabajado o proporcionalmente al tiempo trabajado" |
| `vacaciones_compensacion_proporcional` | proporcional a cualquier tiempo | 2005-11-10 | Ley 995 de 2005, arts. 1 y 2 | [L995] | 2026-11-11 | **verificado** | Deroga el num. 2 del art. 189 (ya no se exigen 3 meses) |
| `indemnizacion_despido` | < 10 SMMLV: 30 + 20/año; ≥ 10: 20 + 15/año; fijo: tiempo faltante; obra: mín. 15 días | 2002-12-27 | CST art. 64 (Ley 789 de 2002, art. 28) | [CST] | 2026-11-11 | **verificado** | Proporcional por fracción. Régimen transitorio (10 años al 1-ene-1991) no se calcula |
| `indemnizacion_moratoria` | 1 día de salario por día de retardo; tope 24 meses si gana > 1 SMMLV | 2002-12-27 | CST art. 65 (Ley 789 de 2002, art. 29) | [CST] | 2026-11-11 | **verificado** | Intereses desde el mes 25: no se calculan |
| `convencion_dias_comerciales` | meses de 30, años de 360 | — | Convención (ninguna norma la fija) | — | — | por verificar | Supuesto S20 |

### Supuestos S1–S8 de v0.1

| # | Resultado | Detalle |
|---|---|---|
| S1 divisor × 5 | por verificar | Ninguna ley fija un divisor (confirmado en las leyes 2101 y 2466); el concepto del Ministerio del Trabajo se leyó el 16-nov y no menciona divisor |
| S2 extras por semana | por verificar | La Ley 2101, art. 2, permite distribuir la jornada en 5 o 6 días "de común acuerdo" (leído). No se leyó el art. 159 CST |
| S3 recargos acumulativos | parcialmente verificado | Los del art. 168 se **excluyen** entre sí (verificado). Que el dominical se **sume** a ellos es un supuesto |
| S4 cambio el 1 de julio | **verificado** | Ley 2466, art. 14 |
| S5 SMMLV y auxilio 2026 | **verificado** (16-nov) | Decretos 1469 y 1470 de 2025, leídos en el normograma de Colpensiones |
| S6 Virgen de Chiquinquirá | por verificar: **discrepante** (16-nov) | Ley 2578 de 2026 leída: el valor coincide; la fecha del YAML no. Demanda sin confirmar |
| S7 exoneración art. 114-1 | **verificado** (16-nov) | Se leyó el artículo del ET, además del concepto DIAN |
| S8 tope 12 h semanales | **verificado** | Se agregaron el tope diario de 2 h y las excepciones de seguridad y salud |

## Lo que el autor debe revisar a mano

Actualizado el 16-nov-2026. Lo resuelto en la revisión (salario mínimo 2026 y decretos 1469/0159, auxilio de transporte
2026, fecha de la Ley 2101, concepto del Ministerio del Trabajo sobre el divisor, Ley 2578 y tasas de aportes con el
art. 114-1) salió de esta lista.

1. **Las 4 fechas discrepantes** (`inicio_nocturno`, `recargo_dominical_festivo`, `tope_horas_extra` y
   `festivo_virgen_chiquinquira`): confirmar si se corrige el YAML con la fecha de la fuente. Hasta entonces siguen `por_verificar`.
2. **Compilaciones como fuente primaria:** decidir si el normograma de Colpensiones y las compilaciones del Senado
   valen como fuente de `verificado`, o si se exige el Gestor Normativo de Función Pública.
3. **Festivo de la Virgen de Chiquinquirá:** estado de la demanda contra el art. 6 de la Ley 2578 de 2026 (la Corte no devolvió resultados
   el 16-nov). Si se declara inexequible, poner `valor: false`.
4. **Providencia del Consejo de Estado** (exp. 11001-03-25-000-2026-00004-00) sobre el Decreto 1469: no se leyó; la nota de
   vigencia del normograma dice que la suspensión se levantó el 9-jul-2026.
5. **Decreto 2616 de 2013, texto oficial:** tabla de semanas y base de la ARL (¿1 SMMLV o IBC por días?):
   https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65326 y su compilación en el Decreto 1072 de 2015:
   https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=72173
6. **Inicio de la jornada nocturna a las 7 p. m.: ¿25 o 26 de diciembre de 2025?** El texto dice "seis (6) meses después de la sanción" (sanción: 25-jun-2025).
7. **Ley 2381 de 2024 (reforma pensional):** la Ley 2466, art. 33, remite a sus arts. 27 y 28 para la cotización a tiempo parcial del servicio doméstico. No se revisó su estado.
8. **Ley 1 de 1963 y Ley 995 de 2005 en una fuente de la lista principal** (se leyeron en el normograma de
   Colpensiones, entidad pública, porque el Gestor Normativo y el Senado no abrieron):
   https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=88002 (Ley 1 de 1963)
9. **Decisiones de diseño sin fuente** (`compensatorio_incluye_festivos`, `auxilio_transporte_tiempo_parcial` y la convención de 360 días): son del autor, no de una norma.
