"""Node_CGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QMenu, QMessageBox, QDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from nodes.base_graphical_node import BaseGraphicalNode


class Node_CGraphicalNode(BaseGraphicalNode):
    """
    Graphical node representing a PyVNT Node_C object.
    
    Features:
    - Inherits professional styling from BaseGraphicalNode
    - Multiple input sockets (squares) on lower left - accepts Key_C and Node_C
    - Single output socket (circle) on upper right - connects to Node_C or Output
    - Name editing widget
    - Lazy evaluation PyVNT object creation
    - Custom element ordering for file output
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Node_C specific setup
        self.width = 220  # Increased from 180 for better visibility
        # Create name widget
        self.create_name_widget("default_node", "Node name...")
        
        # Initialize with one input socket (square - can accept multiple connections) and one output socket
        self.add_input_socket(multi_connection=True)   # Square - can accept multiple Key_C/Node_C
        self.add_output_socket(multi_connection=False) # Circle - single connection to Node_C/Output
        
        # Element ordering state
        self.custom_element_order = None
        
        # Update height after adding content
        self._update_height()
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Node_C"
    
    def get_additional_content_height(self):
        """Add height for the name widget"""
        return 18 + 4  # Name widget height + spacing
        
    def show_context_menu(self, event):
        """Override to add custom context menu for Node_C operations"""
        menu = QMenu()
        
        # Add standard delete action from parent
        delete_action = QAction("Delete Node", menu)
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add element order action
        order_action = QAction("Set Element Order...", menu)
        order_action.triggered.connect(self.show_element_order_dialog)
        menu.addAction(order_action)
        
        # Add a reset element order action
        if self.custom_element_order is not None:
            reset_action = QAction("Reset Element Order", menu)
            reset_action.triggered.connect(self.reset_element_order)
            menu.addAction(reset_action)
        
        # Show the menu at cursor position
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            global_pos = view.mapToGlobal(view.mapFromScene(event.scenePos()))
            menu.exec(global_pos)
        
    def show_element_order_dialog(self):
        """Show dialog to set element order"""
        try:
            from view.element_order_dialog import ElementOrderDialog
            
            # Get all connected elements (Key_C and Node_C)
            connected_elements = self.get_connected_element_names()
            if not connected_elements:
                QMessageBox.information(
                    None,
                    "No Elements",
                    "This node has no connected elements to order."
                )
                return
            # Use custom order if set, else default
            if self.custom_element_order:
                order_names = [name for name in self.custom_element_order if name in connected_elements]
                # Add any new elements not in the custom order
                for name in connected_elements:
                    if name not in order_names:
                        order_names.append(name)
            else:
                order_names = connected_elements
            dialog = ElementOrderDialog(
                parent=None,
                node_data=order_names,
                title=f"Set Element Order for {self.name_edit.text()}"
            )
            
            # Show dialog and get results
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.custom_element_order = dialog.get_ordered_elements()
                if self.on_property_changed:
                    self.on_property_changed(self, 'element_order', self.custom_element_order)
                QMessageBox.information(
                    None,
                    "Order Set",
                    f"Custom element order set for {self.name_edit.text()}"
                )
            
        except Exception as e:
            QMessageBox.warning(
                None,
                "Error",
                f"An error occurred: {str(e)}"
            )
    
    def reset_element_order(self):
        """Reset any custom element order"""
        self.custom_element_order = None
        if self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)
        QMessageBox.information(
            None,
            "Order Reset",
            f"Element order reset to default for {self.name_edit.text()}"
        )
        
    def get_connected_element_names(self):
        """Get names of all elements connected to this node"""
        element_names = []
        
        # Scan all input sockets
        for socket in self.input_sockets:
            for edge in getattr(socket, 'edges', []):
                other_socket = edge.getOtherSocket(socket)
                if other_socket and hasattr(other_socket, 'node'):
                    connected_node = other_socket.node
                    # Get name from connected node
                    if hasattr(connected_node, 'name_edit'):
                        name = connected_node.name_edit.text().strip()
                        if name:
                            element_names.append(name)
        
        return element_names
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Node_C object from current UI state + connected inputs.
        This method is only called when data is actually needed (e.g., file generation).
        """
        try:
            from pyvnt.Container.node import Node_C
            from pyvnt.Container.key import Key_C
            from pyvnt.Container.list import List_CP
        except ImportError:
            # Fall back to different import paths if needed
            try:
                from pyvnt import Node_C, Key_C, List_CP
            except ImportError:
                print("Warning: Could not import Node_C, Key_C, and List_CP from pyvnt")
                return None
        
        # Create fresh Node_C with current name from UI
        current_name = self.name_edit.text().strip()
        if not current_name:
            current_name = "unnamed_node"
        
        # Create new PyVNT object (don't reuse the old one to avoid state issues)
        pyvnt_node = Node_C(current_name)
        
        # Keep track of connected elements and their objects for potential reordering
        element_objects = {}
        
        # Recursively collect children from connected input sockets
        for socket in self.input_sockets:
            for edge in getattr(socket, 'edges', []):
                other_socket = edge.getOtherSocket(socket)
                if other_socket and hasattr(other_socket, 'node'):
                    connected_node = other_socket.node
                    # Recursively ask connected node for its PyVNT object
                    if hasattr(connected_node, 'get_pyvnt_object'):
                        try:
                            child_obj = connected_node.get_pyvnt_object()
                            if child_obj is not None:
                                # Store object with its name for potential reordering later
                                if hasattr(connected_node, 'name_edit'):
                                    element_name = connected_node.name_edit.text().strip()
                                    if element_name:
                                        element_objects[element_name] = child_obj
                                
                                # Node_C can have Node_C children, but Key_C need to be added as data
                                # List_CP should be wrapped in Key_C before adding as data
                                if isinstance(child_obj, Node_C):
                                    pyvnt_node.add_child(child_obj)
                                elif isinstance(child_obj, Key_C):
                                    # Add Key_C as data to this node
                                    pyvnt_node.add_data(child_obj)
                                elif isinstance(child_obj, List_CP):
                                    # List_CP should be wrapped in a Key_C before adding to Node_C
                                    # This shouldn't happen if the node structure is correct
                                    # List_CP should be connected to Key_C, then Key_C to Node_C
                                    print(f"Warning: List_CP '{child_obj.name}' should be connected to a Key_C node, not directly to Node_C")
                                else:
                                    # Try to add as data first, then warn if it fails
                                    try:
                                        pyvnt_node.add_data(child_obj)
                                    except Exception as add_error:
                                        print(f"Warning: Connected node returned unrecognized type: {type(child_obj).__name__}")
                                        print(f"         Error details: {add_error}")
                        except Exception as e:
                            # If child fails to build, continue with others
                            node_type = type(connected_node).__name__ if connected_node else "Unknown"
                            print(f"Warning: Failed to get PyVNT object from connected node (type: {node_type}): {e}")
        
        # Apply custom element order if defined
        if self.custom_element_order is not None and hasattr(pyvnt_node, 'set_order'):
            try:
                # Filter out names that don't exist
                valid_names = [name for name in self.custom_element_order if name in element_objects]
                if valid_names:
                    pyvnt_node.set_order(valid_names)
                    print(f"Applied custom element order: {valid_names}")
            except Exception as e:
                print(f"Warning: Failed to apply custom element order: {e}")
        
        return pyvnt_node
    
    def onSocketConnected(self, socket):
        # When a new element is connected, refresh element order in panel
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)

    def onSocketDisconnected(self, socket):
        # When an element is disconnected, refresh element order in panel
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)
