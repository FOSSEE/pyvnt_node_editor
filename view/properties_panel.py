from PyQt6.QtWidgets import QGroupBox, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLabel, QWidget, QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class PropertiesPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.setMinimumWidth(120)
        self.setMaximumWidth(220)
        self.node = None
        self.fields = {}
        self.setStyleSheet("QGroupBox { font-weight: bold; }")

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.fields = {}
        self.node = None

    def set_node(self, node):
        # Always clear and rebuild, even if node is the same
        self.clear()
        if node is None:
            self.setTitle("Properties")
            return
        self.node = node
        self.setTitle(f"Properties: {getattr(node, 'get_node_title', lambda: type(node).__name__)()}")

        # --- Str_PGraphicalNode: Name and Value fields with two-way sync ---
        if node.__class__.__name__ == 'Str_PGraphicalNode' and hasattr(node, 'name_edit') and hasattr(node, 'value_edit'):
            import weakref
            # Name field
            name_edit = QLineEdit(node.name_edit.text())
            name_edit.textChanged.connect(lambda text: self._update_node_name(text))
            name_edit_ref = weakref.ref(name_edit)
            def sync_name():
                edit = name_edit_ref()
                if edit is not None and edit.text() != node.name_edit.text():
                    edit.setText(node.name_edit.text())
            node.name_edit.textChanged.connect(sync_name)
            self.layout.addRow("Name", name_edit)
            self.fields['name'] = name_edit
            # Value field
            value_edit = QLineEdit(node.value_edit.text())
            def update_node_value(text):
                if node.value_edit.text() != text:
                    node.value_edit.setText(text)
            value_edit.textChanged.connect(update_node_value)
            value_edit_ref = weakref.ref(value_edit)
            def sync_value():
                edit = value_edit_ref()
                if edit is not None and edit.text() != node.value_edit.text():
                    edit.setText(node.value_edit.text())
            node.value_edit.textChanged.connect(sync_value)
            self.layout.addRow("Value", value_edit)
            self.fields['value'] = value_edit
        # --- Name field (QLineEdit or QTextEdit) for other nodes (but not Str_PGraphicalNode) ---
        elif hasattr(node, 'name_edit') and node.__class__.__name__ != 'Str_PGraphicalNode':
            import weakref
            name_edit = QLineEdit(node.name_edit.text())
            # Live sync: update node name as user types
            name_edit.textChanged.connect(lambda text: self._update_node_name(text))
            # Sync node -> panel, avoid accessing deleted widget
            name_edit_ref = weakref.ref(name_edit)
            def sync_name():
                edit = name_edit_ref()
                if edit is not None and edit.text() != node.name_edit.text():
                    edit.setText(node.name_edit.text())
            node.name_edit.textChanged.connect(sync_name)
            self.layout.addRow("Name", name_edit)
            self.fields['name'] = name_edit
        # --- Tensor_PGraphicalNode fields (name, size, components) ---
        if (
            hasattr(node, 'size_spin') and hasattr(node, 'component_spins')
        ):
            # Size field
            import weakref
            size_spin = QSpinBox()
            size_spin.setRange(node.size_spin.minimum(), node.size_spin.maximum())
            size_spin.setValue(node.size_spin.value())
            # Update node when panel changes
            def on_panel_size_changed(v):
                node.size_spin.setValue(v)
                # Immediately refresh panel to match new size
                self.set_node(node)
            size_spin.valueChanged.connect(on_panel_size_changed)
            # Update panel when node changes, avoid deleted widget
            size_spin_ref = weakref.ref(size_spin)
            def sync_size():
                spin = size_spin_ref()
                if spin is not None and spin.value() != node.size_spin.value():
                    spin.setValue(node.size_spin.value())
            node.size_spin.valueChanged.connect(sync_size)
            self.layout.addRow("Size", size_spin)
            self.fields['size'] = size_spin

            # Components fields
            for i, node_comp_spin in enumerate(node.component_spins):
                comp_spin = QDoubleSpinBox()
                comp_spin.setDecimals(node_comp_spin.decimals())
                comp_spin.setRange(node_comp_spin.minimum(), node_comp_spin.maximum())
                comp_spin.setValue(node_comp_spin.value())
                # Update node when panel changes, but only if idx is valid
                def set_value_safe(v, idx=i):
                    if idx < len(node.component_spins):
                        node.component_spins[idx].setValue(v)
                comp_spin.valueChanged.connect(set_value_safe)
                # Update panel when node changes
                def make_node_to_panel_sync(panel_spin=comp_spin, node_spin=node_comp_spin):
                    def sync():
                        if abs(panel_spin.value() - node_spin.value()) > 1e-8:
                            panel_spin.setValue(node_spin.value())
                    node_spin.valueChanged.connect(sync)
                make_node_to_panel_sync()
                self.layout.addRow(f"Component {i+1}", comp_spin)
                self.fields[f"component_{i+1}"] = comp_spin
        # No fallback name field for List_CPGraphicalNode; handled in node UI only

        # --- Vector components (x, y, z) ---
        if hasattr(node, 'x_spin') and hasattr(node, 'y_spin') and hasattr(node, 'z_spin'):
            for comp in ['x', 'y', 'z']:
                spin = QDoubleSpinBox()
                spin.setDecimals(6)
                spin.setRange(-1e6, 1e6)
                node_spin = getattr(node, f"{comp}_spin")
                spin.setValue(node_spin.value())
                # Update node when panel changes
                spin.valueChanged.connect(lambda v, c=comp: getattr(node, f"{c}_spin").setValue(v))
                # Update panel when node changes
                def make_node_to_panel_sync(panel_spin=spin, node_spin=node_spin):
                    def sync():
                        if abs(panel_spin.value() - node_spin.value()) > 1e-8:
                            panel_spin.setValue(node_spin.value())
                    node_spin.valueChanged.connect(sync)
                make_node_to_panel_sync()
                self.layout.addRow(comp.upper(), spin)
                self.fields[comp] = spin

        # --- Dimension set (Dim_Set_PGraphicalNode) ---
        if hasattr(node, 'dim_names') and hasattr(node, 'dim_spins'):
            for name, spinbox in zip(node.dim_names, node.dim_spins):
                spin = QSpinBox()
                spin.setRange(-10, 10)
                spin.setValue(spinbox.value())
                # Update node when panel changes
                spin.valueChanged.connect(lambda v, s=spinbox: s.setValue(v))
                # Update panel when node changes
                def make_node_to_panel_sync(panel_spin=spin, node_spin=spinbox):
                    def sync():
                        if panel_spin.value() != node_spin.value():
                            panel_spin.setValue(node_spin.value())
                    node_spin.valueChanged.connect(sync)
                make_node_to_panel_sync()
                self.layout.addRow(name, spin)
                self.fields[name] = spin

        # --- List elements (List_CPGraphicalNode) ---
        if hasattr(node, 'elements_text'):
            elements_edit = QLineEdit(node.elements_text.toPlainText().replace('\n', ' | '))
            # Two-way sync: panel -> node
            def update_elements():
                new_text = elements_edit.text().replace(' | ', '\n')
                if node.elements_text.toPlainText() != new_text:
                    node.elements_text.setPlainText(new_text)
            elements_edit.editingFinished.connect(update_elements)
            # Two-way sync: node -> panel
            import weakref
            elements_edit_ref = weakref.ref(elements_edit)
            def sync_elements():
                edit = elements_edit_ref()
                node_text = node.elements_text.toPlainText().replace('\n', ' | ')
                if edit is not None and edit.text() != node_text:
                    edit.setText(node_text)
            node.elements_text.textChanged.connect(sync_elements)
            self.layout.addRow("Elements", elements_edit)
            self.fields['elements'] = elements_edit
        if hasattr(node, 'isnode_checkbox'):
            isnode_cb = QCheckBox()
            isnode_cb.setChecked(node.isnode_checkbox.isChecked())
            # Improve visibility: black outline
            isnode_cb.setStyleSheet("""
                QCheckBox { color: black; font-size: 11px; font-family: Arial; }
                QCheckBox::indicator { width: 13px; height: 13px; border: 2px solid black; border-radius: 3px; background-color: #fff; }
                QCheckBox::indicator:checked { background-color: #0078d4; border: 2px solid #0078d4; }
            """)
            # Two-way sync: panel -> node
            def update_isnode(val):
                if node.isnode_checkbox.isChecked() != val:
                    node.isnode_checkbox.setChecked(val)
            isnode_cb.toggled.connect(update_isnode)
            # Two-way sync: node -> panel
            import weakref
            isnode_cb_ref = weakref.ref(isnode_cb)
            def sync_isnode():
                cb = isnode_cb_ref()
                if cb is not None and cb.isChecked() != node.isnode_checkbox.isChecked():
                    cb.setChecked(node.isnode_checkbox.isChecked())
            node.isnode_checkbox.toggled.connect(sync_isnode)
            self.layout.addRow("Is Node List", isnode_cb)
            self.fields['isnode'] = isnode_cb

        # --- Value field (for Int_P, Flt_P, etc) ---
        if hasattr(node, 'value_spinbox'):
            spin = QSpinBox()
            spin.setValue(node.value_spinbox.value())
            spin.valueChanged.connect(lambda v: self._update_node_value(v))
            self.layout.addRow("Value", spin)
            self.fields['value'] = spin
        elif hasattr(node, 'value_spin'):
            dspin = QDoubleSpinBox()
            dspin.setDecimals(10)
            dspin.setValue(node.value_spin.value())
            dspin.valueChanged.connect(lambda v: self._update_node_value(v))
            self.layout.addRow("Value", dspin)
            self.fields['value'] = dspin

        # --- Enum items (for Enm_P) ---
        if hasattr(node, 'items_list'):
            # Multi-select QListWidget for items
            items_widget = QListWidget()
            items_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            items = [node.items_list.item(i).text() for i in range(node.items_list.count())]
            items_widget.addItems(items)
            # Sync selection from node to panel
            for i, item in enumerate(items):
                if node.items_list.item(i).isSelected():
                    items_widget.item(i).setSelected(True)
            # When user changes selection in panel, update node and default combo
            def on_items_selection_changed():
                selected = set()
                for i in range(items_widget.count()):
                    sel = items_widget.item(i).isSelected()
                    node.items_list.item(i).setSelected(sel)
                    if sel:
                        selected.add(items_widget.item(i).text())
                # Update default combo in both panel and node
                update_default_combo(selected)
            items_widget.itemSelectionChanged.connect(on_items_selection_changed)
            self.layout.addRow("Items", items_widget)
            self.fields['items'] = items_widget

            # QComboBox for default value, only from selected items
            default_combo = QComboBox()
            selected_items = [items_widget.item(i).text() for i in range(items_widget.count()) if items_widget.item(i).isSelected()]
            default_combo.addItems(selected_items)
            # Sync default from node to panel
            if hasattr(node, 'default_combo'):
                default_combo.setCurrentText(node.default_combo.currentText())
            # When user changes default in panel, update node
            def on_default_changed(val):
                if hasattr(node, 'default_combo'):
                    node.default_combo.setCurrentText(val)
            default_combo.currentTextChanged.connect(on_default_changed)
            self.layout.addRow("Default", default_combo)
            self.fields['default'] = default_combo

            # Helper to update default combo when items selection changes
            def update_default_combo(selected=None):
                if selected is None:
                    selected = [items_widget.item(i).text() for i in range(items_widget.count()) if items_widget.item(i).isSelected()]
                # Ensure selected is a list for indexing
                if not isinstance(selected, list):
                    selected = list(selected)
                cur = default_combo.currentText()
                default_combo.blockSignals(True)
                default_combo.clear()
                default_combo.addItems(selected)
                if cur in selected:
                    default_combo.setCurrentText(cur)
                elif selected:
                    default_combo.setCurrentText(selected[0])
                default_combo.blockSignals(False)
            # Store for later use (if needed)
            self._update_enum_default_combo = update_default_combo
            # Initial update
            update_default_combo()

        # --- Min/Max (for Flt_P) ---
        if hasattr(node, 'min_spin'):
            minspin = QDoubleSpinBox(); minspin.setDecimals(2)
            minspin.setValue(node.min_spin.value())
            minspin.valueChanged.connect(lambda v: self._update_node_min(v))
            self.layout.addRow("Min", minspin)
            self.fields['min'] = minspin
        if hasattr(node, 'max_spin'):
            maxspin = QDoubleSpinBox(); maxspin.setDecimals(2)
            maxspin.setRange(0.0, 100.0)
            maxspin.setValue(100.00)
            maxspin.valueChanged.connect(lambda v: self._update_node_max(v))
            self.layout.addRow("Max", maxspin)
            self.fields['max'] = maxspin

        # --- Element Order (for Node_C, Key_C) ---
        if hasattr(node, 'show_element_order_dialog'):
            btn = QPushButton("Set Element Order...")
            btn.clicked.connect(node.show_element_order_dialog)

            # Drag-and-drop list for element order
            order_list = QListWidget()
            order_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            order_list.setDefaultDropAction(Qt.DropAction.MoveAction)
            order_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            order_list.setMaximumHeight(80)
            # Get current order or default
            if getattr(node, 'custom_element_order', None):
                order_names = list(node.custom_element_order)
            else:
                # Use current connected element names as default
                order_names = node.get_connected_element_names() if hasattr(node, 'get_connected_element_names') else []
            order_list.addItems(order_names)
            # Sync: when user reorders, update node and trigger callback
            def on_order_changed():
                new_order = [order_list.item(i).text() for i in range(order_list.count())]
                node.custom_element_order = new_order
                if hasattr(node, 'on_property_changed') and node.on_property_changed:
                    node.on_property_changed(node, 'element_order', new_order)
            order_list.model().rowsMoved.connect(lambda *_: on_order_changed())
            # Also update list if order changes from dialog
            def refresh_order_list():
                order_list.clear()
                if getattr(node, 'custom_element_order', None):
                    order_names = list(node.custom_element_order)
                else:
                    order_names = node.get_connected_element_names() if hasattr(node, 'get_connected_element_names') else []
                order_list.addItems(order_names)
            # Auto-refresh panel when tensor size changes
            def refresh_panel_on_size():
                if self.node is node:
                    self.set_node(node)
            if hasattr(node, 'size_spin'):
                node.size_spin.valueChanged.connect(refresh_panel_on_size)
            # Store for later refresh
            self.fields['element_order_list'] = order_list
            # Compose row
            row_widget = QWidget()
            row_layout = QFormLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addRow(btn, order_list)
            self.layout.addRow("Element Order", row_widget)
            # Patch set_node to refresh the list when panel is rebuilt
            self.refresh_order_list = refresh_order_list

        # --- Case Name (for Case Folder Output) ---
        if hasattr(node, 'case_name_edit'):
            case_edit = QLineEdit(node.case_name_edit.text())
            # Two-way sync: panel -> node
            def update_node_case_name(text):
                # Use set_case_name_from_panel if available to avoid signal loops
                if hasattr(node, 'set_case_name_from_panel'):
                    node.set_case_name_from_panel(text)
                else:
                    node.case_name_edit.setText(text)
            case_edit.textChanged.connect(update_node_case_name)
            # Two-way sync: node -> panel
            import weakref
            case_edit_ref = weakref.ref(case_edit)
            def sync_case_name():
                edit = case_edit_ref()
                node_text = node.case_name_edit.text()
                if edit is not None and edit.text() != node_text:
                    edit.setText(node_text)
            node.case_name_edit.textChanged.connect(sync_case_name)
            self.layout.addRow("Case Name", case_edit)
            self.fields['case_name'] = case_edit

        # --- Output Filename (for Output node) ---
        if hasattr(node, 'filename_edit'):
            fname_edit = QLineEdit(node.filename_edit.text())
            # Two-way sync: panel -> node
            def update_node_filename(text):
                # Use set_filename_from_panel if available to avoid signal loops
                if hasattr(node, 'set_filename_from_panel'):
                    node.set_filename_from_panel(text)
                else:
                    node.filename_edit.setText(text)
            fname_edit.textChanged.connect(update_node_filename)
            # Two-way sync: node -> panel
            import weakref
            fname_edit_ref = weakref.ref(fname_edit)
            def sync_filename():
                edit = fname_edit_ref()
                node_text = node.filename_edit.text()
                if edit is not None and edit.text() != node_text:
                    edit.setText(node_text)
            node.filename_edit.textChanged.connect(sync_filename)
            self.layout.addRow("Filename", fname_edit)
            self.fields['filename'] = fname_edit

    def _update_node_name(self, text):
        if self.node and hasattr(self.node, 'name_edit'):
            node_edit = self.node.name_edit
            if node_edit.text() != text:
                old_block = node_edit.blockSignals(True)
                node_edit.setText(text)
                node_edit.blockSignals(old_block)

    def _update_node_value(self, value):
        if self.node:
            if hasattr(self.node, 'value_spinbox'):
                self.node.value_spinbox.setValue(value)
            elif hasattr(self.node, 'value_spin'):
                self.node.value_spin.setValue(value)

    def _update_enum_default(self, value):
        if self.node and hasattr(self.node, 'default_combo'):
            self.node.default_combo.setCurrentText(value)

    def _update_node_min(self, value):
        if self.node and hasattr(self.node, 'min_spin'):
            self.node.min_spin.setValue(value)

    def _update_node_max(self, value):
        if self.node and hasattr(self.node, 'max_spin'):
            self.node.max_spin.setValue(value)

    def _update_case_name(self, text):
        if self.node and hasattr(self.node, 'case_name_edit'):
            self.node.case_name_edit.setText(text)

    def _update_filename(self, text):
        if self.node and hasattr(self.node, 'filename_edit'):
            self.node.filename_edit.setText(text)