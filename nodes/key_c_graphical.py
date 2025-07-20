"""Key_CGraphicalNode class for PyQt6 node editor"""

from PyQt6.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainterPath
from nodes.base_graphical_node import BaseGraphicalNode


class Key_CGraphicalNode(BaseGraphicalNode):
    def __init__(self, parent=None):
        super().__init__()
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
        # Element ordering state
        self.custom_element_order = None
        # Update height after adding content
        self._update_height()

    def show_context_menu(self, event):
        """Override to add custom context menu for Key_C operations"""
        from PyQt6.QtWidgets import QMenu, QMessageBox
        from PyQt6.QtGui import QAction
        menu = QMenu()
        # Add standard delete action from parent
        delete_action = QAction("Delete Node", menu)
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)
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
        """Show dialog to set element order for Key_C"""
        from PyQt6.QtWidgets import QMessageBox, QDialog
        try:
            from view.element_order_dialog import ElementOrderDialog
            # Get all connected element names
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
        from PyQt6.QtWidgets import QMessageBox
        self.custom_element_order = None
        if self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)
        QMessageBox.information(
            None,
            "Order Reset",
            f"Element order reset to default for {self.name_edit.text()}"
        )

    def get_connected_element_names(self):
        """Get names of all elements connected to this node (for ordering)"""
        element_names = []
        for socket in self.input_sockets:
            for edge in getattr(socket, 'edges', []):
                other_socket = edge.getOtherSocket(socket)
                if other_socket and hasattr(other_socket, 'node'):
                    connected_node = other_socket.node
                    if hasattr(connected_node, 'name_edit'):
                        name = connected_node.name_edit.text().strip()
                        if name:
                            element_names.append(name)
        return element_names
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Key_C"
    
    def get_pyvnt_object(self):
        """
        Lazy evaluation: Build PyVNT Key_C object from current UI state + connected inputs.
        This method is only called when data is actually needed (e.g., file generation).
        Allows List_CP as a valid value for Key_C.
        Applies custom element order if set.
        """
        from pyvnt.Container.key import Key_C

        current_name = self.name_edit.text().strip()
        if not current_name:
            current_name = "unnamed_key"

        # Collect connected values and their names
        connected_values = []
        value_name_map = {}
        for socket in self.input_sockets:
            for edge in getattr(socket, 'edges', []):
                other_socket = edge.getOtherSocket(socket)
                if other_socket and hasattr(other_socket, 'node'):
                    connected_node = other_socket.node
                    if hasattr(connected_node, 'get_pyvnt_object'):
                        try:
                            value_obj = connected_node.get_pyvnt_object()
                            if value_obj is not None:
                                connected_values.append(value_obj)
                                # Map name for ordering
                                if hasattr(connected_node, 'name_edit'):
                                    name = connected_node.name_edit.text().strip()
                                    if name:
                                        value_name_map[name] = value_obj
                        except Exception as e:
                            print(f"Warning: Failed to get PyVNT object from connected value node: {e}")

        # Apply custom element order if defined
        ordered_values = None
        if self.custom_element_order is not None:
            # Only include values that are still connected
            ordered_values = [value_name_map[name] for name in self.custom_element_order if name in value_name_map]
            # Add any remaining values not in the order list
            for name, val in value_name_map.items():
                if name not in self.custom_element_order:
                    ordered_values.append(val)
        else:
            ordered_values = connected_values

        # If any value is a List_CP, pass it directly (do not flatten)
        if ordered_values and any(x.__class__.__name__ == "List_CP" for x in ordered_values):
            listcp_values = [x for x in ordered_values if x.__class__.__name__ == "List_CP"]
            return Key_C(current_name, *listcp_values)
        else:
            flat_values = list(self._flatten(ordered_values))
            if flat_values:
                return Key_C(current_name, *flat_values)
            else:
                return Key_C(current_name)

    def onSocketConnected(self, socket):
        # When a new element is connected, refresh element order in panel
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)

    def onSocketDisconnected(self, socket):
        # When an element is disconnected, refresh element order in panel
        if hasattr(self, 'on_property_changed') and self.on_property_changed:
            self.on_property_changed(self, 'element_order', self.custom_element_order)
