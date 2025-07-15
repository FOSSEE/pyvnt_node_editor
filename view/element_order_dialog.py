"""
Dialog for controlling element order in Node_C nodes.
Allows users to reorder elements before file output.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QListWidget, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class ElementOrderDialog(QDialog):
    """
    Dialog for setting the order of Key_C elements and Node_C children 
    in a Node_C object before file output.
    """
    
    def __init__(self, parent=None, node_data=None, title="Set Element Order"):
        """
        Initialize the dialog with the current element names in the Node_C.
        
        Args:
            parent: Parent widget
            node_data: List of element names (strings) currently in the Node_C
            title: Title for the dialog
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        
        # Store the original list for reference
        self.original_elements = node_data.copy() if node_data else []
        self.current_elements = node_data.copy() if node_data else []
        
        # Create UI components
        self.initUI()
        
    def initUI(self):
        """Create the dialog UI elements"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Drag and drop elements to change their order in the output file. "
            "The order will affect how elements appear in generated files.")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #555555; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # List of elements
        self.element_list = QListWidget()
        self.element_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.element_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.element_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # Populate the list
        for element in self.current_elements:
            self.element_list.addItem(element)
            
        layout.addWidget(self.element_list)
        
        # Add buttons for reordering
        btn_layout = QHBoxLayout()
        
        # Move up button
        self.btn_up = QPushButton("↑ Move Up")
        self.btn_up.clicked.connect(self.move_item_up)
        self.btn_up.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        btn_layout.addWidget(self.btn_up)
        
        # Move down button
        self.btn_down = QPushButton("↓ Move Down")
        self.btn_down.clicked.connect(self.move_item_down)
        self.btn_down.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        btn_layout.addWidget(self.btn_down)
        
        # Reset order button
        self.btn_reset = QPushButton("Reset Order")
        self.btn_reset.clicked.connect(self.reset_order)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        btn_layout.addWidget(self.btn_reset)
        
        layout.addLayout(btn_layout)
        
        # Add dialog buttons
        button_layout = QHBoxLayout()
        
        # OK button
        self.ok_button = QPushButton("Apply Order")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086e8;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
        """)
        button_layout.addWidget(self.ok_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def move_item_up(self):
        """Move the selected item up in the list"""
        current_row = self.element_list.currentRow()
        if current_row > 0:
            current_item = self.element_list.takeItem(current_row)
            self.element_list.insertItem(current_row - 1, current_item)
            self.element_list.setCurrentRow(current_row - 1)
    
    def move_item_down(self):
        """Move the selected item down in the list"""
        current_row = self.element_list.currentRow()
        if current_row < self.element_list.count() - 1:
            current_item = self.element_list.takeItem(current_row)
            self.element_list.insertItem(current_row + 1, current_item)
            self.element_list.setCurrentRow(current_row + 1)
    
    def reset_order(self):
        """Reset the order to the original state"""
        self.element_list.clear()
        for element in self.original_elements:
            self.element_list.addItem(element)
    
    def get_ordered_elements(self):
        """Return the current order of elements as a list of strings"""
        elements = []
        for i in range(self.element_list.count()):
            elements.append(self.element_list.item(i).text())
        return elements
