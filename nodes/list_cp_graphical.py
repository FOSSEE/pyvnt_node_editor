"""List_CPGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import (QGraphicsProxyWidget, QLabel, QTextEdit, 
                           QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QCheckBox)
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode

class List_CPGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT List_CP (container list) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 260  # Reduced width for list content
        self._create_list_widgets()
        self.add_input_socket(multi_connection=True)  # Can accept multiple inputs
        self.add_output_socket(multi_connection=False)
        self._update_height()
    
    def _create_list_widgets(self):
        """Create list container widgets"""
        style = "color: white; font-size: 12px; font-family: Arial; font-weight: bold; padding: 2px;"
        input_style = """
            QTextEdit {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                background-color: #404040;
                color: white;
                font-size: 11px;
                font-family: Consolas, monospace;
            }
            QTextEdit:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        button_style = """
            QPushButton {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px 8px;
                background-color: #505050;
                color: white;
                font-size: 10px;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: #606060;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """
        
        # Name input field
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_input = QTextEdit()
        self.name_input.setPlaceholderText("Enter list name (e.g., 'boundary', 'vertices')")
        self.name_input.setText("listVal")
        self.name_input.setStyleSheet(input_style)
        self.name_input.setMaximumHeight(25)
        self.name_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_input)
        
        # IsNode checkbox
        self.isnode_checkbox = QCheckBox("Is Node List")
        self.isnode_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 11px;
                font-family: Arial;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
        """)
        self.isnode_checkbox.setChecked(False)
        self.isnode_checkbox.toggled.connect(self._on_isnode_changed)
        self.isnode_proxy = QGraphicsProxyWidget(self)
        self.isnode_proxy.setWidget(self.isnode_checkbox)
        
        # List elements text area
        self.elements_label = QLabel("Elements:")
        self.elements_label.setStyleSheet(style)
        self.elements_label_proxy = QGraphicsProxyWidget(self)
        self.elements_label_proxy.setWidget(self.elements_label)
        
        self.elements_text = QTextEdit()
        self.elements_text.setPlaceholderText("Enter list elements (one per line):\n1 2 3\n4 5 6\nor use connected nodes")
        self.elements_text.setText("1 2 3\n4 5 6")  # Default example
        self.elements_text.setStyleSheet(input_style)
        self.elements_text.setMaximumHeight(80)
        self.elements_proxy = QGraphicsProxyWidget(self)
        self.elements_proxy.setWidget(self.elements_text)
        
        # Helper buttons container
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(4)
        
        # Add row button
        self.add_button = QPushButton("+ Row")
        self.add_button.setStyleSheet(button_style)
        self.add_button.clicked.connect(self._add_row)
        self.buttons_layout.addWidget(self.add_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(button_style)
        self.clear_button.clicked.connect(self._clear_elements)
        self.buttons_layout.addWidget(self.clear_button)
        
        self.buttons_layout.addStretch()
        
        self.buttons_proxy = QGraphicsProxyWidget(self)
        self.buttons_proxy.setWidget(self.buttons_widget)
    
    def _add_row(self):
        """Add a new row to the elements"""
        current_text = self.elements_text.toPlainText()
        if current_text and not current_text.endswith('\n'):
            current_text += '\n'
        self.elements_text.setPlainText(current_text + "0 0 0")
        
        # Move cursor to end
        cursor = self.elements_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.elements_text.setTextCursor(cursor)
    
    def _clear_elements(self):
        """Clear all elements"""
        self.elements_text.clear()
    
    def _update_height(self):
        """Update node height and position widgets"""
        self.height = self.title_height + self.content_margin * 2 + self.get_additional_content_height()
        
        y = self.title_height + self.content_margin
        
        # Position Name label and input
        self.name_label.setFixedSize(50, 16)
        self.name_label_proxy.setPos(self.content_margin, y)
        y += 20
        
        text_width = self.width - 2 * self.content_margin
        self.name_input.setFixedSize(text_width, 25)
        self.name_proxy.setPos(self.content_margin, y)
        y += 30
        
        # Position IsNode checkbox
        self.isnode_checkbox.setFixedSize(120, 20)
        self.isnode_proxy.setPos(self.content_margin, y)
        y += 25
        
        # Position Elements label
        self.elements_label.setFixedSize(70, 16)
        self.elements_label_proxy.setPos(self.content_margin, y)
        y += 20
        
        # Position Elements text area
        self.elements_text.setFixedSize(text_width, 80)
        self.elements_proxy.setPos(self.content_margin, y)
        y += 84
        
        # Position buttons
        self.buttons_widget.setFixedSize(text_width, 24)
        self.buttons_proxy.setPos(self.content_margin, y)
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def _on_isnode_changed(self, checked):
        """Handle IsNode checkbox state change"""
        if checked:
            self.elements_text.setPlaceholderText("This list will contain child nodes.\nConnect child nodes to input socket.")
            self.elements_text.setEnabled(False)
        else:
            self.elements_text.setPlaceholderText("Enter list elements (one per line):\n1 2 3\n4 5 6\nor use connected nodes")
            self.elements_text.setEnabled(True)
    
    def get_additional_content_height(self):
        """Return height for list widgets"""
        return 16 + 4 + 25 + 4 + 20 + 4 + 16 + 4 + 80 + 4 + 24  # Name + checkbox + elements + buttons
    
    def get_node_title(self):
        return "List_CP"
    
    def get_pyvnt_object(self):
        """Build PyVNT List_CP object from current field values, recursively handling nested lists automatically."""
        try:
            from pyvnt.Container.list import List_CP
            from pyvnt.Reference.basic import Flt_P, Str_P, Int_P
        except ImportError:
            return None

        name = self.name_input.toPlainText().strip() or "listVal"
        is_node = self.isnode_checkbox.isChecked()

        if is_node:
            child_values = []
            for socket in self.input_sockets:
                for edge in getattr(socket, 'edges', []):
                    other_socket = edge.getOtherSocket(socket)
                    if other_socket and hasattr(other_socket, 'node'):
                        connected_node = other_socket.node
                        if hasattr(connected_node, 'get_pyvnt_object'):
                            try:
                                child_obj = connected_node.get_pyvnt_object()
                                print(f"[List_CPGraphicalNode] Got child from connected node: {type(child_obj).__name__} | {child_obj}")
                                if child_obj is not None:
                                    child_values.append(child_obj)
                            except Exception as e:
                                print(f"Warning: Failed to get PyVNT object from connected child: {e}")
            print(f"[List_CPGraphicalNode] All collected child values: {[type(v).__name__ for v in child_values]}")
            return List_CP(name, values=child_values, isNode=True)
        else:
            # Aggregate all connected value nodes (including List_CP) as a single sublist for OpenFOAM block lines
            connected_values = []
            for socket in self.input_sockets:
                for edge in getattr(socket, 'edges', []):
                    other_socket = edge.getOtherSocket(socket)
                    if other_socket and hasattr(other_socket, 'node'):
                        connected_node = other_socket.node
                        if hasattr(connected_node, 'get_pyvnt_object'):
                            try:
                                val_obj = connected_node.get_pyvnt_object()
                                if val_obj is not None:
                                    connected_values.append(val_obj)
                            except Exception as e:
                                print(f"Warning: Failed to get PyVNT object from connected value node: {e}")
            elements_text = self.elements_text.toPlainText().strip()
            rows = []
            if connected_values:
                # If there are connected nodes, treat them as a single sublist (for block lines)
                rows.append(connected_values)
            if elements_text:
                def parse_nested_rows(lines):
                    rows = []
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        values = line.split()
                        row_elements = []
                        for i, val in enumerate(values):
                            try:
                                if '.' not in val and 'e' not in val.lower():
                                    int_val = int(val)
                                    row_elements.append(Int_P(f"val_{i}", int_val))
                                else:
                                    float_val = float(val)
                                    row_elements.append(Flt_P(f"val_{i}", float_val))
                            except ValueError:
                                try:
                                    row_elements.append(Str_P(f"val_{i}", val))
                                except ImportError:
                                    continue
                        if row_elements:
                            rows.append(row_elements)
                    return rows
                lines = elements_text.split('\n')
                rows.extend(parse_nested_rows(lines))
            if not rows:
                rows = [[]]
            return List_CP(name, elems=rows)
