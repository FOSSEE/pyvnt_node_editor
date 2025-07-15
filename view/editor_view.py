"""Editor view for the OpenFOAM Case Generator"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QPointF



class EditorView(QGraphicsView):
    """Graphics view for the node editor with enhanced zoom and pan capabilities"""
    
    node_created = pyqtSignal(object)  # Signal emitted when a new node is created
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        # Enhanced view settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Improved zoom settings
        self.zoom_in_factor = 1.10 
        self.zoom_clamp = True
        self.zoom = 0
        self.zoom_step = 1
        self.zoom_range = [-15, 10]  
        
        # Pan settings
        self._pan_active = False
        self._last_pan_point = None
        
        # Knife tool settings
        self._knife_mode = False
        self._knife_line_start = None
        self._knife_line_end = None
        self._knife_line_item = None
        
        # Start with a better initial view - more zoomed out
        self.reset_view()

    def reset_view(self):
        """Reset view to show a good portion of the scene - more zoomed out"""
        self.resetTransform()
        self.zoom = 0
        self.fitInView(-1000, -1000, 2000, 2000, Qt.AspectRatioMode.KeepAspectRatio)
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel - improved for touchpad"""
        # Get both horizontal and vertical scroll for touchpad
        angle_delta = event.angleDelta()
        
        # Check if this is a zoom gesture (vertical scroll) or pan (horizontal scroll)
        if abs(angle_delta.y()) > abs(angle_delta.x()):
            # Vertical scroll - zoom
            angle = angle_delta.y()
            
            if angle > 0:
                zoom_factor = self.zoom_in_factor
                self.zoom += self.zoom_step
            else:
                zoom_factor = 1 / self.zoom_in_factor
                self.zoom -= self.zoom_step
            
            # Clamp zoom
            if self.zoom_clamp:
                if self.zoom < self.zoom_range[0]:
                    self.zoom = self.zoom_range[0]
                    return
                elif self.zoom > self.zoom_range[1]:
                    self.zoom = self.zoom_range[1]
                    return
            
            # Apply zoom
            self.scale(zoom_factor, zoom_factor)
        else:            # Horizontal scroll - pan horizontally
            delta_x = angle_delta.x()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta_x // 8
            )
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning - improved for touchpad"""
        # Handle knife mode
        if self._knife_mode and event.button() == Qt.MouseButton.LeftButton:
            self._knife_line_start = self.mapToScene(event.position().toPoint())
            return
        
        # Check if we clicked on a graphics item first (but not in knife mode)
        if not self._knife_mode:
            item = self.itemAt(event.position().toPoint())
            if item:
                # Let the graphics item handle the event
                super().mousePressEvent(event)
                return
            
        if (event.button() == Qt.MouseButton.MiddleButton or 
            (event.button() == Qt.MouseButton.LeftButton and not self._knife_mode) or  # Allow left button for touchpad but not in knife mode
            (event.button() == Qt.MouseButton.LeftButton and 
             event.modifiers() & Qt.KeyboardModifier.AltModifier)):
            self._pan_active = True
            self._last_pan_point = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning - improved sensitivity"""
        # Handle knife mode
        if self._knife_mode and self._knife_line_start:
            self._knife_line_end = self.mapToScene(event.position().toPoint())
            self._update_knife_line()
            return
        
        if self._pan_active:
            delta = event.position() - self._last_pan_point
            self._last_pan_point = event.position()
            
            # Increased sensitivity for better touchpad experience
            pan_speed = 1.5  
            
            # Pan the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x() * pan_speed)
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y() * pan_speed)
            )
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        # Handle knife mode
        if self._knife_mode and event.button() == Qt.MouseButton.LeftButton and self._knife_line_start:
            self._knife_line_end = self.mapToScene(event.position().toPoint())
            self._cut_edges_with_knife()
            self._clear_knife_line()
            return
        
        if (event.button() == Qt.MouseButton.MiddleButton or 
            event.button() == Qt.MouseButton.LeftButton):
            self._pan_active = False
            cursor = Qt.CursorShape.CrossCursor if self._knife_mode else Qt.CursorShape.ArrowCursor
            self.setCursor(cursor)
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts - improved"""
        # Check if focus is on an input widget (QLineEdit, QTextEdit, QSpinBox, QListWidget, etc.)
        # If so, let the widget handle the key event instead of processing shortcuts
        focused_widget = self.scene().focusItem()
        if focused_widget and hasattr(focused_widget, 'widget'):
            widget = focused_widget.widget()
            # Check if it's an input widget that should handle text input/navigation
            from PyQt6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QListWidget, QComboBox
            if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QListWidget, QComboBox)):
                # Let the input widget handle the key event
                super().keyPressEvent(event)
                return
        
        # Delete key - delete selected items
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected_items()
        # Undo/Redo shortcuts
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Ctrl+Shift+Z = Redo
                if hasattr(self.scene(), 'undo_manager'):
                    self.scene().undo_manager.redo()
            else:
                # Ctrl+Z = Undo
                if hasattr(self.scene(), 'undo_manager'):
                    self.scene().undo_manager.undo()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Y = Redo (alternative)
            if hasattr(self.scene(), 'undo_manager'):
                self.scene().undo_manager.redo()
        elif event.key() == Qt.Key.Key_Space:
            # Reset to comfortable view
            self.reset_view()
        elif event.key() == Qt.Key.Key_F:
            # Fit all content in view
            self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom = 0
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            # Zoom in with keyboard
            self.scale(self.zoom_in_factor, self.zoom_in_factor)
            self.zoom += self.zoom_step
        elif event.key() == Qt.Key.Key_Minus:
            # Zoom out with keyboard
            self.scale(1/self.zoom_in_factor, 1/self.zoom_in_factor)
            self.zoom -= self.zoom_step
        elif event.key() == Qt.Key.Key_K:
            # Toggle knife mode
            self.toggle_knife_mode()
        # Arrow keys for panning
        elif event.key() == Qt.Key.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 50)
        elif event.key() == Qt.Key.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 50)
        elif event.key() == Qt.Key.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 50)
        elif event.key() == Qt.Key.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 50)
        else:
            # For any other key, pass it to the parent
            super().keyPressEvent(event)
    
    def toggle_knife_mode(self):
        """Toggle knife mode for cutting edges"""
        self._knife_mode = not self._knife_mode
        if self._knife_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
            # Update status bar
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'statusBar'):
                main_window = main_window.parent()
            if main_window:
                main_window.statusBar().showMessage("Knife Mode: Click and drag to cut edges. Press K again to exit.")
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._clear_knife_line()
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'statusBar'):
                main_window = main_window.parent()
            if main_window:
                main_window.statusBar().showMessage("Ready - Wheel: zoom, Left drag: pan, Space: reset view, +/-: zoom, Arrows: pan, K: knife tool, Right-click node: delete")
    
    def _clear_knife_line(self):
        """Clear the knife cutting line"""
        if self._knife_line_item and self.scene():
            self.scene().removeItem(self._knife_line_item)
            self._knife_line_item = None
        self._knife_line_start = None
        self._knife_line_end = None
    
    def _update_knife_line(self):
        """Update the visual knife cutting line"""
        if not self._knife_line_start or not self._knife_line_end:
            return
        
        # Remove old line
        if self._knife_line_item and self.scene():
            self.scene().removeItem(self._knife_line_item)
        
        # Create new line
        pen = QPen()
        pen.setColor(Qt.GlobalColor.red)
        pen.setWidth(3)  # Increased from 2 for better visibility
        pen.setStyle(Qt.PenStyle.DashLine)
        
        self._knife_line_item = self.scene().addLine(
            self._knife_line_start.x(), self._knife_line_start.y(),
            self._knife_line_end.x(), self._knife_line_end.y(),
            pen
        )
        self._knife_line_item.setZValue(1000)  # Always on top
    
    def _cut_edges_with_knife(self):
        """Cut edges that intersect with the knife line"""
        if not self._knife_line_start or not self._knife_line_end or not self.scene():
            return
        
        from view.edge import Edge
        
        # Get all edges in the scene
        edges_to_remove = []
        for item in self.scene().items():
            if isinstance(item, Edge):
                if self._line_intersects_edge(self._knife_line_start, self._knife_line_end, item):
                    edges_to_remove.append(item)
        
        # Remove intersected edges using undo system
        if edges_to_remove:
            if hasattr(self.scene(), 'undo_manager'):
                # Group all edge deletions into one undo operation
                with self.scene().undo_manager.begin_macro("Knife Cut") as macro:
                    for edge in edges_to_remove:
                        from view.commands import DeleteEdgeCommand
                        command = DeleteEdgeCommand(edge)
                        macro.add_command(command)
            else:
                # Fallback to direct removal
                for edge in edges_to_remove:
                    edge.remove()
    
    def _line_intersects_edge(self, line_start, line_end, edge):
        """Check if a line intersects with an edge (bezier curve approximation)"""
        # Approximate the bezier curve with line segments for intersection testing
        path = edge.path()
        
        # Sample points along the path
        sample_count = 20
        for i in range(sample_count):
            t1 = i / sample_count
            t2 = (i + 1) / sample_count
            
            point1 = path.pointAtPercent(t1)
            point2 = path.pointAtPercent(t2)
            
            # Check if knife line intersects this segment
            if self._lines_intersect(line_start, line_end, point1, point2):
                return True
        
        return False
    
    def _lines_intersect(self, p1, p2, p3, p4):
        """Check if two line segments intersect"""
        def ccw(A, B, C):
            return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            node_type = event.mimeData().text().strip()
            # Accept all node types for now - validation will happen in scene
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events - create a new node at the drop position"""
        if event.mimeData().hasText():
            node_type = event.mimeData().text().strip()
            
            # Get the drop position in scene coordinates
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Create the node using undo system
            if hasattr(self.scene(), 'create_node_with_undo'):
                node = self.scene().create_node_with_undo(node_type, scene_pos)
                if node:
                    # Emit signal that a new node was created
                    self.node_created.emit(node)
            elif hasattr(self.scene(), 'create_node'):
                # Fallback to direct creation
                node = self.scene().create_node(node_type, scene_pos)
                if node:
                    # Emit signal that a new node was created
                    self.node_created.emit(node)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def on_node_selected(self, graphics_node):
        """Handle node selection"""
        # You can emit this to main window or handle selection logic here
        pass
    
    def on_node_moved(self, graphics_node):
        """Handle node movement"""
        # You can add snap-to-grid logic here if needed
        pass
    
    def _delete_selected_items(self):
        """Delete all selected items using undo system"""
        selected_items = self.scene().selectedItems()
        if not selected_items:
            return
        
        # Group deletions into a single undo operation if multiple items
        if hasattr(self.scene(), 'undo_manager'):
            if len(selected_items) == 1:
                # Single item - use the item's own delete method for cleaner undo text
                item = selected_items[0]
                if hasattr(item, 'delete_with_undo'):
                    # For edges
                    item.delete_with_undo()
                elif hasattr(item, 'delete_node'):
                    # For nodes
                    item.delete_node()
            else:
                # Multiple items - group into macro
                with self.scene().undo_manager.begin_macro("Delete Selected Items") as macro:
                    for item in selected_items:
                        if hasattr(item, 'delete_with_undo'):
                            # For edges
                            from view.commands import DeleteEdgeCommand
                            command = DeleteEdgeCommand(item)
                            macro.add_command(command)
                        elif hasattr(item, 'delete_node'):
                            # For nodes
                            from view.commands import DeleteNodeCommand
                            command = DeleteNodeCommand(self.scene(), item)
                            macro.add_command(command)
        else:
            # Fallback to direct deletion
            for item in selected_items:
                if hasattr(item, 'remove'):
                    item.remove()
                elif hasattr(item, 'delete_node'):
                    item.delete_node()
