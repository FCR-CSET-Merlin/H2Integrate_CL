# Descarga reproducible de Sup3rWind y NSRDB

`h2integrate.tools.download_nlr_resources` descarga recursos puntuales directamente desde las
API de NLR y conserva cada respuesta CSV sin transformaciones. Por cada archivo crea un JSON
adyacente con la solicitud no sensible, fecha UTC, tamaño y checksum SHA-256.

Las fuentes oficiales son:

- [Sup3rWind South America v1.0.0, 60 minutos](https://developer.nlr.gov/docs/wind/wind-toolkit/wtk-sup3rwind-south-america-v1-0-0-60min-download/), disponible para 2005–2024.
- [NSRDB GOES Full Disc PSM v4](https://developer.nlr.gov/docs/solar/nsrdb/nsrdb-GOES-full-disc-v4-0-0-download/), disponible para 2018–2025 a intervalos de 30 o 60 minutos.
- [Límites de uso de las API](https://developer.nlr.gov/docs/rate-limits/).

El descargador fija resolución de 60 minutos y tiempo UTC. Excluye el 29 de febrero de manera
predeterminada para conservar 8.760 registros en años bisiestos; se puede cambiar con
`--include-leap-day`. Las solicitudes son secuenciales y se separan por 1,1 segundos.

## Credenciales

Use los nombres ya establecidos en H2Integrate:

```bash
export NLR_API_KEY="..."
export NLR_API_EMAIL="..."
```

Las credenciales se envían a NLR, pero no se escriben en el JSON ni se muestran en mensajes de
error. No deben incorporarse a Git ni pasarse como argumentos de línea de comandos.

## Uso general

```bash
python -m h2integrate.tools.download_nlr_resources \
  --site sitio_prueba \
  --lat -25.4 \
  --lon -70.48 \
  --years 2022 2023 \
  --resource both \
  --wind-heights 100 120
```

Los valores de `--resource` son `wind`, `solar` y `both`. Sup3rWind admite alturas de 10, 40,
80, 100, 120, 160 y 200 m. Cada combinación recurso–año se solicita por separado. Una descarga
existente no se repite; un par parcial requiere revisión y `--overwrite` para reemplazarlo.

La salida predeterminada sigue esta estructura y está excluida de Git:

```text
data/raw/
├── sup3rwind/<sitio>/<año>/<sitio>_sup3rwind_<año>.csv
├── sup3rwind/<sitio>/<año>/<sitio>_sup3rwind_<año>.request.json
├── nsrdb/<sitio>/<año>/<sitio>_nsrdb_goes_full_disc_v4_<año>.csv
└── nsrdb/<sitio>/<año>/<sitio>_nsrdb_goes_full_disc_v4_<año>.request.json
```

El CSV es la respuesta binaria original. El JSON permite comprobar el WKT, atributos,
resolución, convención temporal, procedencia y checksum sin revelar la clave ni el correo.

## Recursos de los dos casos DOE chilenos

Estas dos ejecuciones generan los cuatro CSV fuente de 2023 para las coordenadas configuradas:

```bash
python -m h2integrate.tools.download_nlr_resources \
  --site site_01_antofagasta \
  --lat -22.2812687 \
  --lon -69.5698745 \
  --years 2023 \
  --resource both \
  --wind-heights 100 120

python -m h2integrate.tools.download_nlr_resources \
  --site site_02_magallanes \
  --lat -52.8502704 \
  --lon -70.9575804 \
  --years 2023 \
  --resource both \
  --wind-heights 100 120
```

Después de validar contenido, número de horas y compatibilidad con los adaptadores, los cuatro
CSV se copian con el mismo nombre a `examples/chile_hybrid_h2_doe/data/`, se adjuntan a una
Release pública inmutable y sus URL, tamaños y checksums se incorporan a
`resource_manifest.yaml`. Los JSON de procedencia deben conservarse junto a los artefactos de
la Release, aunque no son entradas de la simulación.

Hasta completar esa publicación, el descargador público del DOE rechazará el manifiesto de
forma deliberada. Esta separación permite que quien mantiene los recursos los regenere con
credenciales, mientras los usuarios del ejemplo sólo descargan assets públicos verificados.
