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
- **FAO — Precipitación efectiva:** https://www.fao.org/4/x5560e/x5560e03.htm
- **FAO — Coeficientes de cultivo Kc:** Capítulo 6 del FAO Paper 56

### Planet Labs y procesamiento satelital
- **Planet Labs — Documentación general API:** https://developers.planet.com/docs/
- **Planet Labs — Data API (búsqueda de escenas):** https://developers.planet.com/docs/data/
- **Planet Labs — Orders API (descarga de bandas):** https://developers.planet.com/docs/orders/
- **Planet Labs — Python SDK:** https://planet-sdk-for-python-v2.readthedocs.io/
- **Planet Labs — PlanetScope especificaciones técnicas:** https://docs.planet.com/data/imagery/planetscope/
- **Planet Labs — Programa Education & Research:** https://www.planet.com/industries/education-and-research/
- **Google Earth Engine — Sentinel-2 (fallback):** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- **NDVI a Kc — durum wheat semi-árido:** https://www.sciencedirect.com/science/article/abs/pii/S037837742030233X
- **NDVI a Kcb — viñedo semi-árido (Campos et al. 2010):** https://www.sciencedirect.com/science/article/abs/pii/S0378377410002428
- **Revisión VI → Kc (Glenn et al. 2011):** https://onlinelibrary.wiley.com/doi/10.1002/hyp.8392

### Open-Meteo
- **Documentación API Open-Meteo:** https://open-meteo.com/en/docs
- **Variables disponibles incluyen ETo precalculada:** variable `reference_evapotranspiration`

### Agricultura en San Rafael, Mendoza
- **Panorama económico-productivo de San Rafael:** https://www.scielo.org.ar/scielo.php?script=sci_arttext&pid=S2314-15492011000200003
- **Hortalizas en San Rafael:** https://diariosanrafael.com.ar/san-rafael-registra-mas-de-300-hectareas-cultivadas-con-hortalizas-de-verano/
- **Riego a manto en San Rafael (80%):** https://diariosanrafael.com.ar/el-80-de-las-hectareas-productivas-de-san-rafael-mantienen-el-sistema-de-riego-a-manto/
- **Pequeños productores frutícolas San Rafael:** https://ri.unsam.edu.ar/bitstream/123456789/866/1/TMAG_IDAES_2016_CFN.pdf
- **Cluster ciruela industria Mendoza:** https://www.argentina.gob.ar/agricultura/prosap/cluster-de-ciruela-industria-de-mendoza

### Parámetros de suelo
- **Soil Water Parameters — Cornell:** https://nrcca.cals.cornell.edu/soil/CA2/CA0212.1-3.php
- **Water Balance Approach — Colorado State:** https://extension.colostate.edu/resource/irrigation-scheduling-the-water-balance-approach/

### SoilGrids — tipo de suelo por coordenadas
- **SoilGrids 2.0 REST API (ISRIC):** https://rest.isric.org/soilgrids/v2.0/properties/query
- **Documentación WCS (fallback):** https://docs.isric.org/globaldata/soilgrids/wcs.html

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
