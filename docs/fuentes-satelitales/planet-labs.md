# Planet Labs — Fuente primaria de imágenes satelitales

## Por qué Planet Labs

El sistema utiliza Planet Labs como fuente primaria de NDVI por dos razones principales frente a Sentinel-2:

- **Frecuencia**: PlanetScope captura imágenes diarias vs cada 5-15 días de Sentinel-2 (según nubosidad).
- **Resolución**: 3 metros/pixel vs 10 metros/pixel — más preciso para campos chicos típicos de San Rafael.

El acceso es a través del programa **Education & Research** de Planet Labs, que otorga cuota mensual sin costo para proyectos académicos.

---

## Colección utilizada

**PlanetScope (PSScene)** — satélites de observación terrestre con 4 bandas espectrales.

| Banda | Longitud de onda | Uso |
|-------|-----------------|-----|
| Red (B3) | 0.62–0.67 µm | Cálculo NDVI |
| NIR (B4) | 0.841–0.876 µm | Cálculo NDVI |

**Bundle**: `analytic_sr_udm2` (superficie reflectante, corrección atmosférica aplicada).

**Fórmula NDVI:**
```
NDVI = (NIR - Red) / (NIR + Red)
```

Los valores de SR están escalados × 10,000 — se dividen antes del cálculo.

---

## Flujo de obtención de NDVI

1. **Búsqueda** (Data API): se buscan escenas PSScene sobre el polígono del campo en los últimos 30 días, filtradas por cobertura de nubes < 20%.
2. **Activación** (Orders API): se solicita el asset `analytic_sr_udm2` con clip al polígono. El proceso de corrección atmosférica puede tomar entre 5 y 30 minutos.
3. **Descarga**: se descarga el GeoTIFF recortado con las bandas Red y NIR.
4. **Cálculo**: se calcula el NDVI promedio sobre el polígono usando `rasterio` y `numpy`.
5. **Persistencia**: el resultado se guarda en `satellite_records` con `source = planet`.

El job corre a las **21hs** para que el NDVI esté disponible cuando el job de recomendación ejecute a las **00:01hs**.

---

## Fallback

Si Planet no tiene imagen disponible (nubosidad, cuota agotada, error de API), el sistema recurre a **Google Earth Engine / Sentinel-2**. Si tampoco hay imagen GEE reciente, el Kc se calcula de forma tabular según etapa fenológica (FAO-56).

---

## Autenticación

Variable de entorno: `PLANET_API_KEY`

La API key se obtiene desde **Account → API Keys** en [insights.planet.com](https://insights.planet.com).

---

## Referencias

- Documentación oficial: https://developers.planet.com/docs/
- Python SDK: https://planet-sdk-for-python-v2.readthedocs.io/
- Especificaciones PlanetScope: https://docs.planet.com/data/imagery/planetscope/
