# Reporte de validación eólica con ERA5 Single Levels

## 1. Propósito y alcance

Este reporte consolida los casos ejecutados durante la adaptación de H2Integrate_CL en los
que datos horarios de **ERA5 Single Levels** se transformaron en recurso o generación eólica
y se contrastaron con una referencia independiente. El objetivo es documentar la subestimación
observada, cuantificar su magnitud y definir restricciones para el uso de ERA5 en análisis
tecnoeconómicos georreferenciados.

La fecha de corte es el **25 de agosto de 2026**. Los resultados son diagnósticos de casos
puntuales, no una validación estadística de todo Chile ni de todos los años de ERA5.

Se distinguen dos tipos de evidencia:

1. **Benchmarks con referencia independiente:** comparación con generación bruta CNE/CEN o
   con velocidades del Explorador Eólico de Chile. Estos casos permiten afirmar que existió
   subestimación.
2. **Pruebas de integración sin benchmark:** casos híbridos ERA5–PySAM usados para verificar
   el flujo de software. Sus factores de planta bajos son señales de alerta, pero no prueban
   por sí solos un sesgo sin observaciones del mismo sitio y año.

## 2. Definiciones y convenciones

Para potencia nominal `P_nom`, generación anual `E` y 8.760 horas:

`FC = E / (P_nom × 8.760)`.

El sesgo anual relativo es:

`sesgo_% = 100 × (E_ERA5 / E_ref - 1)`.

Un valor negativo indica subestimación. La correlación diaria `r` es el coeficiente de Pearson
entre energía diaria modelada y reportada. Salvo indicación contraria, los modelos se agregaron
por día UTC; la zona horaria de las series operacionales no estaba declarada.

Las comparaciones usaron curvas de potencia normalizadas a la potencia nominal. No representan
una reconstrucción operacional completa: no reprodujeron indisponibilidades, mantenimientos,
restricciones de despacho ni, en todos los casos, pérdidas de estela y eléctricas. Esta
simplificación es conservadora para diagnosticar subestimación: incorporar pérdidas a una
simulación que ya genera poco reduciría aún más su energía.

## 3. Resumen cuantitativo de los benchmarks

| Caso | Configuración modelada | Referencia | ERA5 | FC ref. | FC ERA5 | Sesgo anual | `r` diario |
|---|---|---:|---:|---:|---:|---:|---:|
| Totoral 2015 | 23 V90/2000; 46 MW; buje 80 m | 80,319 GWh | 25,202 GWh | 19,93 % | 6,25 % | -68,62 % | 0,705 |
| Totoral 2023 | 23 V90/2000; 46 MW; buje 80 m | 72,899 GWh | 22,814 GWh | 18,09 % | 5,66 % | -68,70 % | 0,877 |
| Valle de los Vientos 2023 | Proxy eólico de 90 MW | 155,164 GWh | 24,745 GWh | 19,68 % | 3,14 % | -84,05 % | 0,095 |
| Taltal 2015 | 33 V112/3000; 99 MW | 267,323 GWh | 55,861 GWh | 30,82 % | 6,44 % | -79,10 % | 0,618 |

Notas:

- Las energías se redondean a tres decimales; los cálculos conservaron la precisión completa.
- Taltal dispone de 8.754 horas comunes. Su generación ERA5 se anualizó desde la potencia media
  y las métricas diarias utilizaron 363 días completos.
- En Valle de los Vientos, el artefacto conserva la capacidad de 90 MW y la curva proxy Vestas
  V90; la configuración de sesión correspondió a 30 unidades V90/3000.

Los cuatro benchmarks muestran una subestimación anual de **68,6 % a 84,1 %**. La persistencia
del sesgo en sitios, capacidades y años diferentes impide tratarlo como una anomalía aislada.

## 4. Evidencia directa de subestimación del recurso: Totoral 2015

Totoral permitió comparar ERA5 con el Explorador Eólico basado en reconstrucción WRF antes de
aplicar la curva de potencia. La serie del Explorador contenía 8.760 horas; tres velocidades y
tres direcciones faltantes fueron completadas hacia adelante para simular generación. La
comparación de velocidad utilizó 8.757 pares válidos a 100 m.

| Métrica a 100 m | Explorador | ERA5 | Diferencia ERA5 - Explorador |
|---|---:|---:|---:|
| Media | 6,350 m/s | 4,215 m/s | -2,135 m/s (-33,63 %) |
| Mediana | 6,472 m/s | 4,176 m/s | -2,296 m/s |
| Percentil 90 | 9,848 m/s | 6,707 m/s | -3,141 m/s |

La comparación horaria obtuvo MAE de 2,471 m/s, RMSE de 3,003 m/s y `r = 0,747`. El punto ERA5
`(-31,25°, -71,50°)` quedó a 13,80 km del punto del CSV y a 14,69 km del emplazamiento usado
para generación. El sesgo negativo de velocidad es la evidencia más directa del problema de
recurso. Por la no linealidad de la curva de potencia, una reducción de 33,6 % en velocidad
media produjo una reducción mucho mayor en energía.

Al transformar el recurso a 80 m y aplicar la curva V90/2000, ERA5 produjo 25,202 GWh frente a
80,319 GWh CEN. El Explorador extrapolado a 80 m produjo 87,723 GWh, error de +9,22 % y
`r = 0,798`. Esta comparación controlada indica que la mayor parte de la brecha ERA5 no provino
de la curva de potencia ni de la serie operacional, sino del recurso de entrada.

Un análisis de desplazamiento horario elevó la correlación ERA5 desde 0,705 hasta 0,739 con un
corrimiento de -6 horas, pero prácticamente no modificó el MAE. La incertidumbre temporal puede
alterar la correspondencia diaria, pero no explica el déficit anual de 68,6 %.

## 5. Casos de generación eólica

### 5.1. Totoral 2023

Se repitió la configuración de 46 MW con ERA5 2023. El nodo seleccionado fue nuevamente
`(-31,25°, -71,50°)`, a 14,69 km. La velocidad media ERA5 a 100 m fue 4,125 m/s; 38,86 % de las
horas quedó bajo la velocidad de entrada. La generación modelada fue 22,814 GWh frente a
72,899 GWh observados.

La correlación elevada (`r = 0,877`) muestra que ERA5 capturó parte de la secuencia temporal,
pero con amplitud insuficiente. Una buena correlación no implica una estimación adecuada de
energía ni de factor de planta.

### 5.2. Valle de los Vientos 2023

Para `(-22,52653°, -68,81447°)`, ERA5 seleccionó `(-22,50°, -68,75°)`, a 7,25 km. La velocidad
media a 100 m fue 3,706 m/s. La elevación configurada era 2.250 m, mientras ERA5 representó
2.680 m, diferencia de 430 m que evidencia la dificultad de representar emplazamientos complejos
con una grilla de 0,25°.

La simulación produjo 24,745 GWh y factor de planta de 3,14 %, frente a 155,164 GWh y 19,68 %
reportados. Además del sesgo anual de -84,05 %, la correlación diaria fue 0,095. ERA5 no
reprodujo adecuadamente ni la magnitud ni la variabilidad diaria observada.

### 5.3. Taltal 2015

Taltal contrastó cuatro fuentes con la misma curva V112/3000 y 99 MW:

| Fuente | Velocidad media a 100 m | Generación anualizada | Factor de planta | Error vs. CNE | `r` diario |
|---|---:|---:|---:|---:|---:|
| Explorador WRF | 8,411 m/s | 421,488 GWh | 48,60 % | +57,67 % | 0,724 |
| ERA5 | 3,479 m/s | 55,861 GWh | 6,44 % | -79,10 % | 0,618 |
| Sup3rWind | 6,609 m/s | 293,714 GWh | 33,87 % | +9,87 % | 0,777 |
| MERRA-2 | 5,350 m/s | 187,859 GWh | 21,66 % | -29,73 % | 0,669 |
| CNE bruta | — | 267,323 GWh | 30,82 % | — | — |

ERA5 fue simultáneamente la fuente con menor velocidad, menor energía y mayor subestimación. La
comparación multifuente refuerza la conclusión de Totoral: el déficit aparece antes de considerar
detalles financieros o de integración con hidrógeno.

## 6. Pruebas ERA5 que no constituyen benchmark

La integración YAML → recursos ERA5 → PySAM → OpenMDAO se verificó con dos casos adicionales:

- `ERA5_SL_test_TEA`: 6 MW eólicos, 479,827 MWh y factor de planta aproximado de 0,91 % en
  `(-23,50°, -68,25°)`.
- Caso `(-23,6°, -70,2°)`: 6 MW eólicos, 365,07 MWh y factor de planta de 0,69 %; el nodo quedó
  a 12,23 km y su elevación ERA5 difirió de la configurada.

Estos resultados demostraron que el flujo anual de 8.760 horas funciona y conserva el balance
de energía. No se incluyen como evidencia de subestimación porque carecen de una referencia
independiente para el mismo sitio y año.

## 7. Diagnóstico crítico

Los resultados son compatibles con una combinación de:

1. **Resolución espacial:** la grilla ERA5 de 0,25° suaviza relieve, aceleraciones orográficas y
   corredores locales relevantes para parques eólicos.
2. **Selección `nearest`:** una distancia aceptable no garantiza igual exposición, rugosidad o
   elevación entre nodo y parque.
3. **Altura:** ERA5 llega a 100 m en el contrato actual. Para bujes superiores se usa 100 m con
   advertencia, sin extrapolación vertical configurable.
4. **No linealidad:** sesgos de velocidad se amplifican en la zona ascendente de la curva de
   potencia.
5. **Topografía y densidad:** las diferencias de elevación afectan el viento resuelto y la
   densidad; no todos los benchmarks aplicaron una corrección homogénea.
6. **Referencia operacional:** CNE/CEN incorpora disponibilidad y restricciones. Este efecto
   normalmente reduce la observación y no explica que ERA5 quede 68–84 % por debajo.

## 8. Implicancias tecnoeconómicas y recomendaciones

Usar ERA5 sin corrección en estos casos reduciría artificialmente el factor de planta,
aumentaría la capacidad requerida, alteraría el despacho híbrido y sobrestimaría LCOE y LCOH.
Por tanto:

- No usar ERA5 directamente como estimador puntual de producción en los sitios estudiados.
- Calibrar velocidad o generación con una fuente independiente y validar en un año distinto.
- No aplicar un factor nacional único; considerar zona, topografía, altura y régimen de viento.
- Conservar ERA5 bruto, serie corregida y parámetros de corrección como salidas separadas.
- Priorizar mediciones o reconstrucciones de mayor resolución cuando estén disponibles.

## 9. Proveniencia y reproducibilidad

Los valores provienen de:

- `/tmp/totoral_2015_era5_vs_explorador_corrected_metrics.json`.
- `/tmp/totoral_2015_generation_cen_era5_explorer_metrics.json`.
- `/tmp/totoral_era5_v90_2000_2023_metrics.json`.
- `/tmp/valle_de_los_vientos_era5_v90_metricas_2023.json`.
- `resource_files/wind/taltal_2015_comparison/taltal_2015_metrics.csv`.
- `docs/resource/era5_single_levels_contract.md` y `REGISTRO_ACTIVIDAD.md`.

Los archivos bajo `/tmp` y `resource_files/wind/` no están versionados. Las cifras relevantes
se incorporan explícitamente aquí para preservar el registro, pero reproducirlas requiere
conservar o regenerar los artefactos desde los datos meteorológicos y operacionales originales.
