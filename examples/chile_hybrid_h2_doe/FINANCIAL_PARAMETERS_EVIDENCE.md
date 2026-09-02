# Evidencia y límites del escenario financiero conservador

**Fecha de corte:** 2026-09-02. **Moneda:** USD 2025 constantes para costos
tecnológicos; flujos nominales con inflación de 3% en ProFAST.

La configuración se adaptó del DOE de `FCR-CSET-Merlin/h2v_tea`, rama
`data/chile-financial-data`, commit
`83697595971ba01d1dd3b97ed9ada174917e395c`. Se tomó el extremo conservador de
sus rangos para mantener comparabilidad con el análisis previo.

## Parámetros normativos o respaldados oficialmente

- `inflation_rate: 0.03`: corresponde al centro de la meta de inflación del
  [Banco Central de Chile](https://www.bcentral.cl/es/areas/politica-monetaria),
  no a una predicción anual de IPC.
- `total_income_tax_rate: 0.27`: supone una sociedad de proyecto bajo el régimen
  general del artículo 14 A. El
  [SII registra una tasa de Primera Categoría de 27%](https://www.sii.cl/preguntas_frecuentes/declaracion_renta/001_140_4708.htm)
  desde el año comercial 2020 para ese régimen.
- `depr_type: Straight line`: evita MACRS, que es una convención tributaria de
  Estados Unidos. El período único de 15 años es una simplificación conservadora;
  las vidas tributarias reales dependen de cada clase de activo y deben revisarse
  contra la [tabla de vida útil del SII](https://www.sii.cl/valores_y_fechas/tabla_vida_util.html).
- `sales_tax_rate: 0.0`: el IVA no se trata como ingreso ni costo permanente del
  proyecto. El modelo todavía no representa el desfase de recuperación del IVA
  de construcción como capital de trabajo.

## Supuestos de escenario, no normas chilenas

La tasa de descuento de 10%, deuda/patrimonio 55/45, interés de 8,5%, plazo de
15 años, seis meses de caja y 1% combinado de impuesto territorial y seguros son
supuestos conservadores. Deben sustituirse por términos de financiamiento,
cotizaciones de seguros y avalúos específicos antes de tomar decisiones de
inversión. La tasa regulatoria de 7% usada por la CNE para transmisión no es el
WACC de este proyecto y no se aplica directamente.

Los costos tecnológicos fueron indicados para este estudio y no se presentan
como cotizaciones de mercado. No se incluyen incentivos, crédito por activo fijo,
beneficios regionales ni una eventual ley especial de hidrógeno.

## Limitaciones de ProFAST en este caso

- Un único período de depreciación agrega eólica, FV y electrólisis.
- El IVA recuperable y su costo financiero no se modelan por separado.
- No hay perfil de desembolsos, interés durante construcción, DSRA ni DSCR.
- `property_tax_and_insurance` combina conceptos que deberían desagregarse.
- No se modelan riesgos de tipo de cambio CLP/USD ni contratos de compraventa.

Por estas razones, el resultado es apropiado para ordenar alternativas dentro
del DOE bajo supuestos comunes, no para una decisión financiera definitiva.
