from typing import TYPE_CHECKING, List, Optional, Tuple, TYPE_CHECKING
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsItem

if TYPE_CHECKING:
    from .edge import Edge  # type: ignore
    from .node_base import NodeBase  # type: ignore

class Socket(QGraphicsItem):
    """
    Represents a connection point (socket) on a node in the PyQt6 node editor.
    Handles connection rules, edge management, and visual representation.
    """
    INPUT_SOCKET = 1
    OUTPUT_SOCKET = 2

    LEFT_TOP = 1
    LEFT_CENTER = 2
    LEFT_BOTTOM = 3
    RIGHT_TOP = 4
    RIGHT_CENTER = 5
    RIGHT_BOTTOM = 6

    radius: int = 12  # Increased from 8 for better visibility and easier clicking
    outline_width: int = 3  # Increased from 2 for better visibility

    def __init__(self, node: 'NodeBase', index: int, position: int, socket_type: int, multi_connection: bool = False):
        super().__init__(node)
        self.node: 'NodeBase' = node
        self.index: int = index
        self.position: int = position
        self.socket_type: int = socket_type
        self.multi_connection: bool = multi_connection  # True for square (multi), False for circle (single)
        self.edges: List['Edge'] = []
        self.setZValue(10)  # Always on top of edges and nodes
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

    def hasEdge(self) -> bool:
        """Returns True if this socket has any connected edges."""
        return len(self.edges) > 0

    def canConnectTo(self, other_socket: 'Socket') -> bool:
        """
        Validates if a connection to another socket is allowed.
        - Only input to output
        - Not the same node
        - Not the same socket
        - Single connection sockets (circles) can have only one edge
        - Multi connection sockets (squares) can have multiple edges
        - Enforce valid parent-child rules for PyVNT hierarchy
        """
        if self is other_socket or self.node is other_socket.node:
            return False
        if self.socket_type == other_socket.socket_type:
            return False
        
        # Check single connection limits (circles can only have one edge)
        if not self.multi_connection and self.hasEdge():
            return False
        if not other_socket.multi_connection and other_socket.hasEdge():
            return False
        # Enforce node type rules for proper PyVNT hierarchy
        from nodes.node_c_graphical import Node_CGraphicalNode
        from nodes.key_c_graphical import Key_CGraphicalNode
        from nodes.enm_p_graphical import Enm_PGraphicalNode
        from nodes.int_p_graphical import Int_PGraphicalNode
        from nodes.flt_p_graphical import Flt_PGraphicalNode
        from nodes.str_p_graphical import Str_PGraphicalNode
        from nodes.vector_p_graphical import Vector_PGraphicalNode
        from nodes.dim_set_p_graphical import Dim_Set_PGraphicalNode
        from nodes.tensor_p_graphical import Tensor_PGraphicalNode
        from nodes.list_cp_graphical import List_CPGraphicalNode
        from nodes.output_graphical import OutputGraphicalNode
        
        # Input socket is always self
        input_node = self.node if self.socket_type == Socket.INPUT_SOCKET else other_socket.node
        output_node = self.node if self.socket_type == Socket.OUTPUT_SOCKET else other_socket.node
        
        # Node_C input: accepts Key_C, other Node_C, or List_CP output (for nested structure)
        if isinstance(input_node, Node_CGraphicalNode):
            return isinstance(output_node, (Key_CGraphicalNode, Node_CGraphicalNode, List_CPGraphicalNode))
        
        # Key_C input: accepts all value types and List_CP for OpenFOAM compatibility
        if isinstance(input_node, Key_CGraphicalNode):
            result = isinstance(output_node, (
                Enm_PGraphicalNode, Int_PGraphicalNode, Flt_PGraphicalNode, 
                Str_PGraphicalNode, Vector_PGraphicalNode, Dim_Set_PGraphicalNode,
                Tensor_PGraphicalNode, List_CPGraphicalNode, Node_CGraphicalNode
            ))
            return result
        
        # List_CP input: accepts Key_C, Node_C, and other List_CP for nested lists
        if isinstance(input_node, List_CPGraphicalNode):
            return isinstance(output_node, (
                Key_CGraphicalNode, Node_CGraphicalNode, List_CPGraphicalNode,
                Enm_PGraphicalNode, Int_PGraphicalNode, Flt_PGraphicalNode,
                Str_PGraphicalNode, Vector_PGraphicalNode, Dim_Set_PGraphicalNode,
                Tensor_PGraphicalNode
            ))
        
        # Output node input: accepts Node_C, Key_C, List_CP, and all value types (including Dim_Set_P)
        if isinstance(input_node, OutputGraphicalNode):
            result = isinstance(output_node, (
                Node_CGraphicalNode, Key_CGraphicalNode, List_CPGraphicalNode,
                Enm_PGraphicalNode, Int_PGraphicalNode, Flt_PGraphicalNode,
                Str_PGraphicalNode, Vector_PGraphicalNode, Dim_Set_PGraphicalNode,
                Tensor_PGraphicalNode
            ))
            return result
        
        return True  # Allow other connections for flexibility

    def addEdge(self, edge: 'Edge') -> None:
        """Adds an edge to this socket's edge list."""
        if edge not in self.edges:
            self.edges.append(edge)
            # Notify the node that a socket was connected
            if hasattr(self.node, 'onSocketConnected'):
                try:
                    self.node.onSocketConnected(self)
                except Exception as e:
                    pass

    def removeEdge(self, edge: 'Edge') -> None:
        """Removes an edge from this socket's edge list."""
        if edge in self.edges:
            self.edges.remove(edge)
            # Notify the node that a socket was disconnected
            if hasattr(self.node, 'onSocketDisconnected'):
                try:
                    self.node.onSocketDisconnected(self)
                except Exception as e:
                    pass

    def getSocketPosition(self) -> Tuple[float, float]:
        """
        Returns the absolute scene coordinates of the center of this socket.
        """
        pos = self.scenePos() + QPointF(self.radius, self.radius)
        return (pos.x(), pos.y())

    def getOtherSocket(self, edge: 'Edge') -> Optional['Socket']:
        """
        Returns the socket on the other end of the given edge.
        """
        if edge.start_socket is self:
            return edge.end_socket
        elif edge.end_socket is self:
            return edge.start_socket
        return None

    def boundingRect(self):
        # Make the clickable area larger for easier connection
        extra = 15  # Increased from 10 pixels, for easier snapping with larger sockets
        return self.shape().boundingRect().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        if self.multi_connection:
            # Square shape for multi-connection sockets
            path.addRect(0, 0, self.radius * 2, self.radius * 2)
        else:
            # Circle shape for single-connection sockets
            path.addEllipse(0, 0, self.radius * 2, self.radius * 2)
        return path

    def paint(self, painter, option, widget=None):
        from PyQt6.QtGui import QBrush, QPen, QColor
        
        # Choose color based on socket type
        if self.socket_type == Socket.INPUT_SOCKET:
            brush = QBrush(QColor(255, 140, 0))  # Orange for input
        else:
            brush = QBrush(QColor(0, 120, 215))  # Blue for output
            
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        
        # Draw shape based on connection type
        if self.multi_connection:
            # Square for multiple connections
            painter.drawRect(0, 0, self.radius * 2, self.radius * 2)
        else:
            # Circle for single connection
            painter.drawEllipse(0, 0, self.radius * 2, self.radius * 2)

    def itemChange(self, change, value):
        """
        Handle QGraphicsItem changes, specifically position changes.
        When a socket's position changes (typically because its parent node moved),
        update all connected edges.
        """
        # If the socket's scene position changed, update all connected edges
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            for edge in self.edges[:]:  # Use copy to avoid issues if the list changes during iteration
                if edge:
                    edge.updatePath()
                    
        return super().itemChange(change, value)
