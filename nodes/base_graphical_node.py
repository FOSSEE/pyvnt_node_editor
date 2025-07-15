"""Base graphical node class for the OpenFOAM Case Generator"""

from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsProxyWidget, QLineEdit, QLabel, QMenu
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QAction

from view.socket import Socket


class BaseGraphicalNode(QGraphicsItem):
    """
    Base class for all graphical nodes in the node editor.
    
    Provides common functionality:
    - Professional dark theme styling
    - Socket management with proper positioning
    - Mouse interaction (dragging, selection)
    - Common layout and sizing logic
    - Name widget management
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Node dimensions (can be overridden by subclasses) - Increased for better visibility
        self.width = 300  # Increased from 220 for better visibility
        self.title_height = 40  # Increased from 30 for better title readability
        self.content_margin = 16  # Increased from 12 for better spacing
        self.socket_radius = 12  # Increased from 8 for easier clicking
        self.socket_spacing = 40  # Increased from 30 for better spacing
        self.min_height = 140  # Increased from 100 for better proportions
        
        # Socket management
        self.input_sockets = []
        self.output_sockets = []
        
        # Visual state
        self._dragging = False
        self._drag_start_position = None
        self._initial_drag_position = None  # For undo/redo movement tracking
        
        # Professional dark color scheme
        self.background_color = QColor(43, 43, 43)      # #2b2b2b
        self.border_color = QColor(64, 64, 64)          # #404040
        self.title_background_color = QColor(60, 60, 60)  # #3c3c3c
        self.text_color = QColor(255, 255, 255)         # White text
        self.selected_pen_color = QColor(0, 120, 212)   # #0078d4
        
        # Socket colors - improved for better distinction
        self.input_socket_color = QColor(255, 165, 0)   # Orange for inputs
        self.output_socket_color = QColor(0, 120, 215)  # Blue for outputs
        
        # Make item selectable and movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Height calculated after content is added
        self.height = self.min_height
    
    def create_name_widget(self, default_name="unnamed", placeholder_text=""):
        """Create the name input widget that most nodes need"""
        # Create the "Name:" label
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-family: Arial;
                font-weight: bold;
                padding: 3px;
            }
        """)
        
        # Create proxy widget for the label
        self.name_label_proxy = QGraphicsProxyWidget(self)
        self.name_label_proxy.setWidget(self.name_label)
        
        # Create the QLineEdit
        self.name_edit = QLineEdit()
        self.name_edit.setText(default_name)
        if placeholder_text:
            self.name_edit.setPlaceholderText(placeholder_text)
        self.name_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus
        
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                background-color: #404040;
                color: white;
                font-size: 16px;
                font-family: Arial;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                background-color: #4a4a4a;
            }
        """)
        
        # Create proxy widget to embed QLineEdit in graphics scene
        self.name_proxy = QGraphicsProxyWidget(self)
        self.name_proxy.setWidget(self.name_edit)
        
        # Connect signal for name changes
        self.name_edit.textChanged.connect(self._on_name_changed)
        
        # Store the old name for undo tracking
        self._old_name = default_name
        
        # Position the widgets
        self._position_name_widgets()
    
    def _position_name_widgets(self):
        """Position the name label and widget within the node"""
        if not hasattr(self, 'name_label') or not hasattr(self, 'name_edit'):
            return
            
        # Label positioning
        label_width = 60  # Increased from 45 for better proportions
        label_height = 26  # Increased from 20 for larger font
        label_x = self.content_margin
        label_y = self.title_height + self.content_margin
        
        self.name_label.setFixedSize(label_width, label_height)
        self.name_label_proxy.setPos(label_x, label_y)
        
        # QLineEdit positioning (next to the label)
        widget_width = self.width - 2 * self.content_margin - label_width - 8  # Increased spacing
        widget_height = 26  # Increased from 20 for larger font
        widget_x = self.content_margin + label_width + 8  # Increased spacing after label
        widget_y = self.title_height + self.content_margin
        
        self.name_edit.setFixedSize(widget_width, widget_height)
        self.name_proxy.setPos(widget_x, widget_y)
    
    def _on_name_changed(self, text):
        """Handle name change - create undo command for text changes"""
        # Only create undo command if we have an old name and the scene supports undo
        if (hasattr(self, '_old_name') and self._old_name != text and 
            self.scene() and hasattr(self.scene(), 'undo_manager')):
            
            from view.commands import ChangeNodePropertyCommand
            command = ChangeNodePropertyCommand(self, 'name', self._old_name, text)
            
            # Mark as executed since the change already happened
            command._executed = True
            
            # Only add if this isn't a duplicate
            manager = self.scene().undo_manager
            should_add = True
            if (manager.commands and manager.current_index >= 0 and 
                isinstance(manager.commands[manager.current_index], type(command))):
                last_cmd = manager.commands[manager.current_index]
                if (last_cmd.node == self and last_cmd.property_name == 'name' and 
                    last_cmd.new_value == text and hasattr(last_cmd, '_executed') and last_cmd._executed):
                    should_add = False
            
            if should_add:
                # Remove any commands after current index
                if manager.current_index < len(manager.commands) - 1:
                    manager.commands = manager.commands[:manager.current_index + 1]
                
                # Add the command
                manager.commands.append(command)
                manager.current_index += 1
                manager._emit_state_changed()
            
            # Update old name
            self._old_name = text
    
    def add_input_socket(self, multi_connection=True):
        """
        Add an input socket on the lower left.
        multi_connection: True for square (multiple), False for circle (single)
        """
        idx = len(self.input_sockets)
        socket = Socket(self, idx, Socket.LEFT_BOTTOM, Socket.INPUT_SOCKET, multi_connection)
        socket.setParentItem(self)
        socket.node = self
        self.input_sockets.append(socket)
        # Only update height if it's safe to do so
        self._safe_update_height()
        return socket
    
    def add_output_socket(self, multi_connection=False):
        """
        Add an output socket on the upper right.
        multi_connection: True for square (multiple), False for circle (single)
        """
        idx = len(self.output_sockets)
        socket = Socket(self, idx, Socket.RIGHT_TOP, Socket.OUTPUT_SOCKET, multi_connection)
        socket.setParentItem(self)
        socket.node = self
        self.output_sockets.append(socket)
        # Only update height if it's safe to do so
        self._safe_update_height()
        return socket
    
    def get_socket_position(self, socket_index, is_input=True):
        """
        Get socket position in node coordinates.
        Input sockets: lower left, evenly spaced vertically upward
        Output sockets: upper right, evenly spaced vertically downward
        """
        if is_input:
            if socket_index >= len(self.input_sockets):
                return QPointF(0, self.height)
            
            # Position on left edge, starting from bottom and going up
            x = 0
            if len(self.input_sockets) == 1:
                # Single socket: center it vertically in the lower half
                y = self.height - (self.height - self.title_height) // 4
            else:
                # Multiple sockets: space them in the lower 2/3 of the node
                start_y = self.height - self.content_margin - self.socket_radius
                end_y = self.title_height + (self.height - self.title_height) // 3
                if len(self.input_sockets) > 1:
                    step = (start_y - end_y) / (len(self.input_sockets) - 1)
                    y = start_y - socket_index * step
                else:
                    y = start_y
            
            return QPointF(x, y)
        else:
            if socket_index >= len(self.output_sockets):
                return QPointF(self.width, 0)
            
            # Position on right edge, starting from top and going down
            x = self.width
            if len(self.output_sockets) == 1:
                # Single socket: center it vertically in the upper half
                y = self.title_height + (self.height - self.title_height) // 4
            else:
                # Multiple sockets: space them in the upper 2/3 of the node
                start_y = self.title_height + self.content_margin + self.socket_radius
                end_y = self.title_height + 2 * (self.height - self.title_height) // 3
                if len(self.output_sockets) > 1:
                    step = (end_y - start_y) / (len(self.output_sockets) - 1)
                    y = start_y + socket_index * step
                else:
                    y = start_y
            
            return QPointF(x, y)
    
    def _safe_update_height(self):
        """Safe version of _update_height that doesn't fail if subclass widgets don't exist yet"""
        try:
            self._update_height()
        except AttributeError:
            # If subclass widgets don't exist yet, just set a basic height
            self.height = self.min_height
    
    def _update_height(self):
        """Update node height based on content and sockets"""
        # Calculate minimum height based on sockets
        socket_height = max(
            len(self.input_sockets) * self.socket_spacing if self.input_sockets else 0,
            len(self.output_sockets) * self.socket_spacing if self.output_sockets else 0
        )
        
        # Calculate content height (title + name widget + margins)
        content_height = self.title_height + self.content_margin * 2
        if hasattr(self, 'name_edit'):
            content_height += 26 + 6  # Updated name widget height + spacing
        
        # Add any additional content height from subclasses
        additional_height = self.get_additional_content_height()
        content_height += additional_height
        
        # Use the larger of the two
        self.height = max(self.min_height, content_height, socket_height + self.title_height)
        
        # Reposition widgets after height change
        self._position_name_widgets()
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def _position_sockets(self):
        """Position all socket objects based on current node dimensions"""
        # Position input sockets
        for i, socket in enumerate(self.input_sockets):
            pos = self.get_socket_position(i, is_input=True)
            socket.setPos(pos.x() - socket.radius, pos.y() - socket.radius)
        
        # Position output sockets
        for i, socket in enumerate(self.output_sockets):
            pos = self.get_socket_position(i, is_input=False)
            socket.setPos(pos.x() - socket.radius, pos.y() - socket.radius)
    
    def get_additional_content_height(self):
        """Override in subclasses to add height for additional widgets"""
        return 0
    
    def get_node_title(self):
        """Override in subclasses to provide the node title"""
        return "Base Node"
    
    def boundingRect(self):
        """Return the bounding rectangle of the node"""
        return QRectF(0, 0, self.width, self.height)
    
    def shape(self):
        """Return the shape for collision detection"""
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), 8, 8)
        return path
    
    def paint(self, painter, option, widget):
        """Paint the node with professional dark theme"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw main node body
        rect = QRectF(0, 0, self.width, self.height)
        
        # Selection highlight
        if self.isSelected():
            selection_pen = QPen(self.selected_pen_color, 3)
            painter.setPen(selection_pen)
            painter.setBrush(QBrush(self.background_color))
            painter.drawRoundedRect(rect, 8, 8)
        
        # Node background
        painter.setPen(QPen(self.border_color, 2))
        painter.setBrush(QBrush(self.background_color))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Title bar
        title_rect = QRectF(0, 0, self.width, self.title_height)
        painter.setBrush(QBrush(self.title_background_color))
        painter.drawRoundedRect(title_rect, 8, 8)
        
        # Draw bottom corners of title bar as square to connect with body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, self.title_height - 8, self.width, 8)
        
        # Title text
        painter.setPen(QPen(self.text_color))
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))  # Increased from 14 for better readability
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.get_node_title())
    
    # Mouse interaction methods
    def mousePressEvent(self, event):
        """Handle mouse press for dragging and context menu"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start_position = event.pos()
            self._initial_drag_position = self.pos()  # Store initial position for undo
            
            # Clear all other selections first to prevent multiple nodes moving together
            if self.scene():
                self.scene().clearSelection()
            
            self.setSelected(True)
            self.setZValue(1)  # Bring to front during dragging
        elif event.button() == Qt.MouseButton.RightButton:
            # Show context menu
            self.show_context_menu(event)
        super().mousePressEvent(event)
    
    def show_context_menu(self, event):
        """Show context menu with delete option"""
        menu = QMenu()
        
        # Create delete action
        delete_action = QAction("Delete Node", menu)
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)
        
        # Show the menu at cursor position
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            global_pos = view.mapToGlobal(view.mapFromScene(event.scenePos()))
            menu.exec(global_pos)
    
    def delete_node(self):
        """Delete this node and all its connected edges using undo system"""
        if not self.scene():
            return
        
        # Use undo system if available
        if hasattr(self.scene(), 'undo_manager'):
            from view.commands import DeleteNodeCommand
            command = DeleteNodeCommand(self.scene(), self)
            self.scene().undo_manager.execute_command(command)
        else:
            # Fallback to direct deletion
            self._direct_delete()
    
    def _direct_delete(self):
        """Direct deletion without undo system (fallback)"""
        # Remove all connected edges first
        edges_to_remove = []
        
        # Collect edges from input sockets
        for socket in self.input_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])  # Copy the list
        
        # Collect edges from output sockets
        for socket in self.output_sockets:
            if hasattr(socket, 'edges'):
                edges_to_remove.extend(socket.edges[:])  # Copy the list
        
        # Remove all edges
        for edge in edges_to_remove:
            if hasattr(edge, 'remove'):
                edge.remove()
        
        # Remove the node from the scene
        self.scene().removeItem(self)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # Only move this specific node, not any selected items
            delta = event.pos() - self._drag_start_position
            new_pos = self.pos() + delta
            self.setPos(new_pos)
            
            # Don't call super() to prevent default group dragging behavior
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if node was actually moved and create undo command
            if (self._dragging and self._initial_drag_position is not None and 
                self.pos() != self._initial_drag_position):
                
                # Create move command for undo system
                if self.scene() and hasattr(self.scene(), 'undo_manager'):
                    from view.commands import MoveNodeCommand
                    command = MoveNodeCommand(self, self._initial_drag_position, self.pos())
                    # Don't execute the command since the move already happened
                    command._executed = True
                    
                    # Only add if this isn't a duplicate (check if last command is the same)
                    manager = self.scene().undo_manager
                    should_add = True
                    if (manager.commands and manager.current_index >= 0 and 
                        isinstance(manager.commands[manager.current_index], type(command))):
                        last_cmd = manager.commands[manager.current_index]
                        if (last_cmd.node == self and 
                            last_cmd.new_position == self.pos() and 
                            hasattr(last_cmd, '_executed') and last_cmd._executed):
                            should_add = False
                    
                    if should_add:
                        # Remove any commands after current index
                        if manager.current_index < len(manager.commands) - 1:
                            manager.commands = manager.commands[:manager.current_index + 1]
                        
                        # Add the command
                        manager.commands.append(command)
                        manager.current_index += 1
                        manager._emit_state_changed()
            
            self._dragging = False
            self._initial_drag_position = None
            self.setZValue(0)
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Could add snap-to-grid here
            pass
        return super().itemChange(change, value)
    
    def get_pyvnt_object(self):
        """Override in subclasses to return the appropriate PyVNT object"""
        raise NotImplementedError("Subclasses must implement get_pyvnt_object()")
