"""Command system for undo/redo functionality in the node editor"""

from abc import ABC, abstractmethod
from PyQt6.QtCore import QPointF
from typing import Any, Dict, List, Optional


class Command(ABC):
    """Abstract base class for all commands that can be undone/redone"""
    
    def __init__(self, description: str = ""):
        self.description = description
        self._executed = False
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command. Returns True if successful."""
        pass
    
    def redo(self) -> bool:
        """Redo the command. Default implementation calls execute."""
        return self.execute()
    
    def is_executed(self) -> bool:
        """Returns True if the command has been executed."""
        return self._executed
    
    def __str__(self):
        return self.description or self.__class__.__name__


class CreateNodeCommand(Command):
    """Command for creating a new node"""
    
    def __init__(self, scene, node_type: str, position: QPointF, description: str = ""):
        super().__init__(description or f"Create {node_type}")
        self.scene = scene
        self.node_type = node_type
        self.position = position
        self.node = None
        
    def execute(self) -> bool:
        """Create the node"""
        try:
            self.node = self.scene.create_node(self.node_type, self.position)
            if self.node:
                self._executed = True
                return True
            return False
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Remove the created node"""
        try:
            if self.node and self.node.scene():
                # Remove all connected edges first
                self._remove_node_edges()
                self.scene.removeItem(self.node)
                self._executed = False
                return True
            return False
        except Exception:
            return False
    
    def _remove_node_edges(self):
        """Remove all edges connected to this node"""
        if not hasattr(self.node, 'input_sockets') or not hasattr(self.node, 'output_sockets'):
            return
            
        edges_to_remove = []
        
        # Collect edges from input sockets
        for socket in self.node.input_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])
        
        # Collect edges from output sockets
        for socket in self.node.output_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])
        
        # Remove all edges
        for edge in edges_to_remove:
            if hasattr(edge, 'remove'):
                edge.remove()


class DeleteNodeCommand(Command):
    """Command for deleting a node"""
    
    def __init__(self, scene, node, description: str = ""):
        super().__init__(description or f"Delete {type(node).__name__}")
        self.scene = scene
        self.node = node
        self.node_type = type(node).__name__.replace('GraphicalNode', '').replace('_', '_').replace('C', 'C').replace('P', 'P')
        self.position = node.pos()
        self.node_data = self._capture_node_data()
        self.connected_edges = []
        
    def _capture_node_data(self) -> Dict[str, Any]:
        """Capture the node's current state"""
        data = {}
        
        # Capture name if it exists
        if hasattr(self.node, 'name_edit') and self.node.name_edit:
            data['name'] = self.node.name_edit.text()
        
        # Capture other node-specific data
        if hasattr(self.node, 'get_pyvnt_object'):
            try:
                data['pyvnt_object'] = self.node.get_pyvnt_object()
            except:
                pass
        
        return data
    
    def execute(self) -> bool:
        """Delete the node"""
        try:
            if self.node and self.node.scene():
                # Store connected edges before deletion
                self._store_connected_edges()
                
                # Remove all connected edges
                self._remove_node_edges()
                
                # Remove the node
                self.scene.removeItem(self.node)
                self._executed = True
                return True
            return False
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Recreate the deleted node"""
        try:
            # Recreate the node
            self.node = self.scene.create_node(self.node_type, self.position)
            if not self.node:
                return False
            
            # Restore node data
            self._restore_node_data()
            
            # Restore connected edges
            self._restore_connected_edges()
            
            self._executed = False
            return True
        except Exception:
            return False
    
    def _store_connected_edges(self):
        """Store information about connected edges"""
        self.connected_edges = []
        
        if not hasattr(self.node, 'input_sockets') or not hasattr(self.node, 'output_sockets'):
            return
        
        # Store input socket connections
        for i, socket in enumerate(self.node.input_sockets):
            if hasattr(socket, 'edges'):
                for edge in socket.edges:
                    if hasattr(edge, 'start_socket') and hasattr(edge, 'end_socket'):
                        # The input socket of this node is the end_socket
                        other_socket = edge.start_socket
                        edge_info = {
                            'other_node': other_socket.node,
                            'other_socket_index': other_socket.index,
                            'other_socket_is_input': other_socket.socket_type == other_socket.INPUT_SOCKET,
                            'this_socket_index': i,
                            'this_socket_is_input': True
                        }
                        self.connected_edges.append(edge_info)
        
        # Store output socket connections
        for i, socket in enumerate(self.node.output_sockets):
            if hasattr(socket, 'edges'):
                for edge in socket.edges:
                    if hasattr(edge, 'start_socket') and hasattr(edge, 'end_socket'):
                        # The output socket of this node is the start_socket
                        other_socket = edge.end_socket
                        edge_info = {
                            'other_node': other_socket.node,
                            'other_socket_index': other_socket.index,
                            'other_socket_is_input': other_socket.socket_type == other_socket.INPUT_SOCKET,
                            'this_socket_index': i,
                            'this_socket_is_input': False
                        }
                        self.connected_edges.append(edge_info)
    
    def _remove_node_edges(self):
        """Remove all edges connected to this node"""
        if not hasattr(self.node, 'input_sockets') or not hasattr(self.node, 'output_sockets'):
            return
            
        edges_to_remove = []
        
        # Collect edges from input sockets
        for socket in self.node.input_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])
        
        # Collect edges from output sockets
        for socket in self.node.output_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])
        
        # Remove all edges
        for edge in edges_to_remove:
            if hasattr(edge, 'remove'):
                edge.remove()
    
    def _restore_node_data(self):
        """Restore the node's data"""
        if not self.node_data:
            return
        
        # Restore name
        if 'name' in self.node_data and hasattr(self.node, 'name_edit') and self.node.name_edit:
            self.node.name_edit.setText(self.node_data['name'])
    
    def _restore_connected_edges(self):
        """Restore the edges that were connected to this node"""
        if not self.connected_edges:
            return
        
        from view.edge import Edge
        
        for edge_info in self.connected_edges:
            try:
                # Get the other node
                other_node = edge_info['other_node']
                
                # Skip if the other node doesn't exist anymore
                if not other_node:
                    continue
                
                # Get socket indices
                other_socket_index = edge_info['other_socket_index']
                other_socket_is_input = edge_info['other_socket_is_input']
                this_socket_index = edge_info['this_socket_index']
                this_socket_is_input = edge_info['this_socket_is_input']
                
                # Get the other socket
                other_socket = None
                if other_socket_is_input and hasattr(other_node, 'input_sockets'):
                    if other_socket_index < len(other_node.input_sockets):
                        other_socket = other_node.input_sockets[other_socket_index]
                elif not other_socket_is_input and hasattr(other_node, 'output_sockets'):
                    if other_socket_index < len(other_node.output_sockets):
                        other_socket = other_node.output_sockets[other_socket_index]
                
                # Get this node's socket
                this_socket = None
                if this_socket_is_input and hasattr(self.node, 'input_sockets'):
                    if this_socket_index < len(self.node.input_sockets):
                        this_socket = self.node.input_sockets[this_socket_index]
                elif not this_socket_is_input and hasattr(self.node, 'output_sockets'):
                    if this_socket_index < len(self.node.output_sockets):
                        this_socket = self.node.output_sockets[this_socket_index]
                
                # Create edge if both sockets exist
                if other_socket and this_socket:
                    # Determine start and end sockets (output -> input)
                    if this_socket_is_input:
                        # This socket is input, other socket is output
                        start_socket = other_socket
                        end_socket = this_socket
                    else:
                        # This socket is output, other socket is input
                        start_socket = this_socket
                        end_socket = other_socket
                    
                    edge = Edge(start_socket, end_socket, self.scene)
                    edge.setParentItem(None)
                    edge.updatePath()
                    self.scene.addItem(edge)
                    
            except Exception as e:
                continue


class MoveNodeCommand(Command):
    """Command for moving a node"""
    
    def __init__(self, node, old_position: QPointF, new_position: QPointF, description: str = ""):
        super().__init__(description or "Move Node")
        self.node = node
        self.old_position = old_position
        self.new_position = new_position
        
    def execute(self) -> bool:
        """Move the node to new position"""
        try:
            self.node.setPos(self.new_position)
            self._executed = True
            return True
        except Exception as e:
            return False
    
    def undo(self) -> bool:
        """Move the node back to old position"""
        try:
            self.node.setPos(self.old_position)
            self._executed = False
            return True
        except Exception as e:
            return False


class CreateEdgeCommand(Command):
    """Command for creating an edge between two sockets"""
    
    def __init__(self, scene, start_socket, end_socket, description: str = ""):
        super().__init__(description or "Create Connection")
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.edge = None
        
    def execute(self) -> bool:
        """Create the edge"""
        try:
            # Validate sockets are still valid
            if not self.start_socket or not self.end_socket:
                return False
                
            from view.edge import Edge
            self.edge = Edge(self.start_socket, self.end_socket, self.scene)
            self.edge.setParentItem(None)
            self.edge.updatePath()
            self.scene.addItem(self.edge)
            # Ensure event filters are properly installed now that the edge is in the scene
            self.edge.ensure_event_filters()
            self._executed = True
            
            return True
        except Exception as e:
            return False
    
    def undo(self) -> bool:
        """Remove the edge"""
        try:
            if self.edge and hasattr(self.edge, 'start_socket') and hasattr(self.edge, 'end_socket'):
                # Store socket references before removal
                start_sock = self.edge.start_socket
                end_sock = self.edge.end_socket
                
                # Remove edge from sockets first
                if start_sock and hasattr(start_sock, 'removeEdge'):
                    start_sock.removeEdge(self.edge)
                if end_sock and hasattr(end_sock, 'removeEdge'):
                    end_sock.removeEdge(self.edge)
                
                # Remove from scene
                if self.edge.scene():
                    self.edge.scene().removeItem(self.edge)
                
                self._executed = False
                return True
            return False
        except Exception as e:
            return False


class DeleteEdgeCommand(Command):
    """Command for deleting an edge"""
    
    def __init__(self, edge, description: str = ""):
        super().__init__(description or "Delete Connection")
        self.edge = edge
        # Store socket references before they get nullified
        self.start_socket = edge.start_socket
        self.end_socket = edge.end_socket
        self.scene = edge.scene()
        
    def execute(self) -> bool:
        """Delete the edge"""
        try:
            if self.edge and hasattr(self.edge, 'start_socket') and hasattr(self.edge, 'end_socket'):
                # Remove edge from sockets first
                if self.edge.start_socket and hasattr(self.edge.start_socket, 'removeEdge'):
                    self.edge.start_socket.removeEdge(self.edge)
                if self.edge.end_socket and hasattr(self.edge.end_socket, 'removeEdge'):
                    self.edge.end_socket.removeEdge(self.edge)
                
                # Remove from scene
                if self.edge.scene():
                    self.edge.scene().removeItem(self.edge)
                
                self._executed = True
                return True
            return False
        except Exception as e:
            return False
    
    def undo(self) -> bool:
        """Recreate the edge"""
        try:
            # Validate sockets are still valid
            if not self.start_socket or not self.end_socket:
                return False
                
            from view.edge import Edge
            self.edge = Edge(self.start_socket, self.end_socket, self.scene)
            self.edge.setParentItem(None)
            self.edge.updatePath()
            self.scene.addItem(self.edge)
            self._executed = False
            return True
        except Exception as e:
            return False


class ChangeNodePropertyCommand(Command):
    """Command for changing a node property (e.g., name change)"""
    
    def __init__(self, node, property_name: str, old_value: Any, new_value: Any, description: str = ""):
        super().__init__(description or f"Change {property_name}")
        self.node = node
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        
    def execute(self) -> bool:
        """Change the property to new value"""
        try:
            self._set_property(self.new_value)
            self._executed = True
            return True
        except Exception as e:
            return False
    
    def undo(self) -> bool:
        """Change the property back to old value"""
        try:
            self._set_property(self.old_value)
            self._executed = False
            return True
        except Exception as e:
            return False
    
    def _set_property(self, value):
        """Set the property value"""
        if self.property_name == 'name' and hasattr(self.node, 'name_edit'):
            self.node.name_edit.setText(str(value))
        else:
            # For other properties, use setattr
            setattr(self.node, self.property_name, value)


class CompositeCommand(Command):
    """Command that combines multiple commands into one operation"""
    
    def __init__(self, commands: List[Command], description: str = ""):
        super().__init__(description or "Multiple Operations")
        self.commands = commands
        
    def execute(self) -> bool:
        """Execute all commands in order"""
        executed_commands = []
        try:
            for command in self.commands:
                if command.execute():
                    executed_commands.append(command)
                else:
                    # If any command fails, undo all executed commands
                    for cmd in reversed(executed_commands):
                        cmd.undo()
                    return False
            
            self._executed = True
            return True
        except Exception as e:
            # Undo any partially executed commands
            for cmd in reversed(executed_commands):
                try:
                    cmd.undo()
                except:
                    pass
            return False
    
    def undo(self) -> bool:
        """Undo all commands in reverse order"""
        try:
            for command in reversed(self.commands):
                if command.is_executed():
                    if not command.undo():
                        return False
            
            self._executed = False
            return True
        except Exception as e:
            return False
