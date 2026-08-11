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
