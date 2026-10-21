# Safe Debloat Manager v1.0 - Windows 10 x64

**Safe Debloat Manager** es una utilidad gráfica avanzada y segura desarrollada para Windows 10 x64. Su objetivo principal es identificar y eliminar de forma controlada aplicaciones preinstaladas (bloatware), programas de inicio innecesarios y archivos temporales seguros, protegiendo la estabilidad del sistema operativo mediante reglas de exclusión inteligentes, modo de simulación y mecanismos de recuperación.

---

## 🛡️ Principios de Seguridad y Salvaguardas

Para evitar daños en el sistema operativo, Safe Debloat Manager implementa las siguientes garantías:

1. **Información Transparente Antes de Eliminar**: Muestra para cada elemento identificable:
   - **Ruta o Paquete**: Ruta absoluta en disco o nombre del paquete AppX.
   - **Función**: Descripción clara del propósito del elemento.
   - **Tamaño Real**: Espacio exacto ocupado en disco (formateado en KB, MB o GB).
   - **Dependencias Conocidas**: Impacto en el sistema o aplicaciones vinculadas.
2. **Exclusión por Defecto de Componentes Críticos**: Excluye automáticamente de la selección inicial:
   - **Componentes del Sistema**: Menú Inicio, Explorador de Windows, ShellExperienceHost, etc.
   - **Controladores (Drivers)**: Audio, vídeo, chipset, Bluetooth, Touchpad (Realtek, Intel, NVIDIA, AMD, Synaptics).
   - **Runtimes Compartidos**: Microsoft Visual C++ Redistributables, .NET Framework / Desktop Runtime, DirectX, Universal CRT, XAML.
   - **Herramientas de Seguridad**: Windows Defender, Antivirus de terceros, Firewall, SmartScreen.
   - **Windows Update**: Servicios núcleo de actualizaciones del sistema.
3. **Prohibición de Eliminación de Carpetas Raíz**:
   - Bloqueo estricto de borrado en directorios críticos como `C:\`, `C:\Windows`, `C:\Windows\System32`, `C:\Program Files`.
   - La limpieza de archivos temporales borra únicamente el contenido de las carpetas temporales seguras, gestionando los archivos en uso sin interrumpir el proceso ni usar scripts de borrado masivo sin control.
4. **Modo Simulación (Dry Run)**: Permite previsualizar todo el proceso, calcular el espacio liberado y generar el registro de acciones sin modificar archivos o claves de registro.
5. **Procedimientos de Recuperación**:
   - Creación automática de **Puntos de Restauración del Sistema** previa a la limpieza.
   - **Respaldo del Registro**: Guarda respaldos `.json` en la carpeta `backups/` antes de deshabilitar programas de inicio.
   - **Comandos de Reinstalación AppX**: Muestra comandos oficiales de PowerShell (`Add-AppxPackage -Register...`) para restaurar aplicaciones desinstaladas.

---

## 💻 Características Principales

- **Interfaz Gráfica en Español**: Diseñada con `tkinter` / `ttk`, organizada en 3 pestañas:
  1. `🔍 Escanear y Limpiar`: Tabla interactiva con filtro de casillas `[✓]`, visor de detalles completos y botones de selección rápida.
  2. `📋 Registro de Acciones`: Visor en tiempo real de auditoría de acciones (escaneos, simulaciones, borrados, errores) con opción de exportación a `.log`.
  3. `⏪ Recuperación y Respaldos`: Historial de respaldos de registro de inicio con opción de restauración en un clic e instrucciones de recuperación del sistema.
- **Paso de Confirmación Modal**: Diálogo de confirmación previo que resume la cantidad de elementos, el espacio total a liberar y advierte si se han seleccionado elementos excluidos por defecto.

---

## 🚀 Guía de Instalación y Uso

### Requisitos
- **Sistema Operativo**: Windows 10 x64 (compatible con ejecución simulada en otros sistemas para pruebas).
- **Python**: 3.10 o superior (para ejecutar desde código fuente).
- **Permisos**: Ejecutar como Administrador para modificar claves de registro HKLM o desinstalar ciertos paquetes AppX.

### Ejecución desde el Código Fuente
1. Clone o descargue el repositorio.
2. Ejecute la aplicación mediante el script lanzador:
   ```bash
   python run_safe_debloat_manager.py
   ```
   *Para probar en entornos Linux/macOS o integración continua sin Windows, utilice la opción `--mock`:*
   ```bash
   python run_safe_debloat_manager.py --mock
   ```

### Uso Paso a Paso de la Interfaz Gráfica
1. Haga clic en **`🔍 Escanear Sistema`** para analizar el equipo.
2. Revise la lista de elementos y seleccione una fila para ver su información en el panel **Detalles del Elemento Seleccionado**.
3. Utilice **`Seleccionar Seguros`** para asegurar que los componentes del sistema permancen excluidos.
4. Mantenga activada la casilla **`Modo Simulación`** para verificar las acciones de prueba.
5. Presione **`🧹 Ejecutar Limpieza`** y confirme en el diálogo emergente.
6. Desactive el Modo Simulación si desea aplicar la limpieza real.

---

## 📦 Compilación del Ejecutable e Instalador (.exe)

Para generar el ejecutable autónomo `SafeDebloatManager.exe` para Windows x64:

1. Instale PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Ejecute el script de construcción:
   ```bash
   python safe_debloat_manager/installer/build_installer.py
   ```
3. El ejecutable compilado se guardará en `safe_debloat_manager/installer/dist/SafeDebloatManager.exe`.
4. *(Opcional)* Si utiliza **Inno Setup**, compile el archivo `safe_debloat_manager/installer/setup_installer.iss` para generar el instalador ejecutable `SafeDebloatManager_Setup_x64.exe`.

---

## 🧪 Pruebas Unitarias e Integración

Para ejecutar la suite completa de pruebas:
```bash
pytest tests/test_safe_debloat_manager.py
```

---

## 📄 Licencia
Este módulo forma parte de la distribución del repositorio bajo Licencia MIT.
