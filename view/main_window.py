"""Main window for the OpenFOAM Case Generator"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QTabWidget,
    QHBoxLayout,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QMimeData, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QDrag, QKeySequence, QAction

import os
import sys

from view.editor_scene import EditorScene
from view.editor_view import EditorView
from view.styles import LEFT_PANE_STYLES

# Add the case loader
try:
    from loader.case_loader import CaseLoader
    from loader.node_converter import NodeConverter
except ImportError:
    CaseLoader = None
    NodeConverter = None


class NodeListWidget(QListWidget):
    """Custom list widget with drag and drop support for nodes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        
    def startDrag(self, supportedActions):
        """Override startDrag to provide custom drag data"""
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mimeData = QMimeData()
            # Store the node type in the mime data
            mimeData.setText(item.text().strip())
            drag.setMimeData(mimeData)
            drag.exec(Qt.DropAction.CopyAction)


class MainWindow(QMainWindow):
    def _on_node_property_changed(self, prop, value):
        # Always update the properties panel for the last selected node
        node = self._last_selected_node if hasattr(self, '_last_selected_node') else None
        if node:
            self.update_properties_panel(node)
    def update_properties_panel(self, node=None):
        """Update the properties panel with the selected node's properties"""
        if node is None:
            # Try to get selected node from current scene
            scene = self.get_current_editor_scene()
            if scene:
                selected = [item for item in scene.selectedItems() if hasattr(item, 'get_node_title')]
                node = selected[0] if selected else None
        self.properties_panel.set_node(node)
        # Set up live update callback for node property changes
        if node and hasattr(node, 'on_property_changed'):
            node.on_property_changed = lambda n, prop, value: self._on_node_property_changed(prop, value)
        self._last_selected_node = node

    def highlight_selected_node(self, node):
        """Highlight the selected node with a thick orange border, remove from others"""
        scene = self.get_current_editor_scene()
        if not scene:
            return
        for item in scene.items():
            if hasattr(item, 'set_highlighted'):
                item.set_highlighted(item is node)
    """Main application window"""
    
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("OpenFOAM Case Generator")
        
        # Default output directory for cases
        self.default_output_dir = os.path.join(os.getcwd(), "output")
        
        # Initialize case loader
        self.case_loader = CaseLoader() if CaseLoader else None
        if self.case_loader:
            self.case_loader.loading_started.connect(self._on_loading_started)
            self.case_loader.loading_finished.connect(self._on_loading_finished)
            self.case_loader.loading_error.connect(self._on_loading_error)
            self.case_loader.progress_updated.connect(self._on_progress_updated)
        
        # Progress dialog for loading
        self.progress_dialog = None
        
        # Track current file paths for each tab
        self.tab_file_paths = {}  # {tab_index: file_path}
        self.tab_modified = {}  # {tab_index: bool}
        self.case_counter = 0  # For naming new cases
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)
        
        # Create left pane
        self.left_pane = self._create_left_pane()
        splitter.addWidget(self.left_pane)
        
        # Create tab widget for multiple cases
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Set a simple cross for the close button
        self.tab_widget.setStyleSheet("""
            QTabWidget::close-button {
                image: none;
                background: transparent;
                padding: 2px;
            }
            QTabWidget::close-button:hover {
                background: #ff6b6b;
                border-radius: 3px;
            }
            QTabWidget::close-button:pressed {
                background: #ff5252;
            }
        """)
        
        # Override the close button with a simple cross
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_tab_close_buttons)
        splitter.addWidget(self.tab_widget)
        
        # Create first tab with default case
        self._create_new_case_tab()
        
        # Set splitter proportions (left pane: 180px, editor: rest)
        splitter.setSizes([180, 880])
        splitter.setCollapsible(0, False)  # Left pane cannot be collapsed
        
        self.setGeometry(100, 100, 1200, 800)
        self._create_menu()
        self._create_status_bar()

    def _setup_single_tab_close_button(self, tab_index):
        """Setup custom close button for a single tab"""
        from PyQt6.QtWidgets import QPushButton
        
        # Create a simple close button with × character
        close_button = QPushButton("×")
        close_button.setFixedSize(16, 16)
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: bold;
                color: #666;
                padding: 0px;
            }
            QPushButton:hover {
                background: #ff6b6b;
                color: white;
                border-radius: 2px;
            }
            QPushButton:pressed {
                background: #ff5252;
            }
        """)
        close_button.clicked.connect(lambda checked: self._close_tab(tab_index))
        
        # Set the custom close button for this tab
        self.tab_widget.tabBar().setTabButton(tab_index, self.tab_widget.tabBar().ButtonPosition.RightSide, close_button)

    def _setup_tab_close_buttons(self):
        """Setup custom close buttons with simple cross"""
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt
        
        for i in range(self.tab_widget.count()):
            # Create a simple close button with × character
            close_button = QPushButton("×")
            close_button.setFixedSize(16, 16)
            close_button.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 12px;
                    font-weight: bold;
                    color: #666;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #ff6b6b;
                    color: white;
                    border-radius: 2px;
                }
                QPushButton:pressed {
                    background: #ff5252;
                }
            """)
            close_button.clicked.connect(lambda checked, index=i: self._close_tab(index))
            
            # Set the custom close button for this tab
            self.tab_widget.tabBar().setTabButton(i, self.tab_widget.tabBar().ButtonPosition.RightSide, close_button)

    def _create_new_case_tab(self, file_path=None, tab_name=None):
        """Create a new case tab with editor view and scene"""
        # Create new editor scene and view
        editor_scene = EditorScene()
        editor_view = EditorView(editor_scene)
        
        # Connect signals
        editor_view.node_created.connect(self.on_node_created)
        # Connect selection change to update properties panel and highlight
        def on_selection_changed():
            try:
                selected = [item for item in editor_scene.selectedItems() if hasattr(item, 'get_node_title')]
                node = selected[0] if selected else None
                self.update_properties_panel(node)
                self.highlight_selected_node(node)
            except RuntimeError:
                # Scene or items have been deleted; safely ignore
                return
        editor_scene.selectionChanged.connect(on_selection_changed)
        editor_scene.undo_manager.can_undo_changed.connect(self._update_undo_action)
        editor_scene.undo_manager.can_redo_changed.connect(self._update_redo_action)
        editor_scene.undo_manager.undo_text_changed.connect(self._update_undo_text)
        editor_scene.undo_manager.redo_text_changed.connect(self._update_redo_text)
        
        # Determine tab name
        if tab_name is None:
            if file_path:
                tab_name = os.path.basename(file_path)
            else:
                self.case_counter += 1
                tab_name = f"New Case {self.case_counter}"
        
        # Add tab
        tab_index = self.tab_widget.addTab(editor_view, tab_name)
        
        # Store metadata
        self.tab_file_paths[tab_index] = file_path
        self.tab_modified[tab_index] = False
        
        # Set as current tab
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Setup custom close button for the new tab
        self._setup_single_tab_close_button(tab_index)
        
        return editor_view, editor_scene
    
    def _close_tab(self, index):
        """Close a tab with optional save prompt"""
        if self.tab_widget.count() <= 1:
            # Don't allow closing the last tab, just clear it
            current_view = self.get_current_editor_view()
            if current_view:
                current_view.scene().clear()
                current_view.scene()._setup_scene()
            self._mark_tab_clean(index)
            return
        
        # Check if tab is modified
        if self.tab_modified.get(index, False):
            file_path = self.tab_file_paths.get(index)
            tab_name = self.tab_widget.tabText(index)
            
            reply = QMessageBox.question(
                self, 
                "Save Changes?", 
                f"The case '{tab_name}' has unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self._save_case(index):
                    return  # Don't close if save failed
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # Don't close
        
        # Remove tab metadata
        if index in self.tab_file_paths:
            del self.tab_file_paths[index]
        if index in self.tab_modified:
            del self.tab_modified[index]
        
        # Update indices for remaining tabs
        new_tab_file_paths = {}
        new_tab_modified = {}
        for tab_idx in self.tab_file_paths:
            if tab_idx > index:
                new_tab_file_paths[tab_idx - 1] = self.tab_file_paths[tab_idx]
                new_tab_modified[tab_idx - 1] = self.tab_modified[tab_idx]
            elif tab_idx < index:
                new_tab_file_paths[tab_idx] = self.tab_file_paths[tab_idx]
                new_tab_modified[tab_idx] = self.tab_modified[tab_idx]
        
        self.tab_file_paths = new_tab_file_paths
        self.tab_modified = new_tab_modified
        
        # Remove the tab
        self.tab_widget.removeTab(index)
    
    def _on_tab_changed(self, index):
        """Handle tab change to update window title and undo/redo state"""
        if index >= 0:
            tab_name = self.tab_widget.tabText(index)
            modified_indicator = " *" if self.tab_modified.get(index, False) else ""
            self.setWindowTitle(f"OpenFOAM Case Generator - {tab_name}{modified_indicator}")
            
            # Update undo/redo actions for current scene
            current_view = self.get_current_editor_view()
            if current_view and current_view.scene():
                scene = current_view.scene()
                if hasattr(scene, 'undo_manager'):
                    self._update_undo_action(scene.undo_manager.can_undo())
                    self._update_redo_action(scene.undo_manager.can_redo())
    
    def _mark_tab_modified(self, index=None):
        """Mark a tab as modified"""
        if index is None:
            index = self.tab_widget.currentIndex()
        
        if index >= 0:
            self.tab_modified[index] = True
            tab_name = self.tab_widget.tabText(index)
            if not tab_name.endswith(" *"):
                self.tab_widget.setTabText(index, tab_name + " *")
                self.setWindowTitle(f"OpenFOAM Case Generator - {tab_name} *")
    
    def _mark_tab_clean(self, index=None):
        """Mark a tab as clean (not modified)"""
        if index is None:
            index = self.tab_widget.currentIndex()
        
        if index >= 0:
            self.tab_modified[index] = False
            tab_name = self.tab_widget.tabText(index)
            if tab_name.endswith(" *"):
                clean_name = tab_name[:-2]
                self.tab_widget.setTabText(index, clean_name)
                if index == self.tab_widget.currentIndex():
                    self.setWindowTitle(f"OpenFOAM Case Generator - {clean_name}")
    
    def get_current_editor_view(self):
        """Get the current tab's editor view"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, EditorView):
            return current_widget
        return None
    
    def get_current_editor_scene(self):
        """Get the current tab's editor scene"""
        current_view = self.get_current_editor_view()
        if current_view:
            return current_view.scene()
        return None

    def _create_left_pane(self):
        """Create the left control pane (now extendible, no fixed width)"""
        left_widget = QWidget()
        # Remove fixed width to allow splitter resizing
        left_widget.setStyleSheet(LEFT_PANE_STYLES)

        layout = QVBoxLayout(left_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Node Library Group
        nodes_group = QGroupBox("Node Library")
        nodes_layout = QVBoxLayout(nodes_group)

        # Node list: no scroll bars, show all nodes, no height restriction
        self.node_list = NodeListWidget()
        self.node_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.node_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.node_list.setSizeAdjustPolicy(self.node_list.SizeAdjustPolicy.AdjustToContents)
        self.node_list.setMaximumHeight(16777215)  # No height restriction
        self.node_list.setMinimumHeight(0)
        from PyQt6.QtWidgets import QFrame
        self.node_list.setFrameShape(QFrame.Shape.NoFrame)

        # Add all available node types
        node_types = [
            "Node_C",
            "Key_C",
            "Enm_P",
            "Int_P",
            "Flt_P",
            "Vector_P",
            "Dim_Set_P",
            "Tensor_P",
            "Str_P",
            "List_CP",
            "Output",
            "Case Folder"
        ]
        for node_type in node_types:
            item = QListWidgetItem(node_type)
            self.node_list.addItem(item)

        nodes_layout.addWidget(self.node_list)
        layout.addWidget(nodes_group)

        # --- Properties Panel ---
        from view.properties_panel import PropertiesPanel
        self.properties_panel = PropertiesPanel()
        layout.addWidget(self.properties_panel)

        # Add stretch to push everything to top
        layout.addStretch()
        return left_widget
    
    def _open_case(self):
        """Open a previously saved case file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Case File",
            "",
            "Case Files (*.case);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            self._load_saved_case_file(file_path)
    
    def _new_case(self):
        """Create a new case in a new tab"""
        self._create_new_case_tab()
    
    def _undo_current_scene(self):
        """Undo action in current scene"""
        current_scene = self.get_current_editor_scene()
        if current_scene and hasattr(current_scene, 'undo_manager'):
            current_scene.undo_manager.undo()
    
    def _redo_current_scene(self):
        """Redo action in current scene"""
        current_scene = self.get_current_editor_scene()
        if current_scene and hasattr(current_scene, 'undo_manager'):
            current_scene.undo_manager.redo()
    
    def _clear_current_scene(self):
        """Clear current scene"""
        current_scene = self.get_current_editor_scene()
        if current_scene:
            if hasattr(current_scene, 'undo_manager'):
                current_scene.clear()
                current_scene.undo_manager.clear()
                current_scene._setup_scene()
            self._mark_tab_modified()
    
    def _set_dark_mode(self):
        """Set dark mode for current scene"""
        current_scene = self.get_current_editor_scene()
        if current_scene:
            current_scene.set_dark_mode()
    
    def _set_light_mode(self):
        """Set light mode for current scene"""
        current_scene = self.get_current_editor_scene()
        if current_scene:
            current_scene.set_light_mode()
    
    def _reset_view(self):
        """Reset view for current editor"""
        current_view = self.get_current_editor_view()
        if current_view:
            current_view.reset_view()
    
    def _fit_all(self):
        """Fit all items in current view"""
        current_view = self.get_current_editor_view()
        current_scene = self.get_current_editor_scene()
        if current_view and current_scene:
            current_view.fitInView(
                current_scene.itemsBoundingRect(), 
                Qt.AspectRatioMode.KeepAspectRatio
            )
    
    def _toggle_knife_mode(self):
        """Toggle knife mode for current editor"""
        current_view = self.get_current_editor_view()
        if current_view:
            current_view.toggle_knife_mode()
    
    def _save_case(self, tab_index=None):
        """Save the current case"""
        if tab_index is None:
            tab_index = self.tab_widget.currentIndex()
        
        file_path = self.tab_file_paths.get(tab_index)
        
        if file_path:
            # Save to existing file
            return self._save_case_to_file(file_path, tab_index)
        else:
            # No file path, prompt for save as
            return self._save_case_as(tab_index)
    
    def _save_case_as(self, tab_index=None):
        """Save the current case with a new filename"""
        if tab_index is None:
            tab_index = self.tab_widget.currentIndex()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save OpenFOAM Case",
            "",
            "Case Files (*.case);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            if self._save_case_to_file(file_path, tab_index):
                # Update tab metadata
                self.tab_file_paths[tab_index] = file_path
                tab_name = os.path.basename(file_path)
                self.tab_widget.setTabText(tab_index, tab_name)
                self._mark_tab_clean(tab_index)
                return True
        return False
    
    def _save_case_to_file(self, file_path, tab_index):
        """Save case data to a specific file"""
        try:
            # Get the current scene for this tab
            current_widget = self.tab_widget.widget(tab_index)
            if isinstance(current_widget, EditorView):
                scene = current_widget.scene()
                
                # Collect scene data
                case_data = self._serialize_scene(scene)
                
                # Determine file format and save
                if file_path.lower().endswith('.case'):
                    # Save as our custom case format (JSON with .case extension)
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(case_data, f, indent=2, ensure_ascii=False)
                elif file_path.lower().endswith('.json'):
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(case_data, f, indent=2, ensure_ascii=False)
                elif file_path.lower().endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        with open(file_path, 'w', encoding='utf-8') as f:
                            yaml.dump(case_data, f, default_flow_style=False, allow_unicode=True)
                    except ImportError:
                        QMessageBox.warning(self, "YAML Not Available", 
                                          "YAML module not available. Please save as JSON instead.")
                        return False
                else:
                    # Default to JSON
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(case_data, f, indent=2, ensure_ascii=False)
                
                self._mark_tab_clean(tab_index)
                self.statusBar().showMessage(f"Case saved to {os.path.basename(file_path)}")
                return True
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save case: {str(e)}")
            self.statusBar().showMessage("Save failed")
            return False
    
    def _serialize_scene(self, scene):
        """Serialize scene data to a dictionary with full node recreation capability"""
        case_data = {
            "version": "1.0",
            "case_type": "openfoam_case_generator",
            "nodes": [],
            "connections": [],
            "scene_properties": {
                "dark_mode": getattr(scene, 'is_dark_mode', False)
            }
        }
        
        # Collect all graphical nodes with their complete data
        node_id_map = {}  # Map scene items to unique IDs
        node_counter = 0
        
        for item in scene.items():
            # Skip non-node items (like grid lines, etc.)
            if not hasattr(item, 'pos') or not hasattr(item, '__class__'):
                continue
            # Skip items that are clearly not nodes
            class_name = item.__class__.__name__
            if not any(x in class_name for x in ['Node', 'Key', 'Enm', 'Int', 'Flt', 'Vector', 'Dim', 'Str', 'List', 'Output', 'Case']):
                continue

            node_counter += 1
            node_id = f"node_{node_counter}"
            node_id_map[item] = node_id

            pos = item.pos()
            node_data = {
                "id": node_id,
                "type": class_name,
                "position": {"x": pos.x(), "y": pos.y()},
                "properties": {}
            }

            # Capture node-specific data based on type
            node_data["pyvnt_data"] = {}

            # Get the current name from the UI widget if available
            if hasattr(item, 'name_edit') and hasattr(item.name_edit, 'text'):
                node_name = item.name_edit.text().strip()
                node_data["pyvnt_data"]["name"] = node_name

            # Save common widget states (combo boxes, checkboxes, line edits, value fields, etc.)
            widget_states = {}
            # ComboBox: save current index and text
            if hasattr(item, 'combo_box'):
                cb = item.combo_box
                if hasattr(cb, 'currentIndex') and hasattr(cb, 'currentText'):
                    widget_states['combo_box_index'] = cb.currentIndex()
                    widget_states['combo_box_text'] = cb.currentText()
            # CheckBox: save checked state
            if hasattr(item, 'check_box'):
                chb = item.check_box
                if hasattr(chb, 'isChecked'):
                    widget_states['check_box_checked'] = chb.isChecked()
            # RadioButton: save checked state
            if hasattr(item, 'radio_button'):
                rb = item.radio_button
                if hasattr(rb, 'isChecked'):
                    widget_states['radio_button_checked'] = rb.isChecked()
            # LineEdit: save text
            if hasattr(item, 'line_edit'):
                le = item.line_edit
                if hasattr(le, 'text'):
                    widget_states['line_edit_text'] = le.text()
            # QTextEdit: save plain text
            if hasattr(item, 'text_edit'):
                te = item.text_edit
                if hasattr(te, 'toPlainText'):
                    widget_states['text_edit_plain'] = te.toPlainText()
            # SpinBox: save value
            if hasattr(item, 'spin_box'):
                sb = item.spin_box
                if hasattr(sb, 'value'):
                    widget_states['spin_box_value'] = sb.value()
            # DoubleSpinBox: save value
            if hasattr(item, 'double_spin_box'):
                dsb = item.double_spin_box
                if hasattr(dsb, 'value'):
                    widget_states['double_spin_box_value'] = dsb.value()
            # Slider: save value
            if hasattr(item, 'slider'):
                sl = item.slider
                if hasattr(sl, 'value'):
                    widget_states['slider_value'] = sl.value()
            # Date/Time edits
            if hasattr(item, 'date_edit'):
                de = item.date_edit
                if hasattr(de, 'date'):
                    widget_states['date_edit_value'] = de.date().toString(Qt.ISODate) if hasattr(de.date(), 'toString') else str(de.date())
            if hasattr(item, 'time_edit'):
                te = item.time_edit
                if hasattr(te, 'time'):
                    widget_states['time_edit_value'] = te.time().toString(Qt.ISODate) if hasattr(te.time(), 'toString') else str(te.time())
            if hasattr(item, 'datetime_edit'):
                dte = item.datetime_edit
                if hasattr(dte, 'dateTime'):
                    widget_states['datetime_edit_value'] = dte.dateTime().toString(Qt.ISODate) if hasattr(dte.dateTime(), 'toString') else str(dte.dateTime())
            # ValueEdit: save value for Int_P, Flt_P, etc.
            if hasattr(item, 'value_edit'):
                ve = item.value_edit
                if hasattr(ve, 'text'):
                    widget_states['value_edit_text'] = ve.text()
            # Save any additional custom widgets as needed here
            if widget_states:
                node_data['widget_states'] = widget_states

            # For nodes with pyvnt data (rarely used, but kept for compatibility)
            if hasattr(item, 'pyvnt_node'):
                pyvnt_node = item.pyvnt_node
                if "name" not in node_data["pyvnt_data"]:
                    node_data["pyvnt_data"]["name"] = getattr(pyvnt_node, 'name', '')
                node_data["pyvnt_data"]["value"] = getattr(pyvnt_node, 'value', None)
                node_data["pyvnt_data"]["type"] = type(pyvnt_node).__name__
                # Store additional properties based on node type
                if hasattr(pyvnt_node, 'items') and hasattr(pyvnt_node.items, '__iter__'):
                    # For container nodes like Node_C, List_CP
                    node_data["pyvnt_data"]["children"] = []
                    try:
                        for child in pyvnt_node.items:
                            child_data = {
                                "name": getattr(child, 'name', ''),
                                "value": getattr(child, 'value', None),
                                "type": type(child).__name__
                            }
                            node_data["pyvnt_data"]["children"].append(child_data)
                    except:
                        pass

            # Capture visual properties
            if hasattr(item, 'title_text'):
                node_data["properties"]["title"] = item.title_text
            if hasattr(item, 'content_text'):
                node_data["properties"]["content"] = item.content_text
            if hasattr(item, 'size'):
                size = item.size()
                node_data["properties"]["size"] = {"width": size.width(), "height": size.height()}

            case_data["nodes"].append(node_data)
        
        # Collect connections (edges)
        for item in scene.items():
            if hasattr(item, 'start_socket') and hasattr(item, 'end_socket'):
                # This is an edge/connection
                start_node = getattr(item.start_socket, 'node', None)
                end_node = getattr(item.end_socket, 'node', None)
                
                if start_node in node_id_map and end_node in node_id_map:
                    # Get socket type and index
                    start_socket_type = 'input' if item.start_socket.socket_type == 1 else 'output'
                    end_socket_type = 'input' if item.end_socket.socket_type == 1 else 'output'
                    
                    connection_data = {
                        "start_node": node_id_map[start_node],
                        "end_node": node_id_map[end_node],
                        "start_socket": item.start_socket.index,
                        "end_socket": item.end_socket.index,
                        "start_socket_type": start_socket_type,
                        "end_socket_type": end_socket_type
                    }
                    case_data["connections"].append(connection_data)
        
        return case_data

    def on_node_created(self, graphics_node):
        """Handle when a new node is created in the editor"""
        if hasattr(graphics_node, 'pyvnt_node'):
            pass
        else:
            pass
        
        # Set default output directory for Case Folder Output nodes
        if type(graphics_node).__name__ == 'CaseFolderOutputNode':
            if hasattr(graphics_node, 'set_default_output_dir'):
                graphics_node.set_default_output_dir(self.default_output_dir)
        # Mark current tab as modified
        self._mark_tab_modified()
        self.update_properties_panel(graphics_node)
        self.highlight_selected_node(graphics_node)

    def _create_menu(self):
        """Create the menu bar"""
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        view_menu = menu.addMenu("&View")
        tools_menu = menu.addMenu("&Tools")
        help_menu = menu.addMenu("&Help")
        
        # File menu
        new_action = QAction("&New Case", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_case)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Case...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_case)
        open_action.setToolTip("Open a previously saved case file")
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Import submenu
        import_menu = file_menu.addMenu("&Import")
        
        import_file_action = QAction("Import Case &File...", self)
        import_file_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        import_file_action.triggered.connect(self._load_case_file)
        import_file_action.setToolTip("Import a single OpenFOAM configuration file")
        import_menu.addAction(import_file_action)
        
        import_folder_action = QAction("Import Case &Folder...", self)
        import_folder_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        import_folder_action.triggered.connect(self._load_case_directory)
        import_folder_action.setToolTip("Import an entire OpenFOAM case directory")
        import_menu.addAction(import_folder_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Case", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(lambda: self._save_case())
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Case &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(lambda: self._save_case_as())
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(lambda: self._close_tab(self.tab_widget.currentIndex()))
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu - Add undo/redo actions
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self._undo_current_scene)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setEnabled(False)
        self.redo_action.triggered.connect(self._redo_current_scene)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        edit_menu.addAction("&Clear All", self._clear_current_scene)
        
        # View menu
        view_menu.addAction("&Dark Mode", self._set_dark_mode)
        view_menu.addAction("&Light Mode", self._set_light_mode)
        view_menu.addSeparator()
        view_menu.addAction("&Reset View", self._reset_view)
        view_menu.addAction("&Fit All", self._fit_all)
        
        # Tools menu
        tools_menu.addAction("&Validate Case", lambda: None)
        tools_menu.addSeparator()
        tools_menu.addAction("&Knife Tool (K)", self._toggle_knife_mode)
        
        # Help menu
        help_menu.addAction("&Getting Started", self._show_getting_started)
        help_menu.addAction("&User Guide", self._show_user_guide)
        help_menu.addAction("&Keyboard Shortcuts", self._show_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction("&Node Types Reference", self._show_node_reference)
        help_menu.addAction("&OpenFOAM Documentation", self._open_openfoam_docs)
        help_menu.addSeparator()
        help_menu.addAction("&Report Issue", self._report_issue)
        help_menu.addAction("&About", self._show_about)

    def _create_status_bar(self):
        """Create the status bar"""
        status = QStatusBar()
        status.showMessage("Ready - Ctrl+N: New Case, Ctrl+O: Open Case, Ctrl+S: Save Case | Import: Ctrl+Shift+I (File), Ctrl+Shift+F (Folder)")
        self.setStatusBar(status)
    
    def _update_undo_action(self, can_undo: bool):
        """Update undo action enabled state"""
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(can_undo)
    
    def _update_redo_action(self, can_redo: bool):
        """Update redo action enabled state"""
        if hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(can_redo)
    
    def _update_undo_text(self, text: str):
        """Update undo action text"""
        if hasattr(self, 'undo_action'):
            self.undo_action.setText(text)
    
    def _update_redo_text(self, text: str):
        """Update redo action text"""
        if hasattr(self, 'redo_action'):
            self.redo_action.setText(text)

    def _load_case_file(self):
        """Import a single OpenFOAM case file"""
        if not self.case_loader:
            QMessageBox.warning(self, "Parser Unavailable", 
                              "OpenFOAM parser is not available. Please check pyvnt installation.")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import OpenFOAM File",
            "",
            "OpenFOAM Files (*.*);;Text Files (*.txt);;Dictionary Files (controlDict fvSchemes fvSolution);;All Files (*)"
        )
        
        if file_path:
            # Import the file using the case loader (this is for raw OpenFOAM files)
            self.case_loader.load_case_file(file_path)
    
    def _load_saved_case_file(self, file_path):
        """Load a previously saved case file"""
        try:
            if file_path.lower().endswith(('.case', '.json')):
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
            elif file_path.lower().endswith(('.yaml', '.yml')):
                try:
                    import yaml
                    with open(file_path, 'r', encoding='utf-8') as f:
                        case_data = yaml.safe_load(f)
                except ImportError:
                    QMessageBox.warning(self, "YAML Not Available", 
                                      "YAML module not available. Cannot load YAML files.")
                    return
            
            # Create new tab for loaded case
            tab_name = os.path.basename(file_path)
            editor_view, editor_scene = self._create_new_case_tab(file_path, tab_name)
            
            # Deserialize case data
            self._deserialize_scene(case_data, editor_scene)
            
            # Mark as clean (just loaded)
            current_index = self.tab_widget.currentIndex()
            self._mark_tab_clean(current_index)
            
            self.statusBar().showMessage(f"Loaded case from {tab_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load case: {str(e)}")
            self.statusBar().showMessage("Load failed")
    
    def _deserialize_scene(self, case_data, scene):
        """Deserialize case data into a scene with full node recreation"""
        # Clear existing scene
        scene.clear()
        scene._setup_scene()
        
        # Store reference to scene for connection creation
        self.current_scene = scene
        
        # Set scene properties
        scene_props = case_data.get("scene_properties", {})
        if scene_props.get("dark_mode", False):
            scene.set_dark_mode()
        else:
            scene.set_light_mode()
        
        # Recreate nodes
        nodes_data = case_data.get("nodes", [])
        created_nodes = {}  # Map node IDs to created node objects
        
        for node_data in nodes_data:
            try:
                node_type = node_data.get("type", "")
                position = node_data.get("position", {"x": 0, "y": 0})
                node_id = node_data.get("id", "")
                
                # Create the appropriate node type
                created_node = self._create_node_from_data(scene, node_type, node_data)
                
                if created_node:
                    # Set position
                    created_node.setPos(position["x"], position["y"])
                    created_nodes[node_id] = created_node
                    
                    # Add to scene if not already added
                    if created_node.scene() != scene:
                        scene.addItem(created_node)
                        
            except Exception as e:
                pass
        
        # Recreate connections
        connections_data = case_data.get("connections", [])
        for connection_data in connections_data:
            try:
                start_node_id = connection_data.get("start_node")
                end_node_id = connection_data.get("end_node")
                
                start_node = created_nodes.get(start_node_id)
                end_node = created_nodes.get(end_node_id)
                
                if start_node and end_node:
                    # Create connection between nodes
                    self._create_connection(connection_data, created_nodes)
                    
            except Exception as e:
                pass
        
        pass
    
    def _create_node_from_data(self, scene, node_type, node_data):
        """Create a specific node type from saved data"""
        try:
            pass
            # Import node classes
            from nodes.node_c_graphical import Node_CGraphicalNode
            from nodes.key_c_graphical import Key_CGraphicalNode
            from nodes.enm_p_graphical import Enm_PGraphicalNode
            from nodes.int_p_graphical import Int_PGraphicalNode
            from nodes.flt_p_graphical import Flt_PGraphicalNode
            from nodes.vector_p_graphical import Vector_PGraphicalNode
            from nodes.dim_set_p_graphical import Dim_Set_PGraphicalNode
            from nodes.tensor_p_graphical import Tensor_PGraphicalNode
            from nodes.str_p_graphical import Str_PGraphicalNode
            from nodes.list_cp_graphical import List_CPGraphicalNode
            from nodes.output_graphical import OutputGraphicalNode
            from nodes.case_folder_output_graphical import CaseFolderOutputNode
            
            # Map node types to classes
            node_classes = {
                "Node_CGraphicalNode": Node_CGraphicalNode,
                "Key_CGraphicalNode": Key_CGraphicalNode,
                "Enm_PGraphicalNode": Enm_PGraphicalNode,
                "Int_PGraphicalNode": Int_PGraphicalNode,
                "Flt_PGraphicalNode": Flt_PGraphicalNode,
                "Vector_PGraphicalNode": Vector_PGraphicalNode,
                "Dim_Set_PGraphicalNode": Dim_Set_PGraphicalNode,
                "Tensor_PGraphicalNode": Tensor_PGraphicalNode,
                "Str_PGraphicalNode": Str_PGraphicalNode,
                "List_CPGraphicalNode": List_CPGraphicalNode,
                "OutputGraphicalNode": OutputGraphicalNode,
                "CaseFolderOutputNode": CaseFolderOutputNode,
            }
            
            # Get the node class
            node_class = node_classes.get(node_type)
            if not node_class:
                # ...removed debug print...
                return None
            
            # Create the node
            created_node = node_class()

            # Restore pyvnt data if available
            pyvnt_data = node_data.get("pyvnt_data")
            if pyvnt_data:
                # Set the name in the UI widget first (this is most important for user experience)
                if 'name' in pyvnt_data and hasattr(created_node, 'name_edit'):
                    created_node.name_edit.setText(pyvnt_data['name'])

                # If the node has a persistent pyvnt_node attribute (rare), update it too
                if hasattr(created_node, 'pyvnt_node'):
                    # Restore basic properties
                    if 'name' in pyvnt_data:
                        created_node.pyvnt_node.name = pyvnt_data['name']
                    if 'value' in pyvnt_data and pyvnt_data['value'] is not None:
                        created_node.pyvnt_node.value = pyvnt_data['value']
                    # Restore children for container nodes
                    if 'children' in pyvnt_data:
                        self._restore_node_children(created_node.pyvnt_node, pyvnt_data['children'])

            # Restore widget states (combo boxes, checkboxes, line edits, value fields, etc.)
            widget_states = node_data.get('widget_states', {})
            # ComboBox
            if 'combo_box_index' in widget_states and hasattr(created_node, 'combo_box'):
                try:
                    created_node.combo_box.setCurrentIndex(widget_states['combo_box_index'])
                except Exception:
                    pass
            if 'combo_box_text' in widget_states and hasattr(created_node, 'combo_box'):
                try:
                    # Only set text if index is not enough (for editable combo boxes)
                    if hasattr(created_node.combo_box, 'setEditText'):
                        created_node.combo_box.setEditText(widget_states['combo_box_text'])
                except Exception:
                    pass
            # CheckBox
            if 'check_box_checked' in widget_states and hasattr(created_node, 'check_box'):
                try:
                    created_node.check_box.setChecked(widget_states['check_box_checked'])
                except Exception:
                    pass
            # RadioButton
            if 'radio_button_checked' in widget_states and hasattr(created_node, 'radio_button'):
                try:
                    created_node.radio_button.setChecked(widget_states['radio_button_checked'])
                except Exception:
                    pass
            # LineEdit
            if 'line_edit_text' in widget_states and hasattr(created_node, 'line_edit'):
                try:
                    created_node.line_edit.setText(widget_states['line_edit_text'])
                except Exception:
                    pass
            # QTextEdit
            if 'text_edit_plain' in widget_states and hasattr(created_node, 'text_edit'):
                try:
                    created_node.text_edit.setPlainText(widget_states['text_edit_plain'])
                except Exception:
                    pass
            # SpinBox
            if 'spin_box_value' in widget_states and hasattr(created_node, 'spin_box'):
                try:
                    created_node.spin_box.setValue(widget_states['spin_box_value'])
                except Exception:
                    pass
            # DoubleSpinBox
            if 'double_spin_box_value' in widget_states and hasattr(created_node, 'double_spin_box'):
                try:
                    created_node.double_spin_box.setValue(widget_states['double_spin_box_value'])
                except Exception:
                    pass
            # Slider
            if 'slider_value' in widget_states and hasattr(created_node, 'slider'):
                try:
                    created_node.slider.setValue(widget_states['slider_value'])
                except Exception:
                    pass
            # Date/Time edits
            if 'date_edit_value' in widget_states and hasattr(created_node, 'date_edit'):
                try:
                    from PyQt6.QtCore import QDate
                    created_node.date_edit.setDate(QDate.fromString(widget_states['date_edit_value']))
                except Exception:
                    pass
            if 'time_edit_value' in widget_states and hasattr(created_node, 'time_edit'):
                try:
                    from PyQt6.QtCore import QTime
                    created_node.time_edit.setTime(QTime.fromString(widget_states['time_edit_value']))
                except Exception:
                    pass
            if 'datetime_edit_value' in widget_states and hasattr(created_node, 'datetime_edit'):
                try:
                    from PyQt6.QtCore import QDateTime
                    created_node.datetime_edit.setDateTime(QDateTime.fromString(widget_states['datetime_edit_value']))
                except Exception:
                    pass
            # ValueEdit (for Int_P, Flt_P, etc.)
            if 'value_edit_text' in widget_states and hasattr(created_node, 'value_edit'):
                try:
                    created_node.value_edit.setText(widget_states['value_edit_text'])
                except Exception:
                    pass

            # Restore visual properties
            properties = node_data.get("properties", {})
            if 'title' in properties and hasattr(created_node, 'title_text'):
                created_node.title_text = properties['title']
                created_node.update()
            if 'content' in properties and hasattr(created_node, 'content_text'):
                created_node.content_text = properties['content']
                created_node.update()

            return created_node
            
        except Exception as e:
            pass
            return None
    
    def _restore_node_children(self, pyvnt_node, children_data):
        """Restore child nodes for container types"""
        try:
            # This would need to be implemented based on pyvnt library structure
            pass
        except Exception as e:
            pass
    
    def _create_connection(self, connection_data, nodes_by_id):
        """Create a connection between nodes"""
        try:
            start_node_id = connection_data['start_node']
            end_node_id = connection_data['end_node']
            start_socket_index = connection_data['start_socket']
            end_socket_index = connection_data['end_socket']
            start_socket_type = connection_data['start_socket_type']
            end_socket_type = connection_data['end_socket_type']
            
            # Get the nodes
            start_node = nodes_by_id.get(start_node_id)
            end_node = nodes_by_id.get(end_node_id)
            
            if not start_node or not end_node:
                # ...removed debug print...
                return False
            
            # Get the sockets based on type and index
            if start_socket_type == 'input':
                if start_socket_index < len(start_node.input_sockets):
                    start_socket = start_node.input_sockets[start_socket_index]
                else:
                    # ...removed debug print...
                    return False
            else:  # output
                if start_socket_index < len(start_node.output_sockets):
                    start_socket = start_node.output_sockets[start_socket_index]
                else:
                    # ...removed debug print...
                    return False
            
            if end_socket_type == 'input':
                if end_socket_index < len(end_node.input_sockets):
                    end_socket = end_node.input_sockets[end_socket_index]
                else:
                    # ...removed debug print...
                    return False
            else:  # output
                if end_socket_index < len(end_node.output_sockets):
                    end_socket = end_node.output_sockets[end_socket_index]
                else:
                    # ...removed debug print...
                    return False
            
            # Validate connection is allowed
            if not start_socket.canConnectTo(end_socket):
                # ...removed debug print...
                return False
            
            # Create the edge
            from view.edge import Edge
            edge = Edge(start_socket, end_socket, self.current_scene)
            edge.setParentItem(None)
            edge.updatePath()
            self.current_scene.addItem(edge)
            
            # ...removed debug print...
            return True
            
        except Exception as e:
            # ...removed debug print...
            return False
    
    def _load_case_directory(self):
        """Import an entire OpenFOAM case directory"""
        if not self.case_loader:
            QMessageBox.warning(self, "Parser Unavailable", 
                              "OpenFOAM parser is not available. Please check pyvnt installation.")
            return
            
        case_dir = QFileDialog.getExistingDirectory(
            self,
            "Import OpenFOAM Case Directory",
            ""
        )
        
        if case_dir:
            # Store directory for loading completion
            self._loading_case_dir = case_dir
            # Import the case directory using the case loader
            self.case_loader.load_case_directory(case_dir)
    
    def _on_loading_started(self, path):
        """Handle loading started signal"""
        self.progress_dialog = QProgressDialog("Loading case files...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        self.statusBar().showMessage(f"Loading: {os.path.basename(path)}")
    
    def _on_loading_finished(self, parsed_object):
        """Handle loading finished signal"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        if parsed_object and NodeConverter:
            try:
                # Determine tab name
                if hasattr(self, '_loading_case_dir'):
                    tab_name = os.path.basename(self._loading_case_dir)
                    file_path = self._loading_case_dir
                    delattr(self, '_loading_case_dir')
                else:
                    tab_name = "Loaded Case"
                    file_path = None
                
                # Create new tab for loaded case
                editor_view, editor_scene = self._create_new_case_tab(file_path, tab_name)
                
                # Convert parsed object to visual nodes with connections
                result = NodeConverter.pyvnt_to_visual_nodes(
                    parsed_object, 
                    editor_scene,
                    position_x=600,  # Start with more room for the node tree
                    position_y=-200,  # Start above center
                    spacing=50       # Minimal vertical spacing between nodes
                )
                
                nodes = result.get('nodes', [])
                connections = result.get('connections', [])
                
                # Fit view to show all nodes
                if nodes:
                    editor_view.fitInView(
                        editor_scene.itemsBoundingRect(), 
                        Qt.AspectRatioMode.KeepAspectRatio
                    )
                
                # Mark as clean (just loaded)
                current_index = self.tab_widget.currentIndex()
                self._mark_tab_clean(current_index)
                
                self.statusBar().showMessage(f"Loaded {len(nodes)} nodes with {len(connections)} connections")
                QMessageBox.information(self, "Load Complete", 
                                      f"Successfully loaded case with {len(nodes)} nodes and {len(connections)} connections.")
                
            except Exception as e:
                error_msg = f"Error creating visual nodes: {str(e)}"
                QMessageBox.critical(self, "Load Error", error_msg)
                self.statusBar().showMessage("Load failed")
        else:
            self.statusBar().showMessage("Load failed - no data")
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Check for unsaved changes in any tab
        modified_tabs = []
        for i in range(self.tab_widget.count()):
            if self.tab_modified.get(i, False):
                tab_name = self.tab_widget.tabText(i).replace(" *", "")
                modified_tabs.append((i, tab_name))
        
        if modified_tabs:
            # Ask user what to do with unsaved changes
            tab_names = [name for _, name in modified_tabs]
            if len(tab_names) == 1:
                message = f"The case '{tab_names[0]}' has unsaved changes."
            else:
                message = f"The following cases have unsaved changes:\n" + "\n".join(f"• {name}" for name in tab_names)
            
            message += "\n\nDo you want to save before closing?"
            
            reply = QMessageBox.question(
                self,
                "Save Changes?",
                message,
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Try to save all modified tabs
                for tab_index, _ in modified_tabs:
                    if not self._save_case(tab_index):
                        # If any save fails, don't close
                        event.ignore()
                        return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            # If Discard, continue with closing
        
        event.accept()

    def _on_loading_error(self, error_message):
        """Handle loading error signal"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        QMessageBox.critical(self, "Load Error", error_message)
        self.statusBar().showMessage("Load failed")
    
    def _on_progress_updated(self, percentage, message):
        """Handle progress update signal"""
        if self.progress_dialog:
            self.progress_dialog.setValue(percentage)
            self.progress_dialog.setLabelText(message)

    def _show_getting_started(self):
        """Show getting started guide"""
        getting_started_text = """
<h2>Getting Started with OpenFOAM Case Generator</h2>

<h3>Welcome!</h3>
<p>This tool helps you create OpenFOAM cases visually using a node-based interface.</p>

<h3>New Optimized Workflow:</h3>
<ol>
<li><b>Create Input Nodes:</b> Drag parameter and container nodes from the Node Library</li>
<li><b>Connect to Output Node:</b> Connect your nodes to an Output node for validation</li>
<li><b>Connect to Case Folder:</b> Connect the Output node to a Case Folder node</li>
<li><b>Generate Complete Case:</b> Click "Generate File" on the Case Folder node</li>
</ol>

<h3>Key Benefits:</h3>
<ul>
<li><b>No Duplicate Files:</b> Streamlined workflow prevents creating files twice</li>
<li><b>Validation First:</b> Output nodes validate your configuration before generation</li>
<li><b>Flexible Inputs:</b> Case Folder nodes accept 1-4 connections for partial cases</li>
<li><b>Backward Compatible:</b> Existing cases continue to work normally</li>
</ul>

<h3>Node Types:</h3>
<ul>
<li><b>Node_C:</b> Container nodes for organizing other nodes</li>
<li><b>Key_C:</b> Key-value pairs for OpenFOAM dictionaries</li>
<li><b>Int_P, Flt_P, Str_P:</b> Integer, float, and string values</li>
<li><b>Vector_P:</b> 3D vectors (velocity, coordinates, etc.)</li>
<li><b>Tensor_P:</b> Tensor properties (matrices, stress tensors, etc.)</li>
<li><b>Output:</b> Validates PyVNT objects, optionally generates individual files</li>
<li><b>Case Folder:</b> Generates complete OpenFOAM directory structures</li>
</ul>

<h3>Tips:</h3>
<ul>
<li>Use Input → Output → Case Folder workflow for best results</li>
<li>Output nodes can work standalone for testing individual files</li>
<li>Press K to toggle knife tool for cutting connections</li>
<li>Use View → Fit All to see all nodes</li>
</ul>
        """
        self._show_help_dialog("Getting Started", getting_started_text)

    def _show_user_guide(self):
        """Show detailed user guide"""
        user_guide_text = """
<h2>OpenFOAM Case Generator User Guide</h2>

<h3>Interface Overview</h3>
<p><b>Left Panel:</b> Node Library with all available node types<br>
<b>Main Area:</b> Visual canvas for building case structure<br>
<b>Tabs:</b> Work with multiple cases simultaneously</p>

<h3>New Workflow Architecture</h3>
<p>The application now uses an optimized workflow to eliminate duplicate file generation:</p>

<h4>Recommended Workflow:</h4>
<ol>
<li><b>Input Nodes → Output Node:</b> Connect parameters and containers to Output nodes for validation</li>
<li><b>Output Node → Case Folder Node:</b> Connect validated Output nodes to Case Folder for generation</li>
<li><b>Generate Complete Case:</b> Use Case Folder's "Generate File" button</li>
</ol>

<h4>Alternative Usage:</h4>
<ul>
<li><b>Standalone Output:</b> Output nodes can generate individual files when used alone</li>
<li><b>Partial Cases:</b> Case Folder accepts 1-4 connections for incomplete configurations</li>
<li><b>Mixed Workflow:</b> Combine validated and direct connections as needed</li>
</ul>

<h3>Working with Nodes</h3>
<h4>Creating Nodes:</h4>
<ul>
<li>Drag from Node Library to canvas</li>
<li>Double-click node names to edit them</li>
<li>Use input fields to set values</li>
</ul>

<h4>Connecting Nodes:</h4>
<ul>
<li>Drag from output socket (circle on right) to input socket (circle on left)</li>
<li>Only compatible sockets can be connected</li>
<li>Use Knife Tool (K) to cut connections</li>
</ul>

<h3>File Operations</h3>
<h4>Importing:</h4>
<ul>
<li><b>Import File:</b> Load single OpenFOAM configuration files</li>
<li><b>Import Folder:</b> Load entire OpenFOAM case directories</li>
</ul>

<h4>Saving:</h4>
<ul>
<li><b>Save Case:</b> Save your node structure for later editing</li>
<li><b>Generate Files:</b> Export actual OpenFOAM configuration files</li>
</ul>

<h3>Advanced Features</h3>
<ul>
<li><b>Undo/Redo:</b> Full history of changes (Ctrl+Z/Ctrl+Y)</li>
<li><b>Multiple Tabs:</b> Work on several cases at once</li>
<li><b>Dark/Light Mode:</b> Switch themes in View menu</li>
<li><b>Validation:</b> Output nodes check case consistency before generation</li>
</ul>
        """
        self._show_help_dialog("User Guide", user_guide_text)

    def _show_shortcuts(self):
        """Show keyboard shortcuts reference"""
        shortcuts_text = """
<h2>Keyboard Shortcuts</h2>

<h3>File Operations</h3>
<table border="1" cellpadding="5">
<tr><th>Action</th><th>Shortcut</th></tr>
<tr><td>New Case</td><td>Ctrl+N</td></tr>
<tr><td>Open Case</td><td>Ctrl+O</td></tr>
<tr><td>Save Case</td><td>Ctrl+S</td></tr>
<tr><td>Save As</td><td>Ctrl+Shift+S</td></tr>
<tr><td>Close Tab</td><td>Ctrl+W</td></tr>
<tr><td>Import File</td><td>Ctrl+Shift+I</td></tr>
<tr><td>Import Folder</td><td>Ctrl+Shift+F</td></tr>
<tr><td>Exit</td><td>Ctrl+Q</td></tr>
</table>

<h3>Editing</h3>
<table border="1" cellpadding="5">
<tr><th>Action</th><th>Shortcut</th></tr>
<tr><td>Undo</td><td>Ctrl+Z</td></tr>
<tr><td>Redo</td><td>Ctrl+Y</td></tr>
<tr><td>Knife Tool</td><td>K</td></tr>
<tr><td>Delete Selected</td><td>Delete</td></tr>
</table>

<h3>Navigation</h3>
<table border="1" cellpadding="5">
<tr><th>Action</th><th>Mouse/Key</th></tr>
<tr><td>Pan View</td><td>Middle Mouse + Drag</td></tr>
<tr><td>Zoom</td><td>Mouse Wheel</td></tr>
<tr><td>Select Multiple</td><td>Ctrl + Click</td></tr>
<tr><td>Drag Selection</td><td>Click + Drag</td></tr>
</table>

<h3>Node Operations</h3>
<ul>
<li><b>Create Node:</b> Drag from Node Library</li>
<li><b>Edit Name:</b> Double-click node title</li>
<li><b>Connect:</b> Drag from output to input socket</li>
<li><b>Disconnect:</b> Use Knife Tool (K) and click on connection</li>
</ul>
        """
        self._show_help_dialog("Keyboard Shortcuts", shortcuts_text)

    def _show_node_reference(self):
        """Show node types reference"""
        node_reference_text = """
<h2>Node Types Reference</h2>

<h3>Container Nodes</h3>
<h4>Node_C (Node Container)</h4>
<p><b>Purpose:</b> Groups related nodes together, similar to OpenFOAM subdictionaries<br>
<b>Inputs:</b> Multiple child nodes<br>
<b>Outputs:</b> Container structure<br>
<b>Example:</b> boundaryField, dimensions</p>

<h4>List_CP (List Container)</h4>
<p><b>Purpose:</b> Creates lists or arrays of values<br>
<b>Inputs:</b> Multiple items of same type<br>
<b>Outputs:</b> List structure<br>
<b>Example:</b> Cell zones, boundary patches</p>

<h3>Value Nodes</h3>
<h4>Key_C (Key Container)</h4>
<p><b>Purpose:</b> Key-value pairs for OpenFOAM dictionaries<br>
<b>Inputs:</b> Key name and value<br>
<b>Outputs:</b> Dictionary entry</p>

<h4>Int_P (Integer Parameter)</h4>
<p><b>Purpose:</b> Integer values<br>
<b>Example:</b> startTime, endTime, cell counts</p>

<h4>Flt_P (Float Parameter)</h4>
<p><b>Purpose:</b> Floating-point numbers<br>
<b>Example:</b> deltaT, relaxation factors, tolerance values</p>

<h4>Str_P (String Parameter)</h4>
<p><b>Purpose:</b> Text values<br>
<b>Example:</b> Solver names, file paths, boundary types</p>

<h4>Vector_P (Vector Parameter)</h4>
<p><b>Purpose:</b> 3D vectors (x, y, z)<br>
<b>Example:</b> Velocity vectors, coordinates, forces</p>

<h4>Tensor_P (Tensor Parameter)</h4>
<p><b>Purpose:</b> Multi-dimensional arrays and matrices<br>
<b>Example:</b> Stress tensors, deformation gradients, transformation matrices<br>
<b>Size:</b> Configurable (2x2, 3x3, 4x4, or custom)</p>

<h4>Dim_Set_P (Dimension Set Parameter)</h4>
<p><b>Purpose:</b> Physical dimensions in OpenFOAM format<br>
<b>Format:</b> [mass length time temperature amount current luminosity]<br>
<b>Example:</b> [0 1 -1 0 0 0 0] for velocity</p>

<h4>Enm_P (Enumeration Parameter)</h4>
<p><b>Purpose:</b> Predefined choice from a list of options<br>
<b>Example:</b> Solver types, boundary conditions, schemes</p>

<h3>Output Nodes</h3>
<h4>Output</h4>
<p><b>Purpose:</b> Generate individual OpenFOAM files<br>
<b>Example:</b> controlDict, fvSchemes, fvSolution</p>

<h4>Case Folder</h4>
<p><b>Purpose:</b> Create directory structure for complete OpenFOAM cases<br>
<b>Includes:</b> system/, constant/, 0/ directories</p>

<h3>Connection Rules</h3>
<ul>
<li>Outputs (right side) connect to inputs (left side)</li>
<li>Type compatibility is enforced</li>
<li>One output can connect to multiple inputs</li>
<li>Each input accepts only one connection</li>
</ul>
        """
        self._show_help_dialog("Node Types Reference", node_reference_text)

    def _open_openfoam_docs(self):
        """Open OpenFOAM documentation in browser"""
        import webbrowser
        try:
            webbrowser.open("https://openfoam.org/documentation/")
            self.statusBar().showMessage("Opening OpenFOAM documentation in browser...")
        except Exception as e:
            QMessageBox.warning(self, "Browser Error", 
                              f"Could not open browser: {str(e)}")

    def _report_issue(self):
        """Show information about reporting issues"""
        issue_text = """
<h2>Report an Issue</h2>

<h3>Before Reporting</h3>
<ul>
<li>Check if the issue is reproducible</li>
<li>Try with a simple test case</li>
<li>Check the console output for error messages</li>
</ul>

<h3>What to Include</h3>
<ul>
<li><b>Steps to reproduce:</b> Detailed description of what you did</li>
<li><b>Expected behavior:</b> What should have happened</li>
<li><b>Actual behavior:</b> What actually happened</li>
<li><b>Error messages:</b> Any error dialogs or console output</li>
<li><b>System info:</b> Operating system, Python version</li>
<li><b>Case file:</b> If possible, attach the .case file that causes issues</li>
</ul>

<h3>Where to Report</h3>
<p>Report issues to the project repository or contact the development team.</p>

<h3>Feature Requests</h3>
<p>We welcome suggestions for new features or improvements!</p>

<h3>Development Info</h3>
<p><b>Version:</b> 1.0<br>
<b>Built with:</b> PyQt6, Python<br>
<b>OpenFOAM Support:</b> Compatible with OpenFOAM v8+</p>
        """
        self._show_help_dialog("Report Issue", issue_text)

    def _show_about(self):
        """Show about dialog"""
        about_text = """
<h2>OpenFOAM Case Generator</h2>
<p><b>Version:</b> 1.0</p>
<p><b>Built with:</b> PyQt6, Python</p>

<h3>Description</h3>
<p>A visual node-based editor for creating OpenFOAM computational fluid dynamics cases. 
This tool simplifies the process of setting up complex OpenFOAM simulations by providing 
an intuitive graphical interface.</p>

<h3>Features</h3>
<ul>
<li>Visual node-based case construction</li>
<li>Import existing OpenFOAM cases</li>
<li>Generate complete case directories</li>
<li>Multiple case tabs</li>
<li>Undo/Redo support</li>
<li>Dark/Light themes</li>
</ul>

<h3>OpenFOAM Compatibility</h3>
<p>Compatible with OpenFOAM v8 and newer versions.</p>

<h3>License</h3>
<p>This software is provided as-is for educational and research purposes.</p>

<h3>Acknowledgments</h3>
<p>Built using the PyVNT library for OpenFOAM file parsing and generation.</p>
        """
        self._show_help_dialog("About OpenFOAM Case Generator", about_text)

    def _show_help_dialog(self, title, content):
        """Show a help dialog with formatted HTML content"""
        from PyQt6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QPushButton
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(False)  # Allow interaction with main window
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create text browser for rich text display
        text_browser = QTextBrowser()
        text_browser.setHtml(content)
        text_browser.setOpenExternalLinks(True)
        layout.addWidget(text_browser)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.show()

    def set_default_output_dir(self, output_dir: str):
        """Set the default output directory for cases"""
        self.default_output_dir = output_dir
        
        # Update any existing Case Folder Output nodes in all tabs
        for tab_index in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(tab_index)
            if hasattr(tab_widget, 'scene'):
                scene = tab_widget.scene()
                if hasattr(scene, 'nodes'):
                    for node in scene.nodes:
                        if type(node).__name__ == 'CaseFolderOutputNode':
                            if hasattr(node, 'set_default_output_dir'):
                                node.set_default_output_dir(output_dir)
