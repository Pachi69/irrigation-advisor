# Diseño HU-S2-03 — Recomendación en mm, m³ y tiempo

Documento de diseño (target) de la HU-S2-03. Se valida antes de programar; al terminar
se reconcilian `er-diagram.md`, `arquitectura.md` y `referencias.md`.

> **Revisión junio 2026 (post-implementación):** el caudal pasó a ser **opcional** (sin
> default 1,5 L/s/ha — ver §6), la eficiencia de aspersión es **0,85** (FAO-56) y la
> confirmación de riego acepta **tiempo o volumen (m³)** (ver §4.4). Las secciones afectadas
> están actualizadas más abajo.

Fuentes: `docs/historias-usuario/sprint-2.md`, `docs/entrevistas/entrevista-finca-morgan-2026-05.md`.

---

## 1. Problema y objetivo

El sistema calcula la recomendación en **lámina neta (mm)** — la salida natural del balance
FAO-56 (= el déficit a reponer). Pero el productor opera en **tiempo de riego** (recibe la
orden en horas) y le sirve también el **volumen (m³)**. La HU pide entregar las tres unidades
y, recíprocamente, **aceptar la confirmación de riego en cualquiera de ellas**, normalizándola
a mm para el balance.

Esto se apoya en datos que ya viven en el sector (HU-S2-01): `area_ha`, `flow_rate_ls_ha`
(dotación) e `irrigation_type` (del que se deriva la eficiencia).

---

## 2. Neto vs bruto (decisión clave)

- **Lámina neta (mm):** agua que efectivamente infiltra y reduce el déficit. Es lo que usa el
  balance hídrico. La recomendación se calcula en neto.
- **Volumen y tiempo (bruto):** agua que el sistema debe *entregar*, mayor que la neta porque
  el riego pierde por escurrimiento/percolación. Se obtiene dividiendo por la **eficiencia**.

**Decisión: volumen y tiempo se expresan en BRUTO**, para que las tres unidades representen la
**misma cantidad de agua** de forma consistente entre sí:

```
volumen_bruto (m³) = caudal_total (L/s) × tiempo (s) / 1000
```

Si el volumen fuera neto y el tiempo bruto, no cuadrarían (`caudal × tiempo ≠ volumen`) y el
productor se confundiría. El tiempo manda (es lo que opera); el volumen lo acompaña en la misma
base bruta.

**Eficiencia por método de riego** (FAO-56; vive en `app/calculation/irrigation.py`):

| `irrigation_type` | eficiencia |
|---|---|
| aspersion | 0,85 (FAO-56: aspersión/microaspersión 85–90 %) |
| superficial | 0,6 |

El productor NO la ingresa: se deriva del método (decidido en HU-S2-01).

---

## 3. Fórmulas

`area_ha` = superficie del sector · `flow` = `flow_rate_ls_ha` (dotación, L/s/ha) ·
`eff` = eficiencia · 1 mm sobre 1 ha = 10 m³ = 10.000 L.

### Directas (recomendación: lámina neta mm → unidades brutas)

```
volumen_m3 = lamina_mm × area_ha × 10 / eff
tiempo_min = lamina_mm × 10000 / (flow × eff) / 60
```

Derivación del tiempo (la superficie se cancela, por eso no aparece):
```
volumen_bruto_L = lamina_mm × area_ha × 10000 / eff
caudal_total_Ls = flow × area_ha
tiempo_s        = volumen_bruto_L / caudal_total_Ls = lamina_mm × 10000 / (flow × eff)
```

### Inversa (confirmación: tiempo de riego o volumen → lámina neta mm)

La confirmación de riego se hace **en tiempo** (si el sector tiene caudal cargado) o **en volumen
(m³)** (si no lo tiene, ya que sin caudal no hay equivalencia en tiempo). El backend convierte
cualquiera de los dos a mm neto para el balance:

```
lamina_mm desde tiempo  = tiempo_min × 60 × flow × eff / 10000
lamina_mm desde volumen = volumen_m3 × eff / (area_ha × 10)
```

Son las inversas exactas de las directas. El tiempo/volumen ingresado es **bruto** (lo que el
sistema estuvo entregando) y se convierte a la lámina **neta** que efectivamente infiltró.

### Casos borde
- `lamina_mm = 0` (urgencia baja) → volumen y tiempo = 0.
- `area_ha` o `flow` nulos/0 → volumen/tiempo = None (no se puede convertir). Defensivo; un sector
  con recomendación ya fue aprobado y tiene polígono, así que en la práctica no ocurre.

---

## 4. Backend

### 4.1 Nuevo módulo `app/calculation/irrigation.py`
Funciones **puras** (reciben floats, sin acoplar el modelo Sector) + el lookup de eficiencia:
- `efficiency_for(irrigation_type) -> float`
- `mm_to_volume_m3(lamina_mm, area_ha, eff) -> float | None`  (directa, recomendación)
- `mm_to_time_min(lamina_mm, flow, eff) -> float | None`      (directa, recomendación)
- `time_min_to_mm(time_min, flow, eff) -> float`              (inversa, confirmación por tiempo)
- `volume_m3_to_mm(volume_m3, area_ha, eff) -> float`         (inversa, confirmación por volumen)

> Es el único lugar que usa la eficiencia (como se acordó en HU-S2-01: lookup donde se calcula,
> no columna en la DB).

### 4.2 Persistencia (`Recommendation`)
Se agregan dos columnas **nullable** (snapshot inmutable, como `recommended_irrigation_mm`):
- `volume_m3: float | None`
- `time_min: float | None`

Se calculan y persisten en `save_recommendation` en el momento de generar la recomendación.
Por inmutabilidad **no se recalculan** si el productor luego cambia su dotación/eficiencia: la
recomendación vieja conserva los valores con los que se emitió.

### 4.3 `save_recommendation`
Pasa a recibir el `sector` (sus llamadores en `run_backfill` / `run_recommendation_pipeline` ya lo
tienen en memoria). Con `sector.area_ha`, `sector.flow_rate_ls_ha` e `irrigation_type` calcula
volumen y tiempo y los guarda junto a la lámina.

### 4.4 Confirmación en tiempo de riego o volumen
- `IrrigationConfirmationCreate` acepta `applied_time_min` **o** `applied_volume_m3` (validador
  que exige exactamente uno). El productor confirma en tiempo si el sector tiene caudal; si no,
  en volumen (m³).
- El endpoint de confirmación convierte el dato recibido → mm neto (inversa de tiempo o de
  volumen, con los datos del sector) y se lo pasa a `confirm_irrigation`, que sigue guardando
  `applied_irrigation_mm` (neto) como hoy. El balance no cambia: siempre recibe mm netos.
- Si llega `applied_time_min` pero el sector no tiene caudal, el endpoint responde 400 (sin
  caudal no hay equivalencia en tiempo; debe confirmarse por volumen).
- **Decisión:** se guarda solo el mm neto resultante (mínimo necesario para el balance). No se
  persiste el tiempo/volumen original con el que el productor confirmó (YAGNI; si más adelante se
  quiere mostrar "confirmaste 2 h", se agrega).

### 4.5 Respuesta de la API
`RecommendationResponse` y `RecommendationHistoryItem` exponen `volume_m3` y `time_min` (lectura).

---

## 5. Frontend

- **`SectorRecommendation.vue`:** el hero/recomendación muestra las **tres unidades** (mm, m³,
  tiempo). El tiempo se formatea legible ("2 h 30 min").
- **`SectorConfirmations.vue`:** el modal de confirmar riego cambia el input de "lámina (mm)" por
  **"tiempo de riego"** (horas y minutos). La recomendación pendiente se muestra en las tres
  unidades. Al enviar, manda `applied_time_min`.
- Helper de formato de minutos → "Xh Ym" (en `utils/`).

---

## 6. Caudal opcional (sin default)

**Decisión (revisada junio 2026):** el caudal (`flow_rate_ls_ha`) **no tiene valor por defecto**
y es **nullable**. Se descartó el default de 1,5 L/s/ha porque ese número es el **máximo legal
del derecho de riego del DGI** (el agua que entrega el canal), **no la tasa de aplicación del
sistema de riego** del productor. A diferencia de la eficiencia —justificable por FAO-56 según el
método—, el caudal es específico de cada instalación (caudal de la bomba ÷ superficie) y no es
justificable bibliográficamente, así que debe **cargarlo el productor**.

Consecuencias:
- **Sin caudal:** se calcula el **volumen (m³)** y la **lámina (mm)** pero **no el tiempo**
  (`time_min = None`). La UI muestra el volumen como dato principal y avisa "cargá el caudal de tu
  bomba para calcular el tiempo de riego".
- **Confirmación sin caudal:** se hace por volumen (m³) en vez de por tiempo (ver §4.4).
- El formulario de crear/editar sector permite dejar el caudal vacío o quitarlo (PATCH con
  `exclude_unset` para aplicar el `null` explícito).

---

## 7. Cambios por módulo

- `app/calculation/irrigation.py` — **nuevo**: conversión + eficiencia.
- `app/models/recommendation.py` — `volume_m3`, `time_min` nullable.
- `app/services/recommendation.py` — `save_recommendation` recibe `sector`, calcula y persiste;
  `build_recommendation_response` los expone.
- `app/schemas/recommendation.py` — `volume_m3`, `time_min` en Response e History.
- `app/schemas/irrigation_confirmation.py` — `applied_time_min` en Create (en vez de mm).
- `app/api/recommendation.py` — convierte el tiempo a mm neto antes de delegar al service.
- Alembic — migración para las dos columnas nuevas.
- `frontend` — `SectorRecommendation.vue`, `SectorConfirmations.vue`, helper de formato de tiempo.

---

## 8. Documentación a reconciliar al cerrar
- `docs/referencias/referencias.md` → actualizar la sección de conversión: volumen **bruto** y la
  inversa de volumen con eficiencia (hoy figura volumen neto).
- `docs/modelo-datos/er-diagram.md` → `volume_m3`, `time_min` en `recomendacion`.
