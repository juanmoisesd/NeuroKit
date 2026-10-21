"""Interfaz gráfica de usuario (GUI) en español para Safe Debloat Manager."""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional

from safe_debloat_manager.core.models import DebloatItem, ItemCategory, SafetyLevel, format_size
from safe_debloat_manager.core.scanner import DebloatScanner
from safe_debloat_manager.core.cleaner import DebloatCleaner, CleanerResult
from safe_debloat_manager.core.logger import ActionLogger
from safe_debloat_manager.core.recovery import RecoveryManager


class ConfirmationDialog(tk.Toplevel):
    """Diálogo modal de confirmación antes de la eliminación."""

    def __init__(self, parent, selected_items: List[DebloatItem], simulation_mode: bool, create_restore_point: bool):
        super().__init__(parent)
        self.title("Confirmación de Operación - Safe Debloat Manager")
        self.geometry("650x480")
        self.minsize(550, 400)
        self.grab_set()

        self.confirmed = False
        self.selected_items = selected_items
        self.simulation_mode = simulation_mode
        self.create_restore_point = create_restore_point

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Banner
        header_color = "#2b5797" if self.simulation_mode else "#d9534f"
        header_text = "MODO SIMULACIÓN (Sin cambios reales)" if self.simulation_mode else "¡ATENCIÓN! ELIMINACIÓN REAL"

        lbl_header = tk.Label(
            main_frame,
            text=header_text,
            bg=header_color,
            fg="white",
            font=("Helvetica", 12, "bold"),
            pady=8,
        )
        lbl_header.pack(fill=tk.X, pady=(0, 10))

        # Summary Info
        total_size = sum(item.size_bytes for item in self.selected_items)
        excluded_count = sum(1 for item in self.selected_items if item.is_excluded_by_default)

        info_text = (
            f"Elementos seleccionados para procesar: {len(self.selected_items)}\n"
            f"Espacio estimado a liberar: {format_size(total_size)}\n"
            f"Punto de restauración activado: {'SÍ' if self.create_restore_point else 'NO'}\n"
        )
        if excluded_count > 0:
            info_text += f"\n⚠️ PRECAUCIÓN: Ha seleccionado {excluded_count} elementos excluidos por defecto."

        lbl_info = ttk.Label(main_frame, text=info_text, font=("Helvetica", 10), justify=tk.LEFT)
        lbl_info.pack(anchor=tk.W, pady=(0, 10))

        # Treeview list of items to confirm
        lbl_list = ttk.Label(main_frame, text="Detalle de elementos a procesar:", font=("Helvetica", 9, "bold"))
        lbl_list.pack(anchor=tk.W, pady=(5, 2))

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tree = ttk.Treeview(
            list_frame,
            columns=("Nombre", "Categoría", "Tamaño", "Estado"),
            show="headings",
            height=8,
        )
        tree.heading("Nombre", text="Nombre")
        tree.heading("Categoría", text="Categoría")
        tree.heading("Tamaño", text="Tamaño")
        tree.heading("Estado", text="Estado de Exclusión")

        tree.column("Nombre", width=200)
        tree.column("Categoría", width=140)
        tree.column("Tamaño", width=100, anchor=tk.E)
        tree.column("Estado", width=140)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for item in self.selected_items:
            tree.insert(
                "",
                tk.END,
                values=(
                    item.name,
                    item.category.value if isinstance(item.category, ItemCategory) else str(item.category),
                    item.formatted_size,
                    "Excluido por Defecto" if item.is_excluded_by_default else "Seguro",
                ),
            )

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        btn_confirm = ttk.Button(
            btn_frame,
            text="✓ Confirmar y Continuar",
            command=self._on_confirm,
        )
        btn_confirm.pack(side=tk.RIGHT, padx=5)

        btn_cancel = ttk.Button(
            btn_frame,
            text="✕ Cancelar",
            command=self._on_cancel,
        )
        btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _on_confirm(self):
        self.confirmed = True
        self.destroy()

    def _on_cancel(self):
        self.confirmed = False
        self.destroy()


class SafeDebloatApp(tk.Tk):
    """Aplicación principal gráfica de Safe Debloat Manager."""

    def __init__(self, force_mock: bool = False):
        super().__init__()

        self.title("Safe Debloat Manager v1.0 - Windows 10 x64")
        self.geometry("1024x680")
        self.minsize(850, 550)

        # Configurar icono / tema
        try:
            self.style = ttk.Style()
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        # Componentes del core
        self.logger = ActionLogger()
        self.recovery_mgr = RecoveryManager()
        self.scanner = DebloatScanner(force_mock=force_mock)
        self.cleaner = DebloatCleaner(logger=self.logger, recovery_mgr=self.recovery_mgr)

        self.items: List[DebloatItem] = []

        self._build_ui()
        self._on_scan()

    def _build_ui(self):
        """Construye los controles e interfaz por pestañas."""
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pestañas
        self.tab_scan = ttk.Frame(notebook)
        self.tab_logs = ttk.Frame(notebook)
        self.tab_recovery = ttk.Frame(notebook)

        notebook.add(self.tab_scan, text="  🔍 Escanear y Limpiar  ")
        notebook.add(self.tab_logs, text="  📋 Registro de Acciones  ")
        notebook.add(self.tab_recovery, text="  ⏪ Recuperación y Respaldos  ")

        self._build_scan_tab()
        self._build_logs_tab()
        self._build_recovery_tab()

    def _build_scan_tab(self):
        """Pestaña principal de escaneo y selección."""
        top_frame = ttk.LabelFrame(self.tab_scan, text=" Configuración de Escaneo y Seguridad ", padding="10")
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_scan = ttk.Button(top_frame, text="🔍 Escanear Sistema", command=self._on_scan)
        btn_scan.pack(side=tk.LEFT, padx=5)

        self.var_sim_mode = tk.BooleanVar(value=True)
        chk_sim = ttk.Checkbutton(
            top_frame,
            text="Modo Simulación (Dry-Run seguro sin borrar)",
            variable=self.var_sim_mode,
        )
        chk_sim.pack(side=tk.LEFT, padx=15)

        self.var_restore_point = tk.BooleanVar(value=True)
        chk_rp = ttk.Checkbutton(
            top_frame,
            text="Crear Punto de Restauración antes de limpiar",
            variable=self.var_restore_point,
        )
        chk_rp.pack(side=tk.LEFT, padx=10)

        # Tabla de Elementos
        mid_frame = ttk.Frame(self.tab_scan)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("sel", "name", "cat", "path", "desc", "size", "deps", "safety")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("sel", text="[✓]")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("cat", text="Categoría")
        self.tree.heading("path", text="Ruta / Paquete")
        self.tree.heading("desc", text="Función")
        self.tree.heading("size", text="Tamaño Real")
        self.tree.heading("deps", text="Dependencias Conocidas")
        self.tree.heading("safety", text="Estado de Exclusión")

        self.tree.column("sel", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=150)
        self.tree.column("cat", width=150)
        self.tree.column("path", width=200)
        self.tree.column("desc", width=200)
        self.tree.column("size", width=90, anchor=tk.E)
        self.tree.column("deps", width=180)
        self.tree.column("safety", width=140)

        scrollbar_y = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(mid_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        mid_frame.grid_rowconfigure(0, weight=1)
        mid_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Panel Inferior de Detalles y Selección
        bottom_frame = ttk.Frame(self.tab_scan)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        # Panel Izquierdo: Detalles
        detail_box = ttk.LabelFrame(bottom_frame, text=" Detalles del Elemento Seleccionado ", padding="8")
        detail_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.lbl_detail_text = tk.Text(detail_box, height=5, wrap=tk.WORD, font=("Helvetica", 9), bg="#f8f9fa")
        self.lbl_detail_text.pack(fill=tk.BOTH, expand=True)

        # Panel Derecho: Botones de Acción
        ctrl_box = ttk.LabelFrame(bottom_frame, text=" Controles de Selección y Ejecución ", padding="8")
        ctrl_box.pack(side=tk.RIGHT, fill=tk.Y)

        btn_sel_safe = ttk.Button(ctrl_box, text="Seleccionar Seguros", command=self._select_safe_only)
        btn_sel_safe.pack(fill=tk.X, pady=2)

        btn_desel_all = ttk.Button(ctrl_box, text="Deseleccionar Todo", command=self._deselect_all)
        btn_desel_all.pack(fill=tk.X, pady=2)

        btn_invert = ttk.Button(ctrl_box, text="Invertir Selección", command=self._invert_selection)
        btn_invert.pack(fill=tk.X, pady=2)

        btn_clean = ttk.Button(ctrl_box, text="🧹 Ejecutar Limpieza", command=self._on_execute_clean)
        btn_clean.pack(fill=tk.X, pady=(10, 2))

        # Status Bar
        self.lbl_status = ttk.Label(self.tab_scan, text="Listo.", font=("Helvetica", 9, "italic"))
        self.lbl_status.pack(anchor=tk.W, padx=10, pady=(2, 5))

    def _build_logs_tab(self):
        """Pestaña de visor de registro de acciones."""
        frame = ttk.Frame(self.tab_logs, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        btn_export = ttk.Button(top_bar, text="📁 Exportar Registro (.log)", command=self._on_export_log)
        btn_export.pack(side=tk.LEFT, padx=5)

        btn_refresh = ttk.Button(top_bar, text="🔄 Actualizar Visor", command=self._refresh_logs_view)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        self.txt_logs = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.txt_logs.yview)
        scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.txt_logs.xview)
        self.txt_logs.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.txt_logs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_recovery_tab(self):
        """Pestaña de respaldos y procedimientos de recuperación."""
        frame = ttk.Frame(self.tab_recovery, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_info = ttk.Label(
            frame,
            text="Historial de Respaldos de Inicio y Comandos de Restauración de Aplicaciones",
            font=("Helvetica", 10, "bold"),
        )
        lbl_info.pack(anchor=tk.W, pady=(0, 10))

        # Lista de respaldos de inicio
        frame_backups = ttk.LabelFrame(frame, text=" Respaldos de Registro de Programas de Inicio ", padding="8")
        frame_backups.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tree_backups = ttk.Treeview(
            frame_backups,
            columns=("fecha", "nombre", "clave", "comando"),
            show="headings",
            height=6,
        )
        self.tree_backups.heading("fecha", text="Fecha de Respaldo")
        self.tree_backups.heading("nombre", text="Nombre del Programa")
        self.tree_backups.heading("clave", text="Clave de Registro")
        self.tree_backups.heading("comando", text="Comando Registrado")

        self.tree_backups.column("fecha", width=140)
        self.tree_backups.column("nombre", width=150)
        self.tree_backups.column("clave", width=250)
        self.tree_backups.column("comando", width=300)

        self.tree_backups.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scroll_b = ttk.Scrollbar(frame_backups, orient=tk.VERTICAL, command=self.tree_backups.yview)
        self.tree_backups.configure(yscrollcommand=scroll_b.set)
        scroll_b.pack(side=tk.RIGHT, fill=tk.Y)

        btn_restore_b = ttk.Button(frame, text="⏪ Restaurar Inicio Seleccionado", command=self._on_restore_startup)
        btn_restore_b.pack(anchor=tk.W, pady=(0, 10))

        # Guía de Puntos de Restauración
        frame_guide = ttk.LabelFrame(frame, text=" Instrucciones para Restauración de Sistema ", padding="8")
        frame_guide.pack(fill=tk.X)

        guide_text = (
            "• Para restaurar un paquete AppX eliminado: Utilice el comando de recuperación mostrado en los detalles del elemento en PowerShell.\n"
            "• Para restaurar el sistema completo a un punto anterior: Ejecute 'rstrui.exe' en la consola o busque 'Crear un punto de restauración' en el menú Inicio.\n"
            "• Safe Debloat Manager crea automáticamente un archivo .json de respaldo en la carpeta 'backups/' antes de deshabilitar cualquier programa de inicio."
        )
        lbl_guide = ttk.Label(frame_guide, text=guide_text, justify=tk.LEFT, font=("Helvetica", 9))
        lbl_guide.pack(anchor=tk.W)

        self._refresh_recovery_view()

    def _on_scan(self):
        """Ejecuta el escaneo del sistema."""
        self.lbl_status.config(text="Escaneando el sistema, por favor espere...")
        self.update_idletasks()

        self.items = self.scanner.scan_all()
        self._populate_tree()

        sel_count = sum(1 for item in self.items if item.is_selected)
        total_size = sum(item.size_bytes for item in self.items if item.is_selected)
        self.lbl_status.config(
            text=f"Escaneo completado. Se encontraron {len(self.items)} elementos. "
            f"Seleccionados por defecto: {sel_count} ({format_size(total_size)})"
        )

    def _populate_tree(self):
        """Rellena el Treeview con los elementos escaneados."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.items:
            sel_str = "[✓]" if item.is_selected else "[ ]"
            safety_str = "Excluido por Defecto" if item.is_excluded_by_default else "Seguro"

            self.tree.insert(
                "",
                tk.END,
                iid=item.item_id,
                values=(
                    sel_str,
                    item.name,
                    item.category.value if isinstance(item.category, ItemCategory) else str(item.category),
                    item.path_or_package,
                    item.description,
                    item.formatted_size,
                    item.dependencies,
                    safety_str,
                ),
            )

    def _on_tree_click(self, event):
        """Maneja el clic sobre las casillas de selección del Treeview."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # Columna de casilla de selección
                item_id = self.tree.focus()
                if item_id:
                    for item in self.items:
                        if item.item_id == item_id:
                            item.is_selected = not item.is_selected
                            sel_str = "[✓]" if item.is_selected else "[ ]"
                            self.tree.set(item_id, "sel", sel_str)
                            self._update_status_summary()
                            break

    def _on_tree_select(self, event):
        """Maneja la selección de una fila para actualizar el panel de detalles."""
        selected_id = self.tree.focus()
        if not selected_id:
            return

        for item in self.items:
            if item.item_id == selected_id:
                exc_info = f"\n• Motivo de Exclusión: {item.exclusion_reason}" if item.exclusion_reason else ""
                details_str = (
                    f"Nombre: {item.name}\n"
                    f"Categoría: {item.category.value if isinstance(item.category, ItemCategory) else str(item.category)}\n"
                    f"Ruta o Paquete: {item.path_or_package}\n"
                    f"Función: {item.description}\n"
                    f"Tamaño Real: {item.formatted_size}\n"
                    f"Dependencias Conocidas: {item.dependencies}"
                    f"{exc_info}\n"
                    f"Comando de Recuperación: {item.recovery_command}"
                )
                self.lbl_detail_text.delete("1.0", tk.END)
                self.lbl_detail_text.insert(tk.END, details_str)
                break

    def _select_safe_only(self):
        """Selecciona solo los elementos seguros (excluye por defecto los no recomendados)."""
        for item in self.items:
            item.is_selected = not item.is_excluded_by_default
            sel_str = "[✓]" if item.is_selected else "[ ]"
            if self.tree.exists(item.item_id):
                self.tree.set(item.item_id, "sel", sel_str)
        self._update_status_summary()

    def _deselect_all(self):
        """Deselecciona todos los elementos."""
        for item in self.items:
            item.is_selected = False
            if self.tree.exists(item.item_id):
                self.tree.set(item.item_id, "sel", "[ ]")
        self._update_status_summary()

    def _invert_selection(self):
        """Invierte la selección actual."""
        for item in self.items:
            item.is_selected = not item.is_selected
            sel_str = "[✓]" if item.is_selected else "[ ]"
            if self.tree.exists(item.item_id):
                self.tree.set(item.item_id, "sel", sel_str)
        self._update_status_summary()

    def _update_status_summary(self):
        """Actualiza el resumen de elementos seleccionados en la barra de estado."""
        sel_items = [i for i in self.items if i.is_selected]
        total_bytes = sum(i.size_bytes for i in sel_items)
        self.lbl_status.config(
            text=f"Seleccionados: {len(sel_items)} de {len(self.items)} | "
            f"Espacio total a liberar: {format_size(total_bytes)}"
        )

    def _on_execute_clean(self):
        """Abre el diálogo de confirmación y ejecuta la limpieza si es aceptada."""
        selected_items = [i for i in self.items if i.is_selected]

        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione al menos un elemento para limpiar.")
            return

        sim_mode = self.var_sim_mode.get()
        create_rp = self.var_restore_point.get()

        dialog = ConfirmationDialog(
            parent=self,
            selected_items=selected_items,
            simulation_mode=sim_mode,
            create_restore_point=create_rp,
        )
        self.wait_window(dialog)

        if not dialog.confirmed:
            self.lbl_status.config(text="Operación cancelada por el usuario.")
            return

        # Ejecución
        self.lbl_status.config(text="Procesando limpieza...")
        self.update_idletasks()

        result: CleanerResult = self.cleaner.execute_cleaning(
            items=self.items,
            simulation_mode=sim_mode,
            create_restore_point=create_rp,
        )

        self._refresh_logs_view()
        self._refresh_recovery_view()

        msg = "\n".join(result.summary_messages)
        title = "Simulación Finalizada" if sim_mode else "Limpieza Finalizada"
        messagebox.showinfo(title, msg)

        # Re-escanear para actualizar estado si fue real
        if not sim_mode:
            self._on_scan()

    def _on_export_log(self):
        """Exporta el archivo de registro a una ubicación seleccionada por el usuario."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Archivos de Log", "*.log"), ("Todos los archivos", "*.*")],
            title="Exportar Registro de Acciones",
        )
        if file_path:
            if self.logger.export_log(file_path):
                messagebox.showinfo("Exportación Correcta", f"Registro guardado con éxito en:\n{file_path}")
            else:
                messagebox.showerror("Error de Exportación", "No se pudo guardar el archivo de registro.")

    def _refresh_logs_view(self):
        """Actualiza el cuadro de texto del historial de logs."""
        self.txt_logs.delete("1.0", tk.END)
        records = self.logger.get_all_records()
        for r in records:
            self.txt_logs.insert(tk.END, r.to_string() + "\n")

    def _refresh_recovery_view(self):
        """Carga la lista de respaldos de inicio disponibles."""
        for row in self.tree_backups.get_children():
            self.tree_backups.delete(row)

        backups = self.recovery_mgr.get_all_backups()
        for b in backups:
            self.tree_backups.insert(
                "",
                tk.END,
                iid=b.get("backup_file"),
                values=(
                    b.get("timestamp", "N/A"),
                    b.get("item_name", "Desconocido"),
                    b.get("reg_key", "N/A"),
                    b.get("raw_command", "N/A"),
                ),
            )

    def _on_restore_startup(self):
        """Restaura una entrada de inicio respaldada."""
        selected = self.tree_backups.focus()
        if not selected:
            messagebox.showwarning("Sin Selección", "Seleccione un respaldo de inicio para restaurar.")
            return

        ok, msg = self.recovery_mgr.restore_startup_backup(selected)
        if ok:
            messagebox.showinfo("Restauración Completada", msg)
            self._refresh_recovery_view()
        else:
            messagebox.showerror("Error al Restaurar", msg)
