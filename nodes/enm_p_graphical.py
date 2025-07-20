"""Enm_PGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import (QGraphicsProxyWidget, QComboBox, QLabel, QLineEdit, 
                            QListWidget, QAbstractItemView, QVBoxLayout, QWidget, QGraphicsItem)
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode


class Enm_PGraphicalNode(BaseGraphicalNode):
    """Graphical node representing a PyVNT Enm_P (enum property) object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 280  # Increased from 240 for better visibility of multiselect
        self._create_enum_widgets()
        self.add_output_socket(multi_connection=False)
        self._update_height()
    
    def set_on_property_changed(self, callback):
        self.on_property_changed = callback

    def _create_enum_widgets(self):
        """Create simple, efficient enum property widgets"""
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
        combo_style = """
            QComboBox {
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                background-color: #404040;
                color: white;
                font-size: 14px;
                font-family: Arial;
            }
            QComboBox:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: white;
                selection-background-color: #0078d4;
            }
        """
        
        # Name input
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet(style)
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText("enumVal")  # Default name
        self.name_edit.setPlaceholderText("Enter parameter name")
        self.name_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.name_edit.setStyleSheet(input_style)
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Items multiselect list
        self.items_label = QLabel("Items:")
        self.items_label.setStyleSheet(style)
        self.items_label_proxy = QGraphicsProxyWidget(self)
        self.items_label_proxy.setWidget(self.items_label)
        
        # Create a list widget for multiselect
        self.items_list = QListWidget()
        self.items_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.items_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        
        # Comprehensive OpenFOAM enum values organized by category
        # Each category is clearly separated for better user experience
        
        # === FILE FORMATS & CLASSES ===
        file_formats = [
            "ascii", "binary"
        ]
        
        field_classes = [
            "dictionary", "volScalarField", "volVectorField", "volTensorField", 
            "surfaceScalarField", "surfaceVectorField", "pointScalarField", 
            "pointVectorField", "volSymmTensorField"
        ]
        
        # === SOLVERS & APPLICATIONS ===
        solvers = [
            "PCG", "PBiCG", "PBiCGStab", "GAMG", "smoothSolver", "ICCG", 
            "deflatedPCG", "diagonal", "GaussSeidel", "symGaussSeidel"
        ]
        
        applications = [
            "icoFoam", "simpleFoam", "pisoFoam", "pimpleFoam", "interFoam", 
            "buoyantFoam", "chtMultiRegionFoam", "rhoPimpleFoam", "sonicFoam",
            "blockMesh", "checkMesh", "decomposePar", "reconstructPar"
        ]
        
        # === PRECONDITIONERS & SMOOTHERS ===
        preconditioners = [
            "DIC", "DILU", "FDIC", "diagonal", "none", "GAMG", 
            "GaussSeidel", "symGaussSeidel"
        ]
        
        # === BOUNDARY TYPES & CONDITIONS ===
        boundary_types = [
            "wall", "patch", "inlet", "outlet", "symmetryPlane", "empty", 
            "cyclic", "cyclicAMI", "processor", "wedge", "symmetry"
        ]
        
        boundary_conditions = [
            "fixedValue", "zeroGradient", "noSlip", "slip", "fixedGradient",
            "mixed", "inletOutlet", "outletInlet", "pressureInletOutletVelocity",
            "totalPressure", "fixedFluxPressure", "freestreamPressure"
        ]
        
        # === NUMERICAL SCHEMES ===
        time_schemes = [
            "Euler", "backward", "CrankNicolson", "steadyState"
        ]
        
        grad_schemes = [
            "Gauss", "leastSquares", "linear", "limitedLinear", "cellLimited",
            "faceLimited", "pointLinear"
        ]
        
        div_schemes = [
            "Gauss", "linear", "limitedLinear", "upwind", "limitedLinearV", 
            "LUST", "linearUpwind", "vanLeer", "MUSCL", "limitedCubic",
            "linearUpwindV", "Minmod", "vanAlbada"
        ]
        
        laplacian_schemes = [
            "Gauss", "linear", "orthogonal", "corrected", "limited", 
            "limitedLinear", "uncorrected"
        ]
        
        interpolation_schemes = [
            "linear", "linearUpwind", "upwind", "MUSCL", "Minmod", 
            "vanLeer", "harmonic", "midPoint"
        ]
        
        sngrad_schemes = [
            "orthogonal", "corrected", "limited", "limitedLinear", 
            "uncorrected", "skewCorrected"
        ]
        
        # === MESH & GEOMETRY ===
        block_types = [
            "hex", "prism", "tet", "pyr", "wedge"
        ]
        
        grading_types = [
            "simpleGrading", "edgeGrading", "multiGrading"
        ]
        
        # === CONTROL & TIME ===
        start_from = [
            "startTime", "firstTime", "latestTime"
        ]
        
        stop_at = [
            "endTime", "writeTime", "noWriteNow", "nextWrite"
        ]
        
        write_control = [
            "timeStep", "runTime", "adjustableRunTime", "cpuTime", "clockTime"
        ]
        
        write_format = [
            "ascii", "binary"
        ]
        
        time_format = [
            "fixed", "scientific", "general"
        ]
        
        # === TURBULENCE MODELS ===
        turbulence_models = [
            "kEpsilon", "kOmega", "kOmegaSST", "LES", "RAS", "laminar", 
            "SpalartAllmaras", "realizableKE", "RNGkEpsilon", "qZeta"
        ]
        
        # === COMMON VALUES ===
        common_values = [
            "on", "off", "yes", "no", "true", "false", "uniform", "nonuniform",
            "none", "default"
        ]
        
        # === FIELD NAMES & OBJECTS ===
        field_names = [
            "p", "U", "T", "k", "epsilon", "omega", "nut", "alphat", "alpha",
            "rho", "mu", "nu", "cp", "Pr", "Prt", "phi", "phiAbs", "pcorr",
            "pFinal", "UFinal", "TFinal", "yPlus", "wallShearStress",
            "q", "H", "hs", "he", "thermo", "psi", "dpdt"
        ]
        
        # === OBJECT NAMES ===
        object_names = [
            "controlDict", "fvSchemes", "fvSolution", "blockMeshDict", 
            "snappyHexMeshDict", "decomposeParDict", "changeDictionaryDict",
            "topoSetDict", "createPatchDict", "extrudeMeshDict", "meshDict",
            "transportProperties", "turbulenceProperties", "thermophysicalProperties",
            "radiationProperties", "combustionProperties", "chemistryProperties",
            "g", "RASProperties", "LESProperties"
        ]
        
        # Combine all items into a single alphabetically sorted list
        all_items = (file_formats + field_classes + applications + solvers + 
                    preconditioners + boundary_types + boundary_conditions +
                    time_schemes + grad_schemes + div_schemes + laplacian_schemes +
                    interpolation_schemes + sngrad_schemes + block_types + 
                    grading_types + start_from + stop_at + write_control + 
                    write_format + time_format + turbulence_models + common_values +
                    field_names + object_names)
        
        # Sort alphabetically and add to list widget
        sorted_items = sorted(set(all_items))  # Remove duplicates and sort
        for item in sorted_items:
            self.items_list.addItem(item)
        
        # Don't preselect any items - let user choose
        
        list_style = """
            QListWidget {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #404040;
                color: white;
                font-size: 14px;
                font-family: Arial;
                selection-background-color: #0078d4;
            }
            QListWidget::item {
                padding: 2px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
        """
        self.items_list.setStyleSheet(list_style)
        self.items_proxy = QGraphicsProxyWidget(self)
        self.items_proxy.setWidget(self.items_list)
        
        # Default value selection (dropdown from selected items)
        self.default_label = QLabel("Default:")
        self.default_label.setStyleSheet(style)
        self.default_label_proxy = QGraphicsProxyWidget(self)
        self.default_label_proxy.setWidget(self.default_label)
        
        self.default_combo = QComboBox()
        self.default_combo.setEditable(False)  # Make it single-select only
        self.default_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        self.default_combo.setStyleSheet(combo_style)
        self.default_proxy = QGraphicsProxyWidget(self)
        self.default_proxy.setWidget(self.default_combo)
        
        # Update default combo when items selection changes
        self.items_list.itemSelectionChanged.connect(self._on_items_selection_changed)
        self.default_combo.currentTextChanged.connect(self._on_default_changed)
        
        # Initialize default options
        self._update_default_options()
    
    def _on_items_selection_changed(self):
        self._update_default_options()
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'items', self.get_selected_items())

    def get_selected_items(self):
        return [self.items_list.item(i).text() for i in range(self.items_list.count()) if self.items_list.item(i).isSelected()]

    def _on_default_changed(self, value):
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'default', value)
    
    def _update_default_options(self):
        """Update default combo options when items selection changes"""
        selected_items = []
        first_selected_row = None
        
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if item.isSelected():
                selected_items.append(item.text())
                if first_selected_row is None:
                    first_selected_row = i
        
        current_default = self.default_combo.currentText()
        self.default_combo.clear()
        
        if selected_items:
            self.default_combo.addItems(selected_items)
            
            # Try to restore previous selection
            if current_default in selected_items:
                self.default_combo.setCurrentText(current_default)
            else:
                # Set first selected item as default
                self.default_combo.setCurrentText(selected_items[0])
            
            # Scroll to the first selected item to make it visible
            if first_selected_row is not None:
                self.items_list.scrollToItem(self.items_list.item(first_selected_row))
    
    def _update_height(self):
        """Update node height and position widgets"""
        self.height = self.title_height + self.content_margin * 2 + self.get_additional_content_height()
        
        y = self.title_height + self.content_margin
        label_width = 60
        widget_width = self.width - 2 * self.content_margin - label_width - 5
        
        # Position Name widgets
        self.name_label.setFixedSize(label_width, 18)
        self.name_label_proxy.setPos(self.content_margin, y)
        self.name_edit.setFixedSize(widget_width, 18)
        self.name_proxy.setPos(self.content_margin + label_width + 5, y)
        y += 22
        
        # Position Items widgets (list widget is taller)
        self.items_label.setFixedSize(label_width, 18)
        self.items_label_proxy.setPos(self.content_margin, y)
        list_height = 120  # Increased height for more items with categories
        self.items_list.setFixedSize(widget_width, list_height)
        self.items_proxy.setPos(self.content_margin + label_width + 5, y)
        y += list_height + 4
        
        # Position Default widgets
        self.default_label.setFixedSize(label_width, 18)
        self.default_label_proxy.setPos(self.content_margin, y)
        self.default_combo.setFixedSize(widget_width, 18)
        self.default_proxy.setPos(self.content_margin + label_width + 5, y)
        
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def get_node_title(self):
        return "Enm_P"
    
    def get_additional_content_height(self):
        # 3 rows: Name (18+4), Items (120+4), Default (18)
        return 18 + 4 + 120 + 4 + 18
    
    def get_pyvnt_object(self):
        """Build PyVNT Enm_P object from current field values"""
        from pyvnt.Reference.basic import Enm_P
        
        # Get name from the name field
        name = self.name_edit.text().strip() or "enumVal"  # Default fallback
        
        # Get selected items from the list widget
        selected_items = set()
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if item.isSelected():
                selected_items.add(item.text())
        
        # If nothing is selected, return an enum with empty items set
        # The user needs to select at least one item for a valid enum
        if not selected_items:
            selected_items = set()  # Empty set
        
        # Get selected default value
        default_value = self.default_combo.currentText().strip()
        
        # Ensure default is in items (should be automatically, but just in case)
        if default_value and selected_items:
            selected_items.add(default_value)
        elif selected_items:
            default_value = list(selected_items)[0]
        else:
            default_value = ""  # No default if no items selected
        
        # Constructor call: Enm_P(name, items_set, default_value)
        return Enm_P(name, selected_items, default_value)
