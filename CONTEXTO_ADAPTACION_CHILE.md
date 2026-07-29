# Contexto del repositorio y adaptación de H2Integrate para Chile

## 1. Propósito de este fork

Este repositorio corresponde a un fork de **H2Integrate**, librería desarrollada por el
National Laboratory of the Rockies (NLR, anteriormente NREL) para el diseño, simulación,
optimización y análisis tecnoeconómico de sistemas híbridos de energía.

El propósito del fork es extender H2Integrate para su aplicación en el contexto chileno,
manteniendo la compatibilidad con la implementación original y conservando los modelos,
ejemplos y configuraciones utilizados para Estados Unidos.

La adaptación debe realizarse mediante componentes y configuraciones que se acoplen de
forma análoga a los módulos existentes. En particular, se consideran inicialmente dos
líneas de trabajo:

1. Integración de datos de recurso energético y meteorológico de Chile provenientes de
   archivos NetCDF del producto **ERA5 Hourly Data on Single Levels**.
2. Incorporación de parámetros financieros, tributarios y económicos representativos del
   contexto chileno.

Este documento describe la estructura actual del repositorio e identifica los puntos de
extensión previstos. No define todavía una implementación concreta de los nuevos módulos.

## 2. Estructura general del repositorio

El código fuente principal se encuentra en el paquete `h2integrate/`. Los demás directorios
contienen ejemplos, datos, configuraciones reutilizables, documentación y pruebas.

```text
H2Integrate_CL/
├── h2integrate/       # Código fuente de la librería
├── examples/          # Casos de estudio y scripts ejecutables
├── resource_files/    # Datos de recursos y caché predeterminada
├── library/           # Configuraciones reutilizables de PySAM y FLORIS
├── docs/              # Documentación técnica y de usuario
├── test/              # Fixtures de prueba compartidos
├── .github/workflows/ # Integración continua
├── pyproject.toml     # Metadatos, dependencias y configuración de herramientas
└── environment.yml    # Entorno Conda de referencia
```

### 2.1. Paquetes principales

#### `h2integrate/core`

Contiene el núcleo del framework:

- Carga y validación de archivos de configuración.
- Construcción del problema OpenMDAO.
- Creación de sitios, recursos y tecnologías.
- Conexión de flujos entre tecnologías.
- Configuración de análisis, optimización y registro de resultados.
- Registro de modelos disponibles en `supported_models.py`.

La clase principal es `H2IntegrateModel`, definida en
`h2integrate/core/h2integrate_model.py`.

#### `h2integrate/resource`

Gestiona los recursos energéticos y ambientales utilizados por las tecnologías:

- Recurso eólico.
- Recurso solar.
- Recurso fluvial.
- Recurso mareomotriz.
- Descarga desde APIs.
- Lectura, normalización, validación y almacenamiento local de datos.

Los recursos meteorológicos comparten comportamiento mediante las clases base de
`h2integrate/resource/resource_base.py`.

#### `h2integrate/converters`

Contiene los modelos de generación y conversión de energía y materias primas, entre ellos:

- Energía eólica y solar.
- Electrólisis y producción de hidrógeno.
- Pilas de combustible.
- Amoníaco, metanol, hierro y acero.
- Gas natural y energía nuclear.
- Hidroelectricidad, energía marina y conexión a la red.
- Desalación.

Los modelos pueden incluir componentes separados de desempeño, costos y finanzas.

#### `h2integrate/storage`

Incluye modelos de:

- Baterías.
- Almacenamiento genérico.
- Almacenamiento de hidrógeno.
- Dimensionamiento automático y costos de almacenamiento.

#### `h2integrate/transporters`

Implementa elementos para conectar tecnologías y transportar commodities:

- Cables.
- Tuberías.
- Combinadores.
- Divisores.
- Transportadores genéricos.

#### `h2integrate/control`

Contiene reglas y estrategias de operación y despacho:

- Controladores de almacenamiento en lazo abierto.
- Controladores heurísticos.
- Despacho optimizado mediante Pyomo.
- Reglas de operación para tecnologías y almacenamiento.

#### `h2integrate/demand`

Representa perfiles de demanda fija y flexible.

#### `h2integrate/finances`

Contiene los modelos de análisis financiero:

- Modelos basados en ProFAST.
- Cálculo de valor presente neto.
- Ajustes de CAPEX y OPEX.
- Herramientas financieras comunes.

#### `h2integrate/preprocess`, `h2integrate/postprocess` y `h2integrate/tools`

Proporcionan utilidades para:

- Preparar archivos de entrada.
- Procesar configuraciones de turbinas.
- Ejecutar múltiples casos.
- Exportar resultados SQL a CSV.
- Crear gráficos y mapas.
- Aplicar índices de inflación.

### 2.2. Directorios auxiliares

#### `examples`

Cada subdirectorio contiene un caso de estudio. Normalmente incluye:

- Un script Python de ejecución.
- Un archivo YAML principal.
- Un `driver_config.yaml`.
- Un `plant_config.yaml`.
- Un `tech_config.yaml`.
- Datos adicionales requeridos por el caso.

#### `resource_files`

Almacena datos de entrada incluidos en el repositorio y actúa como directorio
predeterminado para recursos descargados. Actualmente contiene ejemplos de datos eólicos,
mareomotrices, undimotrices, de red y otros recursos.

#### `library`

Contiene configuraciones reutilizables, como parámetros de PySAM y definiciones de turbinas
para FLORIS. Estos archivos pueden ser incluidos desde los YAML mediante `!include`.

#### `docs`

Contiene la documentación de instalación, configuración, tecnologías, recursos, finanzas,
control, pruebas y desarrollo.

## 3. Punto de entrada y ejecución de una simulación

El repositorio no define actualmente un comando de consola único. El punto de entrada
programático es:

```python
from h2integrate.core.h2integrate_model import H2IntegrateModel

model = H2IntegrateModel("configuracion_principal.yaml")
model.run()
model.post_process()
```

Al construir `H2IntegrateModel`, la librería:

1. Carga el YAML principal.
2. Carga y valida las configuraciones de driver, tecnologías y planta.
3. Crea los sitios y sus recursos.
4. Crea las tecnologías y modelos financieros.
5. Conecta recursos y tecnologías.
6. Configura el driver de análisis u optimización.

Los scripts ubicados en `examples/` aplican este patrón a cada caso de estudio.

## 4. Configuración de los casos de estudio

### 4.1. Archivo YAML principal

Es la entrada de alto nivel del caso y referencia tres configuraciones:

```yaml
name: nombre_del_caso
system_summary: descripción del sistema
driver_config: driver_config.yaml
technology_config: tech_config.yaml
plant_config: plant_config.yaml
```

Las rutas pueden ser relativas al YAML principal, relativas al directorio de ejecución,
relativas a la raíz del repositorio o absolutas. La resolución de rutas se implementa en
`h2integrate/core/file_utils.py`.

### 4.2. `driver_config.yaml`

Define cómo se ejecutará el caso:

- Carpeta de resultados.
- Generación de reportes OpenMDAO.
- Simulación directa u optimización.
- Solver y tolerancias.
- Variables de diseño, restricciones y objetivo.
- Diseño de experimentos.
- Registro de resultados.

### 4.3. `tech_config.yaml`

Define las tecnologías incluidas y los modelos asociados:

- Modelo de desempeño.
- Modelo de costos.
- Modelo financiero, cuando corresponde.
- Parámetros compartidos.
- Parámetros de desempeño.
- Parámetros de costos.
- Parámetros financieros propios de la tecnología.

Los nombres declarados en el YAML se traducen a clases Python mediante
`h2integrate/core/supported_models.py`.

En general, los parámetros tecnológicos deben declararse explícitamente. Los ejemplos
existentes son la referencia principal para conocer la estructura requerida por cada
modelo.

### 4.4. `plant_config.yaml`

Describe la planta completa:

- Sitios, coordenadas y elevación.
- Recursos disponibles en cada sitio.
- Vida útil de la planta.
- Paso de tiempo y número de pasos de simulación.
- Conexiones entre tecnologías.
- Conexiones entre recursos y tecnologías.
- Parámetros financieros comunes.
- Grupos financieros y commodities evaluados.

Las conexiones entre recursos y tecnologías usan la forma:

```yaml
resource_to_tech_connections:
  - [site.wind_resource, wind, wind_resource_data]
  - [site.solar_resource, solar, solar_resource_data]
```

### 4.5. Ejecución de múltiples casos

`h2integrate/tools/run_cases.py` permite cargar un CSV con variaciones de parámetros del
`tech_config` y ejecutar varios escenarios. También existe soporte para diseño de
experimentos desde el `driver_config`.

Esta capacidad puede utilizarse para comparar:

- Diferentes ubicaciones de Chile.
- Distintos años meteorológicos.
- Escenarios de costos.
- Escenarios tributarios y financieros.
- Alternativas de dimensionamiento tecnológico.

## 5. Gestión actual de datos meteorológicos

Los recursos meteorológicos se declaran dentro de la sección `sites` del
`plant_config.yaml`:

```yaml
sites:
  site:
    latitude: 0.0
    longitude: 0.0
    resources:
      wind_resource:
        resource_model: OpenMeteoHistoricalWindResource
        resource_parameters:
          resource_year: 2022
```

Cada recurso es instanciado como un componente OpenMDAO y entrega un diccionario discreto
normalizado. Las tecnologías consumidoras esperan actualmente:

- `wind_resource_data` para tecnologías eólicas.
- `solar_resource_data` para tecnologías solares.
- `discharge` para recursos fluviales.

### 5.1. Flujo de obtención de datos

La lógica común de `ResourceBaseAPIModel` sigue este orden:

1. Utiliza datos entregados directamente mediante `resource_data`, si existen.
2. Busca un archivo en `resource_dir` con `resource_filename`.
3. Si el archivo existe, lo carga y normaliza.
4. Si no existe y el modelo soporta descarga, consulta la fuente remota.
5. Guarda el archivo descargado en el directorio de recursos.
6. Carga el archivo y entrega el diccionario normalizado.

El directorio se determina mediante:

1. `resource_dir` declarado en el caso.
2. La variable de entorno `RESOURCE_DIR`.
3. El directorio predeterminado `resource_files/`.

### 5.2. Fuentes meteorológicas existentes

Entre los modelos disponibles se encuentran:

- Open-Meteo para recurso histórico eólico y solar.
- Wind Toolkit mediante la API de NLR.
- Productos solares GOES, Meteosat y Himawari.

Los modelos Open-Meteo son globales y permiten configurar un caso preliminar para Chile.
Sin embargo, la adaptación propuesta busca incorporar además archivos ERA5 Single Levels
alojados localmente o en un servidor controlado por el proyecto.

### 5.3. Contrato de datos esperado

El recurso eólico normalizado utiliza claves como:

- `wind_speed_<altura>m`.
- `wind_direction_<altura>m`.
- `temperature_<altura>m`.
- `pressure_<altura>m`.
- Información temporal y metadatos del sitio.

El recurso solar normalizado utiliza, entre otras:

- `ghi`.
- `dni`.
- `dhi`.
- `temperature`.
- `pressure`.
- `wind_speed`.
- `wind_direction`.
- Año, mes, día, hora y minuto.
- Latitud, longitud, elevación y zona horaria.

Mantener estos contratos permitirá incorporar ERA5 sin modificar los convertidores eólicos
y solares existentes.

## 6. Ejecución de pruebas

El proyecto utiliza `pytest`. Su configuración se encuentra en `pyproject.toml`.

Las pruebas se clasifican mediante marcadores:

- `unit`: pruebas unitarias.
- `regression`: estabilidad de resultados.
- `integration`: interacción entre componentes y casos completos.

Comandos habituales:

```bash
pytest .
pytest . -m unit
pytest . -m regression
pytest . -m integration
pytest . --cov=h2integrate
```

Las dependencias de desarrollo se instalan con:

```bash
pip install ".[develop]"
```

Algunas pruebas de control y optimización requieren los solvers GLPK y CBC. La integración
continua se configura en `.github/workflows/ci.yml`.

Las pruebas están distribuidas principalmente en directorios `test/` dentro de cada paquete.
Los casos completos se prueban en `examples/test/test_all_examples.py`. Los fixtures
compartidos usan directorios temporales para evitar que las pruebas modifiquen los ejemplos
originales.

## 7. Principios para la adaptación chilena

La adaptación debe cumplir los siguientes principios:

1. Conservar los modelos, configuraciones y ejemplos originales.
2. Añadir nuevos componentes en lugar de reemplazar componentes estadounidenses.
3. Mantener las interfaces públicas y los contratos de datos existentes siempre que sea
   posible.
4. Reutilizar las clases base de recursos, finanzas y tecnologías.
5. Separar los datos y parámetros chilenos de los archivos compartidos por los casos
   originales.
6. Incorporar pruebas unitarias, de integración y regresión para cada extensión.
7. Documentar la fuente, versión, unidades y transformaciones de los datos.

## 8. Tarea de adaptación 1: recursos ERA5 para Chile

### 8.1. Objetivo

Incorporar datos solares, eólicos y meteorológicos provenientes de archivos NetCDF de
**ERA5 Hourly Data on Single Levels**, ya sea:

- Desde archivos disponibles localmente.
- Desde archivos descargables desde un servidor.
- En una fase posterior, desde un almacenamiento remoto con acceso parcial, como Zarr u
  OPeNDAP.

La descarga directa desde Copernicus Climate Data Store debería considerarse una tarea de
aprovisionamiento de datos y no una dependencia obligatoria durante cada simulación.

### 8.2. Extensión propuesta

Se propone añadir dos recursos análogos a los modelos existentes:

- `ERA5SingleLevelsWindResource`.
- `ERA5SingleLevelsSolarResource`.

Ambos deberían:

- Reutilizar las clases base actuales.
- Leer un mismo archivo ERA5 cuando contenga variables solares y eólicas.
- Seleccionar el punto o interpolar la grilla según latitud y longitud.
- Normalizar nombres, unidades, coordenadas y tiempo.
- Producir exactamente `wind_resource_data` y `solar_resource_data`.
- Mantener el tratamiento existente de directorios, archivos y caché.

Una configuración prevista sería:

```yaml
sites:
  chile_site:
    latitude: -23.45
    longitude: -68.25
    elevation: 2400
    resources:
      wind_resource:
        resource_model: ERA5SingleLevelsWindResource
        resource_parameters:
          resource_year: 2022
          resource_dir: data/era5
          resource_filename: chile_era5_2022.nc
          spatial_interpolation: nearest
      solar_resource:
        resource_model: ERA5SingleLevelsSolarResource
        resource_parameters:
          resource_year: 2022
          resource_dir: data/era5
          resource_filename: chile_era5_2022.nc
          spatial_interpolation: nearest
```

Para archivos alojados en un servidor se podría añadir un parámetro opcional específico de
estos recursos, conservando `resource_filename` como nombre de caché local:

```yaml
resource_url: https://servidor.example/era5/chile_era5_2022.nc
```

### 8.3. Variables ERA5 mínimas

Para viento:

- Componentes `u` y `v` a 10 m.
- Componentes `u` y `v` a 100 m.
- Temperatura a 2 m.
- Presión superficial.
- Geopotencial o elevación, si está disponible.

Para solar:

- Radiación solar descendente en superficie, SSRD.
- Radiación solar directa en superficie, FDIR.
- Temperatura y punto de rocío a 2 m.
- Presión superficial.
- Componentes de viento a 10 m.
- Albedo y geopotencial, opcionalmente.

### 8.4. Transformaciones requeridas

El módulo deberá considerar:

- Cálculo de velocidad y dirección desde componentes `u` y `v`.
- Conversión de Kelvin a grados Celsius.
- Conversión de presión a las unidades esperadas por H2Integrate.
- Conversión de radiación acumulada en J/m² a irradiancia media en W/m².
- Obtención de GHI, DHI y DNI compatibles con PySAM.
- Convención temporal de las acumulaciones horarias de ERA5.
- Datos en UTC y efecto de la zona horaria chilena.
- Tratamiento de años bisiestos.
- Normalización de longitudes en los rangos `[-180, 180]` y `[0, 360]`.
- Selección por vecino más cercano o interpolación espacial.
- Detección de datos faltantes, duplicados o fuera de rango.

La conversión de la componente directa horizontal acumulada de ERA5 a DNI debe validarse
especialmente, ya que requiere considerar la geometría solar durante cada intervalo.

### 8.5. Almacenamiento local y remoto

Para una primera implementación se recomienda:

- NetCDF anual por sitio o por una región acotada.
- Descarga mediante HTTPS y almacenamiento en caché local.
- Lectura con `xarray` y un backend NetCDF como dependencia opcional.

Un NetCDF nacional o multianual de gran tamaño servido como archivo estático obligaría a
descargar el objeto completo. Si el proyecto requiere evaluar muchos sitios directamente
sobre una grilla nacional, se debería estudiar una segunda fase con:

- Zarr y `fsspec`.
- OPeNDAP.
- Un servicio que genere subconjuntos espaciales y temporales.

### 8.6. Pruebas previstas

La integración ERA5 deberá incluir:

- Un archivo NetCDF pequeño usado como fixture local.
- Pruebas de lectura y validación de variables.
- Pruebas de unidades y conversiones.
- Pruebas de dirección y velocidad del viento.
- Pruebas de GHI, DHI y DNI.
- Pruebas de selección espacial y normalización de longitud.
- Pruebas de orden temporal, UTC y año bisiesto.
- Prueba de descarga binaria con un servidor simulado.
- Paridad entre lectura local y remota.
- Integración con los modelos PySAM solar y eólico.
- Comparación de control con otra fuente y, cuando sea posible, con observaciones chilenas.

## 9. Tarea de adaptación 2: parámetros financieros de Chile

### 9.1. Objetivo

Incorporar parámetros económicos, financieros y tributarios representativos de proyectos
energéticos desarrollados en Chile, sin reemplazar los valores estadounidenses presentes en
los ejemplos originales.

### 9.2. Estrategia de integración

La primera etapa debería ser de configuración. Los parámetros chilenos deben declararse en
archivos propios del nuevo caso y utilizar los modelos financieros existentes cuando sus
interfaces sean suficientes.

Los parámetros generales de la planta se ubican en `plant_config.yaml`, dentro de
`finance_parameters`. Los parámetros específicos de cada tecnología se ubican en
`tech_config.yaml`, dentro de sus secciones de costos y finanzas.

Solo se debería crear un nuevo modelo financiero si los modelos actuales no pueden
representar adecuadamente la normativa o estructura financiera chilena.

### 9.3. Parámetros por revisar

Como mínimo, se deberá definir y documentar:

- Moneda base del análisis y conversión a USD cuando corresponda.
- Año monetario de referencia.
- Inflación.
- Tasa de descuento nominal o real.
- Estructura deuda/capital.
- Tasa y plazo de la deuda.
- Impuesto corporativo.
- Tratamiento de ganancias de capital, si aplica.
- IVA y tratamiento de su recuperación.
- Vida útil tributaria y método de depreciación.
- Seguros y costos administrativos.
- Costos de desarrollo, permisos y conexión.
- Incentivos, exenciones o mecanismos regulatorios aplicables.
- Precio de electricidad y estructura tarifaria.
- Costos de transmisión, peajes y cargos del sistema.
- Riesgo cambiario para equipos importados.
- Fuentes oficiales, fecha de vigencia y supuestos de cada parámetro.

Debe distinguirse claramente entre:

- Parámetros macroeconómicos.
- Parámetros tributarios.
- Parámetros de financiamiento.
- Costos tecnológicos locales.
- Costos de conexión y operación del sistema eléctrico.

### 9.4. Configuración chilena

Se recomienda crear archivos separados, por ejemplo:

```text
examples/chile_hybrid_h2/
├── chile_hybrid_h2.yaml
├── driver_config.yaml
├── plant_config.yaml
├── tech_config.yaml
├── run_chile_hybrid_h2.py
└── data/
```

El `plant_config.yaml` contendría los parámetros financieros comunes de Chile. El
`tech_config.yaml` contendría CAPEX, OPEX, vida útil, reemplazos y demás valores específicos
de las tecnologías.

Si varios casos chilenos comparten una configuración financiera, podría incorporarse un
archivo reutilizable en un directorio específico para Chile y cargarlo mediante `!include`,
evitando modificar configuraciones compartidas por los ejemplos originales.

### 9.5. Validación financiera

La adaptación deberá incluir:

- Validación dimensional y de unidades.
- Diferenciación consistente entre tasas reales y nominales.
- Pruebas de resultados financieros conocidos.
- Análisis de sensibilidad.
- Trazabilidad de las fuentes.
- Comparación con evaluaciones de proyectos energéticos chilenos de referencia.

## 10. Archivos previstos para la adaptación

### 10.1. Nuevos archivos recomendados

- Módulo común de lectura y normalización de ERA5.
- Modelo de recurso eólico ERA5.
- Modelo de recurso solar ERA5.
- Tests unitarios e integración para ambos recursos.
- Fixture NetCDF pequeño.
- Documentación de variables y conversiones ERA5.
- Nuevo caso de estudio para Chile.
- Configuración financiera chilena.
- CSV de escenarios, tarifas u otros insumos, si corresponde.

### 10.2. Archivos existentes que podrían requerir cambios acotados

- `h2integrate/core/supported_models.py`: registrar los nuevos modelos ERA5.
- `pyproject.toml`: declarar dependencias ERA5 opcionales.
- `examples/test/test_all_examples.py`: incorporar el caso chileno a las pruebas de
  integración, o crear un test separado.
- `docs/_toc.yml`: enlazar la nueva documentación, si se integra al libro.
- `docs/resource/resource_index.md`: documentar la fuente ERA5.
- Documentación financiera: describir parámetros y supuestos chilenos.

### 10.3. Archivos que no deberían modificarse inicialmente

- Interfaces públicas de `H2IntegrateModel`.
- Firmas de las clases base de recursos.
- Convertidores PySAM solar y eólico.
- Modelos de recursos Open-Meteo, NLR y satelitales.
- Ejemplos y parámetros originales de Estados Unidos.
- Esquemas YAML, salvo que posteriormente se requiera validar claves nuevas de manera
  explícita.

## 11. Secuencia sugerida de trabajo

1. Definir y documentar el contrato de datos ERA5.
2. Preparar un archivo NetCDF mínimo y reproducible de Chile.
3. Implementar el lector común ERA5.
4. Implementar el recurso eólico manteniendo `wind_resource_data`.
5. Implementar el recurso solar manteniendo `solar_resource_data`.
6. Añadir pruebas locales y de integración.
7. Crear un caso chileno mínimo.
8. Recopilar y documentar parámetros financieros de Chile.
9. Configurar el análisis financiero chileno con los modelos existentes.
10. Evaluar si alguna particularidad normativa requiere un modelo financiero adicional.
11. Validar recursos y resultados financieros con referencias independientes.

## 12. Resultado esperado

La adaptación debería permitir seleccionar, desde los mismos archivos YAML utilizados por
H2Integrate, entre recursos originales y recursos ERA5 para Chile. Del mismo modo, los
parámetros financieros estadounidenses y chilenos deberían coexistir como configuraciones
independientes.

El resultado debe conservar el flujo habitual de H2Integrate:

```text
YAML principal
    ├── driver_config
    ├── plant_config
    │   ├── sitios y recursos ERA5
    │   └── parámetros financieros de Chile
    └── tech_config
        ├── tecnologías originales
        └── costos y parámetros locales
```

Así, el fork mantendrá compatibilidad con la librería original y añadirá capacidades
específicas para estudiar sistemas energéticos en Chile mediante extensiones modulares,
trazables y verificables.
