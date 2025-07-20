"""Flt_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QDoubleSpinBox, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode

class Flt_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Flt_P (float property) object"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 300  # Increased from 250 for better visibility
        # Create the UI widgets
        self._create_float_widgets()
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        # Update height based on content
        self._update_height()
    def set_on_property_changed(self, callback):
        self.on_property_changed = callback

    def _create_float_widgets(self):
        """Create float property widgets with name field"""
        style = "color: white; font-size: 14px; font-family: Arial; font-weight: bold; padding: 2px;"
        spin_style = """
            QDoubleSpinBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 14px;
                font-family: Arial;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        
        # Name
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("tolerance")  # Default OpenFOAM-like name
        self.name_edit.setPlaceholderText("Enter parameter name")
        self.name_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.name_edit.setStyleSheet("""
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
        """)
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Value
        self.value_label = QLabel("Value:")
        self.value_label.setStyleSheet(style)
        self.value_label_proxy = QGraphicsProxyWidget(self)
        self.value_label_proxy.setWidget(self.value_label)
        
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setDecimals(10)  # More decimals to support scientific notation
        self.value_spin.setRange(-1000000, 1000000)
        self.value_spin.setValue(1e-06)  # Set default to 1e-06 like in demo cases
        self.value_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.value_spin.setStyleSheet(spin_style)
        self.value_spin.valueChanged.connect(self._on_value_changed)
        self.value_proxy = QGraphicsProxyWidget(self)
        self.value_proxy.setWidget(self.value_spin)
        
        # Min
        self.min_label = QLabel("Min:")
        self.min_label.setStyleSheet(style)
        self.min_label_proxy = QGraphicsProxyWidget(self)
        self.min_label_proxy.setWidget(self.min_label)
        
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setDecimals(10)  # More decimals to support scientific notation
        self.min_spin.setRange(-1000000, 1000000)
        self.min_spin.setValue(0.0)  # PyVNT default minimum
        self.min_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.min_spin.setStyleSheet(spin_style)
        self.min_spin.valueChanged.connect(self._on_min_changed)
        self.min_proxy = QGraphicsProxyWidget(self)
        self.min_proxy.setWidget(self.min_spin)
        
        # Max
        self.max_label = QLabel("Max:")
        self.max_label.setStyleSheet(style)
        self.max_label_proxy = QGraphicsProxyWidget(self)
        self.max_label_proxy.setWidget(self.max_label)
        
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setDecimals(10)  # More decimals to support scientific notation
        self.max_spin.setRange(-1000000, 1000000)
        self.max_spin.setValue(100.0)  # PyVNT default maximum
        self.max_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.max_spin.setStyleSheet(spin_style)
        self.max_spin.valueChanged.connect(self._on_max_changed)
        self.max_proxy = QGraphicsProxyWidget(self)
        self.max_proxy.setWidget(self.max_spin)
        
        self._position_float_widgets()
    def _position_float_widgets(self):
        y = self.title_height + self.content_margin
        label_w, label_h = 50, 18
        spin_w, spin_h = self.width - 2 * self.content_margin - label_w - 5, 18
        max_spin_w = 140
        spin_w = min(spin_w, max_spin_w)  # Clamp spinbox width
        
        # Name
        self.name_label.setFixedSize(label_w, label_h)
        self.name_label_proxy.setPos(self.content_margin, y)
        self.name_edit.setFixedSize(spin_w, spin_h)
        self.name_proxy.setPos(self.content_margin + label_w + 5, y)
        y += label_h + 4
        
        # Value
        self.value_label.setFixedSize(label_w, label_h)
        self.value_label_proxy.setPos(self.content_margin, y)
        self.value_spin.setFixedSize(spin_w, spin_h)
        self.value_proxy.setPos(self.content_margin + label_w + 5, y)
        y += label_h + 4
        
        # Min
        self.min_label.setFixedSize(label_w, label_h)
        self.min_label_proxy.setPos(self.content_margin, y)
        self.min_spin.setFixedSize(spin_w, spin_h)
        self.min_proxy.setPos(self.content_margin + label_w + 5, y)
        y += label_h + 4
        
        # Max
        self.max_label.setFixedSize(label_w, label_h)
        self.max_label_proxy.setPos(self.content_margin, y)
        self.max_spin.setFixedSize(spin_w, spin_h)
        self.max_proxy.setPos(self.content_margin + label_w + 5, y)
    def _update_height(self):
        total_h = self.title_height + self.content_margin * 2 + (18 + 4) * 4  # Four rows now
        self.height = total_h
        self._position_float_widgets()
        # Important: Position sockets after height update
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_additional_content_height(self):
        """Return the height needed for float-specific widgets"""
        # Add height for: 4 rows of (label + spinbox + spacing)
        return (18 + 4) * 4
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Flt_P"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Flt_P object from current UI state.
        No recursion needed - this is a leaf node.
        """
        from pyvnt.Reference.basic import Flt_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "tolerance"  # Default fallback
        
        # Get the value and ensure it's properly formatted for scientific notation
        value = float(self.value_spin.value())
        min_val = float(self.min_spin.value())
        max_val = float(self.max_spin.value())
        
        # Create Flt_P with correct constructor signature: name, default, minimum, maximum
        # Use the user-specified min/max values to allow values outside default range
        pyvnt_float = Flt_P(
            name,            # Use the user-specified name
            default=value,   # This is the actual value
            minimum=min_val, # User-specified minimum
            maximum=max_val  # User-specified maximum
        )
        return pyvnt_float

    def _on_value_changed(self, value):
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'value', value)

    def _on_min_changed(self, value):
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'min', value)

    def _on_max_changed(self, value):
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'max', value)
