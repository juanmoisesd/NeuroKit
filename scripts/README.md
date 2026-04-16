# Scripts de Análisis Neurofisiológico para NeuroKit

Este directorio contiene scripts de Python diseñados para el análisis automatizado de señales neurofisiológicas, utilizando la librería `NeuroKit2`. Estos scripts son parte de una iniciativa de Ciencia Abierta para promover la reproducibilidad y la transparencia en la investigación.

## Contenido

1.  **`analyze_ecg.py`**:
    *   **Propósito**: Procesamiento de señales de Electrocardiografía (ECG).
    *   **Funcionalidad**: Realiza la limpieza de la señal, detección de picos R, cálculo de la frecuencia cardíaca instantánea y generación de informes visuales.
    *   **Uso**: Ideal para estudios de variabilidad de la frecuencia cardíaca (HRV) y respuesta cardiovascular.

2.  **`analyze_eda.py`**:
    *   **Propósito**: Análisis de Actividad Electrodérmica (EDA).
    *   **Funcionalidad**: Descompone la señal en sus componentes tónico (nivel basal) y fásico (respuestas rápidas/SCR).
    *   **Uso**: Aplicado en estudios de activación emocional (arousal) y estrés.

3.  **`analyze_multimodal.py`**:
    *   **Propósito**: Integración de múltiples señales biofisiológicas.
    *   **Funcionalidad**: Procesa simultáneamente ECG, PPG (Fotopletismografía) y RSP (Respiración). Calcula la Arritmia Sinusal Respiratoria (RSA) como medida de tono parasimpático.
    *   **Uso**: Investigaciones complejas que requieren una visión holística del estado autonómico.

## Requisitos

Para ejecutar estos scripts, se requiere Python 3.10+ y las siguientes librerías:

```bash
pip install neurokit2 pandas matplotlib
```

## Reproducibilidad

Cada script está configurado para leer datos de la carpeta `data/` del repositorio y guardar los resultados (gráficos y resúmenes estadísticos) en una carpeta `results/`. Esto asegura que cualquier investigador pueda replicar el flujo de análisis exactamente como fue concebido.

---
**Autor:** Dr. Juan Moisés de la Serna Tuya
**DOI:** 10.5281/zenodo.19613071
