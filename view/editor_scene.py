"""Editor scene for the OpenFOAM Case Generator"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem
from PyQt6.QtGui import QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

from config.themes import ThemeConfig
from view.undo_redo_manager import UndoRedoManager
from view.commands import CreateNodeCommand, CreateEdgeCommand
from nodes.node_c_graphical import Node_CGraphicalNode
from nodes.key_c_graphical import Key_CGraphicalNode
from nodes.enm_p_graphical import Enm_PGraphicalNode
from nodes.int_p_graphical import Int_PGraphicalNode
from nodes.flt_p_graphical import Flt_PGraphicalNode
from nodes.vector_p_graphical import Vector_PGraphicalNode
from nodes.dim_set_p_graphical import Dim_Set_PGraphicalNode
from nodes.tensor_p_graphical import Tensor_PGraphicalNode
from nodes.str_p_graphical import Str_PGraphicalNode
from nodes.list_cp_graphical import List_CPGraphicalNode
from nodes.output_graphical import OutputGraphicalNode
from nodes.case_folder_output_graphical import CaseFolderOutputNode


class EditorScene(QGraphicsScene):
    """Graphics scene for the node editor"""
    
    # Signals
    node_created = pyqtSignal(object)  # Emitted when a node is created
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize undo/redo manager
        self.undo_manager = UndoRedoManager()
        
        # Scene size (fixed but scrollable)
        self.scene_width = 20000
        self.scene_height = 20000
        self.setSceneRect(-self.scene_width//2, -self.scene_height//2, 
                         self.scene_width, self.scene_height)
        
        # Current theme
        self.current_theme = ThemeConfig.LIGHT_THEME
        self.is_dark_mode = False
        
        # Grid settings
        self.grid_size = ThemeConfig.GRID_SIZE
        self.grid_squares = ThemeConfig.GRID_SQUARES
        self.fine_grid_divisions = ThemeConfig.FINE_GRID_DIVISIONS

        # Temporary edge for connection
        self._dragging_edge = None
        # Socket where drag started
        self._start_socket = None   
        
        # Set selection mode to single selection only
        self.setSelectionArea = lambda: None  # Disable rubber band selection

        self._setup_scene()
    
    def _setup_scene(self):
        """Setup the scene with background and grid"""
        self.setBackgroundBrush(QBrush(self.current_theme['background']))
        self._draw_grid()
    
    def _draw_grid(self):
        """Draw grid lines on the scene"""
        # Clear existing grid items
        for item in self.items():
            if hasattr(item, 'is_grid_line'):
                self.removeItem(item)
        
        # Main grid pen (major lines)
        main_pen = QPen(self.current_theme['grid_main'])
        main_pen.setWidth(2)
        
        # Sub grid pen (minor lines)
        sub_pen = QPen(self.current_theme['grid_sub'])
        sub_pen.setWidth(1)
        
        # Fine sub-grid pen (finest lines)
        fine_pen = QPen(self.current_theme['grid_sub'])
        fine_pen.setWidth(1)
        fine_pen.setStyle(Qt.PenStyle.DotLine)  # Dotted style for finest grid
        
        # Draw vertical lines
        left = int(self.sceneRect().left())
        right = int(self.sceneRect().right())
        top = int(self.sceneRect().top())
        bottom = int(self.sceneRect().bottom())
        
        # Fine sub-grid lines (every 10 units)
        fine_grid_size = self.grid_size // 5  # 10 units if grid_size is 50
        for x in range(left, right + 1, fine_grid_size):
            if x % self.grid_size != 0:  # Don't draw over main/sub grid lines
                line = self.addLine(x, top, x, bottom, fine_pen)
                line.is_grid_line = True
                line.setZValue(-3)  # Behind everything else
        
        for y in range(top, bottom + 1, fine_grid_size):
            if y % self.grid_size != 0:
                line = self.addLine(left, y, right, y, fine_pen)
                line.is_grid_line = True
                line.setZValue(-3)
        
        # Sub-grid lines (every 50 units)
        for x in range(left, right + 1, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                line = self.addLine(x, top, x, bottom, sub_pen)
                line.is_grid_line = True
                line.setZValue(-2)
        
        for y in range(top, bottom + 1, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                line = self.addLine(left, y, right, y, sub_pen)
                line.is_grid_line = True
                line.setZValue(-2)
        
        # Major grid lines (every 250 units)
        for x in range(left, right + 1, self.grid_size * self.grid_squares):
            line = self.addLine(x, top, x, bottom, main_pen)
            line.is_grid_line = True
            line.setZValue(-1)  # Behind nodes but in front of sub-grids
        
        for y in range(top, bottom + 1, self.grid_size * self.grid_squares):
            line = self.addLine(left, y, right, y, main_pen)
            line.is_grid_line = True
            line.setZValue(-1)

    def set_dark_mode(self):
        """Switch to dark mode"""
        self.current_theme = ThemeConfig.DARK_THEME
        self.is_dark_mode = True
        self._setup_scene()
        self.update()
    
    def set_light_mode(self):
        """Switch to light mode"""
        self.current_theme = ThemeConfig.LIGHT_THEME
        self.is_dark_mode = False
        self._setup_scene()
        self.update()
    
    def get_current_theme(self):
        """Get current theme colors"""
        return self.current_theme
    
    def create_node(self, node_type, position):
        """Create a new node at the specified position"""
        if node_type == "Node_C":
            node = Node_CGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Key_C":
            node = Key_CGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Enm_P":
            node = Enm_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Int_P":
            node = Int_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Flt_P":
            node = Flt_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Vector_P":
            node = Vector_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Dim_Set_P":
            node = Dim_Set_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Tensor_P":
            node = Tensor_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Str_P":
            node = Str_PGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "List_CP":
            node = List_CPGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Output":
            node = OutputGraphicalNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        elif node_type == "Case Folder":
            node = CaseFolderOutputNode()
            node.setPos(position)
            self.addItem(node)
            self.node_created.emit(node)
            return node
        else:
            # For other node types, you can add more cases here
            # ...removed debug print...
            return None
    
    def create_node_with_undo(self, node_type, position):
        """Create a new node using the undo system"""
        command = CreateNodeCommand(self, node_type, position)
        if self.undo_manager.execute_command(command):
            return command.node
        return None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        from view.socket import Socket
        if isinstance(item, Socket):
            self._start_socket = item
            self._dragging_edge = QGraphicsPathItem()
            self._dragging_edge.setZValue(100)
            pen = QPen(QColor("#9CA3AF"), 3)  # Increased from 2 for better visibility
            self._dragging_edge.setPen(pen)
            self.addItem(self._dragging_edge)
            return  # Don't call super to prevent node selection
        else:
            self._start_socket = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_edge and self._start_socket:
            pos = event.scenePos()
            sx, sy = self._start_socket.getSocketPosition()
            ex, ey = pos.x(), pos.y()
            ctrl_offset = max(abs(ex - sx) * 0.5, 40)
            ctrl1 = (sx + ctrl_offset, sy)
            ctrl2 = (ex - ctrl_offset, ey)
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.moveTo(sx, sy)
            path.cubicTo(ctrl1[0], ctrl1[1], ctrl2[0], ctrl2[1], ex, ey)
            self._dragging_edge.setPath(path)
            self._dragging_edge.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        from view.socket import Socket
        from view.edge import Edge
        if self._dragging_edge and self._start_socket:
            snap_distance = 48  # Increased from 32 to match larger sockets
            mouse_pos = event.scenePos()
            nearest_socket = None
            min_dist = float('inf')
            for item in self.items():
                if isinstance(item, Socket) and item is not self._start_socket:
                    dist = (item.scenePos() - mouse_pos).manhattanLength()
                    if dist < snap_distance and dist < min_dist and self._start_socket.canConnectTo(item):
                        nearest_socket = item
                        min_dist = dist
            if nearest_socket:
                # Create edge using command system
                command = CreateEdgeCommand(self, self._start_socket, nearest_socket)
                self.undo_manager.execute_command(command)
            self.removeItem(self._dragging_edge)
            self._dragging_edge = None
            self._start_socket = None
            return
        super().mouseReleaseEvent(event)
