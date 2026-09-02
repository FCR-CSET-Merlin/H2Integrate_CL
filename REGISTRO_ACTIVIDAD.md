# Registro de actividad

Este archivo mantiene la trazabilidad cronológica de las modificaciones realizadas en el
repositorio H2Integrate para Chile. Las fechas y horas se expresan en la zona horaria
`America/Santiago`.

Las entradas deben agregarse sin reemplazar ni eliminar registros anteriores y deben usar
la siguiente estructura:

```markdown
## AAAA-MM-DD HH:MM:SS TZ — Título breve

- **Resumen y propósito:** Descripción concisa de la actividad.
- **Archivos modificados:** Lista de rutas relativas al repositorio.
- **Supuestos o decisiones:** Supuestos, criterios y decisiones relevantes, o `Ninguno`.
- **Verificación:** Pruebas o comprobaciones ejecutadas y sus resultados.
- **Estado:** Completado, parcial o pendiente.
- **Responsable:** Persona o agente que realizó la modificación.
```

No se deben incluir credenciales, información sensible, datasets meteorológicos
descargados ni resultados voluminosos.

## 2026-08-06 14:59:45 -04 — Creación del registro de actividad

- **Resumen y propósito:** Se creó el registro cronológico de modificaciones y se
  incorporó su uso obligatorio en el contexto y en las reglas para agentes.
- **Archivos modificados:** `REGISTRO_ACTIVIDAD.md`,
  `CONTEXTO_ADAPTACION_CHILE.md` y `AGENTS.md`.
- **Supuestos o decisiones:** Se adoptó `America/Santiago` como zona horaria del registro.
  Las inspecciones de solo lectura quedan excluidas, salvo que produzcan una decisión o un
  hallazgo que afecte materialmente al proyecto.
- **Verificación:** Revisión del diff y comprobación del formato documental.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-11 09:54:23 -04 — Incorporación del plan de implementación ERA5-SL

- **Resumen y propósito:** Se añadió al contexto del proyecto una versión resumida del plan
  incremental acordado para implementar la lectura, normalización y validación de datos
  ERA5 Single Levels en H2Integrate_CL.
- **Archivos modificados:** `CONTEXTO_ADAPTACION_CHILE.md` y `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** La primera entrega se limitará a archivos NetCDF mensuales
  locales, resolución horaria, UTC, selección por vecino más cercano y un año completo. No
  se aplicará extrapolación eólica sobre 100 m de forma implícita. Las capacidades remotas y
  el procesamiento masivo se postergan hasta validar la integración local.
- **Verificación:** Revisión del diff, comprobación de formato Markdown y
  `git diff --check`.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-11 17:05:51 -04 — Formalización del contrato técnico ERA5-SL

- **Resumen y propósito:** Se creó el contrato formal de entrada, procesamiento,
  validación, salida y proveniencia para los recursos ERA5 Single Levels, y se incorporó a
  la documentación de recursos.
- **Archivos modificados:** `docs/resource/era5_single_levels_contract.md`,
  `docs/resource/resource_index.md`, `docs/_toc.yml`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Se adoptaron patrones mensuales configurables, UTC,
  resolución horaria, `nearest` con advertencia configurable desde 15 km, un único miembro
  determinista, FDIR como radiación directa horizontal y compatibilidad de unidades con
  PySAM. Para bujes sobre 100 m se usará el dato de 100 m con advertencia y sin
  extrapolación. Las listas explícitas, la cobertura estricta del año calendario, la
  interpolación espacial y la extrapolación eólica quedan registradas como mejoras futuras.
- **Verificación:** Revisión del diff, comprobación de enlaces documentales, validación YAML
  de `docs/_toc.yml` y `git diff --check`, todas correctas. La compilación documental no se
  ejecutó porque `jupyter-book` no está instalado en el entorno; no se generaron artefactos
  en el repositorio.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-11 17:26:13 -04 — Dependencias opcionales ERA5 y pruebas de instalación

- **Resumen y propósito:** Se incorporó el extra opcional `era5` para habilitar lectura
  NetCDF4/HDF5 y geometría solar, junto con pruebas de declaración, instalación y operación
  de sus dependencias.
- **Archivos modificados:** `pyproject.toml`,
  `h2integrate/resource/test/test_era5_optional_dependencies.py`,
  `docs/resource/era5_single_levels_contract.md`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** El extra contiene `xarray`, `h5netcdf` y `pvlib`, permanece
  separado de la instalación base y se incluye en el extra `all`. Los timestamps NetCDF de
  prueba se almacenan sin zona embebida y se interpretan como UTC.
- **Verificación:** Instalación editable `.[era5]` correcta; 3 pruebas unitarias aprobadas;
  apertura correcta de un NetCDF ERA5 real con `h5netcdf`; compilación sintáctica correcta.
  Ruff no se ejecutó porque no está instalado en el entorno actual.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 11:04:02 -04 — Implementación del lector común ERA5-SL

- **Resumen y propósito:** Se implementó el lector común de archivos ERA5 Single Levels
  mensuales para seleccionar un sitio por vecino más cercano y entregar una serie anual
  validada, reutilizable por los futuros recursos eólico y solar.
- **Archivos modificados:** `h2integrate/resource/era5_reader.py`,
  `h2integrate/resource/test/test_era5_reader.py`,
  `docs/resource/era5_single_levels_contract.md` y `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** El lector acepta patrones relativos configurables, exige doce
  archivos por categoría, un miembro determinista, un `expver` homogéneo, grillas idénticas
  y frecuencia horaria UTC. La advertencia de distancia `nearest` conserva el valor
  predeterminado configurable de 15 km. Las transformaciones meteorológicas quedan fuera de
  esta capa.
- **Verificación:** 9 pruebas ERA5 aprobadas; lectura de los 36 NetCDF reales correcta,
  produciendo 8.760 horas y 13 variables para el sitio solicitado; sintaxis Python y
  `git diff --check` correctos.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 12:02:23 -04 — Transformaciones eólicas comunes ERA5-SL

- **Resumen y propósito:** Se implementó una transformación reutilizable del dataset anual
  puntual ERA5 al contrato `wind_resource_data` consumido por los convertidores eólicos de
  H2Integrate.
- **Archivos modificados:** `h2integrate/resource/era5_wind.py`,
  `h2integrate/resource/test/test_era5_wind.py`,
  `docs/resource/era5_single_levels_contract.md`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Se aplican las fórmulas vectoriales acordadas a 10 y 100 m,
  temperatura K a °C, presión Pa a atm y elevación `z / 9.80665`. La elevación configurada
  prevalece y no modifica la presión. Las calmas conservan el resultado determinista de la
  fórmula angular, pero su dirección no tiene significado físico. La advertencia para
  bujes sobre 100 m se reserva para la integración que conoce la altura solicitada.
- **Verificación:** 18 pruebas ERA5 aprobadas. Los 24 NetCDF reales eólicos y auxiliares
  produjeron 8.760 registros; la salida fue aceptada por los formateadores existentes de
  PySAM (matriz 8.760 × 4 finita) y FLORIS (8.760 estados). Compilación sintáctica y
  `git diff --check` correctos. Ruff no está instalado en el entorno actual.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 12:37:35 -04 — Transformaciones solares comunes ERA5-SL

- **Resumen y propósito:** Se implementó la transformación reutilizable del dataset puntual
  ERA5 al contrato `solar_resource_data`, incluyendo irradiancia, variables meteorológicas,
  geometría solar, controles físicos y proveniencia.
- **Archivos modificados:** `h2integrate/resource/era5_solar.py`,
  `h2integrate/resource/test/test_era5_solar.py`,
  `docs/resource/era5_single_levels_contract.md`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Las acumulaciones son horarias y terminan en `valid_time`; la
  geometría se calcula 30 minutos antes con `pvlib`. DNI se anula desde un cenit configurable
  de 88° por defecto. `fdir > ssrd` se limita en la salida con advertencia, sin modificar el
  dataset fuente. La presión se entrega en mbar y la elevación configurada prevalece sobre
  `z / 9.80665` sin corregir la presión.
- **Verificación:** 28 pruebas ERA5 aprobadas. La transformación de los 36 NetCDF reales
  produjo 8.760 registros finitos: GHI máximo 1.221,16 W/m², DHI 490,79 W/m² y DNI
  1.113,18 W/m²; no hubo correcciones `fdir > ssrd` y 420 registros directos se anularon por
  el control cenital. `PySAM.Pvwattsv8` aceptó el recurso formateado. Sintaxis Python,
  longitud de línea, espacios finales y `git diff --check` correctos; Ruff no está instalado.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 14:48:16 -04 — Componentes OpenMDAO ERA5-SL

- **Resumen y propósito:** Se crearon y registraron los componentes
  `ERA5SingleLevelsWindResource` y `ERA5SingleLevelsSolarResource` para integrar el lector y
  las transformaciones ERA5 con el grafo OpenMDAO de H2Integrate.
- **Archivos modificados:** `h2integrate/resource/era5_resource.py`,
  `h2integrate/resource/test/test_era5_resource_components.py`,
  `h2integrate/core/supported_models.py`,
  `h2integrate/converters/wind/wind_plant_baseclass.py`,
  `docs/resource/era5_single_levels_contract.md`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Los componentes leen exclusivamente archivos locales y exigen
  `dt = 3600` segundos y UTC. La ubicación es fija por defecto; si se habilita el cambio
  espacial, el recurso se recalcula solamente al cambiar las coordenadas. La elevación del
  sitio prevalece sobre ERA5. La política de buje superior se implementó en el convertidor
  eólico:
  utiliza la máxima altura disponible, emite advertencia y no extrapola.
- **Verificación:** 76 pruebas y 88 subpruebas aprobadas, incluyendo los recursos ERA5 y los
  convertidores PySAM/FLORIS existentes. Los componentes procesaron los 36 NetCDF reales y
  entregaron 8.760 registros; PySAM eólico recibió una matriz 8.760 × 4, FLORIS recibió
  8.760 estados y `PySAM.Pvwattsv8` aceptó los 17 campos solares. Las seis advertencias de la
  suite provienen de una operación interna preexistente de FLORIS. Sintaxis y
  `git diff --check` correctos; Ruff no está instalado.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 15:33:09 -04 — Prueba integral híbrida ERA5-SL con PySAM

- **Resumen y propósito:** Se incorporó una configuración YAML completa que conecta recursos
  ERA5-SL eólico y solar con tecnologías PySAM y combina ambos perfiles eléctricos en el
  grafo OpenMDAO de H2Integrate.
- **Archivos modificados:** Los cuatro YAML de
  `h2integrate/resource/test/era5_hybrid_config/`,
  `h2integrate/resource/test/test_era5_resource_components.py`,
  `docs/resource/era5_single_levels_contract.md`, `CONTEXTO_ADAPTACION_CHILE.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** La simulación usa 2023, 8.760 pasos horarios y UTC. La ruta de
  recursos se representa mediante un marcador y sólo se sustituye en una copia temporal.
  El fixture solar sintético respeta el ciclo diurno y la geometría en el centro de la hora
  acumulada. El combinador y los cables de prueba no aplican pérdidas.
- **Verificación:** Las 36 pruebas de recursos ERA5 fueron aprobadas, incluida la ejecución
  anual YAML → recursos ERA5 → PySAM eólico/FV → combinador. También aprobaron 36 pruebas y
  58 subpruebas de los convertidores PySAM eólico y solar. La misma configuración procesó
  los 36 NetCDF reales: 8.760 horas, 479.826,79 kWh eólicos, 10.484.520,09 kWh solares y
  10.964.346,88 kWh combinados; el error máximo de balance fue 4,55 × 10⁻¹³ kW.
  `git diff --check`, espacios finales y longitud de línea correctos. Black y Ruff no están
  instalados en el entorno.
- **Estado:** Completado; permanecen pendientes las comparaciones independientes del paso 8.
- **Responsable:** Codex.

## 2026-08-12 16:28:16 -04 — Publicación local del gráfico híbrido ERA5-SL

- **Resumen y propósito:** Se copió el gráfico previamente generado desde el directorio
  temporal del sistema a una ubicación visible dentro del repositorio para facilitar su
  consulta desde VS Code.
- **Archivos modificados:** `outputs/era5_hybrid/era5_hybrid_generation_profiles.png` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** El gráfico es un resultado reproducible de simulación y se
  mantiene fuera del control de versiones mediante la regla `output*` de `.gitignore`.
- **Verificación:** PNG RGBA válido de 2.578 × 1.618 píxeles y 712.134 bytes; la ruta de
  salida fue confirmada como ignorada por Git.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 16:37:12 -04 — Simulación híbrida ERA5-SL en (-23,6°, -70,2°)

- **Resumen y propósito:** Se ejecutó el mismo caso híbrido PySAM eólico/FV para las
  coordenadas solicitadas y se generó un gráfico anual y de detalle horario.
- **Archivos modificados:**
  `outputs/era5_hybrid/era5_hybrid_generation_profiles_lat_m23p6_lon_m70p2.png` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Se modificaron únicamente latitud y longitud; se conservaron
  dos aerogeneradores de 3 MW, 5 MWdc FV y la elevación configurada de 1.250 m. El punto
  `nearest` fue (-23,50°, -70,25°), a 12,23 km. Su elevación ERA5 es 717,48 m, diferencia
  que debe revisarse antes de tratar el caso como representativo del sitio.
- **Verificación:** Simulación de 8.760 horas completada. Se obtuvieron 365,07 MWh eólicos,
  9.529,35 MWh solares y 9.894,42 MWh combinados; factores de planta de 0,69 % eólico y
  26,11 % solar AC. El error máximo del balance fue 4,55 × 10⁻¹³ kW. PNG RGBA válido de
  2.578 × 1.618 píxeles y 827.559 bytes, ignorado por Git.
- **Estado:** Completado.
- **Responsable:** Codex.

## 2026-08-12 16:58:34 -04 — Cierre de jornada de integración ERA5-SL

- **Resumen y propósito:** Se consolidaron en un commit los componentes OpenMDAO ERA5-SL,
  su registro en H2Integrate, la política eólica para alturas superiores a 100 m, la prueba
  híbrida mediante YAML y la documentación asociada.
- **Archivos modificados:** `h2integrate/resource/era5_resource.py`,
  `h2integrate/resource/test/test_era5_resource_components.py`, los cuatro YAML de
  `h2integrate/resource/test/era5_hybrid_config/`,
  `h2integrate/converters/wind/wind_plant_baseclass.py`,
  `h2integrate/core/supported_models.py`, `docs/resource/era5_single_levels_contract.md`,
  `CONTEXTO_ADAPTACION_CHILE.md` y `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Los resultados gráficos, los NetCDF y los directorios de
  reportes OpenMDAO permanecen fuera del control de versiones. El trabajo continuará en la
  misma rama de funcionalidad en la próxima jornada.
- **Verificación:** Se revisaron el diff completo, los archivos nuevos y las exclusiones de
  Git. Las verificaciones finales de pruebas y formato se ejecutaron antes del commit.
- **Estado:** Jornada cerrada; quedan pendientes las validaciones independientes indicadas
  en el paso 8 y las optimizaciones del paso 9.
- **Responsable:** Codex.

## 2026-08-21 11:10:27 -04 — Incorporación de catálogo JSON de aerogeneradores

- **Resumen y propósito:** Se incorporó al control de versiones el catálogo de 67 archivos
  JSON de modelos de aerogeneradores proporcionado por el usuario, destinado a ampliar las
  curvas de potencia disponibles para evaluaciones eólicas y casos de validación como el
  Parque Eólico Totoral.
- **Archivos modificados:** Los 67 archivos JSON nuevos de
  `resource_files/wombat_library/turbines/` y `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Las magnitudes de velocidad y potencia se interpretan como
  m/s y W, respectivamente, de acuerdo con la estructura y escala de los datos. En esta
  actividad se validó la consistencia interna del catálogo, pero no su procedencia técnica,
  licencia ni correspondencia con curvas certificadas de fabricantes. Los CSV meteorológicos
  de `resource_files/wind/` permanecen excluidos por `.gitignore` y no se incorporan al commit,
  en cumplimiento de la política de no versionar datasets descargados. Se normalizaron los
  finales de línea de los JSON de CRLF a LF, sin alterar sus datos.
- **Verificación:** Los 67 archivos se decodificaron correctamente como JSON; todos contienen
  `name`, `rated_power`, `cut_in`, `rated_speed`, `wind_speeds` y `power`; los nombres son
  únicos; las curvas tienen longitudes coincidentes, valores numéricos finitos, velocidades
  estrictamente crecientes y potencias no negativas. El catálogo normalizado suma 87.106 bytes.
- **Resultado:** Catálogo válido para su incorporación como datos de referencia; no se
  modificaron interfaces públicas ni dependencias.
- **Estado:** Completado y preparado para commit.
- **Responsable:** Codex.

## 2026-08-24 11:09:19 -04 — Comparación eólica multifuente del Parque Eólico Taltal

- **Resumen y propósito:** Se simuló la generación horaria y diaria del Parque Eólico Taltal
  durante 2015 a partir de velocidades a 100 m del Explorador Eólico (WRF), ERA5, Sup3rWind y
  MERRA-2, y se comparó con la generación bruta diaria proporcionada por el usuario y atribuida
  a la CNE.
- **Archivos modificados:** Se generaron siete resultados ignorados por Git en
  `resource_files/wind/taltal_2015_comparison/` (cuatro CSV y tres PNG), y se actualizó
  `REGISTRO_ACTIVIDAD.md`. Los dos archivos meteorológicos de entrada no fueron modificados.
- **Supuestos o decisiones:** La referencia `V12/3000` se interpretó como Vestas V112/3000,
  coherente con la capacidad informada de 33 unidades de 3 MW (99 MW). Se utilizó la curva
  `V112_3000.json`, normalizada de 3,075 MW a 3 MW por unidad, y las velocidades a 100 m sin
  extrapolación. La simulación representa generación bruta ideal, sin pérdidas de estela,
  disponibilidad o eléctricas y sin corrección de densidad del aire. Los días se agregaron en
  UTC. El archivo conjunto tiene 8.754 horas; sus seis horas faltantes no se imputaron y la
  energía anual comparable se anualizó desde la potencia media. La columna de generación de
  Renewables.Ninja no se usó porque corresponde a una V90/2000; MERRA-2 se convirtió desde su
  columna de velocidad con la misma curva V112/3000 aplicada a las demás fuentes.
- **Verificación:** Se confirmaron 365 observaciones CNE (267,323 GWh; factor de planta
  30,82 %), límites horarios simulados de 0 a 99 MW, 8.754 horas sin nulos para WRF/ERA5/
  Sup3rWind y 8.760 para MERRA-2. Los CSV cubren 2015 y los tres PNG se abrieron y verificaron
  correctamente. Se compararon sólo días de 24 horas: 363 para las primeras tres fuentes y
  365 para MERRA-2.
- **Resultado:** Sup3rWind presentó la mejor aproximación conjunta: 293,714 GWh anualizados,
  factor de planta 33,87 %, error energético de +9,9 % y correlación diaria de Pearson 0,777.
  WRF sobreestimó (+57,7 %), ERA5 subestimó (-79,1 %) y MERRA-2 subestimó (-29,7 %).
- **Estado:** Completado como comparación exploratoria no calibrada; las pérdidas, densidad
  del aire y convención temporal de la serie CNE deben formalizarse antes de usar los valores
  como validación definitiva.
- **Responsable:** Codex.

## 2026-08-24 14:21:24 -04 — Simulación Sup3rWind de tres parques eólicos chilenos

- **Resumen y propósito:** Se simuló la generación horaria, diaria, mensual y el factor de
  planta de Monte Redondo, Negrete y Valle de los Vientos durante 2015 usando Sup3rWind, y se
  compararon los resultados con las series diarias suministradas por el usuario y atribuidas
  a la CNE.
- **Archivos modificados:** Se leyeron sin modificar tres CSV meteorológicos ignorados por Git
  en `resource_files/wind/`; se generaron 23 CSV y PNG ignorados en
  `resource_files/wind/sup3rwind_parks_2015_comparison/`; se actualizó
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Se modelaron 24 V90/2000 de 2 MW en Monte Redondo, 10 V126/3450
  de 3,45 MW como proxy de las V136/3450 de Negrete y 45 V90/2000 de 2 MW como proxy de las
  V100/2000 informadas para Valle de los Vientos. El encabezado Sup3rWind de este último indica
  V110/2000, discrepancia conservada como antecedente. Las curvas se normalizaron a la potencia
  nominal y, cuando terminan antes de la velocidad de corte, se mantuvo su última potencia hasta
  25 m/s y se supuso generación nula sobre ese valor. El escenario principal usa directamente
  el viento a 100 m para conservar comparabilidad con Taltal. Como sensibilidad física se aplicó
  densidad seca `rho=p/(R*T)` y velocidad equivalente `v*(rho/1,225)^(1/3)` con presión a 0 m y
  temperatura a 2 m. No se modelaron estelas, disponibilidad ni pérdidas eléctricas; la
  agregación diaria es UTC.
- **Verificación:** Cada recurso contiene 8.760 horas completas, sin duplicados ni nulos; las
  distancias a los nodos son 0,601 km, 0,210 km y 0,791 km. Las tres series CNE contienen 365
  días y suman 99,601 GWh, 94,114 GWh y 232,216 GWh. Se comprobaron límites de generación,
  nueve filas de métricas, 365 días, 12 meses y ausencia de nulos por parque; los diez PNG se
  abrieron correctamente.
- **Resultado:** Sin corrección de densidad, los errores anuales fueron +61,1 % en Monte
  Redondo, +68,4 % en Negrete y +15,0 % en Valle de los Vientos. Con corrección fueron +59,5 %,
  +68,0 % y -3,8 %, respectivamente. Las correlaciones diarias ajustadas fueron 0,830, 0,822 y
  0,406. La densidad sólo cambió materialmente el resultado del emplazamiento de mayor altitud.
- **Estado:** Completado como comparación exploratoria no calibrada. Deben confirmarse modelos
  exactos, alturas de buje, convención temporal CNE y pérdidas antes de una validación definitiva.
- **Responsable:** Codex.

## 2026-08-25 14:59:03 -04 — Simulación Sup3rWind 2023 de cuatro parques eólicos

- **Resumen y propósito:** Se simuló y comparó con generación bruta CNE la producción horaria,
  diaria, mensual y el factor de planta de La Flor, Malleco, Renaico y San Gabriel durante 2023.
- **Archivos modificados:** Se leyeron sin modificar cuatro CSV Sup3rWind ignorados en
  `resource_files/wind/`; se generaron 32 CSV y PNG ignorados en
  `resource_files/wind/sup3rwind_parks_2023_comparison/`; se actualizó
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** Se adoptaron como capacidades principales las potencias nominales
  informadas: 32,4 MW para La Flor, 273 MW para Malleco, 88 MW para Renaico y 183 MW para San
  Gabriel. En La Flor y Malleco difieren en +4,35 % y +2,77 % de `n_turbinas × 3,45 MW`. Se
  sumaron las series CNE de Malleco Norte y Sur. Se emplearon V126/3450, V90/2000 y N131/3000
  como proxies acordados, normalizando sus curvas a la capacidad del parque. Se usó viento a
  100 m, meseta de potencia hasta 25 m/s y corte sobre esa velocidad. Se evaluó el escenario
  directo y una sensibilidad de densidad con `rho=p/(R*T)` y `v_eq=v*(rho/1,225)^(1/3)`. No se
  incluyeron estelas, disponibilidad ni pérdidas eléctricas; la agregación diaria es UTC. Para
  aislar parcialmente las indisponibilidades se calcularon métricas adicionales sobre días CNE
  mayores que cero.
- **Verificación:** Los cuatro recursos contienen 8.760 horas completas sin nulos ni duplicados;
  las distancias a los nodos son 0,329, 0,960, 1,085 y 1,160 km. Las cinco series CNE contienen
  365 días: 72,812 GWh La Flor, 360,861 GWh Malleco Sur, 325,229 GWh Malleco Norte, 226,455 GWh
  Renaico y 471,857 GWh San Gabriel; Malleco totaliza 686,090 GWh. Se verificaron 12 filas de
  métricas, 8.760 horas, 365 días y 12 meses por parque, ausencia de nulos, límites de potencia
  y apertura correcta de los 13 PNG.
- **Resultado:** En el escenario ajustado por densidad, La Flor produjo 169,109 GWh (FP 59,58 %,
  error +132,3 %, r diario 0,621 y r en días activos 0,764); Malleco 1.215,675 GWh (FP 50,83 %,
  +77,2 %, r 0,781); Renaico 416,626 GWh (FP 54,05 %, +84,0 %, r 0,792); y San Gabriel
  943,340 GWh (FP 58,85 %, +99,9 %, r 0,822). La densidad tuvo efecto menor en estos cuatro
  sitios. Sup3rWind capturó parte de la temporalidad, pero sobreestimó sistemáticamente la
  energía y requiere calibración antes de un uso tecnoeconómico.
- **Estado:** Completado como comparación exploratoria no calibrada. Deben confirmarse pérdidas,
  disponibilidad, alturas de buje, modelos exactos y convención temporal CNE.
- **Responsable:** Codex.

## 2026-08-25 16:12:42 -04 — Consolidación de reportes de validación eólica

- **Resumen y propósito:** Se elaboraron dos reportes técnicos versionables para consolidar los
  benchmarks eólicos ejecutados con ERA5 Single Levels y Sup3rWind durante 2015 y 2023. Se
  documentaron metodología, supuestos, métricas, limitaciones, diagnóstico e implicancias para
  análisis tecnoeconómicos.
- **Archivos modificados:** Se crearon
  `docs/resource/reporte_validacion_eolica_era5.md` y
  `docs/resource/reporte_validacion_eolica_sup3rwind.md`; se añadieron sus enlaces a
  `docs/resource/resource_index.md`; se actualizó `REGISTRO_ACTIVIDAD.md`. No se modificaron
  datos meteorológicos, resultados de simulación ni código fuente.
- **Supuestos o decisiones:** El reporte ERA5 sólo califica como evidencia de subestimación los
  cuatro casos con referencia independiente; las pruebas de integración sin benchmark se
  identifican por separado. El reporte Sup3rWind adopta el escenario ajustado por densidad para
  siete casos y el escenario directo disponible para Taltal. Se conservaron las convenciones
  UTC, las curvas proxy y las capacidades empleadas en cada simulación, explicitando sus
  limitaciones y sin interpretar correlación como equivalencia energética.
- **Verificación:** Se contrastaron las cifras publicadas de los 12 casos con tres CSV de
  métricas y cuatro JSON fuente. Se comprobaron presencia de indicadores clave, contenido no
  vacío, finales de línea y ausencia de espacios finales. También se verificaron los enlaces
  documentales y `git diff --check`.

## 2026-09-02 11:43:13 -04 — Integración local Sup3rWind y caso híbrido NSRDB Chile

- **Resumen y propósito:** Se implementó un componente de recurso eólico local para CSV de
  Sup3rWind y se configuró un caso híbrido horario Sup3rWind–NSRDB en Monte Redondo, Chile.
- **Archivos modificados:** `h2integrate/resource/wind/sup3rwind.py`,
  `h2integrate/resource/wind/test/test_sup3rwind.py`,
  `h2integrate/core/supported_models.py`, los cuatro archivos de
  `examples/chile_sup3rwind_nsrdb/`, `docs/resource/resource_index.md` y
  `REGISTRO_ACTIVIDAD.md`.
- **Supuestos o decisiones:** El adaptador es local y no descarga Sup3rWind; admite el CSV
  compacto usado en las validaciones chilenas y el formato tipo Wind Toolkit. El contrato es
  horario UTC y elimina el 29 de febrero salvo configuración contraria. El caso usa 2015 y las
  coordenadas de Monte Redondo; NSRDB se representa con GOES Aggregated PSM v4. Los parámetros
  tecnológicos y financieros del ejemplo 15 son sólo ilustrativos y no están calibrados para
  Chile ni para el parque real.
- **Verificación:** Se añadieron pruebas de registro, lectura de ambos formatos, conversión de
  presión Pa a atm, metadatos, rechazo de resolución no horaria y ausencia de descarga implícita.
  Se obtuvieron 9 pruebas y 13 subpruebas aprobadas; también se verificaron sintaxis, carga YAML,
  longitudes de línea y `git diff --check`. Ruff no estaba instalado en el entorno del proyecto.
- **Resultado:** H2Integrate puede consumir recursos locales Sup3rWind mediante
  `Sup3rWindResource` y dispone de un caso híbrido reproducible al instalar los dos datasets o
  configurar las credenciales NSRDB.
- **Estado:** Completado para integración meteorológica; pendiente calibrar tecnologías, costos
  y pérdidas para un caso tecnoeconómico representativo de Chile.
- **Responsable:** Codex.

## 2026-09-02 12:20:36 -04 — Dos casos híbridos DOE conservadores para Chile

- **Resumen y propósito:** Se adaptó el DOE financiero de `h2v_tea`, commit
  `83697595971ba01d1dd3b97ed9ada174917e395c`, para evaluar por separado los sitios de
  Antofagasta `(-22.2812687, -69.5698745)` y Magallanes
  `(-52.8502704, -70.9575804)` con recursos Sup3rWind y NSRDB de 2023.
- **Archivos modificados:** Se creó `examples/chile_hybrid_h2_doe/` con configuraciones comunes,
  dos configuraciones de sitio, 72 diseños DOE, escenario financiero, manifiesto, descargador,
  ejecutor, documentación y exclusiones de datos/resultados. Se creó
  `examples/test/test_chile_hybrid_h2_doe.py`, se sustituyó el enlace en
  `docs/resource/resource_index.md` y se retiró el caso provisional
  `examples/chile_sup3rwind_nsrdb/`.
- **Supuestos o decisiones:** Cada sitio evalúa cuatro tamaños FV, tres cantidades de turbinas
  de 6 MW y seis tamaños PEM, para 72 diseños por sitio y 144 en total. Se conservó el DOE de
  referencia sin la variante de 35 clústeres. El escenario usa USD 2025, descuento de 10%,
  deuda/patrimonio 55/45, interés de 8,5%, impuesto de 27%, inflación de 3% y depreciación lineal
  de 15 años. No se modelan red, batería, almacenamiento, agua, compresión, transporte,
  oxígeno, incentivos ni créditos de carbono.
- **Verificación:** Finalizaron correctamente 13 tests y 13 subpruebas del DOE, del adaptador
  Sup3rWind y de las herramientas eólicas relacionadas. Se validaron los esquemas YAML, las 72
  combinaciones únicas, la fusión financiera, la lectura de un CSV Sup3rWind anual real y el
  rechazo seguro de un manifiesto sin publicar.
- **Resultado:** Los dos casos y el flujo de descarga pública quedan implementados. El
  descargador exige URL HTTPS, tamaño y SHA-256 reales para los cuatro CSV y no usa credenciales
  NLR.
- **Estado:** Implementación estructural completada; bloqueada la ejecución meteorológica y la
  publicación del manifiesto hasta obtener, validar y adjuntar los cuatro CSV a una Release.
- **Responsable:** Codex.

## 2026-09-02 15:20:20 -04 — Descargador reproducible NLR para Sup3rWind y NSRDB

- **Resumen y propósito:** Se cerró la brecha de adquisición directa de datos meteorológicos
  implementando un CLI genérico para descargar recursos puntuales horarios de Sup3rWind South
  America v1.0.0 y NSRDB GOES Aggregated PSM v4 desde `developer.nlr.gov`.
- **Archivos modificados:** Se crearon
  `h2integrate/tools/download_nlr_resources.py`,
  `h2integrate/tools/test/test_download_nlr_resources.py` y
  `docs/resource/nlr_resource_downloader.md`; se actualizaron `.gitignore`,
  `docs/resource/resource_index.md`, `examples/chile_hybrid_h2_doe/README.md` y este registro.
- **Supuestos o decisiones:** El contrato fija intervalos de 60 minutos en UTC, excluye el 29 de
  febrero de forma predeterminada y solicita de manera secuencial cada recurso–año con una pausa
  configurable de 1,1 segundos. Sup3rWind admite las alturas publicadas de 10, 40, 80, 100,
  120, 160 y 200 m; los casos chilenos solicitan 100 y 120 m. Los años se validan como 2005–2024
  para Sup3rWind y 1998–2025 para NSRDB. Se conservaron `NLR_API_KEY` y `NLR_API_EMAIL` como
  convención de credenciales del repositorio. Los CSV se almacenan byte por byte sin modificar y
  sus JSON laterales omiten clave y correo. `data/raw/` queda ignorado por Git.
- **Verificación:** Se añadieron 21 pruebas unitarias sin acceso a red para WKT y precisión de
  coordenadas, validación de límites, años y alturas, parámetros específicos de cada API,
  respuestas 200/400/500, timeout, contenido no CSV, escritura exacta y atómica, protección
  contra sobrescritura, metadatos sin secretos y solicitudes separadas por recurso y año.
  El conjunto dirigido del descargador, adaptador Sup3rWind y DOE completó 30 pruebas; también
  pasaron la compilación, la revisión de longitud de líneas y `git diff --check`. Ruff no está
  instalado en el entorno `h2integrate`.
- **Resultado:** El mantenedor puede generar de forma trazable los cuatro CSV de 2023 para
  `site_01_antofagasta` y `site_02_magallanes`. La publicación de esos archivos en una Release y
  la incorporación de sus URL/checksums al manifiesto siguen siendo el paso necesario para que
  usuarios sin credenciales ejecuten los casos.
- **Estado:** Descarga directa implementada y probada; publicación de assets pendiente.
- **Responsable:** Codex.

## 2026-09-02 16:23:50 -04 — Recursos 2023 Full Disc y manifiesto publicable para DOE Chile

- **Resumen y propósito:** Por autorización explícita se sustituyó NSRDB GOES Aggregated por
  GOES Full Disc PSM v4 en los dos casos híbridos de Antofagasta y Magallanes. Se descargaron,
  validaron y prepararon para publicación los cuatro CSV horarios de 2023 y se completó el
  manifiesto de assets para la Release `chile-weather-2023-v1`.
- **Archivos modificados:** `h2integrate/tools/download_nlr_resources.py` y su prueba,
  `examples/chile_hybrid_h2_doe/resource_manifest.yaml`, ambos `plant_config.yaml`, el README
  del ejemplo, `examples/test/test_chile_hybrid_h2_doe.py`,
  `h2integrate/core/pose_optimization.py`, `h2integrate/core/test/test_recorder.py` y este
  registro. Los cuatro CSV y sus JSON de procedencia se almacenaron en rutas ignoradas bajo
  `data/raw/` y `examples/chile_hybrid_h2_doe/data/`; no se versionaron datos ni credenciales.
- **Supuestos o decisiones:** Los dos sitios usan 2023, UTC, 60 minutos y 8.760 registros. La
  consulta GOES Aggregated devolvió ausencia de datos para ambas coordenadas, mientras que GOES
  Full Disc respondió datos puntuales válidos; se adopta por tanto el endpoint Full Disc,
  disponible para 2018--2025. La Release prevista contendrá sólo los cuatro CSV sin secretos;
  cada URL del manifiesto incluye el tag `chile-weather-2023-v1` y permanece inaccesible hasta
  su publicación. La ruta de salida del driver continúa siendo texto, como exige su esquema;
  el registrador la convierte internamente a `Path` al crear una carpeta nueva.
- **Verificación:** Se validaron los cuatro CSV con 8.760 horas únicas desde 2023-01-01 00:00
  hasta 2023-12-31 23:00 UTC, resolución de 60 minutos y cero celdas nulas. Los SHA-256 y
  tamaños del manifiesto coincidieron con los archivos: Antofagasta Sup3rWind 1.200.722 bytes,
  Full Disc 615.304 bytes; Magallanes Sup3rWind 1.201.922 bytes, Full Disc 611.302 bytes.
  `download_resources.py --verify-only`, compilación de módulos y `git diff --check` pasaron.
  Los dos modelos construyen como `H2IntegrateModel` bajo el caso financiero `conservative`.
  Las pruebas dirigidas completaron 31 aprobadas; sólo quedó una advertencia externa de
  deprecación de `h5pyd`.
- **Resultado:** Los dos casos quedan configurados con Sup3rWind y GOES Full Disc, recursos
  locales verificados y manifiesto íntegro listo para una Release pública descargable sin cuenta
  NLR. La corrección del registrador elimina el fallo al crear una carpeta de salida inexistente
  especificada como texto.
- **Estado:** Preparado para publicar la Release; pendiente autorización explícita para commit y
  push de los cambios versionados antes de hacer pública una Release asociada al código.
- **Responsable:** Codex.
