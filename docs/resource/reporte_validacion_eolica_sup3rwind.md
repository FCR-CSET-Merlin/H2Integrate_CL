# Reporte de validación eólica con Sup3rWind: casos 2015 y 2023

## 1. Propósito y alcance

Este reporte consolida las simulaciones realizadas con **Sup3rWind South America v1.0.0** para
parques eólicos chilenos durante 2015 y 2023. El objetivo es evaluar su capacidad para reproducir
energía anual, factor de planta y variabilidad diaria respecto de generación bruta CNE/CEN.

La fecha de corte es el **25 de agosto de 2026**. Los resultados corresponden a ocho casos
parque-año y no deben extrapolarse automáticamente a otros emplazamientos o periodos.

## 2. Metodología común

Las velocidades Sup3rWind se transformaron mediante curvas de potencia JSON del catálogo local.
Las curvas se normalizaron a la potencia nominal de cada turbina o parque. Cuando una curva
terminaba antes de la velocidad de corte, se conservó su última potencia hasta 25 m/s y se
asumió generación nula sobre ese valor.

Los resultados representan **generación bruta ideal**: no incluyen un modelo explícito de
estelas, disponibilidad, pérdidas eléctricas, mantenimiento ni restricciones de despacho. La
energía diaria se agregó en UTC y se comparó con valores CNE/CEN suministrados en orden de
1 de enero a 31 de diciembre, cuya zona horaria no estaba declarada.

Se calcularon dos escenarios cuando presión y temperatura estaban disponibles:

- **Directo:** aplicación de velocidad a 100 m a la curva de potencia.
- **Ajustado por densidad:** `rho = p/(R*T)` y `v_eq = v*(rho/1,225)^(1/3)`.

El escenario ajustado se adopta como referencia principal. Taltal 2015 sólo dispone de la
conversión directa homogénea y se identifica expresamente.

El factor de planta y el error anual se calcularon como:

`FC = E / (P_nom × 8.760)`

y

`error_% = 100 × (E_modelo / E_CNE - 1)`.

## 3. Resumen consolidado

| Año | Parque | Curva empleada | Capacidad | CNE: GWh / FC | Sup3rWind: GWh / FC | Error anual | MAE diario | `r` diario |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 2015 | Taltal | V112/3000 | 99 MW | 267,323 / 30,82 % | 293,714 / 33,87 % | +9,87 % | 383,5 MWh | 0,777 |
| 2015 | Monte Redondo | V90/2000 | 48 MW | 99,601 / 23,69 % | 158,905 / 37,79 % | +59,54 % | 190,1 MWh | 0,830 |
| 2015 | Negrete | V126/3450, proxy | 34,5 MW | 94,114 / 31,14 % | 158,137 / 52,33 % | +68,03 % | 186,4 MWh | 0,822 |
| 2015 | Valle de los Vientos | V90/2000, proxy | 90 MW | 232,216 / 29,45 % | 223,351 / 28,33 % | -3,82 % | 166,0 MWh | 0,406 |
| 2023 | La Flor | V126/3450, proxy | 32,4 MW | 72,812 / 25,65 % | 169,109 / 59,58 % | +132,25 % | 266,3 MWh | 0,621 |
| 2023 | Malleco Norte + Sur | V126/3450, proxy | 273 MW | 686,090 / 28,69 % | 1.215,675 / 50,83 % | +77,19 % | 1.522,7 MWh | 0,781 |
| 2023 | Renaico | V90/2000, proxy | 88 MW | 226,455 / 29,38 % | 416,626 / 54,05 % | +83,98 % | 527,7 MWh | 0,792 |
| 2023 | San Gabriel | N131/3000, proxy | 183 MW | 471,857 / 29,43 % | 943,340 / 58,85 % | +99,92 % | 1.301,8 MWh | 0,822 |

Notas:

- Taltal usa el escenario directo, 8.754 horas comunes anualizadas y 363 días completos para
  métricas diarias.
- Los otros siete casos usan el escenario ajustado por densidad y 8.760 horas.
- La correlación de La Flor aumenta de 0,621 a 0,764 al restringir la evaluación a los 297 días
  con generación CNE mayor que cero.

## 4. Casos 2015

### 4.1. Taltal

Taltal se modeló con 33 V112/3000 y 99 MW. Sup3rWind tuvo velocidad media de 6,609 m/s y produjo
293,714 GWh, 9,87 % sobre los 267,323 GWh CNE. Fue la mejor aproximación conjunta en la
comparación con ERA5, WRF y MERRA-2, y obtuvo `r = 0,777`.

El resultado es favorable para energía anual, pero el MAE diario de 383,5 MWh y la ausencia de
corrección de densidad o pérdidas impiden considerarlo una validación definitiva.

### 4.2. Monte Redondo

La configuración de 24 V90/2000 y 48 MW utilizó el mismo modelo declarado para la planta.
Sup3rWind ajustado produjo 158,905 GWh frente a 99,601 GWh CNE. La correlación de 0,830 indica
representación temporal buena, pero el error anual de +59,54 % demuestra un sesgo de magnitud
importante incluso sin incertidumbre por curva proxy.

### 4.3. Negrete

Se modelaron 10 V126/3450 como proxy de V136/3450, con 34,5 MW. La simulación produjo
158,137 GWh frente a 94,114 GWh CNE. El error de +68,03 % no puede atribuirse únicamente a la
proxy: una V136 de mayor rotor tendería a aumentar, no reducir, la captación a velocidades bajas.
La correlación diaria fue 0,822.

### 4.4. Valle de los Vientos

Se usaron 45 V90/2000 como proxy de las V100/2000 informadas, con 90 MW. El encabezado del CSV
identifica V110/2000 como turbina instalada, discrepancia que debe resolverse con una fuente
técnica del parque.

Este sitio tuvo densidad media de 0,921 kg/m³. Sin ajuste produjo 267,008 GWh (+14,98 %); con
ajuste produjo 223,351 GWh (-3,82 %), cerca de los 232,216 GWh CNE. Sin embargo, `r = 0,406`
evidencia una representación diaria débil. El acuerdo anual podría ocultar compensación de
errores temporales.

## 5. Casos 2023

### 5.1. La Flor

Se adoptó la capacidad nominal de 32,4 MW, aunque nueve turbinas de 3,45 MW suman 31,05 MW,
diferencia de +4,35 %. Se usó V126/3450 como proxy de V136/3450.

CNE reportó 68 días con generación nula. Sup3rWind produjo 169,109 GWh frente a 72,812 GWh,
con error de +132,25 %. Eliminar los días nulos mejora la correlación, pero no resuelve la gran
diferencia energética. La serie operacional sugiere indisponibilidad prolongada que un modelo
meteorológico ideal no puede reproducir.

### 5.2. Malleco

Se sumaron las series CNE de Malleco Norte (325,229 GWh) y Sur (360,861 GWh), obteniendo
686,090 GWh. Se adoptaron 273 MW nominales; 77 turbinas de 3,45 MW suman 265,65 MW, diferencia de
+2,77 %. La simulación produjo 1.215,675 GWh, factor de planta de 50,83 % y error de +77,19 %,
aunque conservó `r = 0,781`.

### 5.3. Renaico

La planta de 88 MW se representó con 44 V90/2000 como proxy de V110/2000. Sup3rWind produjo
416,626 GWh y factor de planta de 54,05 %, frente a 226,455 GWh y 29,38 % CNE. El error fue
+83,98 % y la correlación 0,792.

### 5.4. San Gabriel

La planta de 183 MW se representó con N131/3000 como proxy de Nordex AW-3000/132. La generación
modelada fue 943,340 GWh, prácticamente el doble de los 471,857 GWh CNE. Pese al error de
+99,92 %, la correlación diaria alcanzó 0,822, reforzando el patrón de temporalidad razonable y
magnitud excesiva.

## 6. Efecto de la densidad del aire

| Caso | Densidad media | Energía directa | Energía ajustada | Cambio |
|---|---:|---:|---:|---:|
| Monte Redondo 2015 | 1,205 kg/m³ | 160,435 GWh | 158,905 GWh | -0,95 % |
| Negrete 2015 | 1,220 kg/m³ | 158,450 GWh | 158,137 GWh | -0,20 % |
| Valle de los Vientos 2015 | 0,921 kg/m³ | 267,008 GWh | 223,351 GWh | -16,35 % |
| La Flor 2023 | 1,222 kg/m³ | 169,200 GWh | 169,109 GWh | -0,05 % |
| Malleco 2023 | 1,194 kg/m³ | 1.230,437 GWh | 1.215,675 GWh | -1,20 % |
| Renaico 2023 | 1,222 kg/m³ | 416,977 GWh | 416,626 GWh | -0,08 % |
| San Gabriel 2023 | 1,221 kg/m³ | 944,121 GWh | 943,340 GWh | -0,08 % |

La corrección sólo fue material en Valle de los Vientos. La sobreestimación centro-sur no puede
explicarse por haber omitido densidad en el escenario directo.

## 7. Heterogeneidad espacial y calibración

Como diagnóstico, `k = E_CNE/E_modelo` es el factor anual que igualaría energía. No constituye
por sí mismo una calibración válida, pero demuestra la heterogeneidad:

| Caso | `k` diagnóstico |
|---|---:|
| Taltal 2015 | 0,910 |
| Monte Redondo 2015 | 0,627 |
| Negrete 2015 | 0,595 |
| Valle de los Vientos 2015 | 1,040 |
| La Flor 2023 | 0,431 |
| Malleco 2023 | 0,564 |
| Renaico 2023 | 0,544 |
| San Gabriel 2023 | 0,500 |

La dispersión entre 0,431 y 1,040 descarta un único factor de corrección nacional. Los casos
del norte y de mayor altitud tuvieron buen acuerdo anual después de considerar densidad,
mientras los emplazamientos centro-sur sobreestimaron entre 59,5 % y 132,3 %.

## 8. Diagnóstico crítico

1. **Temporalidad útil:** correlaciones de 0,78–0,83 en varios parques indican que Sup3rWind
   puede representar la secuencia relativa de eventos.
2. **Magnitud no transferible:** una buena correlación coexistió con factores de planta modelados
   cercanos a 51–60 %, frente a 26–31 % observados en 2023.
3. **Operación no modelada:** días CNE nulos, indisponibilidad, estelas, pérdidas y restricciones
   explican parte de la brecha, pero errores cercanos a 100 % requieren revisar también recurso,
   altura y curvas.
4. **Curvas proxy:** V126 por V136, V90 por V100/V110 y N131 por AW-132 introducen incertidumbre.
5. **Representación puntual:** distancias pequeñas al nodo no garantizan igual exposición o
   rugosidad.

## 9. Recomendaciones para uso tecnoeconómico

- No usar directamente los factores de planta Sup3rWind de los casos centro-sur.
- Calibrar por zona y régimen, separando corrección del recurso, curva y pérdidas del parque.
- Ajustar con un subconjunto temporal y validar con otro año para evitar sobreajuste.
- Reportar escenarios bruto ideal, ajustado por densidad, calibrado y neto de pérdidas.
- Conservar métricas de energía y temporalidad: igualar GWh no asegura correlación ni estacionalidad.
- Investigar días de indisponibilidad CNE antes de atribuir toda diferencia al producto meteorológico.

## 10. Proveniencia y reproducibilidad

Las tablas se construyeron desde:

- `resource_files/wind/taltal_2015_comparison/taltal_2015_metrics.csv`.
- `resource_files/wind/sup3rwind_parks_2015_comparison/sup3rwind_parks_2015_metrics.csv`.
- `resource_files/wind/sup3rwind_parks_2023_comparison/sup3rwind_parks_2023_metrics.csv`.
- CSV horarios, diarios y mensuales de esos directorios.
- `REGISTRO_ACTIVIDAD.md` para supuestos y verificaciones.

Los directorios bajo `resource_files/wind/` están excluidos mediante `.gitignore`. Este reporte
conserva los indicadores principales, pero reproducirlos exige mantener o regenerar las entradas
meteorológicas y series CNE/CEN originales.
