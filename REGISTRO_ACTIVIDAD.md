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
