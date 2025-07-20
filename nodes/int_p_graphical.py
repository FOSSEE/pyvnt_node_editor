"""Int_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QSpinBox, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode

class Int_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Int_P (integer property) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 260
        # Create the UI widgets
        self._create_integer_widgets()
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        # Update height based on content
        self._update_height()
    
    def set_on_property_changed(self, callback):
        self.on_property_changed = callback

    def _create_integer_widgets(self):
        """Create integer property widgets"""
        style = "color: white; font-size: 14px; font-family: Arial; font-weight: bold; padding: 2px;"
        input_style = "QLineEdit { border: 1px solid #555555; border-radius: 3px; padding: 2px; background-color: #404040; color: white; font-size: 14px; font-family: Arial; } QLineEdit:focus { border: 1px solid #0078d4; background-color: #4a4a4a; }"
        spinbox_style = "QSpinBox { border: 1px solid #555555; border-radius: 3px; padding: 2px; background-color: #404040; color: white; font-size: 14px; font-family: Arial; } QSpinBox:focus { border: 1px solid #0078d4; background-color: #4a4a4a; }"
        
        # Name input
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("nCorrectors")
        self.name_edit.setPlaceholderText("Enter parameter name")
        self.name_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.name_edit.setStyleSheet(input_style)
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Value input
        self.value_label = QLabel("Value:")
        self.value_label.setStyleSheet(style)
        self.value_label_proxy = QGraphicsProxyWidget(self)
        self.value_label_proxy.setWidget(self.value_label)
        
        self.value_spinbox = QSpinBox()
        self.value_spinbox.setRange(-999999, 999999)
        self.value_spinbox.setValue(2)
        self.value_spinbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.value_spinbox.setStyleSheet(spinbox_style)
        self.value_spinbox.valueChanged.connect(self._on_value_changed)
        self.value_proxy = QGraphicsProxyWidget(self)
        self.value_proxy.setWidget(self.value_spinbox)
    
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
        self.value_spinbox.setFixedSize(input_w, 20)
        self.value_proxy.setPos(self.content_margin + label_w + 5, y)
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_additional_content_height(self):
        """Return the height needed for integer-specific widgets"""
        return (20 + 4) * 2  # 2 rows of (label + input)
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Int_P"
        
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Int_P object from current UI state.
        No recursion needed - this is a leaf node.
        """
        from pyvnt.Reference.basic import Int_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "value"  # Default fallback
        
        # Get the value from the spinbox
        value = self.value_spinbox.value()
        
        # Create Int_P with correct constructor signature: name, default value
        pyvnt_int = Int_P(
            name,          # Use the user-specified name
            default=value  # This is the actual value
        )
        
        return pyvnt_int
    
    def _on_value_changed(self, value):
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'value', value)
