from PyQt6.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from typing import Optional
from nodes.base_graphical_node import BaseGraphicalNode
from pyvnt.Converter.Writer.writer import writeTo

class OutputGraphicalNode(BaseGraphicalNode):
    """
    Terminal node for OpenFOAM file generation using PyVNT.
    Visual node with a single input socket and file generation controls.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 240  # Increased from 200 for better visibility
        
        # Output node has input socket (for receiving data) and output socket (for chaining to case folder)
        self.add_input_socket(multi_connection=True)
        self.add_output_socket(multi_connection=True)  # Add output socket for case folder connection
        
        # Create the UI widgets
        self._create_widgets()
        
        # Update height based on content
        self._update_height()
    
    def get_additional_content_height(self):
        """Return the height needed for output-specific widgets"""
        # Add height for: validate button (24+4) + generate button (24+4) + status (18)
        return 24 + 4 + 24 + 4 + 18
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Output"

    def _create_widgets(self):
        # Filename input field
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("Optional filename (without extension)")
        self.filename_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px 6px;
                background-color: #2a2a2a;
                color: white;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #0078d4; }
        """)
        self.filename_proxy = QGraphicsProxyWidget(self)
        self.filename_proxy.setWidget(self.filename_edit)
        
        self.validate_button = QPushButton("Validate")
        self.validate_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; border-radius: 3px; padding: 4px 10px; font-size: 12px; font-family: Arial; } QPushButton:pressed { background-color: #005fa3; }")
        self.validate_button.clicked.connect(self.validate_input)
        self.validate_proxy = QGraphicsProxyWidget(self)
        self.validate_proxy.setWidget(self.validate_button)
        
        self.generate_button = QPushButton("Generate File")
        self.generate_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; border-radius: 3px; padding: 4px 10px; font-size: 12px; font-family: Arial; } QPushButton:pressed { background-color: #1e7e34; }")
        self.generate_button.clicked.connect(self.generate_file)
        self.generate_proxy = QGraphicsProxyWidget(self)
        self.generate_proxy.setWidget(self.generate_button)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: white; 
            font-size: 10px; 
            font-family: Arial; 
            padding: 3px; 
            background: rgba(0,0,0,0.2);
            border-radius: 3px;
        """)
        self.status_label.setWordWrap(True)
        self.status_proxy = QGraphicsProxyWidget(self)
        self.status_proxy.setWidget(self.status_label)

    def _update_height(self):
        """Update the node's height to accommodate all widgets including the status label"""
        y = self.title_height + self.content_margin
        
        # Position filename input
        self.filename_edit.setFixedSize(self.width - 2 * self.content_margin, 22)
        self.filename_proxy.setPos(self.content_margin, y)
        y += 22 + 4
        
        # Position validate button
        self.validate_button.setFixedSize(self.width - 2 * self.content_margin, 24)
        self.validate_proxy.setPos(self.content_margin, y)
        y += 24 + 4
        
        # Position generate button
        self.generate_button.setFixedSize(self.width - 2 * self.content_margin, 24)
        self.generate_proxy.setPos(self.content_margin, y)
        y += 24 + 4
        
        # Position status label
        status_width = self.width - 2 * self.content_margin
        self.status_label.setFixedWidth(status_width)
        self.status_label.setWordWrap(True)
        self.status_label.adjustSize()
        
        label_text = self.status_label.text()
        if label_text:
            label_height = max(18, self.status_label.sizeHint().height() + 4)
        else:
            label_height = 18
            
        self.status_label.setFixedHeight(label_height)
        self.status_proxy.setPos(self.content_margin, y)
        
        y += label_height + self.content_margin
        self.height = y
        
        # Position sockets after height update
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def _validate_pyvnt_tree(self, node, depth=0, max_depth=10):
        """
        Recursively validate the PyVNT object tree to ensure it can generate valid output.
        Returns dict with 'valid' boolean and 'message' string.
        Adds debug output and always treats List_CP as valid.
        """
        print(f"DEBUG: Validating node at depth {depth}: {type(node).__name__}")
        try:
            from pyvnt.Reference.basic import Int_P, Flt_P, Enm_P, Str_P
            from pyvnt.Reference.vector import Vector_P
            from pyvnt.Reference.dimension_set import Dim_Set_P
            from pyvnt.Reference.tensor import Tensor_P
            from pyvnt.Container.list import List_CP
            from pyvnt.Container.node import Node_C
            from pyvnt.Container.key import Key_C as PyVNT_Key_C
        except ImportError:
            Int_P = Flt_P = Enm_P = Str_P = Vector_P = Dim_Set_P = Tensor_P = List_CP = Node_C = PyVNT_Key_C = type(None)

        if depth > max_depth:
            return {"valid": False, "message": "Tree is too deep (possible circular reference)"}

        # Node_C
        if isinstance(node, Node_C):
            if not hasattr(node, 'name') or not node.name or not str(node.name).strip():
                return {"valid": False, "message": f"Node_C at depth {depth} has no name"}
            has_children = hasattr(node, 'children') and len(node.children) > 0
            has_data = hasattr(node, 'data') and len(node.data) > 0
            if not has_children and not has_data:
                print(f"Warning: Node_C '{node.name}' has no children or data. It will generate an empty block.")
            if has_children:
                for i, child in enumerate(node.children):
                    child_result = self._validate_pyvnt_tree(child, depth + 1, max_depth)
                    if not child_result["valid"]:
                        return {"valid": False, "message": f"In Node_C '{node.name}' → Child {i+1}: {child_result['message']}"}
            if has_data:
                for i, data_item in enumerate(node.data):
                    data_result = self._validate_pyvnt_tree(data_item, depth + 1, max_depth)
                    if not data_result["valid"]:
                        return {"valid": False, "message": f"In Node_C '{node.name}' → Data {i+1}: {data_result['message']}"}
        # Key_C
        elif isinstance(node, PyVNT_Key_C):
            if not hasattr(node, 'name') or not node.name or not str(node.name).strip():
                return {"valid": False, "message": f"Key_C at depth {depth} has no name"}
            try:
                if hasattr(node, '_privateDict'):
                    items = node._privateDict.items()
                elif hasattr(node, 'get_items'):
                    items = node.get_items()
                else:
                    return {"valid": False, "message": f"Key_C '{node.name}' cannot access its values"}
                if not items:
                    return {"valid": False, "message": f"Key_C '{node.name}' has no values. Connect Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P, or List_CP nodes to its inputs."}
                for i, (key, value) in enumerate(items):
                    print(f"DEBUG: Key_C '{node.name}' value '{key}' type: {type(value).__name__}")
                    # Always treat List_CP as valid
                    if isinstance(value, List_CP):
                        continue
                    # Accept all valid PyVNT types
                    valid_types = (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P, List_CP, Node_C, PyVNT_Key_C)
                    if not isinstance(value, valid_types):
                        return {"valid": False, "message": f"Key_C '{node.name}' has invalid value type: {type(value).__name__}. Expected one of: {[t.__name__ for t in valid_types]}"}
                    # Recursively validate complex values
                    if hasattr(value, '__class__') and any(ctype in value.__class__.__name__ for ctype in ['List_CP', 'Node_C', 'Key_C']):
                        child_result = self._validate_pyvnt_tree(value, depth + 1, max_depth)
                        if not child_result["valid"]:
                            return {"valid": False, "message": f"In Key_C '{node.name}' → Value '{key}': {child_result['message']}"}
            except Exception as e:
                return {"valid": False, "message": f"Key_C '{node.name}' validation error: {str(e)}"}
        # List_CP
        elif hasattr(node, '__class__') and 'List_CP' in node.__class__.__name__:
            print(f"DEBUG: List_CP node at depth {depth} is always valid.")
            # Always treat List_CP as valid
            pass
        # Value nodes (leaf nodes)
        elif (isinstance(node, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)) or 
              hasattr(node, '__class__') and any(ptype in node.__class__.__name__ for ptype in ['Int_P', 'Flt_P', 'Enm_P', 'Str_P', 'Vector_P', 'Dim_Set_P', 'Tensor_P'])):
            pass
        else:
            print(f"DEBUG: Unknown node type at depth {depth}: {type(node).__name__}")
            return {"valid": False, "message": f"Unknown PyVNT object type: {type(node).__name__}"}
        return {"valid": True, "message": "Valid"}

    def validate_input(self):
        """Validate the input PyVNT object without writing to disk"""
        try:
            if not self.input_sockets or not self.input_sockets[0].hasEdge():
                self.status_label.setText("No input node connected. Connect a Key_C or Node_C node.")
                self.status_label.setStyleSheet("""
                    color: #ff9999; 
                    font-size: 10px; 
                    font-family: Arial; 
                    padding: 3px;
                    background: rgba(40,0,0,0.3);
                    border-radius: 3px;
                """)
                self._update_height()
                return
                
            edge = self.input_sockets[0].edges[0]
            other_socket = edge.getOtherSocket(self.input_sockets[0])
            
            if other_socket is None or not hasattr(other_socket, 'node'):
                self.status_label.setText("Invalid input connection.")
                self.status_label.setStyleSheet("""
                    color: #ff9999; 
                    font-size: 10px; 
                    font-family: Arial; 
                    padding: 3px;
                    background: rgba(40,0,0,0.3);
                    border-radius: 3px;
                """)
                self._update_height()
                return
                
            connected_node = other_socket.node
            
            try:
                # Check if the connected node has a method to get a PyVNT object
                if hasattr(connected_node, 'get_pyvnt_object'):
                    head_node = connected_node.get_pyvnt_object()
                else:
                    # If no get_pyvnt_object method, see if the node itself is the PyVNT object
                    head_node = connected_node
            except Exception as e:
                self.status_label.setText(f"Error building PyVNT object: {str(e)}")
                self.status_label.setStyleSheet("""
                    color: #ff9999; 
                    font-size: 10px; 
                    font-family: Arial; 
                    padding: 3px;
                    background: rgba(40,0,0,0.3);
                    border-radius: 3px;
                """)
                self._update_height()
                return
                
            try:
                from pyvnt.Container.key import Key_C
                from pyvnt.Container.node import Node_C
                from pyvnt.Container.list import List_CP
                from pyvnt.Reference.basic import Enm_P, Int_P, Flt_P, Str_P
                from pyvnt.Reference.vector import Vector_P
                from pyvnt.Reference.dimension_set import Dim_Set_P

                # Accept all PyVNT types that can generate output, including List_CP
                valid_types = (Key_C, Node_C, List_CP, Enm_P, Int_P, Flt_P, Str_P, Vector_P, Dim_Set_P)
                if not isinstance(head_node, valid_types):
                    self.status_label.setText(f"Error: Must connect a PyVNT node. Got: {type(head_node).__name__}")
                    self.status_label.setStyleSheet("""
                        color: #ff9999; 
                        font-size: 10px; 
                        font-family: Arial; 
                        padding: 3px;
                        background: rgba(40,0,0,0.3);
                        border-radius: 3px;
                    """)
                    self._update_height()
                    return
            except ImportError as ie:
                self.status_label.setText(f"PyVNT import error: {str(ie)}. Please check PyVNT installation.")
                self.status_label.setStyleSheet("""
                    color: #ff9999; 
                    font-size: 10px; 
                    font-family: Arial; 
                    padding: 3px;
                    background: rgba(40,0,0,0.3);
                    border-radius: 3px;
                """)
                self._update_height()
                return
                
            validation_result = self._validate_pyvnt_tree(head_node)
            if not validation_result["valid"]:
                self.status_label.setText(f"Validation Error: {validation_result['message']}")
                self.status_label.setStyleSheet("""
                    color: #ff9999; 
                    font-size: 10px; 
                    font-family: Arial; 
                    padding: 3px;
                    background: rgba(40,0,0,0.3);
                    border-radius: 3px;
                """)
                self._update_height()
                return

            # Store the validated PyVNT object
            self.validated_pyvnt_object = head_node
            
            # Success message
            self.status_label.setText(f"✓ Valid PyVNT object: {head_node.name}")
            self.status_label.setStyleSheet("""
                color: #83ff83; 
                font-size: 10px; 
                font-family: Arial; 
                padding: 3px;
                background: rgba(0,40,0,0.3);
                border-radius: 3px;
            """)
            self._update_height()
                
        except Exception as e:
            self.status_label.setText(f"Validation error: {str(e)}")
            self.status_label.setStyleSheet("""
                color: #ff9999; 
                font-size: 10px; 
                font-family: Arial; 
                padding: 3px;
                background: rgba(40,0,0,0.3);
                border-radius: 3px;
            """)
            self._update_height()
    
    @property
    def output_filename(self):
        """Get the custom output filename if specified"""
        custom_name = self.filename_edit.text().strip()
        if custom_name:
            return custom_name
        return None

    def get_pyvnt_object(self):
        """Return the validated PyVNT object"""
        if hasattr(self, 'validated_pyvnt_object'):
            return self.validated_pyvnt_object
        else:
            raise RuntimeError("No validated PyVNT object. Click 'Validate' first.")
    
    def generate_file(self):
        """Generate individual file to output directory"""
        try:
            # Validate first if not already done
            if not hasattr(self, 'validated_pyvnt_object'):
                self.validate_input()
                if not hasattr(self, 'validated_pyvnt_object'):
                    return
            
            head_node = self.validated_pyvnt_object
            
            # Use output directory
            import os
            output_dir = os.path.join(os.getcwd(), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Determine the filename to use
            custom_filename = self.output_filename
            if custom_filename:
                # Use custom filename
                filename = custom_filename
                # Temporarily change the PyVNT object's name for file generation
                original_name = head_node.name
                head_node.name = filename
                
                # Generate the file using PyVNT
                writeTo(head_node, output_dir, fileType='txt')
                
                # Restore original name
                head_node.name = original_name
                
                file_path = os.path.join(output_dir, f"{filename}.txt")
            else:
                # Use default PyVNT object name
                writeTo(head_node, output_dir, fileType='txt')
                file_path = os.path.join(output_dir, f"{head_node.name}.txt")
            
            # Success message
            rel_path = os.path.relpath(file_path, os.getcwd())
            
            self.status_label.setText(f"✓ File generated: {rel_path}")
            self.status_label.setStyleSheet("""
                color: #83ff83; 
                font-size: 10px; 
                font-family: Arial; 
                padding: 3px;
                background: rgba(0,40,0,0.3);
                border-radius: 3px;
            """)
            self._update_height()
            
        except Exception as e:
            self.status_label.setText(f"Generation error: {str(e)}")
            self.status_label.setStyleSheet("""
                color: #ff9999; 
                font-size: 10px; 
                font-family: Arial; 
                padding: 3px;
                background: rgba(40,0,0,0.3);
                border-radius: 3px;
            """)
            self._update_height()
