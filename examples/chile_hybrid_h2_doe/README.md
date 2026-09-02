# DOE híbrido solar–eólico–PEM para dos sitios de Chile

Este ejemplo evalúa dos localidades independientes con un escenario financiero
conservador y selecciona, después del DOE, el menor LCOH que produce al menos
20 millones de kg de hidrógeno al año.

| Caso | Latitud | Longitud | Año meteorológico |
|---|---:|---:|---:|
| `site_01_antofagasta` | -22.2812687 | -69.5698745 | 2023 |
| `site_02_magallanes` | -52.8502704 | -70.9575804 | 2023 |

## Alcance

Cada sitio combina generación horaria solar NSRDB y eólica Sup3rWind, sin red,
para alimentar electrólisis PEM con degradación y reposición. No se modelan
batería, almacenamiento de H₂, conexión a red, agua o desalación, compresión,
transporte, oxígeno, incentivos ni créditos de carbono.

El DOE contiene 72 diseños por sitio:

- FV: 100, 200, 300 y 400 MWdc.
- Eólica: 10, 20 y 30 turbinas PySAM de 6 MW.
- PEM: 10, 15, 20, 25, 30 y 40 clústeres de 10 MW.

La alternativa de 35 clústeres mencionada inicialmente no forma parte del DOE
de referencia. Añadirla produciría 84 diseños por sitio y debe tratarse como una
variante explícita.

## Recursos públicos

Los cuatro CSV meteorológicos quedan fuera de Git. `resource_manifest.yaml`
define nombre, URL pública, tamaño y SHA-256 para cada archivo. El descargador
no usa credenciales NLR y rechaza manifiestos sin publicar o archivos que no
coincidan exactamente con sus checksums.

Los cuatro CSV de 2023 fueron validados y el manifiesto contiene sus tamaños,
SHA-256 y URLs para la Release `chile-weather-2023-v1`. Hasta que se publique,
las URLs previstas no serán descargables. La opción inicial GOES Aggregated no
entregó datos en ninguna de las dos coordenadas; por autorización explícita se usa
NSRDB GOES Full Disc PSM v4 a resolución temporal de 60 minutos. Después de
publicar la GitHub Release inmutable, cualquier usuario puede ejecutar:

```bash
conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/download_resources.py
```

Para verificar archivos ya descargados:

```bash
conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/download_resources.py --verify-only
```

### Generación de los archivos fuente desde NLR

Quien prepare la Release puede obtener los cuatro CSV originales con credenciales
`NLR_API_KEY` y `NLR_API_EMAIL` mediante el
[descargador reproducible](../../docs/resource/nlr_resource_downloader.md). Los dos comandos
exactos, la estructura de salida y el procedimiento para trasladar los archivos validados a
este caso están documentados allí. Este flujo guarda además un JSON de procedencia por CSV y
no altera los bytes recibidos de NLR.

La descarga desde NLR y la descarga pública son etapas distintas: sólo la primera exige una
cuenta; el usuario final ejecuta `download_resources.py` contra los assets verificados de la
Release.

## Ejecución

Después de publicar y descargar los recursos:

```bash
# ambos sitios: 144 ejecuciones
conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/run_case_study.py all

# un solo sitio: 72 ejecuciones
conda run -n h2integrate python \
  examples/chile_hybrid_h2_doe/run_case_study.py site_01_antofagasta
```

Los resultados se escriben bajo `outputs/<sitio>/`. El umbral de producción es
un filtro posterior; no transforma el DOE en una optimización continua.

## Escenario conservador

- Vida del proyecto: 30 años.
- Construcción: 60 meses desde 2027; año monetario objetivo USD 2025.
- Tasa de descuento: 10%; deuda/patrimonio: 55/45.
- Interés: 8,5%; préstamo: 15 años; inflación: 3%.
- Impuesto corporativo y ganancias de capital: 27%.
- Depreciación lineal: 15 años; IVA modelado como 0% en ProFAST.
- Eólica: 1.900 USD/kW y 55 USD/kW-año.
- Solar: 1.100 USD/kWac y 22 USD/kWac-año; DC/AC 1,30.
- PEM: 1.200 USD/kW y 20 USD/kW-año; reposición 20%.

Estos parámetros permiten comparar diseños bajo una convención conservadora;
no constituyen una oferta de financiamiento ni asesoría tributaria. La evidencia
y las limitaciones están en `FINANCIAL_PARAMETERS_EVIDENCE.md`.
