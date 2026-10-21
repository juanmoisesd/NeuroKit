# Telemetry Control Center

Aplicación nativa de escritorio para Windows 10 enfocada en auditar y modificar de manera segura políticas de telemetría, publicidad, privacidad y tareas programadas.

## Características

1. **Modo Sólo Lectura (Análisis):** Permite revisar el estado actual de las configuraciones desde el registro sin hacer modificaciones inmediatas.
2. **Aplicación Individual:** Modifica configuraciones específicas una a una, mostrando la justificación técnica, el valor recomendado y las limitaciones impuestas por la edición de Windows.
3. **Respaldo y Reversión:** Respalda temporalmente en memoria el valor previo de cada clave del registro modificada, permitiendo revertir los cambios si es necesario.
4. **Seguridad Intacta:** Diseñado expresamente para excluir de su impacto a Windows Defender, Firewall, SmartScreen, UAC y Windows Update. No altera componentes de seguridad.

## Aclaración Importante
Esta herramienta audita la **configuración local** del Registro de Windows. Es importante notar que *no* se afirma que se elimina toda la telemetría, dado que ciertos componentes a nivel de red pueden seguir interactuando con los servidores de Microsoft independientemente de la política del Registro, lo cual resulta evidente si se analiza el tráfico de red observado en un firewall de borde.

## Requisitos
- Windows 10 (64-bit)
- Privilegios de Administrador (necesarios para modificar claves en HKEY_LOCAL_MACHINE).

## Uso
- Ejecuta `TelemetryControlCenterApp.exe`.
- Clic en "Analizar" para leer las configuraciones actuales.
- Selecciona una política en la lista y presiona "Aplicar Seleccionado" para fijar el valor recomendado.
- Presiona "Revertir Seleccionado" si deseas deshacer la aplicación reciente.
