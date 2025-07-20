"""
Case Folder Output Node for OpenFOAM Case Generation

This node creates complete OpenFOAM case folder structures by accepting
multiple inputs and routing them to appropriate subfolders.

Features:
- Supports both case names (uses default output dir) and full directory paths
- Handles existing cases intelligently
- Creates backups when overwriting existing files
- Flexible file routing to system/constant/0 folders
"""

from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsProxyWidget, QLineEdit, 
                           QPushButton, QLabel, QComboBox, QVBoxLayout, QWidget,
                           QCheckBox, QMessageBox)
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from typing import Optional
import os
from nodes.base_graphical_node import BaseGraphicalNode
from pyvnt.Converter.Writer.writer import writeTo
from utils.case_utils import resolve_case_path, CaseManager, validate_case_name, get_case_summary


class CaseFolderOutputNode(BaseGraphicalNode):
    def set_case_name_from_panel(self, text):
        """Set the case_name_edit text from the properties panel, avoiding signal loops."""
        if self.case_name_edit.text() != text:
            old_block = self.case_name_edit.blockSignals(True)
            self.case_name_edit.setText(text)
            self.case_name_edit.blockSignals(old_block)
    """
    Advanced output node that creates complete OpenFOAM case folder structures.
    
    Features:
    - Multiple input sockets for different file types
    - Automatic folder structure creation (0/, constant/, system/)
    - Intelligent file routing based on socket labels
    - Complete case validation
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = 320  # Increased width to accommodate sockets and labels
        
        # Store default output directory (will be set by main window)
        self.default_output_dir = os.path.join(os.getcwd(), "output")
        
        # Define OpenFOAM case structure
        self.case_structure = {
            "system": ["controlDict", "fvSolution", "fvSchemes", "blockMeshDict", "decomposeParDict"],
            "constant": ["transportProperties", "turbulenceProperties", "thermophysicalProperties"],
            "0": ["p", "U", "T", "k", "omega", "epsilon", "nut", "alphat"]
        }
        
        # Create efficient input sockets
        self._create_input_sockets()
        
        # Create the UI widgets
        self._create_widgets()
        
        # Update height based on content
        self._update_height()
    
    def _create_input_sockets(self):
        """Create efficient input sockets"""
        self.add_input_socket(multi_connection=True, label="System")
        self.add_input_socket(multi_connection=True, label="Constant") 
        self.add_input_socket(multi_connection=True, label="Initial (0/)")
        self.add_input_socket(multi_connection=True, label="Other")
    
    def get_additional_content_height(self):
        """Return increased height to accommodate sockets"""
        return 140  # Reduced from 160 to make node more compact
    
    def get_node_title(self):
        """Return the title for this node type"""
        return "Case Folder Output"
    
    def _create_widgets(self):
        """Create optimal UI widgets"""
        # Case name/path input with tooltip
        self.case_name_edit = QLineEdit()
        self.case_name_edit.setPlaceholderText("Case name or full path")
        self.case_name_edit.setToolTip("Enter either:\n• Case name (uses default output folder)\n• Full directory path (e.g., C:\\Cases\\myCase)")
        self.case_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #666;
                border-radius: 3px;
                padding: 4px 6px;
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #0078d4; }
        """)
        self.case_name_proxy = QGraphicsProxyWidget(self)
        self.case_name_proxy.setWidget(self.case_name_edit)
        
        # Overwrite existing files checkbox
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.overwrite_checkbox.setToolTip("Allow overwriting files in existing cases (creates backups)")
        self.overwrite_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 12px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #666;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0078d4;
                background-color: #0078d4;
            }
        """)
        self.overwrite_proxy = QGraphicsProxyWidget(self)
        self.overwrite_proxy.setWidget(self.overwrite_checkbox)
        
        # Generate button
        self.gen_button = QPushButton("Generate")
        self.gen_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:disabled { background-color: #555; }
        """)
        self.gen_button.clicked.connect(self.generate_case_folder)
        self.button_proxy = QGraphicsProxyWidget(self)
        self.button_proxy.setWidget(self.gen_button)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            color: #aaa; 
            font-size: 12px; 
            font-family: Arial; 
            padding: 2px;
            background: rgba(0,0,0,0.2);
            border-radius: 3px;
        """)
        self.status_label.setWordWrap(True)
        self.status_proxy = QGraphicsProxyWidget(self)
        self.status_proxy.setWidget(self.status_label)
        
        # Create file count label
        self.file_count_label = QLabel("")
        self.file_count_label.setStyleSheet("""
            color: #aaa; 
            font-size: 12px; 
            font-family: Arial; 
            padding: 2px;
        """)
        self.file_count_label.setWordWrap(True)
        self.file_count_proxy = QGraphicsProxyWidget(self)
        self.file_count_proxy.setWidget(self.file_count_label)
        
        self._update_file_count()
    
    def _update_height(self):
        """Layout with increased size to prevent overlaps"""
        y = self.title_height + 12  # Reduced from 15
        
        # Move widgets further right to accommodate socket labels
        widget_x = 100  # Increased from 60 to give more space for socket labels
        widget_width = self.width - 110  # Adjusted width
        
        self.case_name_edit.setFixedSize(widget_width, 24)  # Reduced from 26
        self.case_name_proxy.setPos(widget_x, y)
        y += 30  # Reduced from 35
        
        # Overwrite checkbox
        self.overwrite_checkbox.setFixedSize(widget_width, 18)  # Reduced from 20
        self.overwrite_proxy.setPos(widget_x, y)
        y += 25  # Reduced from 30
        
        self.gen_button.setFixedSize(widget_width, 24)  # Reduced from 26
        self.button_proxy.setPos(widget_x, y)
        y += 30  # Reduced from 35
        
        # Status label with dynamic height
        self.status_label.setFixedWidth(widget_width)
        self.status_label.setWordWrap(True)
        self.status_label.adjustSize()
        label_height = max(18, self.status_label.sizeHint().height() + 4)  # Reduced from 20
        self.status_label.setFixedHeight(label_height)
        self.status_proxy.setPos(widget_x, y)
        y += label_height + 8  # Reduced from 10
        
        # File count label with dynamic height
        self.file_count_label.setFixedWidth(widget_width)
        self.file_count_label.setWordWrap(True)
        self.file_count_label.adjustSize()
        file_count_height = max(18, self.file_count_label.sizeHint().height() + 4)  # Reduced from 20
        self.file_count_label.setFixedHeight(file_count_height)
        self.file_count_proxy.setPos(widget_x, y)
        y += file_count_height + 12  # Reduced from 15
        
        self.height = y
        
        # Position sockets after height update
        self._position_sockets()
        self.prepareGeometryChange()
        self.update()
    
    def _update_file_count(self):
        """Efficient file count update"""
        count = sum(len(socket.edges) for socket in self.input_sockets if socket.hasEdge())
        
        # Log detailed socket information
        for i, socket in enumerate(self.input_sockets):
            socket_label = getattr(socket, 'label', f'Input {i+1}')
            edge_count = len(socket.edges) if socket.hasEdge() else 0
        
        self.gen_button.setEnabled(count > 0)
        
        if hasattr(self, 'status_label'):
            if count > 0:
                self.status_label.setText(f"{count} files connected")
                self.status_label.setStyleSheet("""
                    color: #83ff83; 
                    font-size: 12px; 
                    font-family: Arial; 
                    padding: 2px;
                    background: rgba(0,40,0,0.3);
                    border-radius: 3px;
                """)
            else:
                self.status_label.setText("Connect files to sockets")
                self.status_label.setStyleSheet("""
                    color: #aaa; 
                    font-size: 12px; 
                    font-family: Arial; 
                    padding: 2px;
                    background: rgba(0,0,0,0.2);
                    border-radius: 3px;
                """)
            # Update layout to adjust for the new text
            self._update_height()
    
    def _determine_file_destination(self, file_name, socket_label):
        """Determine which subfolder a file should go to based on its name and socket label"""
        # Use the utility function for better file categorization
        from utils.case_utils import CaseManager
        
        # Create a temporary manager to use the categorization logic
        temp_manager = CaseManager("")
        return temp_manager.get_folder_for_file(file_name, socket_label)
    
    def generate_case_folder(self):
        """Generate the complete OpenFOAM case folder structure with enhanced handling"""
        try:
            # Get and validate case input
            case_input = self.case_name_edit.text().strip()
            
            if not case_input:
                self._show_error("Please enter a case name or directory path")
                return
            
            # Validate case name if it's just a name (not a path)
            if not ('\\' in case_input or '/' in case_input or os.path.isabs(case_input)):
                is_valid, error_msg = validate_case_name(case_input)
                if not is_valid:
                    self._show_error(f"Invalid case name: {error_msg}")
                    return
            
            # Resolve full case path
            try:
                case_input_path = resolve_case_path(case_input, self.default_output_dir)
                
                # Check if the path includes a filename (has extension or doesn't end with separator)
                if os.path.splitext(case_input_path)[1] or (not case_input_path.endswith(('\\', '/')) and '.' in os.path.basename(case_input_path)):
                    # Path includes filename - extract directory
                    case_path = os.path.dirname(case_input_path)
                    suggested_filename = os.path.splitext(os.path.basename(case_input_path))[0]
                    self._show_info(f"Using directory: {os.path.basename(case_path)}, detected filename: {suggested_filename}")
                else:
                    # Path is just directory
                    case_path = case_input_path
                    
            except ValueError as e:
                self._show_error(str(e))
                return
            
            # Create case manager
            case_manager = CaseManager(case_path)
            
            # Check if case exists and show info
            if case_manager.case_exists():
                case_info = case_manager.get_case_info()
                total_existing = sum(len(files) for files in case_info.values())
                self._show_info(f"Adding to existing case with {total_existing} files")
            else:
                self._show_info("Creating new case...")
            
            # Check for connected files
            connected_nodes = []
            socket_labels = []
            
            for i, socket in enumerate(self.input_sockets):
                socket_label = getattr(socket, 'label', f'Input {i+1}')
                
                if socket.hasEdge():
                    for edge_idx, edge in enumerate(socket.edges):  # Handle multiple connections per socket
                        other_socket = edge.getOtherSocket(socket)
                        
                        if other_socket:
                            if hasattr(other_socket, 'node'):
                                connected_node = other_socket.node
                                if hasattr(connected_node, 'get_pyvnt_object'):
                                    connected_nodes.append(connected_node)
                                    socket_labels.append(socket_label)
                            
            if not connected_nodes:
                self._show_error("No files connected to sockets")
                return

            # Get overwrite setting
            allow_overwrite = self.overwrite_checkbox.isChecked()
            
            # Generate files
            generated_files = []
            skipped_files = []
            
            for idx, (node, socket_label) in enumerate(zip(connected_nodes, socket_labels)):
                try:
                    # Get PyVNT object from the node
                    pyvnt_obj = node.get_pyvnt_object()
                    
                    # Validate PyVNT object
                    from pyvnt.Container.key import Key_C
                    from pyvnt.Container.node import Node_C
                    if not isinstance(pyvnt_obj, (Key_C, Node_C)):
                        continue
                    
                    # Determine file name (use custom name from Output node if available)
                    if hasattr(node, 'output_filename') and node.output_filename:
                        file_name = node.output_filename
                    else:
                        file_name = pyvnt_obj.name
                    
                    # Determine destination folder
                    destination_folder = self._determine_file_destination(file_name, socket_label)
                    
                    # Check if file exists and handle accordingly
                    if case_manager.file_exists(destination_folder, f"{file_name}.txt"):
                        if not allow_overwrite:
                            skipped_files.append(f"{destination_folder}/{file_name}.txt")
                            continue
                        else:
                            # Create backup
                            case_manager.backup_existing_file(destination_folder, f"{file_name}.txt")
                    
                    # Ensure case structure exists
                    from utils.case_utils import ensure_case_structure
                    ensure_case_structure(case_path)
                    
                    # Write file to destination
                    destination_path = os.path.join(case_path, destination_folder)
                    writeTo(pyvnt_obj, destination_path, fileType='txt')
                    
                    # Track generated file
                    file_path = f"{destination_folder}/{file_name}.txt"
                    generated_files.append(file_path)
                    
                except Exception as e:
                    error_msg = f"Error processing {socket_label}: {str(e)[:50]}..."
                    self._show_error(error_msg)
                    return

            # Show results
            self._show_results(case_path, generated_files, skipped_files)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)[:50]}..."
            self._show_error(error_msg)
    
    def add_input_socket(self, multi_connection=False, label=""):
        """Override to add labeled sockets"""
        socket = super().add_input_socket(multi_connection)
        socket.label = label  # Add label attribute
        return socket
    
    def _position_sockets(self):
        """Position sockets with proper spacing, shifted up"""
        if not self.input_sockets:
            return
        
        # Position sockets vertically with generous spacing, starting higher
        start_y = self.title_height + 8  # Reduced from 10 to shift up more
        spacing = 26  # Reduced from 30 for more compact layout
        
        for i, socket in enumerate(self.input_sockets):
            y = start_y + i * spacing
            socket.setPos(-self.socket_radius, y)
    
    def paint(self, painter: QPainter, option, widget):
        """Paint socket labels with much more spacing"""
        super().paint(painter, option, widget)
        
        # Draw socket labels much further to the right
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        for socket in self.input_sockets:
            if hasattr(socket, 'label') and socket.label:
                x = int(socket.pos().x() + self.socket_radius + 20)  # Increased from 10 to 20
                y = int(socket.pos().y() + 3)
                painter.drawText(x, y, socket.label)
    
    def onSocketConnected(self, socket):
        """Called when a socket is connected"""
        socket_label = getattr(socket, 'label', 'Unknown')
        self._update_file_count()
    
    def onSocketDisconnected(self, socket):
        """Called when a socket is disconnected"""
        socket_label = getattr(socket, 'label', 'Unknown')
        self._update_file_count()
    
    def get_pyvnt_object(self):
        """Case folder output nodes are consumers of PyVNT objects, not providers"""
        raise RuntimeError("Case folder output nodes don't provide PyVNT objects. They consume them from connected nodes.")
    
    def set_default_output_dir(self, output_dir: str):
        """Set the default output directory for cases"""
        self.default_output_dir = output_dir
    
    def _show_error(self, message: str):
        """Show error message in status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            color: #ff9999; 
            font-size: 12px; 
            font-family: Arial; 
            padding: 2px;
            background: rgba(40,0,0,0.3);
            border-radius: 3px;
        """)
        self._update_height()
    
    def _show_info(self, message: str):
        """Show info message in status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            color: #87ceeb; 
            font-size: 12px; 
            font-family: Arial; 
            padding: 2px;
            background: rgba(0,20,40,0.3);
            border-radius: 3px;
        """)
        self._update_height()
    
    def _show_success(self, message: str):
        """Show success message in status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            color: #83ff83; 
            font-size: 12px; 
            font-family: Arial; 
            padding: 2px;
            background: rgba(0,40,0,0.3);
            border-radius: 3px;
        """)
        self._update_height()
    
    def _show_results(self, case_path: str, generated_files: list, skipped_files: list):
        """Show generation results"""
        case_name = os.path.basename(case_path)
        
        if generated_files:
            success_msg = f"Case '{case_name}' updated with {len(generated_files)} files!"
            self._show_success(success_msg)
            
            # Build detailed file count message
            details = []
            if generated_files:
                details.append(f"Generated: {len(generated_files)} files")
            if skipped_files:
                details.append(f"Skipped: {len(skipped_files)} files (already exist)")
            
            self.file_count_label.setText(" | ".join(details))
            self.file_count_label.setStyleSheet("""
                color: #83ff83; 
                font-size: 12px; 
                font-family: Arial; 
                padding: 2px;
                background: rgba(0,40,0,0.2);
                border-radius: 3px;
            """)
        else:
            if skipped_files:
                self._show_error(f"All {len(skipped_files)} files already exist. Enable 'Overwrite' to replace them.")
            else:
                self._show_error("No files were generated")
        
        self._update_height()
