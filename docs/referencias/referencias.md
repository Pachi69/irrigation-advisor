# Referencias del proyecto — irrigation-advisor

Documentos consultados durante la investigación técnica del sistema. Útiles para redactar la tesis.

---

## Documentos descargados

| Archivo | Descripción |
|---|---|
| `FAO56_Penman-Monteith.pdf` | FAO Irrigation and Drainage Paper 56 — Allen et al. (1998). Documento central del método ETo Penman-Monteith, balance hídrico, Kc por cultivo y etapa fenológica. |
| `INTA_AreaSur_Mendoza.pdf` | Informe del Área Sur de Mendoza — cultivos, superficies, economía regional de San Rafael. |

---

## Referencias web consultadas

### FAO-56 y métodos de cálculo
- **FAO Paper 56 (online):** https://www.fao.org/4/x0490e/x0490e00.htm
- **FAO — Precipitación efectiva (Brouwer & Heibloem, 1986):** https://www.fao.org/4/x5560e/x5560e03.htm
- **Effective Rainfall Calculation Methods for Field Crops — overview comparativo (Ali, 2017):** https://www.researchgate.net/publication/321363262_Effective_Rainfall_Calculation_Methods_for_Field_Crops_An_Overview_Analysis_and_New_Formulation
- **FAO — Coeficientes de cultivo Kc, Tabla 11 (duración de etapas de desarrollo) y Tabla 12 (valores de Kc por cultivo):** Capítulo 6 — https://www.fao.org/4/x0490e/x0490e0b.htm

### Sentinel-2 y procesamiento satelital
- **Google Earth Engine — Sentinel-2 SR Harmonized (fuente satelital del sistema):** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- **NDVI a Kc — durum wheat semi-árido:** https://www.sciencedirect.com/science/article/abs/pii/S037837742030233X
- **NDVI a Kcb — viñedo semi-árido (Campos et al. 2010):** https://www.sciencedirect.com/science/article/abs/pii/S0378377410002428
- **Revisión VI → Kc (Glenn et al. 2011):** https://onlinelibrary.wiley.com/doi/10.1002/hyp.8392

### Open-Meteo
- **Documentación API Open-Meteo:** https://open-meteo.com/en/docs
- **Variables disponibles incluyen ETo precalculada:** variable `et0_fao_evapotranspiration`

### Agricultura en San Rafael, Mendoza
- **Panorama económico-productivo de San Rafael:** https://www.scielo.org.ar/scielo.php?script=sci_arttext&pid=S2314-15492011000200003
- **Hortalizas en San Rafael:** https://diariosanrafael.com.ar/san-rafael-registra-mas-de-300-hectareas-cultivadas-con-hortalizas-de-verano/
- **Riego a manto en San Rafael (80%):** https://diariosanrafael.com.ar/el-80-de-las-hectareas-productivas-de-san-rafael-mantienen-el-sistema-de-riego-a-manto/
- **Pequeños productores frutícolas San Rafael:** https://ri.unsam.edu.ar/bitstream/123456789/866/1/TMAG_IDAES_2016_CFN.pdf
- **Cluster ciruela industria Mendoza:** https://www.argentina.gob.ar/agricultura/prosap/cluster-de-ciruela-industria-de-mendoza

### Manejo del suelo en frutales y viñedos de Mendoza
- **Manejo de suelo mediante coberturas vegetales establecidas — INTA EEA Mendoza:** https://www.researchgate.net/publication/327793143_MANEJO_DE_SUELO_MEDIANTE_DIFERENTES_COBERTURAS_VEGETALES_ESTABLECIDAS_SU_INFLUENCIA_EN_EL_MICROCLIMA_DE_VINEDOS_BAJO_RIEGO
- **Evaluación y elección de especies de coberturas vegetales en viñedos bajo riego de Mendoza:** https://www.researchgate.net/publication/328146017_Evaluacion_y_eleccion_de_diferentes_especies_de_coberturas_vegetales_en_vinedos_bajo_riego_de_Mendoza
- **Uso del agua en agricultura, sistemas de riego — Aquabook (Departamento General de Irrigación, Mendoza):** https://aquabook.irrigacion.gov.ar/296_0

### Fenología de cultivos en Mendoza
- **FAO-56 Cap. 6 — Tabla 11 (duración de etapas) y Tabla 12 (Kc):** https://www.fao.org/4/x0490e/x0490e0b.htm
- **Caracterización fenológica de variedades de durazno para industria en Mendoza:** https://quatrebcn.es/caracterizacion-fenologica-de-variedades-de-durazno-para-industria-en-mendoza
- **Durazno Don Carlos INTA (fechas de floración y brotación):** https://www.argentina.gob.ar/inta/relaciones-estrategicas-del-inta/durazno-don-carlos-inta
- **Fenología de cultivares de vid — UNCuyo, Luján de Cuyo:** https://repositoriosdigitales.mincyt.gob.ar/vufind/Record/BDUNCU_49cf8f4b373ce570bc6ad1ec8c88cc15
- **Manual de Fenología — Gobierno de Mendoza:** https://mza-dicaws-portal-uploads-media-prod.s3.amazonaws.com/informacion-oficial/uploads/sites/17/2025/09/manualdefenologia.pdf
- **Fenología de Vid — IDR Mendoza:** https://www.idr.org.ar/fenologia-de-vid/

### Parámetros de suelo
- **Soil Water Parameters — Cornell:** https://nrcca.cals.cornell.edu/soil/CA2/CA0212.1-3.php
- **Water Balance Approach — Colorado State:** https://extension.colostate.edu/resource/irrigation-scheduling-the-water-balance-approach/
- **Saxton & Rawls (2006) — propiedades hídricas por textura USDA (θ_fc, θ_wp):** https://acsess.onlinelibrary.wiley.com/doi/10.2136/sssaj2005.0117

### SoilGrids — tipo de suelo por coordenadas
- **SoilGrids 2.0 REST API (ISRIC):** https://rest.isric.org/soilgrids/v2.0/properties/query
- **Documentación WCS (fallback):** https://docs.isric.org/globaldata/soilgrids/wcs.html

### Conversión de lámina de riego a tiempo (riego a manto, Mendoza)
- **Aquabook — ¿Cuánta agua voy a recibir? (ejemplo de dotación L/s/ha por turno):** https://aquabook.agua.gob.ar/1011_0
- **Aquabook — Modalidades de distribución del agua:** https://aquabook.agua.gob.ar/1010_0
- **Ley de Aguas de Mendoza (dotación máxima 1,5 L/s/ha):** https://www.mendoza.gov.ar/wp-content/uploads/sites/15/2021/04/LEY-DE-AGUAS.pdf
- **Cuadro de turno — DGI:** https://www.irrigacion.gov.ar/web/cuadro-de-turno/
- **Cálculo de tiempo de riego T = Lámina / Intensidad de aplicación:** https://www.riego.elesteliano.com/ayuda/Fto2_Requerimientos_de_riego.htm
- **Cómo estimar la tasa de aplicación del agua:** https://www.rcdsantacruz.org/images/brochures/pdf/Estimate_the_application_rate_Spanish_FINAL.pdf

### Integración de pronóstico climático
- **Forecast integration in irrigation:** https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023WR035810

---

## Citas clave para la tesis

> Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. FAO, Rome.

Esta es la cita principal del método de cálculo ETo Penman-Monteith y balance hídrico que usa el sistema.

> Campos, I., Neale, C.M.U., Calera, A., Balbontín, C., González-Piqueras, J. (2010). *Assessing satellite-based basal crop coefficients for irrigated grapes (Vitis vinifera L.).* Agricultural Water Management, 98(1), 45–54. https://doi.org/10.1016/j.agwat.2010.07.011

Justifica el uso de NDVI como único índice satelital para estimar Kcb en viñedo bajo condiciones semiáridas. El sistema usa la misma estrategia: Kcb = f(NDVI) con fallback tabular FAO-56 cuando no hay imagen disponible.

> Glenn, E.P., Neale, C.M.U., Hunsaker, D.J., Nagler, P.L. (2011). *Vegetation index-based crop coefficients to estimate evapotranspiration by remote sensing in agricultural and natural ecosystems.* Hydrological Processes, 25(26), 4050–4062. https://doi.org/10.1002/hyp.8392

Revisión de referencia que valida el uso de índices de vegetación (NDVI principalmente) para estimar Kc en múltiples cultivos. Confirma que NDVI es suficiente para estimar transpiración potencial y que el estrés hídrico debe modelarse por separado vía balance hídrico (Ks), no mediante modificadores del índice.

> Poggio, L., de Sousa, L.M., Batjes, N.H., Heuvelink, G.B.M., Kempen, B., Ribeiro, E., Rossiter, D. (2021). *SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty.* SOIL, 7, 217–240. https://doi.org/10.5194/soil-7-217-2021

Fuente de datos de textura del suelo (arena/limo/arcilla en g/kg a 250m de resolución) usada para determinar automáticamente el tipo de suelo del campo desde sus coordenadas. Validado contra ~240.000 perfiles globales. Licencia CC-BY 4.0.

> Calera, A., Campos, I., Osann, A., D'Urso, G., Menenti, M. (2017). *Remote Sensing for Crop Water Management: From ET Modelling to Services for the End Users.* Sensors, 17(5), 1104. https://doi.org/10.3390/s17051104

Establece el marco de trabajo de combinar datos de teledetección con el balance hídrico FAO-56 para scheduling operativo de riego — precisamente el enfoque de este sistema. Valida el uso de datos de suelo en grilla como entrada estándar para derivar θ_fc y θ_wp.

> Saxton, K.E., Rawls, W.J. (2006). *Soil Water Characteristic Estimates by Texture and Organic Matter for Hydrologic Solutions.* Soil Science Society of America Journal, 70(5), 1569–1578. https://doi.org/10.2136/sssaj2005.0117

Fuente de las propiedades hidráulicas del suelo (θ_fc a −33 kPa y θ_wp a −1500 kPa) por clase textural. Provee estimaciones para las 12 clases del triángulo textural USDA, consistentes con la clasificación derivada de SoilGrids 2.0, y alimentan el cálculo de TAW y RAW en el balance hídrico.

---

## Decisiones del modelo y su respaldo

### Anclaje de la temporada de cultivo y etapas fenológicas

El sistema no solicita al productor la fecha de brotación. Para cada cultivo perenne (vid, durazno) la temporada se ancla a una fecha típica regional de brotación y se reancla automáticamente cada año; al superar la duración total de las cuatro etapas, el cultivo entra en una etapa de reposo invernal.

- **Duración de las etapas (FAO-56, Tabla 11):** vid según la fila "wine, Mid Latitudes" → 30 / 60 / 40 / 80 días (inicial / desarrollo / media / tardía); durazno según "stone fruit, Low Latitudes" → 20 / 70 / 120 / 60 días.
- **Valores de Kc (FAO-56, Tabla 12):** vid wine → Kc 0,30 / 0,70 / 0,45.
- **Inicio de temporada — 1 de septiembre para vid y durazno.** La floración del durazno para industria en Mendoza ocurre entre el 1 y el 15 de septiembre; la variedad Don Carlos INTA registra inicio de brotación el 30/08. La brotación de la vid en Mendoza ocurre en septiembre. FAO-56 indica "abril" para la vid, valor del Hemisferio Norte equivalente a octubre en el Sur; se adopta septiembre por corresponder a la fenología local y porque hace que el ciclo de 210 días cierre en marzo/abril, coincidente con la cosecha mendocina.
- **Reposo — Kc = 0,20.** FAO-56 indica que tras la caída de hoja el Kc de un cultivo deciduo es ≈ 0,20 con suelo desnudo y seco (0,50–0,80 con cobertura activa).

### Kc del durazno

Se adoptan los valores de FAO-56 Tabla 12 para la fila **"stone fruit, no ground cover, killing frost"**: Kc ini = 0,45, Kc mid = 0,90, Kc end = 0,65. Reemplaza la combinación previa (0,45 / 1,15 / 0,75) que mezclaba valores de filas distintas de la misma tabla.

- **Killing frost:** Mendoza tiene heladas fuertes en invierno, por lo que la columna "with killing frost" de la Tabla 12 aplica directamente.
- **No ground cover:** el manejo tradicional del suelo en frutales y viñedos de Mendoza es por **labranza** (rotocultivado, arada, rastreada), con el interfilar de tierra desnuda. Las coberturas vegetales activas aparecen en la bibliografía regional como una alternativa estudiada y promovida por INTA, no como la práctica predominante. Además, el riego por manto que predomina en el sur de Mendoza es consistente con suelo desnudo: una cobertura activa compite con el agua del riego a manto. Fuentes en "Manejo del suelo en frutales y viñedos de Mendoza" más arriba.

### Precipitación efectiva

El sistema estima la fracción de lluvia que efectivamente infiltra el suelo con la siguiente regla:

- Lluvias menores a 2 mm se asumen completamente evaporadas (suelo árido, superficie caliente).
- Lluvias mayores o iguales a 2 mm aportan al balance el 80 % de su valor; el 20 % restante representa pérdidas por evaporación superficial y escurrimiento.

**Por qué este criterio.** FAO (Brouwer & Heibloem, 1986) describe varios métodos para estimar la precipitación efectiva (Stamm, USDA-SCS, ratio India, métodos basados en humedad del suelo) y aclara que **no existe una fórmula universal**: la elección depende del clima y del régimen de lluvias. Estudios comparativos modernos muestran que los métodos clásicos tipo USDA-SCS tienden a **subestimar la precipitación efectiva en climas áridos** (Ali, 2017).

El sistema opera en San Rafael, Mendoza —clima árido con ~300 mm anuales—, donde los eventos de lluvia chicos a moderados (2 a 10 mm) son habituales y aportan al balance hídrico aunque sea parcialmente. Un umbral mínimo más alto descartaría una fracción significativa de la lluvia anual real. La combinación umbral 2 mm + coeficiente 0,8 es una calibración coherente con la práctica documentada en modelos diarios de balance hídrico para clima árido.

El valor del umbral y del coeficiente es ajustable: la calibración fina debería hacerse contra datos locales (lisímetro o sensores de humedad de suelo) si están disponibles.

### Propiedades hidráulicas del suelo (θ_fc y θ_wp)

El balance hídrico requiere, para cada campo, el contenido volumétrico de agua a capacidad de campo (θ_fc, −33 kPa) y en punto de marchitez permanente (θ_wp, −1500 kPa). De su diferencia surge el agua total disponible en la zona radicular: **TAW = 1000 · (θ_fc − θ_wp) · Zr** [FAO-56, Ec. 82].

El tipo de suelo se determina automáticamente clasificando las fracciones de arena/limo/arcilla de SoilGrids 2.0 según el **triángulo textural USDA**, que define **12 clases**. Las propiedades hidráulicas se toman de **Saxton & Rawls (2006)**, que cubre las 12 clases USDA de forma consistente con esa clasificación. FAO-56 Tabla 19 tabula solo 9 de las 12 texturas USDA —no incluye *franco arcillo arenoso*, *franco arcilloso* ni *arcillo arenoso*—, por lo que no es suficiente para un clasificador USDA completo; se reserva como referencia de validación cruzada.

Valores adoptados (θ volumétrico, suelo con ~2,5 % de materia orgánica):

| Clase USDA | θ_fc | θ_wp | AWC = θ_fc − θ_wp |
|---|---|---|---|
| sand (arena) | 0,10 | 0,05 | 0,05 |
| loamy sand (arena franca) | 0,12 | 0,05 | 0,07 |
| sandy loam (franco arenoso) | 0,18 | 0,08 | 0,10 |
| sandy clay loam (franco arcillo arenoso) | 0,27 | 0,17 | 0,10 |
| loam (franco) | 0,28 | 0,14 | 0,14 |
| clay loam (franco arcilloso) | 0,36 | 0,22 | 0,14 |
| silt loam (franco limoso) | 0,31 | 0,11 | 0,20 |
| silt (limoso) | 0,30 | 0,06 | 0,24 |
| silty clay loam (franco arcillo limoso) | 0,38 | 0,22 | 0,16 |
| sandy clay (arcillo arenoso) | 0,36 | 0,25 | 0,11 |
| silty clay (arcillo limoso) | 0,41 | 0,27 | 0,14 |
| clay (arcilloso) | 0,42 | 0,30 | 0,12 |

La columna AWC (θ_fc − θ_wp) es la que efectivamente entra en el TAW. Los valores son ajustables: la calibración fina debería hacerse contra datos locales (lisímetro o sensores de humedad de suelo) si están disponibles.

### Fuente satelital: Sentinel-2 (descarte de Planet Labs)

El sistema usa exclusivamente **Sentinel-2 (10 m)** vía Google Earth Engine. Se evaluó **Planet Labs (PlanetScope, 3 m)** como alternativa de mayor resolución, pero se descartó: el acceso a las imágenes de alta resolución requiere suscripción paga, y los productos públicos gratuitos de la plataforma son los mismos Sentinel-2 ya disponibles gratis en GEE. La resolución de 10 m de Sentinel-2 es suficiente para promediar el NDVI sobre el polígono de un campo agrícola.

### Conversión de lámina de riego a tiempo y volumen (definida — entrevista finca Morgan, mayo 2026; revisada junio 2026)

La recomendación se calcula en **lámina neta (mm)** —la salida natural del balance FAO-56— y se expresa además en **volumen (m³)** y **tiempo de riego**. La entrevista confirmó que el productor recibe la orden de regar en **horas** y le sirve también el volumen, por lo que se entregan las tres unidades.

El **caudal** es propio de la instalación: es el caudal de la bomba dividido por la superficie del sector (L/s/ha). **No** es la dotación del derecho de riego del DGI (esa es el agua que entrega el canal, no la tasa de aplicación del sistema). Por eso lo **carga el productor** y es **opcional**: sin él se calcula el volumen pero no el tiempo. Al despejar el tiempo, **la superficie se cancela**.

Volumen y tiempo se expresan en **bruto** (agua que el sistema debe *entregar*, mayor que la neta por pérdidas), dividiendo por la **eficiencia**, para que las tres unidades representen la misma cantidad de agua de forma consistente entre sí:

```
volumen (m³) = lámina (mm) × superficie (ha) × 10 / eficiencia
tiempo (s)   = 10.000 × lámina (mm) / (caudal (L/s/ha) × eficiencia)
```

Inversa, para confirmar un riego ingresado en tiempo o volumen y normalizarlo a lámina neta (mm):

```
lámina (mm) desde tiempo   = tiempo (s) × caudal (L/s/ha) × eficiencia / 10.000
lámina (mm) desde volumen  = volumen (m³) × eficiencia / (superficie (ha) × 10)
```

- **Caudal (L/s/ha):** caudal de la bomba / superficie del sector. Opcional; sin él no se calcula el tiempo. **No** se aplica default: es específico de cada instalación y no es justificable bibliográficamente (a diferencia de la eficiencia). El máximo legal del DGI (1,5 L/s/ha) es el derecho de agua del canal, no la tasa de aplicación del sistema, por eso ya no se usa como default.
- **Eficiencia:** corrige pérdidas; **0,85 aspersión** (FAO-56: aspersión/microaspersión 85–90 %) y **0,6 superficial**. Se deriva del método de riego (no la ingresa el productor).
- `volumen_m3` y `tiempo_min` se **persisten** en la recomendación al generarse (inmutables).
- La confirmación de riego acepta **tiempo** (si el sector tiene caudal) o **volumen (m³)**; ambos se normalizan a lámina neta para el balance.

**Riego por goteo (pendiente / futuro):** la tasa NO se deriva de la dotación/ha sino de los emisores (caudal por gotero × densidad), y FAO-56 añade un factor de **fracción mojada** al balance. La conversión se implementa como estrategia por `tipo_riego` para incorporarlo sin refactor. Ver `docs/diseno/sprint-2-sectores.md`.
