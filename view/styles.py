"""UI styling constants for the OpenFOAM Case Generator"""

LEFT_PANE_STYLES = """
QWidget {
    background-color: #f5f5f5;
    border-right: 1px solid #d0d0d0;
    color: #333333;
}
QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 5px;
    margin-top: 1ex;
    color: #333333;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #333333;
}
QPushButton {
    background-color: #e1e1e1;
    border: 1px solid #b0b0b0;
    border-radius: 3px;
    padding: 5px;
    min-height: 20px;
    color: #333333;
}
QPushButton:hover {
    background-color: #d1d1d1;
    color: #333333;
}
QPushButton:pressed {
    background-color: #c1c1c1;
    color: #333333;
}
QLabel {
    color: #333333;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 3px;
    color: #333333;
}
QListWidget::item {
    padding: 3px;
    color: #333333;
}
QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #e5f3ff;
    color: #333333;
}
"""
