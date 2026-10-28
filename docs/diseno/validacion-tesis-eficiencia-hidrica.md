# Validación de la tesis — Estudio de eficiencia hídrica

> **Estado: RESULTADOS + SENSIBILIDAD (16-17-jun-2026).** El harness corrió sobre clima ERA5 +
> NDVI S2 reales: el sistema es **Pareto-óptimo contra el calendario realista (calendario a requerimiento) en las 9/9
> configuraciones** del barrido p × suelo, con ahorro de agua 15–53% (§11). El stress-test de
> igual-agua (calendario a igual agua) revela una sub-optimalidad de timing acotada al suelo más pesado en años
> húmedos (límite del "refill a FC", §11.5). Antes se corrigió el motor a FAO-56 estricto (gatillo en
> RAW + ETc_adj, §11.0) y el steelman se re-fundó en **dos baselines** (§3, §5.2). Próximo paso:
> redacción del cap. 3 (figuras ya hechas). Este documento consolida **todo**: objetivo, diseño,
> decisiones, fuentes, código y resultados.

---

## 1. Objetivo

Demostrar, de forma **fiable y lo más real posible**, que el sistema hace un **uso más
eficiente del agua** que la práctica de riego habitual. Es el reclamo central de la tesis.

La forma anterior de mostrarlo ("agua evitada vs riego a ciegas") **no convence**: el número
resultaba ser literalmente la lluvia caída, comparada contra un contrafáctico (regar toda la
ETc todos los días ignorando la lluvia) que nadie hace. Es un artificio de cálculo, no una
medición. Por eso se rediseña.

---

## 2. Qué es y qué NO es (separar dos cosas distintas)

Hay **dos entregables distintos con públicos distintos**. Confundirlos es lo que hacía que la
métrica no convenciera.

| | **Estudio de eficiencia hídrica** (este doc) | **Métrica del productor** |
|---|---|---|
| Público | Tribunal / documento de tesis | Productor, en la app |
| Naturaleza | Estudio de simulación, se corre **una vez** sobre temporadas históricas | Indicador en vivo sobre datos reales de su finca |
| Compara | Calendario hipotético **vs** sistema | Lo que el productor **realmente** hizo vs lo que la planta necesitó |
| Salida | Tablas y gráficos para el documento | Tarjetas en la vista de Evaluación |
| Doc | Este archivo | (Parte B; ver `SectorMetrics.vue` + `metrics.py`) |

**Por qué separarlas:** no se le puede mostrar al productor "ahorrás X% vs el riego por
calendario" porque él **no regó por calendario** — ese calendario solo existe en la simulación.
Para el productor, lo honesto es compararlo contra lo que él mismo hizo y contra lo que la
planta necesitó (eso es la métrica del productor).

**Comparten el mismo motor:** balance FAO-56, percolación y días de estrés. Se construye una
vez y se usa para las dos.

---

## 3. El diseño (el flujo, paso a paso)

1. **Motor de suelo (ya existe):** el balance hídrico FAO-56 (`calculation/water_balance.py`).
   Dado el clima de un día dice cuánta agua tiene el suelo, cuánta usó la planta y cuánta falta.
2. **Entradas reales, no inventadas:** clima histórico real (Open-Meteo / ERA5) + cultivo real
   vía NDVI satelital (lo que ya hace el sistema).
3. **Dos formas de regar, idénticas en todo menos la decisión** (misma finca, mismo clima, mismo
   suelo, mismo cultivo, **misma aspersión**):

   | | Riego por calendario (el común) | Riego del sistema |
   |---|---|---|
   | Cuándo riega | días fijos, pase lo que pase | solo cuando el suelo lo necesita (Dr ≥ RAW) |
   | Cuánto | cantidad fija | lo justo para reponer hasta capacidad de campo |
   | ¿Mira clima/suelo? | **No** | **Sí** |

4. **Se mide, por temporada, en cada forma de regar:**
   - Agua aplicada total.
   - **Agua desperdiciada** = percolación profunda (la que se filtra bajo las raíces y la planta
     nunca usa).
   - **Días en estrés hídrico** = días con Ks < 1.
5. **Comparación (Pareto-optimalidad):** el sistema es **Pareto-óptimo** — **no es superado** por
   ninguna variante de calendario en el espacio (agua aplicada, percolación, días en estrés). El
   calendario siempre pierde en al menos un eje: o riega de más (más agua + más desperdicio) o, a
   igual agua, riega en el momento equivocado (más percolación y más estrés). Ver §11.

### La jugada clave: "steelman" del calendario en DOS baselines

Para que el resultado sea indiscutible se le da al calendario **la mejor versión posible**, y se
parte en dos baselines que **separan dos efectos** que de otro modo se mezclan:
- **calendario a requerimiento** — dosado para que el total estacional = IRN (óptimo físico FAO-56). Mide
  cuánto **menos agua** usa el sistema.
- **calendario a igual agua** — dosado a la **misma agua neta** que aplicó el sistema. Aísla el
  **timing puro**: misma agua, ¿quién la reparte mejor? Aun con el total idéntico el calendario
  pierde, porque regar en días fijos significa que el momento está mal (riega tras la lluvia →
  percola; o llega tarde en una ola de calor → estrés).

**La ventaja es estructural (mistiming), no producto de elegir un rival débil — y el sistema no
usa ni un dato de la finca más allá de clima y NDVI.**

---

## 4. Decisiones tomadas (y por qué)

1. **El baseline NO sale del hábito del productor.** El dato de "21 hs/semana" de la entrevista
   a la finca de estudio se **descarta**: fue un comentario suelto ("a veces 21, a veces menos"), no una
   medición fiable. Además **no hay ningún registro real** de la finca (sin registros, sin
   turnos DGI porque tienen reservorio). El baseline se define por **literatura y física**, no
   por anécdota.

2. **Dos pilares para el baseline:**
   - **Referencia dura = IRN** (requerimiento neto de riego, FAO-56) = el agua que el cultivo
     realmente necesita. Es el **óptimo físico**, no contestable, no depende de ningún baseline
     humano.
   - **Contraste = calendario arquetípico "just-in-case"** (Srinivasan et al. 2021): regar fijo
     sin mirar demanda. No se apuesta a un único número: se define una **familia** de calendarios
     y se **barre** (la robustez sale de que el sistema gane en todo el rango).

3. **La caja de valores plausibles del calendario** se acota con fuentes, no con la entrevista:
   rango estacional FAO para vid (**500–1200 mm**) + anclas locales (**módulo 700–1100 mm**,
   De Lorenzi/Tacchini).

4. **Enfoque en ASPERSIÓN, no en surco.** La finca de estudio riega por aspersión (efic. ≈ 0,85, DGI; Schilardi et al., 2015). El
   método se mantiene **constante en ambos brazos**, así la comparación **aísla el valor de la
   decisión** (cuándo/cuánto), no el del método de riego. Comparar surco-baseline vs
   aspersión-sistema mezclaría dos cosas e **inflaría el ahorro** (sería un strawman). Las
   fuentes de surco (De Lorenzi, Tacchini) cambian de rol: pasan a ser **contexto** (evidencia
   de ineficiencia local) y **anclas de cordura** (verificar que los números simulados caen en
   el rango real local), NO el baseline.

5. **Encuadre honesto a escala parcela/planta, NO ahorro de cuenca.** Por la *paradoja de la
   eficiencia* (Perry & Steduto 2017; Grafton et al. 2018): más eficiencia de aplicación no
   implica menos consumo a escala cuenca por los retornos de flujo. El reclamo se limita a
   "menos agua aplicada para el mismo estado del cultivo" a nivel finca.

---

## 5. Decisiones operativas (CERRADAS 16-jun-2026)

Los 6 puntos que estaban abiertos quedaron resueltos con defaults fundados en las fuentes (§8):

1. **Calendario hipotético** → familia de **intervalos fijos {7, 10, 14} días** (semanal / decadal
   / quincenal: el "just-in-case" de Srinivasan 2021). Se **barre** la familia; la robustez sale
   de que el sistema gane en todo el rango.
2. **Steelman en DOS baselines** (§3) → **calendario a requerimiento** (lámina calibrada a Σ neta estacional =
   IRN, óptimo físico FAO-56) para medir el ahorro de agua, y **calendario a igual agua** (lámina
   calibrada a la misma agua neta que aplicó el sistema) para aislar el *timing* puro. Ambos aplican
   un total "correcto" y aun así pierden por momento.
3. **Temporadas** → **3 temporadas de riego completas** recientes con buena cobertura S2 (oct–mar):
   **21/22, 22/23, 23/24**. Multi-temporada → el ahorro sale como rango, no cherry-pick.
4. **Sector/suelo/cultivo** → el **Malbec real** del sistema (vid/vino, **aspersión efic. 0.85**
   (DGI; Schilardi et al., 2015), raíz 1.5 m, p = 0.45, suelo SoilGrids real, TAW ≈ 150 / RAW ≈ 67.5). El método de riego
   se mantiene constante en ambos brazos (aísla el valor de la decisión, no del método — §4.4); la
   eficiencia se **cancela** en la comparación %, solo escala el bruto. El **factor de agotamiento
   `p`** (FAO-56) es la fracción del agua disponible (TAW) que el cultivo consume **sin estrés**; fija
   el umbral de riego **RAW = p·TAW** (Tabla 22: vid vinífera p ≈ 0,45). Por eso se barre en la
   sensibilidad (§5.6, §11.5): es influyente y algo subjetivo.
5. **Definición de los ejes** (alineada con `water_balance.py` y `metrics.py`):
   - **Agua aplicada** = Σ riego (bruto = neto / 0.85).
   - **Agua desperdiciada** = Σ **percolación profunda** (`deep_percolation_mm`).
   - **Día en estrés** = día con **Ks < 1** (severo: Ks < 0.5).
6. **Sensibilidad (robustez)** → barrer **p ∈ {0.40, 0.45, 0.50}**, **clase de suelo / profundidad
   de raíz (±1)**, **coef. de lluvia efectiva**, y la familia de calendarios. Ahorro reportado como
   rango. Respaldado por el análisis de sensibilidad de Torres Prieto 2010 (ET0, Kcb, fc, raíz y p
   = las variables más influyentes del modelo).

---

## 6. Pieza compartida con la métrica del productor

> **Estado: HECHO (ya en `main`).** La percolación ya se recupera, persiste y agrega — esta
> sección queda como referencia del mecanismo, no como tarea pendiente.

La **recuperación de la percolación** se construyó para la métrica del productor, y sirve
directamente como uno de los dos ejes del estudio de tesis. El cálculo del balance **ya** la
expone (`deep_percolation_mm = max(0.0, -raw_deficit)`); antes la descartaba en el `max(0,…)`:

```python
# calculation/water_balance.py
water_deficit_mm = max(0.0, min(raw_deficit, taw_mm))
#                   ^^^^^^^ cuando raw_deficit < 0, el exceso (-raw_deficit) es
#                           percolación profunda y se tira. Hay que recuperarlo:
#   deep_percolation_mm = max(0.0, -raw_deficit)
#                       = max(0.0, (pe + I) - previous_deficit - etc)
```

Esto ya está implementado: se devuelve en `WaterBalanceResult`, se persiste en `DailyWaterBalance`
(columna + migración `90679de08752`) y se agrega en `metrics.py`.

**Nota:** el balance diario ya se calcula con el **riego real confirmado** por el productor
(`services/water_balance.py:115`, `irrigation_mm = confirmed_irrigation_mm(...)`), así que la
percolación medida es la pérdida real de lo que el productor efectivamente hizo.

---

## 7. Archivos de código involucrados

| Archivo | Rol en el estudio |
|---|---|
| `backend/app/calculation/water_balance.py` | Motor FAO-56. Percolación recuperada + **ETc_adj = Ks·Kc·ETo** (§11.0). |
| `backend/app/calculation/urgency.py` | Gatillo de riego anclado en **RAW** (§11.0); dosis con **refill parcial** modulado por pronóstico (§11.5). |
| `backend/evaluation/sim_efficiency.py` | **Harness del estudio** (offline, reusa el motor; 2 baselines). |
| `backend/app/calculation/eto.py` | ETo Penman-Monteith. |
| `backend/app/calculation/kc.py` | Kc desde NDVI (Kc = 0.30 + 0.40·fc) o tabular. |
| `backend/app/calculation/crop_params.py` | Profundidad de raíz y factor p por cultivo. |
| `backend/app/services/water_balance.py` | Balance diario; usa el riego confirmado real. |
| `backend/app/services/metrics.py` | Agregación de KPIs (reusable para la simulación). |
| `backend/app/models/daily_water_balance.py` | Agregar columna de percolación. |
| `backend/app/ingestion/climate.py` | Clima histórico (Open-Meteo / ERA5). |
| `backend/app/services/satellite.py` | NDVI satelital (GEE / Sentinel-2). |

(El frontend `SectorMetrics.vue` y la API `metrics.py` son de la **métrica del productor**, no del estudio.)

---

## 8. Fuentes (todas verificadas y contrastadas)

> Verificadas en la web (14-jun-2026). Las de ScienceDirect/Springer están tras paywall →
> acceso institucional UM. Los textos extraídos con pdfminer quedaron en `%TEMP%/*.txt`.
> Espejo de esta sección en la memoria `fuentes-evaluacion.md`.

### 8.1 Método base + parámetros de vid (fundamenta el motor)

- **FAO-56** — Allen, Pereira, Raes, Smith (1998). *Crop evapotranspiration — Guidelines for
  computing crop water requirements*. FAO Irrigation and Drainage Paper 56. → ETo
  Penman-Monteith, Kc·ETo, balance Dr, RAW = p·TAW, percolación profunda, requerimiento neto,
  lluvia efectiva. HTML oficial: `fao.org/4/x0490e/x0490e00.htm`.
- **FAO Land & Water — Grape** (`fao.org/land-water/databases-and-software/crop-information/grape/en/`):
  Kc ini **0.30** / mid **0.85 (mesa) o 0.70 (vino)** / end **0.45**; **p = 0.35 (mesa) / 0.45
  (vino)**; raíz **1.5 m**; ciclo 180–240 d; estacional **500–1200 mm**. → confirma que los
  parámetros del sistema (vid vino, p = 0.45) están alineados con FAO.

### 8.2 Kc desde NDVI / cobertura (fundamenta lo satelital)

- **Allen & Pereira (2009)**. *Estimating crop coefficients from fraction of ground cover and
  height*. Irrigation Science 28(1):17–34. doi:10.1007/s00271-009-0182-z. **[texto extraído]**
  Ec. 5a: **Kcb = Kc_min + Kd·(Kcb_full − Kc_min)**; Kc_min ≈ 0.15 (suelo desnudo);
  Kd = min(1, ML·fc_eff, fc_eff^(1/(1+h))) con ML ∈ [1.5–2.0]. Respalda el `Kc = 0.30 + 0.40·fc`.
- **Pereira et al. (2020)**. *Prediction of crop coefficients from fraction of ground cover and
  height...*. Agric. Water Manag. 241:106197. **[texto extraído]** Kc = Kc_min + Kd·(Kc_full −
  Kc_min); Kcb_full = Fr·min(1.0, 1+kh·h, 1.20), kh = 0.1 frutales/vid; **fc = 1.26·NDVI − 0.18**
  (Trout et al. 2008, marco SIMS); validación R² ≥ 0.90.
- **Campos et al. (2010)**. *Assessing satellite-based basal crop coefficients for irrigated
  grapes (Vitis vinifera L.)*. Agric. Water Manag. 98(1):45–54. **[texto extraído]** **VID
  específico: Kcb = 1.44·NDVI − 0.10**; validado contra eddy-covariance en viñedo (Castilla-La
  Mancha): Kc medido = 0.96·Kc modelado, r² = 0.67.
- **Torres Prieto, E. A. (2010)**. *El modelo FAO-56 asistido por satélite en la estimación de la
  evapotranspiración en un cultivo bajo estrés hídrico y suelo desnudo. Caso de estudio: Acuífero
  Mancha Oriental, España*. Tesis doctoral, Univ. de Castilla-La Mancha (dir. A. Calera, E. M.
  Rubio). **[texto extraído]** Mismo grupo (Albacete) que Campos et al. (2010). **Roles acotados
  para este estudio:** (1) **precedente de análisis de sensibilidad** de FAO-56 — perturbación
  +10 % por variable de entrada; las salidas más sensibles a **ET0, Kcb, fc, profundidad de raíz y
  p (fracción de agotamiento)**, y la menos sensible la altura del cultivo (la profundidad de raíz
  es difícil de medir y muy influyente) → respalda el barrido de sensibilidad del §5.6; (2)
  **autoridad del motor**: coeficiente dual, Ks y balance en zona radicular, evaporación de suelo
  desnudo, relaciones lineales NDVI→Kcb (Bausch & Neale 1987; Neale 1989; González 2006 ≈
  Kcb = 1.36·NDVI − …); (3) **precedente de validación de ET** de FAO-56 contra mediciones de campo
  (razón de Bowen, lisímetros). **NO es:** vid ni Mendoza (trigo + suelo desnudo, España) → no es
  ancla local ni vid-específica; **no compara sistema-vs-calendario** (eso sigue siendo Srinivasan
  2021); su escala de acuífero es de cuenca (solo contexto del caveat de escala, no modelo a imitar).

### 8.3 Comparación de estrategias + magnitud del ahorro

- **Srinivasan et al. (2021)**. *Comparing the water use metrics of just-in-case, just-in-time
  and justified irrigation strategies using a scenario-based tool*. Agric. Water Manag. (NIWA,
  Nueva Zelanda; herramienta IrriSET). **[texto extraído] ← PRECEDENTE peer-reviewed casi exacto
  de esta metodología.** Compara 3 estrategias con 3 métricas (agua aplicada, drenaje/percolación,
  tiempo en rango óptimo): **just-in-case** (≈ calendario) → más agua + más drenaje; **just-in-time**
  (balance de suelo); **justified** (balance + pronóstico, ≈ nuestro sistema) → mejor desempeño.
  Valida el doble/triple eje.
- Ahorro típico **10–30%** (rango amplio 14–55% según método/clima) de programar por balance/ET/DSS
  vs práctica del productor: AI/smart-irrigation systematic review `S2772375525002151`; DSS review
  Scientific Reports 2025; MDPI Agriculture 14(7):1141 (2024); extensión UGA B974; SAI Platform
  Tech Brief 6. Citar peer-reviewed; usar como **rango**.

### 8.4 Eje percolación / eficiencia de aplicación

- *From Flood to Drip: A Review of Irrigation Modernization Trade-Offs*, MDPI Water 17(20):3018
  (2025) → riego superficial ~60% efic. (~40% pérdidas).
- *Economic efficiency of drip and flood... DEA*, Agric. Water Manag. (2025), `S0378377425000289`.

### 8.5 Crítica honesta — paradoja de la eficiencia (IMPRESCINDIBLE)

- **Perry & Steduto (2017)**. *Does improved irrigation technology save water? A review of the
  evidence*. FAO, Cairo. + versión peer-reviewed Perry et al. (2020), Review of Environmental
  Economics and Policy 14(2). + (canon) **Grafton et al. (2018), Science, "The paradox of
  irrigation efficiency".** → más eficiencia ≠ menos consumo a escala cuenca (return flows).
  Obliga a encuadrar el reclamo a **escala parcela/planta**.

### 8.6 Riego deficitario en vid (matiz: menos agua puede ser deseable)

- Wample & Smithyman. *Regulated deficit irrigation... Vitis vinifera*. FAO (`y3655e`). →
  distribución fenológica del consumo: cuajado→envero **60%**, envero→cosecha **20%**.
- **Acevedo-Opazo, Ortega-Farias, Fuentes (2010)**. *Effects of grapevine water status on water
  consumption, vegetative growth and grape quality...RDI*. Agric. Water Manag. (Cabernet, Isla de
  Maipo, Chile — clima afín a Mendoza). **[texto extraído]** RDI por umbrales de potencial hídrico
  de tallo: correlaciona con calidad sin detrimento de rendimiento.
- Otras: AJEV 67(4):426 (2016); VineyardTeam *RDI Management for Winegrapes* (guía práctica).

### 8.7 Datos LOCALES Mendoza (anclan el caso + validan el motor)

- **De Lorenzi, Morábito, Menenti, Dell'Aquila & Briles**. *Evapotranspiración, transpiración y
  evaporación en un viñedo var Malbec. Mendoza* (INA-CRA / CNR Italia; proyecto CONICET-CNR
  2003/08). **[texto extraído — ¡ORO LOCAL!]** Malbec en espaldero bajo malla, Las Compuertas
  (Luján de Cuyo), riego por **surcos**. Datos reales: eficiencia de riego superficial en Mendoza
  **35–40%**; ciclo 2005/06 = **3 riegos de ~233 mm c/u = 700 mm brutos** en 7 meses (80% infiltra
  → 560 mm); **fc del viñedo ≈ 20%**; **ETc ≈ 3.67 mm/día**; rinde 10.900 kg/ha (06/07). Valida el
  motor (ETc, fc bajo↔Kc bajo) y aporta ancla de lámina real local.
- **Tacchini, F. (INA)** — *El Recurso Agua en el Dpto. de General Alvear* (cuenca Atuel, sur de
  Mendoza, junto a San Rafael). **[texto extraído]** **Eficiencia total ≈ 28%** = conducción 80%
  × distribución 70% × **aplicación 50%**; **módulo ≈ 11.000 m³/ha-año (= 1.100 mm)**; método
  predominante gravedad/surcos en vid/frutales/hortalizas. 2º ancla local, consistente con De
  Lorenzi.
- ⚠️ **INA Cra_8** (Morábito, Salatino & Hernández): **NO sirve** (NE argentino, trigo/maíz/soja,
  sin vid ni Mendoza). Candidatos válidos para ETc/Kc de vid local: **INTA repositorio digital**
  (repositorio.inta.gob.ar; buscar Hernán Vila / vid ET Mendoza) e **INA CRA – Jornadas de Riego
  y Fertirriego** (ina.gob.ar/cra).
- **DGI Informe Anual 21/22** (extraído): da derrames por río en hm³ (escala cuenca, ~3224 hm³),
  **NO lámina por ha** → no es la fuente del baseline. Ley de Aguas 1884: derecho hasta **1.5
  L/s/ha** = máximo concesional, NO aplicación real.

### 8.8 Insumo climático (justifica ERA5 / Open-Meteo)

- **Tunca, Novák, Šařec, Köksal (2026)**. *Optimizing Reference Evapotranspiration Estimation in
  Data-Scarce Regions Using ERA5 Reanalysis and Machine Learning*. Agronomy 16(2):253 (open
  access). **[texto extraído]** ERA5-Land: radiación solar y temperatura muy precisas, pero
  **viento (U2) y HR con sesgos sistemáticos** (caveat honesto); con corrección ML (XGBoost):
  R² = 0.95, RMSE 0.43 mm/día.
- Pendiente (paywall, opcional y redundante con Tunca): *Reference crop ET for data-sparse
  regions using reanalysis*, Agric. Water Manag. (2021) `S0378377421005965`.

---

## 9. Cómo leer las fuentes en PDF en este entorno

El tool Read **falla con PDFs** (falta `pdftoppm`/poppler). WebFetch a
ScienceDirect/ResearchGate/openknowledge.fao da **403** (pero **guarda el PDF binario local**).
Solución que funciona: bajar el PDF local y extraer texto con **pdfminer** (instalado en el venv):

```bash
backend/venv/Scripts/python.exe -c "from pdfminer.high_level import extract_text; \
open(r'salida.txt','w',encoding='utf-8').write(extract_text(r'ruta.pdf'))"
```

Luego Grep/Read el `.txt`. Solo sirve si el PDF tiene texto (los escaneados fallan). Si una ruta
con `%20` no se encuentra, el navegador pudo haber decodificado el espacio al guardar → buscar con
comodín: `Get-ChildItem "C:\...\*palabra*.pdf"`.

---

## 10. Estado de la recolección de datos

**Esencialmente CERRADA (14-jun-2026). Nada bloqueante.** Único pendiente: el paper ERA5 con
paywall (AWM 2021), que es **opcional y redundante** (Tunca 2026 ya lo cubre). Detalle del cierre
en la memoria `fuentes-evaluacion.md`.

---

## 11. Resultados (16-jun-2026)

### 11.0 Corrección previa del motor a FAO-56 estricto

Antes de correr la validación se saldaron 3 desvíos de FAO-56 detectados en la auditoría (la
eficiencia 0.85 estaba **fundada**; estos no lo estaban). La lluvia efectiva 0.8/2mm, que en esta
auditoría se consideró fundada, no tenía fuente documentada; en octubre de 2026 se reemplazó por el
umbral de FAO-56 (ver `docs/referencias/referencias.md`, "Precipitación efectiva"):

1. **Gatillo a RAW** (`urgency.py`): se reemplazó el umbral sin respaldo `Dr/TAW = 0.35` por el
   anclaje FAO-56 en RAW. La urgencia es `low` mientras `Dr < RAW` (Ks=1, no riega) y escala por Ks
   dentro de la zona de estrés (≥0.75 medium, ≥0.5 high, <0.5 critical). Para Malbec gatilla en
   `RAW = 0.45·TAW = 67.5 mm` (antes regaba antes, en `0.35·150 = 52.5 mm`).
2. **ETc_adj = Ks·Kc·ETo** (`water_balance.py`, Ec. 81 FAO-56): la ET se reduce por el **Ks de inicio
   de día** (calculado del déficit previo, evita circularidad) cuando `Dr > RAW`. Con `Dr ≤ RAW` es
   Ks=1 → idéntico al comportamiento previo; solo cambia bajo estrés. Necesario para que el
   calendario (que seca el suelo bajo RAW) se mida con física correcta.
3. **Eficiencia 0.85** (aspersión, 85–90 % según el DGI; Schilardi et al., 2015) ya estaba en `irrigation.py`.

El harness `evaluation/sim_efficiency.py` reusa exactamente estas funciones puras, así que valida el
sistema corregido tal cual corre en producción (con una excepción documentada en §11.5: la dosis con
*refill parcial* modulado por pronóstico, que el backtest no replica por carecer de pronóstico
histórico).

### 11.1 Tabla (3 temporadas reales, sector Malbec). Ejes a minimizar: agua / perc / estrés (Ks<1)

`agua` = riego neto mm · `perc` = percolación profunda mm · `estrés` = días con Ks<1.

| Temporada | Sistema | calendario a requerimiento (7/10/14 d) | calendario a igual agua (7/10/14 d) |
|---|---|---|---|
| 2021/22 | 276 / 54 / 4 | 406 / 171–172 / 0 | 276 / 55–58 / 6–10 |
| 2022/23 | 344 / 23 / 5 | 471 / 149–156 / 51–55 | 344 / 103–106 / 98 |
| 2023/24 | 345 / 3 / 5 | 466 / 104–110 / 27–36 | 345 / 39–43 / 87–89 |

(IRN estacional: 406 / 471 / 465 mm. CSV completo en `backend/scripts/_out/sim_results.csv`.)

### 11.2 Veredicto sobre la configuración nominal (sandy_loam, p=0.45)

Los dos baselines **no tienen el mismo estatus**:
- **calendario a requerimiento = baseline realista** (un productor de calendario que dosa al
  requerimiento neto estacional, IRN). Es contra el que se mide la afirmación central de la tesis.
- **calendario a igual agua = diagnóstico** (misma agua neta que el sistema, dato que ningún productor
  conoce a priori). Solo sirve para **aislar el timing**.

**Contra el baseline realista (calendario a requerimiento) el sistema es Pareto-óptimo en las 3 temporadas:** usa
26–32% **menos agua** y no es superado en ningún eje (calendario a requerimiento siempre usa más agua, así que no puede
dominar). En 2022/23 y 2023/24 además **gana en los tres ejes a la vez**; en 2021/22 está sobre la
frontera (cede 4 vs 0 días en estrés, pero calendario a requerimiento paga +47% agua y 3× percolación por esos días).

**Contra el diagnóstico (calendario a igual agua)** el timing del sistema gana en la config nominal:
percolación hasta **12× menor** (23/24) y días en estrés de ~98 a 5. El valor del *cuándo* es enorme en
años secos. (Pero esto **no** es universal en la grilla de sensibilidad — ver §11.5.)

### 11.3 Criterio de éxito 1.1.5 (reescrito y anclado al baseline realista)

El criterio original ("el sistema domina al calendario en los tres ejes de forma simultánea")
**fallaba** ya en la config nominal (2021/22: 4 vs 0 días en estrés) y es conceptualmente inalcanzable
(las tres métricas del calendario están acopladas por su único total de agua). Se reescribe
anclándolo al **baseline realista** (calendario a requerimiento):

> **1.1.5.** El sistema es **Pareto-óptimo** respecto de la práctica realista de riego por calendario
> (calendario dosado al requerimiento estacional, *calendario a requerimiento*): **no es superado** por ninguna de sus
> variantes en el espacio de objetivos (agua aplicada, percolación profunda, días de estrés Ks<1) —
> ninguna logra simultáneamente igual-o-menos en los tres ejes con al menos uno estrictamente menor
> (frontera de Pareto) — y aplica **menos agua** en todos los casos. Debe sostenerse en el barrido
> {7,10,14} d y fases, y en la sensibilidad (p ∈ {0.40, 0.45, 0.50}, suelo ±1 clase textural).

### 11.4 Matices honestos (para no sobrevender)

- **2021/22 es año húmedo**: la percolación del sistema ya es alta (54 mm) por lluvias que pasan
  capacidad de campo *pase lo que pase* → hay un piso de percolación que ninguna política evita, y por
  eso el beneficio de timing casi no aparece esa temporada (en 23/24 el sistema casi no percola,
  3.3 mm). El beneficio del *cuándo* depende del régimen de lluvia.
- **Los 4–5 días en estrés del sistema** son leves (`severo ≈ 0` siempre): es el desfasaje de 1 día en el
  cruce de RAW (Dr cruza el umbral durante el día y el riego entra al siguiente). Realista, no es un
  defecto.

### 11.5 Barrido de sensibilidad (p × suelo) — robustez y límite del refill-a-FC

Se barrió `p ∈ {0.40, 0.45, 0.50}` × suelo `{loamy_sand (TAW 105), sandy_loam (150, nominal),
loam (210)}` = 9 configuraciones, verificando Pareto-optimalidad por (config, temporada) contra las
6 variantes de calendario. Salida en `backend/scripts/_out/sim_sweep.csv`.

- **Contra el baseline realista (calendario a requerimiento): Pareto-óptimo en las 9/9 configuraciones**, con ahorro de
  agua **15–53%**. La afirmación central es robusta a la elección de p y a una mala clasificación de
  suelo de ±1 clase.
- **Contra el diagnóstico (calendario a igual agua): Pareto-óptimo en 7/9.** Las 2 excepciones son
  `p=0.45/loam` y `p=0.50/loam`, ambas en **2021/22 (año húmedo)**.

| config (TAW) | ¿Pareto-óptimo 3 temp? | ahorro agua vs calendario a requerimiento |
|---|---|---|
| p=0.40 · loamy_sand (105) | sí | 16–26% |
| p=0.40 · sandy_loam (150) | sí | 21–25% |
| p=0.40 · loam (210) | sí | 27–37% |
| p=0.45 · loamy_sand (105) | sí | 15–28% |
| **p=0.45 · sandy_loam (150, nominal)** | **sí** | **26–32%** |
| p=0.45 · loam (210) | no (solo timing) | 18–53% |
| p=0.50 · loamy_sand (105) | sí | 19–34% |
| p=0.50 · sandy_loam (150) | sí | 18–44% |
| p=0.50 · loam (210) | no (solo timing) | 31–48% |

(El "no" es **únicamente** contra calendario a igual agua; contra calendario a requerimiento las 9 son "sí".)

**Por qué falla en loam + año húmedo (límite real del "refill a FC"):** con TAW grande (210) y p
alto, el sistema espera hasta Dr=RAW (94–105 mm) y descarga un **refill grande de una vez, llenando
a capacidad de campo**. En un año húmedo, la lluvia que cae justo después sobre el suelo lleno **se
va entera a percolación**. El calendario reparte la misma agua en dosis chicas y frecuentes, dejando
**colchón** para absorber la lluvia → percola la mitad. Medido en `p=0.50/loam`, 2021/22: sistema
perc=58 vs calendario a igual agua/7d perc=27, con estrés igual o menor.

Es el límite del **estándar FAO-56 de "regar a capacidad de campo"** (Ec. 90: cada riego repone el
déficit íntegro hasta `Dr = 0`): es la práctica que el modelo prescribe, no un bug del código. El
downgrade binario por lluvia pronosticada que ya tenía el sistema **no lo rescata** (solo *saltea* el
riego si la lluvia pronosticada supera el déficit entero, raro con RAW≈100; y aun cuando riega,
repone a FC).

**Respuesta de diseño (implementada en producción, `urgency.py`):** *refill parcial modulado por
pronóstico*. Al regar, el sistema ya no llena a FC: deja un **colchón** igual a la lluvia efectiva
esperada (ponderada por probabilidad) de los próximos `_RAIN_BUFFER_HORIZON = 3` días, acotado a
`_RAIN_BUFFER_CAP_FRACTION·RAW = RAW/2` (`_rain_buffer`). Así la lluvia que viene infiltra en vez de
percolar. Dos guardas: si no hay lluvia pronosticada el colchón es 0 → repone a FC (idéntico al
comportamiento anterior); bajo **estrés severo (Ks < 0.5)** repone a FC completo (no apuesta a la
lluvia con la planta ya sufriendo). El tope RAW/2 evita dejar el suelo tan vacío que el riego
re-gatille de inmediato o que roce el estrés si la lluvia no se concreta.

**Límite de validación (honesto):** el backtest **no mide** este refill parcial, porque la simulación
corre sobre lluvia **observada** (ERA5) y no existe un pronóstico histórico con el que reproducir el
colchón sin caer en *hindsight*. Se presenta entonces como **respuesta de diseño, no como resultado
medido**. La simulación cumplió aquí un **rol diagnóstico**: reveló el límite del refill-a-FC en
loam + año húmedo, y el sistema en producción lo corrige. Los resultados de §11.1–§11.5 (Pareto-
optimalidad vs el calendario realista, ahorro 15–53%) siguen siendo el **núcleo empírico intacto**:
no dependen del refill parcial (el harness simula la política refill-a-FC), así que la corrección no
los invalida ni los mejora artificialmente.

**Lectura para la defensa:** se probó el sistema hasta romperlo y se entiende exactamente cuándo y
por qué. La afirmación central (más eficiente en agua que el calendario realista) aguanta toda la
grilla; el stress-test de igual-agua revela una sub-optimalidad de timing **acotada al suelo más
pesado en años húmedos**, que el sistema desplegado mitiga con refill parcial (sin backtest, por lo
ya dicho).

### 11.6 Pendiente

Redacción del capítulo de resultados (cap. 3); las figuras ya están hechas. El *refill parcial* dejó
de ser trabajo futuro: está **implementado en producción** como respuesta de diseño al límite del
refill-a-FC (§11.5), con la salvedad de que el backtest no lo mide (no hay pronóstico histórico).
