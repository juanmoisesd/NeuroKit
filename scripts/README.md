# Scripts de Análisis Neurofisiológico para NeuroKit

Este directorio contiene scripts de Python diseñados para el análisis automatizado de señales neurofisiológicas, utilizando la librería `NeuroKit2`.

## Contenido

1.  **`analyze_ecg.py`**: Procesamiento de señales de Electrocardiografía (ECG).
2.  **`analyze_eda.py`**: Análisis de Actividad Electrodérmica (EDA).
3.  **`analyze_multimodal.py`**: Integración de señales ECG, PPG y RSP.

## Requisitos

```bash
pip install neurokit2 pandas matplotlib
```

## Reproducibilidad

Cada script lee datos de `data/` y guarda resultados en `results/`.

---
**Autor:** Dr. Juan Moisés de la Serna Tuya
**DOI:** 10.5281/zenodo.19613071
