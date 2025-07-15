from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsScene
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtCore import Qt
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .socket import Socket

class Edge(QGraphicsPathItem):
    """
    Represents a visual connection (edge) between two sockets in the node editor.
    Draws a smooth bezier curve and manages socket references and cleanup.
    """
    def __init__(self, start_socket: 'Socket', end_socket: 'Socket', scene: QGraphicsScene):
        super().__init__()
        self.start_socket: 'Socket' = start_socket
        self.end_socket: 'Socket' = end_socket
        self.scene_ref: QGraphicsScene = scene
        self.setZValue(1)
        self.setFlags(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.normal_color = QColor("#9CA3AF")
        self.selected_color = QColor("#10B981")
        self.line_width = 3  # Increased from 2 for better visibility
        self.start_socket.addEdge(self)
        self.end_socket.addEdge(self)
        
        # Set up event filters to track node movements - DISABLED to prevent Qt errors
        # self._setup_event_filters()
        
        # Don't add to scene here - let the caller handle it
        self.updatePath()

    def _setup_event_filters(self):
        """Set up event filters for tracking node movements, with comprehensive scene checking."""
        # Skip event filter setup entirely if there are any issues
        try:
            if not (self.start_socket and self.end_socket and 
                    self.start_socket.node and self.end_socket.node):
                return
                
            start_node = self.start_socket.node
            end_node = self.end_socket.node
            
            # Get scene references safely
            start_scene = None
            end_scene = None
            try:
                start_scene = start_node.scene()
                end_scene = end_node.scene()
            except:
                # If we can't get scene references, skip event filters
                return
            
            # Only proceed if both nodes are in the same scene AND that scene matches our edge scene
            if not (start_scene and end_scene and 
                    start_scene == end_scene and 
                    start_scene == self.scene_ref):
                return
            
            # Additional safety check - verify nodes are actually in the scene
            if (start_node not in start_scene.items() or 
                end_node not in end_scene.items()):
                return
                
            # Prevent duplicate event filters
            if not hasattr(start_node, '_edge_event_filters'):
                start_node._edge_event_filters = set()
            if not hasattr(end_node, '_edge_event_filters'):
                end_node._edge_event_filters = set()
            
            # Only install if not already installed
            if self not in start_node._edge_event_filters:
                start_node.installSceneEventFilter(self)
                start_node._edge_event_filters.add(self)
                
            if self not in end_node._edge_event_filters:
                end_node.installSceneEventFilter(self)
                end_node._edge_event_filters.add(self)
                
        except Exception as e:
            # Completely suppress all event filter related errors
            # The edge will still work for visual connections, just without movement tracking
            pass
            # Nodes are in different scenes, cannot install event filters
            pass

    def _cleanup_event_filters(self):
        """Clean up event filters from nodes safely."""
        try:
            if self.start_socket and self.start_socket.node:
                start_node = self.start_socket.node
                if hasattr(start_node, '_edge_event_filters') and self in start_node._edge_event_filters:
                    try:
                        start_node.removeSceneEventFilter(self)
                        start_node._edge_event_filters.discard(self)
                    except:
                        pass
                        
            if self.end_socket and self.end_socket.node:
                end_node = self.end_socket.node
                if hasattr(end_node, '_edge_event_filters') and self in end_node._edge_event_filters:
                    try:
                        end_node.removeSceneEventFilter(self)
                        end_node._edge_event_filters.discard(self)
                    except:
                        pass
        except:
            # Ignore all cleanup errors
            pass

    def ensure_event_filters(self):
        """Ensure event filters are installed. Call this after adding edge to scene."""
        # DISABLED to prevent Qt Graphics Scene errors
        # self._setup_event_filters()
        pass

    def updatePath(self):
        """Recalculates and redraws the bezier curve path between sockets."""
        start_pos = self.start_socket.getSocketPosition()
        end_pos = self.end_socket.getSocketPosition()
        sx, sy = start_pos
        ex, ey = end_pos
        dx = ex - sx
        dy = ey - sy
        ctrl_offset = max(abs(dx) * 0.5, 40)
        ctrl1 = (sx + ctrl_offset, sy)
        ctrl2 = (ex - ctrl_offset, ey)
        path = QPainterPath()
        path.moveTo(sx, sy)
        path.cubicTo(ctrl1[0], ctrl1[1], ctrl2[0], ctrl2[1], ex, ey)
        self.setPath(path)
        self.update()

    def getOtherSocket(self, socket: 'Socket') -> Optional['Socket']:
        """Returns the opposite socket from the given socket."""
        if socket is self.start_socket:
            return self.end_socket
        elif socket is self.end_socket:
            return self.start_socket
        return None

    def remove(self):
        """Removes this edge from both sockets and the scene."""
        # Clean up event filters properly
        self._cleanup_event_filters()
            
        # Safely remove from sockets
        if self.start_socket and hasattr(self.start_socket, 'removeEdge'):
            self.start_socket.removeEdge(self)
        if self.end_socket and hasattr(self.end_socket, 'removeEdge'):
            self.end_socket.removeEdge(self)
        
        # Remove from scene
        if self.scene_ref:
            self.scene_ref.removeItem(self)
        
        # Clear references
        self.start_socket = None  # type: ignore
        self.end_socket = None  # type: ignore
        self.scene_ref = None  # type: ignore
    
    def delete_with_undo(self):
        """Delete this edge using the undo system"""
        if self.scene_ref and hasattr(self.scene_ref, 'undo_manager'):
            from view.commands import DeleteEdgeCommand
            command = DeleteEdgeCommand(self)
            self.scene_ref.undo_manager.execute_command(command)
        else:
            # Fallback to direct deletion
            self.remove()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        color = self.selected_color if self.isSelected() else self.normal_color
        pen = QPen(color, self.line_width)
        painter.setPen(pen)
        painter.drawPath(self.path())

    def itemChange(self, change, value):
        # Auto-update path if either socket moves
        if change == QGraphicsPathItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.updatePath()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.setSelected(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def sceneEventFilter(self, watched, event):
        """
        Filter scene events to catch when connected nodes move.
        This ensures the edge updates its path when either node moves.
        """
        from PyQt6.QtCore import QEvent
        
        # Check if this is a position change for one of our connected nodes
        if event.type() == QEvent.Type.GraphicsSceneMove:
            # If the watched item is one of our nodes, update the path
            if ((watched is self.start_socket.node or watched is self.end_socket.node) and
                (hasattr(self, 'updatePath'))):
                self.updatePath()
                
        # Always return False to allow further processing of the event
        return False
