# WiFi Performance Manager

## Resumen del Proyecto

WiFi Performance Manager es una aplicación de escritorio desarrollada con Python (PySide6) que monitoriza y optimiza conexiones Wi-Fi en Windows 10/11 (64-bit). El objetivo principal es maximizar la estabilidad y rendimiento utilizando mediciones reales y herramientas nativas del sistema operativo.

## Características

*   **Diagnóstico en tiempo real:** Utiliza `netsh` y `powershell` (o WMI) para leer datos reales (SSID, BSSID, potencia de señal, banda).
*   **Métricas de Calidad:** Mide latencia, pérdida de paquetes y jitter usando pings reales.
*   **Histórico y Base de datos local:** Almacena todos los cambios y métricas en SQLite de forma privada.
*   **Optimizador Reversible:** Aplica cambios a propiedades avanzadas del adaptador mediante PowerShell, manteniendo registro para poder deshacerlos en cualquier momento.
*   **Operación Silenciosa:** Un hilo de monitorización verifica el rendimiento en segundo plano y registra alertas ante caídas de calidad.

## Componentes y Arquitectura

*   `src/network/`: Obtiene información de la interfaz y comprueba la conectividad (pings).
*   `src/wifi/`: Analiza el entorno y busca canales congestionados o señales débiles.
*   `src/optimizer/`: Aplica propiedades avanzadas (ej. _RoamingAggressiveness_) usando PowerShell.
*   `src/storage/`: Administra la base de datos `wifi_performance.db`.
*   `src/monitoring/`: Lazo de retroalimentación inteligente para diagnosticar desconexiones o latencias altas.

## Notas Técnicas para Pruebas en Windows Real

Dado que el desarrollo actual se realiza en un entorno Linux, gran parte de los comandos de bajo nivel de Windows (`netsh`, comandos `powershell`, privilegios UAC) se han simulado (Mocked) en el código y en los tests.

**Para validar el 100% de la funcionalidad, es REQUISITO INDISPENSABLE compilar y ejecutar en un entorno Windows nativo:**

1.  **Conectividad:** Validar que los pings devuelven latencias reales.
2.  **Escaneo Wi-Fi:** Verificar que `netsh wlan show networks mode=bssid` devuelve las redes correctas (se requiere que el hardware soporte escaneo activo).
3.  **Optimizador:** Probar el cambio de propiedades de red. **Nota:** `Set-NetAdapterAdvancedProperty` requiere permisos de **Administrador**. El instalador o la ejecución deben solicitar elevación (UAC). El script `build.py` incluye el flag `--uac-admin`.

## Compilación

```bash
pip install -r requirements.txt
python scripts/build.py
```
El ejecutable se generará en la carpeta `dist/`.
