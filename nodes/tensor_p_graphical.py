"""Tensor_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QDoubleSpinBox, QLabel, QLineEdit, QSpinBox
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode

class Tensor_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Tensor_P (tensor property) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 320  # Decreased width to fit components tightly
        # Create the UI widgets
        self._create_tensor_widgets()
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        # Update height based on content
        self._update_height()
    
    def _create_tensor_widgets(self):
        """Create tensor property widgets"""
        style = "color: white; font-size: 12px; font-family: Arial; font-weight: bold; padding: 2px;"
        spin_style = """
            QDoubleSpinBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 12px;
                font-family: Arial;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        
        size_spin_style = """
            QSpinBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 12px;
                font-family: Arial;
            }
            QSpinBox:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        
        # Name field
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("tensor")  # Default OpenFOAM-like name
        self.name_edit.setPlaceholderText("Enter parameter name")
        self.name_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 12px;
                font-family: Arial;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Tensor size selector
        self.size_label = QLabel("Size:")
        self.size_label.setStyleSheet(style)
        self.size_label_proxy = QGraphicsProxyWidget(self)
        self.size_label_proxy.setWidget(self.size_label)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 20)  # Reasonable range for tensor size
        self.size_spin.setValue(9)  # Default 3x3 tensor (9 components)
        self.size_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.size_spin.setStyleSheet(size_spin_style)
        self.size_spin.valueChanged.connect(self._update_tensor_components)
        self.size_proxy = QGraphicsProxyWidget(self)
        self.size_proxy.setWidget(self.size_spin)
        
        # Tensor components
        self.components_label = QLabel("Components:")
        self.components_label.setStyleSheet(style)
        self.components_label_proxy = QGraphicsProxyWidget(self)
        self.components_label_proxy.setWidget(self.components_label)
        
        # Initialize component spin boxes
        self.component_spins = []
        self.component_proxies = []
        self._create_tensor_components()
    
    def _create_tensor_components(self):
        """Create spin boxes for tensor components"""
        spin_style = """
            QDoubleSpinBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 11px;
                font-family: Arial;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """
        
        # Clear existing components
        for proxy in self.component_proxies:
            proxy.setParent(None)
        self.component_spins.clear()
        self.component_proxies.clear()
        
        # Create new components based on size
        size = self.size_spin.getValue() if hasattr(self.size_spin, 'getValue') else self.size_spin.value()
        for i in range(size):
            component_spin = QDoubleSpinBox()
            component_spin.setDecimals(6)
            component_spin.setRange(-1000000, 1000000)
            component_spin.setValue(0.0)
            component_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            component_spin.setStyleSheet(spin_style)
            
            component_proxy = QGraphicsProxyWidget(self)
            component_proxy.setWidget(component_spin)
            
            self.component_spins.append(component_spin)
            self.component_proxies.append(component_proxy)
    
    def _update_tensor_components(self):
        """Update tensor components when size changes"""
        self._create_tensor_components()
        self._update_height()
        self._position_widgets()
    
    def _position_widgets(self):
        """Position all widgets within the node"""
        y_offset = self.title_height + self.content_margin  # Start below node title using proper spacing
        widget_height = 25
        margin = 5
        
        # Name widgets
        self.name_label_proxy.setPos(self.content_margin, y_offset)
        self.name_proxy.setPos(60, y_offset)
        y_offset += widget_height + margin
        
        # Size widgets
        self.size_label_proxy.setPos(self.content_margin, y_offset)
        self.size_proxy.setPos(60, y_offset)
        y_offset += widget_height + margin
        
        # Components label
        self.components_label_proxy.setPos(self.content_margin, y_offset)
        y_offset += widget_height
        
        # Component spin boxes (arrange in grid if 3x3, 2x2, etc.)
        size = len(self.component_spins)
        # Always use 2 columns per row for all sizes
        cols = 2
        rows = (size + cols - 1) // cols

        component_width = 110  # More width per component
        component_height = 36
        start_x = self.content_margin

        h_spacing = 32  # Increased horizontal spacing to prevent overlap
        v_spacing = 4  # Reduced vertical spacing, but enough to avoid overlap

        for i, proxy in enumerate(self.component_proxies):
            row = i // cols
            col = i % cols
            x = start_x + col * (component_width + h_spacing)
            y = y_offset + row * (component_height + v_spacing)
            proxy.setPos(x, y)
    
    def _update_height(self):
        """Update node height based on number of components"""
        base_height = 140  # Increased from 120 for better spacing

        # Calculate additional height for components
        size = len(self.component_spins) if hasattr(self, 'component_spins') else 0
        cols = 2
        rows = (size + cols - 1) // cols if size > 0 else 0
        component_height = rows * 36 + max(0, (rows - 1) * 4)  # Match reduced vertical spacing
        self.height = base_height + component_height

        # Position widgets after height update
        self._position_widgets()

        # Position sockets and update graphics
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_tensor_data(self):
        """Get the current tensor data as a dictionary"""
        return {
            'name': self.name_edit.text(),
            'size': self.size_spin.value(),
            'components': [spin.value() for spin in self.component_spins]
        }
    
    def set_tensor_data(self, data):
        """Set tensor data from a dictionary"""
        if 'name' in data:
            self.name_edit.setText(data['name'])
        if 'size' in data:
            self.size_spin.setValue(data['size'])
        if 'components' in data:
            for i, value in enumerate(data['components']):
                if i < len(self.component_spins):
                    self.component_spins[i].setValue(value)
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Tensor_P object from current UI state.
        This is the standard method name used by the framework.
        """
        from pyvnt.Reference.tensor import Tensor_P
        from pyvnt.Reference.basic import Flt_P
        
        name = self.name_edit.text()
        components = [Flt_P(f"component_{i}", spin.value()) 
                     for i, spin in enumerate(self.component_spins)]
        
        return Tensor_P(name, components)
    
    def from_pyvnt_object(self, tensor_obj):
        """Update this graphical node from a PyVNT Tensor_P object"""
        if hasattr(tensor_obj, 'name'):
            self.name_edit.setText(tensor_obj.name)
        if hasattr(tensor_obj, 'value') and isinstance(tensor_obj.value, list):
            self.size_spin.setValue(len(tensor_obj.value))
            self._update_tensor_components()
            for i, flt_p in enumerate(tensor_obj.value):
                if i < len(self.component_spins) and hasattr(flt_p, 'value'):
                    self.component_spins[i].setValue(flt_p.value)
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Tensor_P"
    
    def get_node_color(self):
        """Return the color for this node type - purple for tensor parameters"""
        return "#8E44AD"  # Purple color for tensor parameters
