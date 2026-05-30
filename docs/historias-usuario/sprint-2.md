# Historias de usuario — Sprint 2

Derivadas de la entrevista a la finca Morgan
(`docs/entrevistas/entrevista-finca-morgan-2026-05.md`).

> Roles del sistema: **productor** y **desarrollador**.
> Prod y dev solo tienen datos de prueba → el esquema se rediseña limpio (sin migración de datos).
> `tipo_suelo` y `alerta` quedan a nivel campo.

---

### HU-S2-01 — Sectores dentro de un campo
**Como** productor **quiero** dividir mi campo en sectores (variedad + polígono propios)
**para** gestionar el riego y las recomendaciones de cada uno por separado.
**Detalle:** nueva entidad `sector`; el balance, el NDVI y la recomendación se calculan por sector.
**Story points:** 13 · **Prioridad:** Alta

### HU-S2-03 — Recomendación en mm, m³ y tiempo
**Como** productor **quiero** ver la recomendación en lámina (mm), volumen (m³) y tiempo de riego
**para** aplicarla como opero (recibo la orden en horas).
**Detalle:** reincorporar `tipo_riego` + `dotación` + `eficiencia` por sector; persistir `volumen_m3` y `tiempo_min` en la recomendación (inmutables).
**Story points:** 5 · **Prioridad:** Alta

### HU-S2-04 — Notificaciones configurables por sector
**Como** productor **quiero** elegir a qué hora y cada cuánto recibo notificaciones por sector
**para** que me lleguen cuando me sirven.
**Detalle:** hora + frecuencia por sector; el cálculo se separa de la notificación; la recomendación se registra siempre pero solo se notifica si la lámina > 0.
**Story points:** 8 · **Prioridad:** Media

### HU-S2-05 — Malla antigranizo por sector
**Como** productor **quiero** indicar si mi sector tiene malla antigranizo y de qué tipo
**para** que la recomendación ajuste la confianza del NDVI/Kc.
**Detalle:** marcar malla + tipo por sector (UX de la pregunta a definir al implementar); regla abierta→NDVI confianza media, densa/color→Kc tabular, sin malla→NDVI normal. Incluye spike de validación emparejada.
**Story points:** 5 · **Prioridad:** Media

### HU-S2-06 — Calibración con historial real
**Como** desarrollador **quiero** comparar lo recomendado vs el historial de riego real de Morgan
**para** validar y calibrar el balance.
**Detalle:** análisis offline por sector (recomendado vs aplicado). Bloqueada hasta recibir el historial.
**Story points:** 3 · **Prioridad:** Baja
