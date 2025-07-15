"""Dim_Set_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QSpinBox, QLabel, QLineEdit
from nodes.base_graphical_node import BaseGraphicalNode

class Dim_Set_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Dim_Set_P (dimension set) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 250  # Further reduced width for dimension controls
        
        # Create the UI widgets
        self._create_dimension_widgets()
        
        # Add output socket (circular for single connection)
        self.add_output_socket(multi_connection=False)
        
        # Update height based on content
        self._update_height()
    
    def _create_dimension_widgets(self):
        """Create dimension set widgets for [mass, length, time, temperature, moles, current, luminosity]"""
        style = "color: white; font-size: 14px; font-family: Arial; font-weight: bold; padding: 2px;"
        spin_style = """
            QSpinBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 14px;
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
        self.name_edit.setText("dimensions")  # Default OpenFOAM-like name
        self.name_edit.setPlaceholderText("Enter parameter name")
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
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Dimension labels and default values
        self.dim_names = ["Mass", "Length", "Time", "Temp", "Moles", "Current", "Luminosity"]
        self.dim_labels = []
        self.dim_spins = []
        self.dim_proxies = []
        self.dim_label_proxies = []
        
        # Default dimensions for velocity: [0, 1, -1, 0, 0, 0, 0]
        default_values = [0, 1, -1, 0, 0, 0, 0]
        
        for i, (name, default_val) in enumerate(zip(self.dim_names, default_values)):
            # Label
            label = QLabel(f"{name}:")
            label.setStyleSheet(style)
            label_proxy = QGraphicsProxyWidget(self)
            label_proxy.setWidget(label)
            
            # Spinbox
            spin = QSpinBox()
            spin.setRange(-10, 10)  # Typical range for dimensions
            spin.setValue(default_val)
            spin.setStyleSheet(spin_style)
            spin_proxy = QGraphicsProxyWidget(self)
            spin_proxy.setWidget(spin)
            
            self.dim_labels.append(label)
            self.dim_label_proxies.append(label_proxy)
            self.dim_spins.append(spin)
            self.dim_proxies.append(spin_proxy)
    
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
        
        # Dimension components
        dim_label_w = 70
        spin_w = 60
        
        for i in range(len(self.dim_names)):
            # Position label
            self.dim_labels[i].setFixedSize(dim_label_w, label_h)
            self.dim_label_proxies[i].setPos(self.content_margin, y)
            
            # Position spinbox
            self.dim_spins[i].setFixedSize(spin_w, 20)
            self.dim_proxies[i].setPos(self.content_margin + dim_label_w + 5, y)
            
            y += 24
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_additional_content_height(self):
        """Return the height needed for dimension-specific widgets"""
        # Add height for: 8 rows (name + 7 dimensions) * (height + spacing)
        return (20 + 4) * 8
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Dim_Set_P"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Dim_Set_P object from current UI state.
        """
        from pyvnt.Reference.dimension_set import Dim_Set_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "dimensions"  # Default fallback
        
        # Get values from all spinboxes
        dimensions = [spin.value() for spin in self.dim_spins]
        
        # Create Dim_Set_P with list of dimensions
        pyvnt_dimset = Dim_Set_P(name, dimensions)
        return pyvnt_dimset
