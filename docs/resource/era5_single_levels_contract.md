# Contrato técnico de datos ERA5 Single Levels

Este documento define el contrato de entrada, procesamiento y salida para la primera
implementación de recursos ERA5 Single Levels en H2Integrate_CL.

## 1. Estado y alcance

El contrato se aplica inicialmente a:

- Archivos NetCDF4/HDF5 disponibles localmente.
- Un año meteorológico por ejecución.
- Archivos mensuales separados en viento, solar y variables auxiliares.
- Resolución temporal horaria.
- Timestamps y metadatos temporales en UTC.
- Selección espacial por vecino más cercano (`nearest`).
- Recursos eólico y solar compatibles con los contratos actuales de H2Integrate.

Quedan fuera del primer alcance la descarga remota, Zarr, OPeNDAP, interpolación bilineal,
listas explícitas de archivos, extrapolación vertical del viento y procesamiento masivo de
sitios.

### 1.1. Dependencias opcionales

La lectura y transformación ERA5 utilizará:

- `xarray` para trabajar con datasets etiquetados.
- `h5netcdf` como backend NetCDF4/HDF5.
- `pvlib` para geometría solar y transformaciones radiométricas validadas.

Estas dependencias no forman parte de la instalación base. Se instalan mediante:

```bash
pip install -e ".[era5]"
```

## 2. Configuración de archivos

La primera implementación utilizará patrones mensuales configurables:

```yaml
resource_year: 2023
resource_dir: /ruta/administrada/era5
file_patterns:
  wind: era5_chile_wind_{year}_{month:02d}.nc
  solar: era5_chile_solar_{year}_{month:02d}.nc
  auxiliary: era5_chile_auxiliary_{year}_{month:02d}.nc
```

El lector deberá resolver, ordenar y validar los doce meses de cada categoría requerida. La
partición mensual será transparente para H2Integrate: cada recurso recibirá una única serie
anual normalizada.

Los patrones no podrán contener rutas locales codificadas en el módulo. Una lista explícita
de archivos se registra como mejora futura para nombres irregulares, archivos anuales o
particiones distintas de la mensual.

## 3. Variables ERA5

### 3.1. Variables obligatorias para viento

| Variable | Unidad de entrada | Uso |
| --- | --- | --- |
| `u10` | m/s | Componente zonal a 10 m |
| `v10` | m/s | Componente meridional a 10 m |
| `u100` | m/s | Componente zonal a 100 m |
| `v100` | m/s | Componente meridional a 100 m |
| `t2m` | K | Temperatura a 2 m |
| `sp` | Pa | Presión superficial |
| `z` | m²/s² | Geopotencial de superficie |

### 3.2. Variables obligatorias para solar

| Variable | Unidad de entrada | Uso |
| --- | --- | --- |
| `ssrd` | J/m² | Radiación solar total horizontal acumulada |
| `fdir` | J/m² | Radiación solar directa horizontal acumulada |
| `t2m` | K | Temperatura a 2 m |
| `d2m` | K | Punto de rocío a 2 m |
| `sp` | Pa | Presión superficial |
| `u10`, `v10` | m/s | Viento a 10 m |
| `z` | m²/s² | Geopotencial de superficie |

`fsr`, `ssr` y `tisr` serán opcionales. Se conservará registro de su disponibilidad para
controles de calidad y mejoras futuras, sin convertirlas en requisitos del primer lector.

## 4. Coordenadas y dimensiones

Las variables deberán usar las dimensiones `valid_time`, `latitude` y `longitude`.
Se admitirán latitudes ascendentes o descendentes y longitudes en `[-180, 180]` o
`[0, 360]`.

`expver` se tratará como coordenada temporal de versión. La primera implementación admitirá
una versión homogénea; varias versiones solo podrán combinarse en el futuro cuando sean
segmentos complementarios y no conflictivos.

`number` se admitirá únicamente si es escalar o de longitud uno y representa un miembro
determinista. Un ensemble con varios miembros producirá un error explícito.

## 5. Selección espacial

El método inicial será `nearest`: se seleccionará el centro de grilla más próximo, sin
interpolar ni promediar.

La distancia geodésica entre las coordenadas solicitadas y seleccionadas se registrará
siempre. El umbral de advertencia será configurable y tendrá el valor predeterminado:

```yaml
nearest_distance_warning_km: 15.0
```

Un sitio fuera del dominio producirá error. Una distancia superior al umbral continuará el
procesamiento con advertencia. El contrato no establece inicialmente un límite duro por
distancia para sitios que estén dentro del dominio.

## 6. Contrato temporal

Los datos se interpretarán como reanalysis ERA5:

- Frecuencia: una hora.
- Zona horaria: UTC.
- Separación exigida entre timestamps: 3.600 segundos.
- Sin timestamps faltantes ni duplicados.
- `valid_time`: final del período de acumulación.
- Inicio del período: `valid_time - 1 hora`.
- Instante representativo para geometría solar: `valid_time - 30 minutos`.

Se esperan 8.760 registros para un año normal. Los años bisiestos seguirán la opción
`include_leap_day` y deberán coincidir con `n_timesteps`.

Para las pruebas iniciales, `resource_year` seleccionará los registros cuyo `valid_time`
pertenezca al año solicitado. Esto implica que el registro de las 00 UTC representa parte
del día anterior. La cobertura estricta de un año calendario, usando el registro de las
00 UTC del año siguiente, queda registrada como mejora futura y no bloqueará las pruebas
con los datos disponibles.

## 7. Transformaciones eólicas

Para cada altura disponible:

```text
wind_speed = sqrt(u² + v²)
wind_direction = (270° - atan2(v, u)) mod 360°
```

La dirección seguirá la convención meteorológica: dirección desde la cual sopla el viento.
Primero se seleccionarán o interpolarán las componentes `u` y `v`; nunca se interpolará
directamente un ángulo.

Para bujes superiores a 100 m se utilizará el viento de 100 m y se emitirá una advertencia
con la altura solicitada y utilizada. No se aplicará extrapolación implícita.

Se registra como mejora futura una opción configurable de tratamiento vertical, con
alternativas como ley potencial, perfil logarítmico o error estricto.

## 8. Transformaciones solares

Para datos horarios:

```text
GHI = SSRD / 3600
BHI = FDIR / 3600
DHI = max(GHI - BHI, 0)
DNI = BHI / cos(ángulo cenital)
```

`BHI` representa irradiancia directa horizontal. El ángulo cenital se evaluará en el centro
del período de acumulación. DNI será cero durante la noche o cuando el ángulo cenital no
permita una división numéricamente estable.

El umbral predeterminado será un ángulo cenital de 88°, consistente con el control de
horizonte predeterminado de `pvlib`, y podrá configurarse. Los registros con componente
directa horizontal positiva que sean anulados por este control se contabilizarán.

Si `FDIR > SSRD`, la componente directa horizontal se limitará a GHI, se contabilizará la
corrección y se emitirá una advertencia de control de calidad. Los valores originales no se
sobrescribirán en los datos fuente.

La integración con PySAM deberá validar experimentalmente la convención de timestamps,
incluyendo el comportamiento del registro de las 00 UTC y el uso del centro del intervalo.

## 9. Unidades y elevación

El lector común conservará unidades SI. Los adaptadores convertirán solamente en el límite
con las interfaces existentes:

| Magnitud | Interna | Salida eólica | Salida solar |
| --- | --- | --- | --- |
| Temperatura | K o °C normalizado | °C | °C |
| Presión | Pa | atm | mbar |
| Geopotencial | m²/s² | elevación en m | elevación en m |
| Viento | m/s | m/s | m/s |
| Radiación | J/m² | no aplica | W/m² |

La elevación ERA5 se calculará como `z/g`. Si el sitio declara elevación, tendrá prioridad;
la elevación ERA5 se conservará como metadato. No se corregirá automáticamente la presión
por diferencias entre ambas elevaciones.

## 10. Validación y control de calidad

Producirán error:

- Archivos o meses requeridos ausentes o duplicados.
- Variables o dimensiones obligatorias ausentes.
- Unidades incompatibles.
- Sitio fuera del dominio.
- Ensemble con varios miembros.
- Timestamps desordenados, duplicados o no horarios.
- Longitud distinta de `n_timesteps`.
- Valores faltantes en variables obligatorias.
- Valores físicamente imposibles que no correspondan a tolerancias documentadas.

Producirán advertencia:

- Distancia `nearest` superior al umbral configurable.
- Uso de viento a 100 m para un buje superior.
- Diferencias entre FDIR y SSRD que requieran limitar DHI.
- Diferencia relevante entre elevación declarada y elevación ERA5.
- Correcciones menores debidas a precisión numérica.

No se rellenarán automáticamente horas o variables meteorológicas faltantes.

## 11. Contratos de salida

El recurso eólico producirá `wind_resource_data` y el solar producirá
`solar_resource_data`, sin modificar las interfaces públicas existentes.

Todos los arrays temporales deberán:

- Tener longitud igual a `n_timesteps`.
- Compartir el mismo orden temporal.
- Contener valores numéricos finitos.
- Incluir año, mes, día, hora y minuto.
- Declarar `data_tz = 0` y `dt = 3600`.

La presión se entregará en atm para el contrato eólico PySAM y en mbar para el contrato
solar PySAM.

## 12. Proveniencia

Cada salida registrará, como mínimo:

- Producto ERA5 y año solicitado.
- Archivos utilizados.
- Variables y unidades originales.
- Coordenadas solicitadas y seleccionadas.
- Distancia al punto de grilla.
- Método espacial.
- `number` y valores de `expver`.
- Cobertura temporal y zona horaria.
- Período de acumulación.
- Elevación ERA5 y elevación utilizada.
- Transformaciones, advertencias y correcciones aplicadas.

## 13. Mejoras futuras registradas

- Listas explícitas de archivos.
- Interpolación bilineal de variables primitivas.
- Cobertura estricta del año calendario con datos del año siguiente.
- Extrapolación eólica vertical configurable.
- Descarga HTTPS y caché persistente.
- Zarr, OPeNDAP o subconjuntos remotos.
- Optimización para evaluaciones de múltiples sitios.
- Validación con observaciones y fuentes meteorológicas independientes.

## 14. Criterios de aceptación

La implementación deberá demostrar mediante pruebas que:

- Oculta la partición mensual y entrega una serie anual.
- Conserva continuidad, orden y unidades.
- Reproduce transformaciones eólicas analíticas.
- Produce GHI, DHI y DNI consistentes.
- Emite los errores y advertencias definidos.
- Mantiene compatibilidad con PySAM eólico y solar.
- No altera los recursos meteorológicos existentes.

## 15. Lector común implementado

`ERA5SingleLevelsReader`, definido en `h2integrate/resource/era5_reader.py`, implementa la
primera capa del contrato. Su responsabilidad termina en la entrega de un `xarray.Dataset`
anual seleccionado y validado; no calcula todavía las variables derivadas eólicas o
solares.

Ejemplo de uso:

```python
from h2integrate.resource.era5_reader import ERA5SingleLevelsReader

reader = ERA5SingleLevelsReader(
    resource_dir="/ruta/administrada/era5",
    resource_year=2023,
    nearest_distance_warning_km=15.0,
)
annual_site_data = reader.read_site(
    latitude=-23.45,
    longitude=-68.25,
    categories=["wind", "solar", "auxiliary"],
)
```

El lector resuelve los doce archivos de cada categoría, valida variables, unidades,
dimensiones, grilla, `number`, `expver` y continuidad horaria, y carga solamente el punto
de grilla seleccionado. La salida registra los archivos utilizados, coordenadas solicitadas
y seleccionadas, distancia a la grilla, método espacial, versión, miembro y cobertura
temporal.

## 16. Transformaciones eólicas comunes implementadas

`transform_era5_wind_dataset`, definida en `h2integrate/resource/era5_wind.py`, transforma
el dataset puntual anual de las categorías `wind` y `auxiliary` al contrato
`wind_resource_data` existente. La función no depende de OpenMDAO y puede reutilizarse por
los adaptadores PySAM y FLORIS.

La salida incluye:

- `wind_speed_10m`, `wind_direction_10m`, `wind_speed_100m` y
  `wind_direction_100m`.
- `temperature_2m` en °C y `pressure_0m` en atm.
- Año, mes, día, hora y minuto; `data_tz = 0` y `dt = 3600`.
- Elevación utilizada y elevación ERA5 calculada con `z / 9.80665`.
- Coordenadas, archivos fuente, unidades originales y transformaciones aplicadas.

La transformación exige datos UTC explícitos, unidades ERA5 compatibles, series finitas,
presión positiva, temperatura no inferior al cero absoluto y geopotencial superficial
constante. Si existe una elevación configurada para el sitio, esta prevalece sin corregir
automáticamente la presión; la elevación ERA5 permanece disponible como metadato.

Cuando `u = v = 0`, la fórmula vectorial devuelve de manera determinista 270°, aunque la
dirección carece de significado físico porque la velocidad es cero. Los consumidores no
deben interpretar la dirección de muestras calmas.

La advertencia por uso de viento de 100 m en bujes superiores se implementará en la capa de
integración que conoce la altura de buje solicitada. El transformador común conserva ambas
alturas ERA5 y no decide qué altura consume cada tecnología.

## 17. Transformaciones solares comunes implementadas

`transform_era5_solar_dataset`, definida en `h2integrate/resource/era5_solar.py`, transforma
el dataset puntual anual de las categorías `solar`, `wind` y `auxiliary` al contrato
`solar_resource_data`. La función utiliza `pvlib` para calcular la posición solar verdadera
en `valid_time - 30 minutos` y mantiene los timestamps de salida en `valid_time` UTC.

La salida incluye:

- `ghi`, `dhi` y `dni` en W/m², además del ángulo cenital usado.
- Temperatura y punto de rocío en °C, presión en mbar, y viento a 10 m.
- Año, mes, día, hora y minuto; `data_tz = 0` y `dt = 3600`.
- Elevación utilizada, elevación ERA5, parámetros de geometría, conteos de correcciones y
  proveniencia del lector común.

La transformación rechaza acumulaciones negativas, unidades incompatibles, presión no
positiva, temperaturas inferiores al cero absoluto, punto de rocío más de 0,1 K sobre la
temperatura y geopotencial superficial variable. Si `fdir > ssrd`, limita la componente
directa horizontal a GHI, conserva intacto el dataset fuente, emite una advertencia y
registra el número de correcciones.

El umbral cenital es configurable y vale 88° por defecto. Para ángulos iguales o superiores,
noche o coseno cenital no positivo, DNI se fija en cero. La validación anual inicial confirmó
que el recurso resultante es aceptado por `PySAM.Pvwattsv8`; la evaluación energética de un
componente PV completo y la sensibilidad a la convención del registro de las 00 UTC se
mantienen como pruebas de integración posteriores.
