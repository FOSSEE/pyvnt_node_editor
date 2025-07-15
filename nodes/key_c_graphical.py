"""Key_CGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainterPath
from nodes.base_graphical_node import BaseGraphicalNode


class Key_CGraphicalNode(BaseGraphicalNode):
    def _flatten(self, items):
        """Recursively flatten a nested list/tuple structure, handling List_CP objects."""
        for x in items:
            # Detect List_CP by class name (no direct import)
            if x.__class__.__name__ == "List_CP":
                # For node lists, flatten .children
                if hasattr(x, "is_a_node") and x.is_a_node():
                    yield from self._flatten(getattr(x, "children", []))
                # For value lists, flatten .get_elems()
                elif hasattr(x, "get_elems"):
                    yield from self._flatten(x.get_elems())
                else:
                    yield x
            elif isinstance(x, (list, tuple)):
                yield from self._flatten(x)
            else:
                yield x
    """
    Graphical node representing a PyVNT Key_C object.
    
    Features:
    - Inherits professional styling from BaseGraphicalNode
    - Multiple input sockets (squares) on lower left - accepts Value_P (Int_P, Flt_P, Enm_P)
    - Single output socket (circle) on upper right - connects to Node_C
    - Name editing widget
    - Lazy evaluation PyVNT object creation
    """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        # Key_C specific setup
        self.width = 200  # Increased from 160 for better visibility
        
        # Create name widget using base class method
        self.create_name_widget("default_key", "e.g., solver, tolerance")
        
        # Add sockets: one multi-input, one single-output
        self.add_input_socket(multi_connection=True)   # Square - can accept multiple Value_P
        self.add_output_socket(multi_connection=False) # Circle - single connection to Node_C
        
        # Update height after adding content
        self._update_height()
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Key_C"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Key_C object from current UI state + connected inputs.
        This method is only called when data is actually needed (e.g., file generation).
        Allows List_CP as a valid value for Key_C.
        """
        from pyvnt.Container.key import Key_C

        current_name = self.name_edit.text().strip()
        if not current_name:
            current_name = "unnamed_key"

        connected_values = []
        for socket in self.input_sockets:
            for edge in getattr(socket, 'edges', []):
                other_socket = edge.getOtherSocket(socket)
                if other_socket and hasattr(other_socket, 'node'):
                    connected_node = other_socket.node
                    if hasattr(connected_node, 'get_pyvnt_object'):
                        try:
                            value_obj = connected_node.get_pyvnt_object()
                            print(f"[Key_CGraphicalNode] Got value from connected node: {type(value_obj).__name__} | {value_obj}")
                            if value_obj is not None:
                                connected_values.append(value_obj)
                        except Exception as e:
                            print(f"Warning: Failed to get PyVNT object from connected value node: {e}")

        print(f"[Key_CGraphicalNode] All connected values: {[type(v).__name__ for v in connected_values]}")
        # If any value is a List_CP, pass it directly (do not flatten)
        if connected_values and any(x.__class__.__name__ == "List_CP" for x in connected_values):
            listcp_values = [x for x in connected_values if x.__class__.__name__ == "List_CP"]
            print(f"[Key_CGraphicalNode] Passing List_CP values directly: {listcp_values}")
            return Key_C(current_name, *listcp_values)
        else:
            flat_values = list(self._flatten(connected_values))
            print(f"[Key_CGraphicalNode] Passing flattened values: {flat_values}")
            if flat_values:
                return Key_C(current_name, *flat_values)
            else:
                return Key_C(current_name)
