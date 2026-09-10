# Resultados de los casos híbridos de hidrógeno verde en Chile — 2023

## Propósito y trazabilidad

Este reporte resume los resultados existentes de los dos casos de ejemplo en
`examples/chile_hybrid_h2_doe/outputs/`. Corresponden a un DOE de 72 diseños
por sitio, con recursos horarios UTC de 2023, para un total de 144 ejecuciones.
Los recursos son Sup3rWind South America v1.0.0 para viento y NSRDB GOES Full
Disc PSM v4 para solar; el manifiesto, URLs y checksums están en
[`resource_manifest.yaml`](../examples/chile_hybrid_h2_doe/resource_manifest.yaml).

El criterio de selección es el menor LCOH entre diseños que produzcan al menos
20.000.000 kg H₂/año (20 kt/año). Los resultados fueron leídos de
`doe_results.csv` el 10 de septiembre de 2026. No son resultados de una
optimización continua: sólo comparan las combinaciones discretas del DOE.

## Alcance del modelo

Cada caso combina FV, eólica y electrólisis PEM aisladas de red. El escenario
financiero conservador usa vida de proyecto de 30 años, USD 2025, tasa de
descuento de 10%, deuda/patrimonio 55/45, interés de 8,5%, impuesto de 27%,
inflación de 3% y depreciación lineal a 15 años. Los costos de referencia son
1.900 USD/kW y 55 USD/kW-año para eólica, 1.100 USD/kWac y 22 USD/kW-año
para FV, y 1.200 USD/kW y 20 USD/kW-año para PEM.

No incorpora batería, red, almacenamiento de H₂, agua o desalación, compresión,
transporte, venta de oxígeno, incentivos ni créditos de carbono. Por ello, el
LCOH reportado representa el costo a la salida del bloque de producción
modelado, y no un costo de hidrógeno entregado a cliente.

## Resultados principales

| Indicador | Antofagasta (`site_01_antofagasta`) | Magallanes (`site_02_magallanes`) |
|---|---:|---:|
| Diseños evaluados | 72 | 72 |
| Diseños factibles (≥20 kt/año) | 6 (8,3%) | 17 (23,6%) |
| Menor LCOH sin aplicar la meta | 7,18 USD/kg | 5,61 USD/kg* |
| Menor LCOH factible | **7,18 USD/kg** | **6,08 USD/kg** |
| Producción del diseño seleccionado | 20,41 kt/año | 20,58 kt/año |
| Factor de planta PEM seleccionado | 41,4% | 63,3% |
| LCOE del diseño seleccionado | 61,08 USD/MWh | 67,97 USD/MWh |
| Producción máxima del DOE | 22,80 kt/año | 27,19 kt/año |

\* El mínimo no restringido de Magallanes produce 18,05 kt/año y no cumple la
meta. Exigir 20 kt/año aumenta el LCOH mínimo en 0,47 USD/kg (8,5%) dentro del
espacio discreto evaluado.

### Diseño seleccionado por sitio

| Sitio | FV | Eólica | PEM | Producción | Factor PEM | LCOE | LCOH |
|---|---:|---:|---:|---:|---:|---:|---:|
| Antofagasta | 400 MWdc | 10 turbinas / 60 MW | 300 MW | 20,41 kt/año | 41,4% | 61,08 USD/MWh | **7,18 USD/kg** |
| Magallanes | 200 MWdc | 30 turbinas / 180 MW | 200 MW | 20,58 kt/año | 63,3% | 67,97 USD/MWh | **6,08 USD/kg** |

## Interpretación

- **Magallanes obtiene el LCOH factible más bajo**, 1,10 USD/kg (15,3%) por
  debajo de Antofagasta, aunque su LCOE seleccionado es 6,89 USD/MWh mayor.
  En este DOE, el mayor factor de planta del PEM en Magallanes (63,3% frente a
  41,4%) compensa ese mayor costo eléctrico mediante una mejor utilización del
  activo de electrólisis.
- **La meta anual es restrictiva en Antofagasta**: sólo 6 de 72 diseños cumplen
  el umbral, y todos usan 400 MWdc FV. En Magallanes, 17 configuraciones son
  factibles; las mejores combinan 30 turbinas con 100–200 MWdc FV.
- **No debe inferirse una capacidad óptima fuera del DOE.** Por ejemplo, el
  mínimo de Magallanes sin restricción incumple la meta; una búsqueda con más
  tamaños intermedios de FV, turbinas y PEM podría reducir el costo de la
  primera alternativa factible.

## Comparación con estudios de plantas híbridas *off-grid*

La comparación siguiente es un **benchmark de orden de magnitud**, no una
validación numérica. Los estudios usan años de costo, escalas, tecnologías,
tasas de descuento y límites de sistema distintos. En particular, el presente
DOE no incluye almacenamiento de H₂, batería, desalación, compresión ni
transporte, mientras que algunos referentes sí los incluyen.

| Referencia | Caso y resultado publicado | Lectura frente al DOE actual |
|---|---|---|
| [León et al. (2023), *Energies*](https://doi.org/10.3390/en16145327) | Estudio autónomo en Antofagasta y Patagonia; planta base de 1 kt/año, electrólisis alcalina y desalación. Reporta costo de producción de 4,80 USD/kg para el caso eólico patagónico; el precio mínimo para 4% de retorno fue 7,84 USD/kg. | El LCOH factible de Magallanes (6,08 USD/kg) está entre esos indicadores, pero no es comparación directa: cambia PEM/alcalina, escala, agua/desalación y definición de costo. |
| [USM, tesis de pregrado (2023)](https://repositorio.usm.cl/handle/123456789/75020) | Casos chilenos norte, centro-sur y sur con FV, eólica, batería, PEM y almacenamiento de H₂. Reporta LCOH de 10,0–16,8 USD/kg y LCOE de 215–383 USD/MWh. | Los valores del DOE (6,08–7,18 USD/kg; 61–68 USD/MWh en diseños seleccionados) son menores, coherente con su mayor escala y con excluir batería y almacenamiento de H₂. No prueba exactitud por sí solo. |
| [IRENA (2022)](https://www.irena.org/Publications/2022/May/Global-hydrogen-trade-to-meet-the-1.5C-climate-goal-Part-III) | Proyección optimista a 2050: para los mejores recursos de Chile, 0,73 USD/kg con FV y 0,76 USD/kg con eólica; la combinación óptima depende de recurso, costos y WACC. | Es una proyección tecnológica de largo plazo, no un benchmark contemporáneo. Confirma la importancia de la complementariedad recurso–PEM, pero no debe usarse para validar LCOH 2025. |
| [IEA (2025)](https://www.iea.org/data-and-statistics/charts/supply-cost-curves-for-renewable-hydrogen-based-on-hybrid-onshore-wind-pv-configurations-2035) | Curvas 2035 para configuraciones híbridas, con activos optimizados por celda geográfica. Sus supuestos incluyen 1.183 USD/kW para electrólisis, 1.315 USD/kW eólico y 639 USD/kW FV. | Es útil para una sensibilidad futura: los costos FV y eólicos asumidos por el DOE son mayores, por lo que no corresponde esperar sus costos de 2035 en el escenario actual. |

## Conclusión de comparación y pasos de validación

Los resultados son plausibles como **screening conservador de configuraciones
sin almacenamiento**: la mayor disponibilidad eólica en Magallanes eleva la
utilización PEM y reduce el LCOH frente a Antofagasta. Sin embargo, no se debe
afirmar una validación completa a partir de la literatura porque las fronteras
de costo no coinciden.

Para una comparación más rigurosa se recomienda:

1. Recalcular el DOE con los supuestos de un estudio de referencia (tecnología
   de electrólisis, año monetario, WACC, tamaño y alcance) y comparar el mismo
   KPI.
2. Añadir agua/desalación, compresión, almacenamiento de H₂ y transporte si el
   objetivo es costo de H₂ entregado, no sólo costo de producción.
3. Hacer sensibilidad sobre CAPEX, WACC, degradación/reposición PEM y año
   meteorológico; publicar rangos de LCOH, no sólo el mínimo puntual.
4. Ampliar el DOE cerca de los diseños factibles de menor LCOH, especialmente
   alrededor de 100–250 MWdc FV, 180 MW eólicos y 150–250 MW PEM en Magallanes.

## Reproducción

Los casos se ejecutan desde la raíz del repositorio:

```bash
conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/run_case_study.py site_01_antofagasta

conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/run_case_study.py site_02_magallanes
```

Los resultados se escriben en `outputs/<sitio>/doe_results.csv`. Antes de
ejecutar, los cuatro recursos públicos deben descargarse y verificarse según el
procedimiento del [README del ejemplo](../examples/chile_hybrid_h2_doe/README.md).
