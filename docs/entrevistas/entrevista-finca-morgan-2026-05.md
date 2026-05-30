# Entrevista a campo — Finca familia Morgan (San Rafael, Mendoza)

**Fecha:** mayo 2026
**Contexto:** validación de supuestos del modelo de recomendación de riego (Sprint 1 → planning Sprint 2).
**Cultivo:** vid (varias variedades).

---

## Hallazgos

### 1. El productor conoce su caudal y sus turnos
- Conoce el **caudal de agua** de su derecho de riego.
- Conoce sus **turnos de riego**.
- **Reservorios:** este caso tiene reservorio, pero hay casos que no.
- **Decisión de modelado:** se dejan los turnos de lado. Se asume que el productor
  **dispone del agua y el caudal que le da el permiso** (dotación). Esto mantiene la
  fórmula de conversión basada en dotación (donde el área se cancela).

### 2. Método de riego: ASPERSIÓN (no melga)
- El regador mencionó "melga", pero **melga es riego superficial por tablones inundados**.
- Lo que realmente tienen es **aspersión**: una **manguera con aspersores por hilera**
  (una por fila de vides). El propio productor confirmó que es por aspersión.
- **Corrige el supuesto previo** del MVP, que asumía riego por surco/manto y había
  eliminado el campo `irrigation_type` (commit `f8c6d98`). **Hay que reincorporarlo.**
- **Eficiencia:** aspersión ≈ 0,75–0,85 (vs 0,5–0,7 del riego superficial).

### 3. La finca está dividida en sectores, por variedad
- Cada **sector** tiene una **variedad distinta** de vid y **riego independiente**.
- Distintas variedades consumen distinto: las de **base champagne** usan más agua que
  el **Malbec**.
- Las **duraciones de riego varían por sector** (ej. 15 hs vs 21 hs).
- **Implica un cambio estructural del modelo:** `Campo → Sectores` (cada sector con
  variedad, polígono/superficie, su recomendación y sus notificaciones).

### 4. Notificaciones — el productor quiere controlarlas
- **Frecuencia configurable por sector** (no todos se riegan a la vez ni necesitan lo mismo).
- **Hora de la notificación** elegible por el productor.
- **Estacionalidad:** dejan de regar en **mayo** y retoman en **agosto**. Una
  recomendación de riego no es útil en esa ventana → suprimir/atenuar recomendaciones
  en reposo invernal (coincide con el Kc=0,20 de reposo del modelo).

### 5. Patrón de riego concreto de Morgan
- Regaban **21 hs por SEMANA** (no por día) por sector.
- Ejemplo de turno: desde las **23:00 del domingo hasta las 7:00** del día siguiente (8 hs).
- **Reciben la orden de regar en HORAS de riego.**
- **Requisito de salida:** dar la recomendación en **ambas** unidades: lámina/volumen
  (mm o m³) **y** tiempo de riego.

### 6. Malla antigranizo
- Tienen malla antigranizo **sobre la planta** (tendida sobre la hilera).
- Observación en campo: **no muy gruesa, abierta, deja pasar bastante luz**
  (se ve la planta claramente a través de ella), patrón **romboidal**, monofilamento.
- Ver prueba empírica de NDVI y análisis más abajo.

### 7. Pendientes
- El productor quedó en pasar su **historial de riego** (aún no entregado) → clave para
  **calibrar/validar** el balance hídrico.

---

## Conversión lámina → tiempo / volumen (cerrada con datos de la entrevista)

Asumiendo el caudal/dotación del permiso y aspersión:

```
tiempo (s)   = 10.000 × lámina(mm) / dotación(L/s/ha) / eficiencia    (eficiencia ≈ 0,8)
volumen (m³) = lámina(mm) × superficie(ha) × 10
```

- La superficie se cancela en el tiempo cuando la dotación está en L/s/ha.
- Default sugerido: dotación máxima legal 1,5 L/s/ha (Ley de Aguas de Mendoza) si el
  productor no la carga.

---

## Prueba empírica: NDVI con malla vs sin malla (datos reales del campo)

Se compararon dos bloques **adyacentes** de la finca vía Sentinel-2 (GEE), dibujados a mano
sobre imagen satelital (script `backend/scripts/compare_ndvi_malla.py`, resultados en
`backend/scripts/ndvi_result.json`). Cada bloque tiene 330–410 píxeles válidos (≈3–4 ha).

**NDVI medio por ventana (compuesto mediano):**

| Ventana | SIN malla | CON malla |
|---|---|---|
| Verano 25/26 (Dic–Feb) | 0,374 | 0,326 |
| Otoño 2026 (Mar–May) | 0,140 | 0,202 |
| Invierno 2025 (Jun–Ago) | 0,219 | 0,170 |

**Serie por imagen del verano (dato clave):** los dos bloques **se cruzan**. A principio de
verano (Dic) el bloque con malla está algo más bajo (~0,28–0,32 vs ~0,33–0,37), pero a fin de
verano (fines Ene–Feb) **se igualan e incluso se invierte** (24/01: 0,452 con malla vs 0,447
sin; 08/02: 0,456 con malla vs 0,414 sin).

### Limitación importante (confound confirmado)
Los dos bloques son de **variedades distintas**: uno de **base champagne** y otro de
**Malbec** (confirmado por el productor; consumen agua distinta). Por lo tanto **esta
comparación NO aísla el efecto de la malla** — mezcla malla + variedad + vigor + estructura.
El cruce de fin de verano es consistente con que domina la diferencia de variedad, no una
atenuación fija por malla.

### Lo que sí se puede afirmar
- El bloque **con malla llega a NDVI ~0,45 en verano**, igual que el descubierto → la **malla
  abierta NO ciega al satélite**; el NDVI bajo ella sigue vivo y respondiendo a la canopia.
- No hay evidencia de una caída drástica y sistemática del NDVI por la malla en este caso.

### Pendiente para aislar el efecto (spike HU-S2-05)
Comparación **emparejada**: misma variedad y edad, idealmente el **mismo bloque antes vs
después** de instalar la malla, o dos bloques contiguos de **igual variedad** que solo
difieran por la malla.

---

## Análisis de respaldo bibliográfico (solo fuentes de malla)

**Conclusión sostenible:** para una malla **abierta / de bajo sombreo** (como la de Morgan),
el NDVI satelital sigue siendo **usable con confianza media** (idealmente con corrección);
el descarte a Kc tabular se reserva para mallas **densas / de alto sombreo** o **de color**
(espectralmente selectivas). Regla por sector: abierta → NDVI confianza media; densa/color →
Kc tabular; sin malla → NDVI normal.

Respaldo:
- **Atenuación óptica de la malla es modesta y de banda ancha** → como el NDVI es un cociente
  normalizado (rojo/NIR), una atenuación ~neutra se cancela en gran parte. Malla antigranizo
  negra reduce ~22% la luz (PPFD), gris ~14% en días soleados (Solomakhin & Blanke, *Plants*
  2021).
- **Caso aplicado malla + NDVI:** bajo malla antigranizo el valor **absoluto** del NDVI cambia,
  pero el patrón **relativo** se mantiene confiable y coincidió con el estado real del cultivo
  (Pix4D — fuente de industria, no peer-reviewed).
- **La malla de color es espectralmente selectiva** (transmite distinto según banda) → distorsiona
  el NDVI más que una negra/gris neutra (netting fotoselectivo, *HortScience/PMC*).

**Hueco de investigación (a favor de la tesis):** la revisión peer-reviewed específica de malla
antigranizo + teledetección declara explícitamente que integrar mallas con teledetección/NDVI
satelital está **poco estudiado** (no hay un número publicado del efecto de la malla sobre el
NDVI satelital). El experimento emparejado propuesto sería una **contribución original** sobre
un tema reconocido como vacío.

### Fuentes (solo malla)
- Revisión malla antigranizo + teledetección (peer-reviewed; declara el gap): https://www.mdpi.com/2225-1154/13/10/203
- Reducción de luz por malla antigranizo negra/gris (peer-reviewed): https://pmc.ncbi.nlm.nih.gov/articles/PMC8708770/
- Malla + NDVI, absoluto cambia / relativo confiable (industria, Pix4D): https://www.pix4d.com/blog/drone-mapping-high-value-crops-viticulture
- Netting fotoselectivo de color, selectividad espectral (peer-reviewed): https://pmc.ncbi.nlm.nih.gov/articles/PMC7761960/
