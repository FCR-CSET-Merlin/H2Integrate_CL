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
