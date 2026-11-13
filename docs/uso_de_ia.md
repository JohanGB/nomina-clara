# Declaración de uso de IA

- **Claude (Anthropic)** redactó el código, las pruebas y la documentación de v0.1, v0.2 y v0.3.
- En v0.2, Claude consultó en la web el texto oficial de las normas (Gestor Normativo de Función
  Pública, Corte Constitucional, UGPP y DIAN) el 2026-11-11. Marcó como `verificado` solo las
  reglas cuyo texto leyó y que coinciden, y registró en el YAML la URL, la fecha de consulta y una
  cita corta. Los sitios que no pudo abrir (SUIN-Juriscol, Secretaría del Senado, Ministerio del
  Trabajo y algunos PDF escaneados) se listan en `docs/verificacion_reglas.md`. Esas reglas quedan
  `por_verificar`.
- La lectura se hizo con una herramienta automática que resume páginas largas. Las citas textuales
  son fragmentos cortos y algunas notas son paráfrasis (se indica cuándo). **El autor debe abrir
  cada enlace antes de usar el motor en un caso real.**
- **El autor** definió el alcance (empleador primero, escenarios complejos primero), decide los
  supuestos marcados en `docs/decisiones.md` y responde por el contenido.
- En v0.3 (liquidación) leyó los arts. 64, 65, 186–192, 249, 253 y 306 del CST, el Decreto 116 de 1976,
  la Ley 1 de 1963, la Ley 995 de 2005 y el texto completo de la Ley 2466 de 2025 para confirmar qué no cambió.
- Verificación técnica: 72 pruebas automáticas (casos resueltos a mano con el cálculo en el
  comentario, regresiones de cada error corregido y pruebas por propiedades con `hypothesis`).
- Nada de esto es asesoría jurídica.
