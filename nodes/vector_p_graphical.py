"""Vector_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QDoubleSpinBox, QLabel, QLineEdit
from nodes.base_graphical_node import BaseGraphicalNode

class Vector_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Vector_P (vector property) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 280  # Wider for vector input controls
        
        # Create the UI widgets
        self._create_vector_widgets()
        
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        
        # Update height based on content
        self._update_height()
    
    def _create_vector_widgets(self):
        """Create vector property widgets"""
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
        
        # Name field
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("velocity")  # Default OpenFOAM-like name
        self.name_edit.setPlaceholderText("Enter parameter name")
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
        
        # X component
        self.x_label = QLabel("X:")
        self.x_label.setStyleSheet(style)
        self.x_label_proxy = QGraphicsProxyWidget(self)
        self.x_label_proxy.setWidget(self.x_label)
        
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setDecimals(6)
        self.x_spin.setRange(-1000000, 1000000)
        self.x_spin.setValue(0.0)
        self.x_spin.setStyleSheet(spin_style)
        self.x_proxy = QGraphicsProxyWidget(self)
        self.x_proxy.setWidget(self.x_spin)
        
        # Y component
        self.y_label = QLabel("Y:")
        self.y_label.setStyleSheet(style)
        self.y_label_proxy = QGraphicsProxyWidget(self)
        self.y_label_proxy.setWidget(self.y_label)
        
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setDecimals(6)
        self.y_spin.setRange(-1000000, 1000000)
        self.y_spin.setValue(0.0)
        self.y_spin.setStyleSheet(spin_style)
        self.y_proxy = QGraphicsProxyWidget(self)
        self.y_proxy.setWidget(self.y_spin)
        
        # Z component
        self.z_label = QLabel("Z:")
        self.z_label.setStyleSheet(style)
        self.z_label_proxy = QGraphicsProxyWidget(self)
        self.z_label_proxy.setWidget(self.z_label)
        
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setDecimals(6)
        self.z_spin.setRange(-1000000, 1000000)
        self.z_spin.setValue(0.0)
        self.z_spin.setStyleSheet(spin_style)
        self.z_proxy = QGraphicsProxyWidget(self)
        self.z_proxy.setWidget(self.z_spin)
    
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
        y += 24
        
        # X, Y, Z components
        component_label_w = 25
        spin_w = min(input_w, 120)
        
        # X component
        self.x_label.setFixedSize(component_label_w, label_h)
        self.x_label_proxy.setPos(self.content_margin, y)
        self.x_spin.setFixedSize(spin_w, 20)
        self.x_proxy.setPos(self.content_margin + component_label_w + 5, y)
        y += 24
        
        # Y component
        self.y_label.setFixedSize(component_label_w, label_h)
        self.y_label_proxy.setPos(self.content_margin, y)
        self.y_spin.setFixedSize(spin_w, 20)
        self.y_proxy.setPos(self.content_margin + component_label_w + 5, y)
        y += 24
        
        # Z component
        self.z_label.setFixedSize(component_label_w, label_h)
        self.z_label_proxy.setPos(self.content_margin, y)
        self.z_spin.setFixedSize(spin_w, 20)
        self.z_proxy.setPos(self.content_margin + component_label_w + 5, y)
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_additional_content_height(self):
        """Return the height needed for vector-specific widgets"""
        # Add height for: name field + 3 components (X, Y, Z)
        return (24 * 4)  # 24 pixels per row, 4 rows (name + x + y + z)
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Vector_P"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Vector_P object from current UI state.
        """
        from pyvnt.Reference.vector import Vector_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "velocity"  # Default fallback
        
        # Create Vector_P with simple constructor: name, x, y, z
        pyvnt_vector = Vector_P(
            name,
            float(self.x_spin.value()),
            float(self.y_spin.value()),
            float(self.z_spin.value())
        )
        return pyvnt_vector
