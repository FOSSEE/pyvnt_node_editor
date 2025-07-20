"""Str_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel
from nodes.base_graphical_node import BaseGraphicalNode

class Str_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Str_P (string property) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 260  # Wider for text input
        # Create the UI widgets
        self._create_string_widgets()
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        # Update height based on content
        self._update_height()
    
    def _create_string_widgets(self):
        """Create string property widgets"""
        style = "color: white; font-size: 14px; font-family: Arial; font-weight: bold; padding: 2px;"
        input_style = """
            QLineEdit {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 14px;
                font-family: Arial;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        
        # Name input
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("format")  # Default OpenFOAM-like name
        self.name_edit.setPlaceholderText("Enter parameter name")
        self.name_edit.setStyleSheet(input_style)
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Value input
        self.value_label = QLabel("Value:")
        self.value_label.setStyleSheet(style)
        self.value_label_proxy = QGraphicsProxyWidget(self)
        self.value_label_proxy.setWidget(self.value_label)
        
        self.value_edit = QLineEdit()
        self.value_edit.setText("stringValue")
        self.value_edit.setPlaceholderText("Enter string value...")
        self.value_edit.setStyleSheet(input_style)
        self.value_proxy = QGraphicsProxyWidget(self)
        self.value_proxy.setWidget(self.value_edit)
    
    def _update_height(self):
        """Update node height and position widgets"""
        self.height = self.title_height + self.content_margin * 2 + self.get_additional_content_height()
        
        y = self.title_height + self.content_margin
        label_w, label_h = 50, 20
        input_w = self.width - 2 * self.content_margin - label_w - 5
        
        # Name input
        self.name_label.setFixedSize(label_w, label_h)
        self.name_label_proxy.setPos(self.content_margin, y)
        self.name_edit.setFixedSize(input_w, 20)
        self.name_proxy.setPos(self.content_margin + label_w + 5, y)
        y += label_h + 4
        
        # Value input
        self.value_label.setFixedSize(label_w, label_h)
        self.value_label_proxy.setPos(self.content_margin, y)
        self.value_edit.setFixedSize(input_w, 20)
        self.value_proxy.setPos(self.content_margin + label_w + 5, y)
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_additional_content_height(self):
        """Return the height needed for string-specific widgets"""
        # Add height for: 2 rows of (label + input)
        return (20 + 4) * 2
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Str_P"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Str_P object from current UI state.
        """
        from pyvnt.Reference.basic import Str_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "format"  # Default fallback
        
        # Create Str_P with name and value
        pyvnt_string = Str_P(name, self.value_edit.text())
        return pyvnt_string
