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

### Sentinel-2 y procesamiento satelital
- **Google Earth Engine — Sentinel-2:** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- **Google Earth Engine — Sentinel-1:** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD
- **NDVI a Kc (investigación):** https://www.sciencedirect.com/science/article/abs/pii/S037837742030233X

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

### Integración de pronóstico climático
- **Forecast integration in irrigation:** https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023WR035810

---

## Citas clave para la tesis

> Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. FAO, Rome.

Esta es la cita principal del método de cálculo ETo Penman-Monteith y balance hídrico que usa el sistema.
