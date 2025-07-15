"""Theme configuration for the OpenFOAM Case Generator"""

from PyQt6.QtGui import QColor


class ThemeConfig:
    """Theme configuration class"""
    
    # Grid settings
    GRID_SIZE = 50
    GRID_SQUARES = 5  # Every 5th line is a major line
    FINE_GRID_DIVISIONS = 5  # Number of fine divisions within each grid square
    
    # Node type colors
    NODE_COLORS = {
        'p_node': QColor(231, 76, 60),      # Red for pressure node
        'solver': QColor(46, 204, 113),     # Green for solver nodes  
        'boundary': QColor(243, 156, 18),   # Orange for boundary nodes
        'scheme': QColor(155, 89, 182),     # Purple for scheme nodes
        'default': QColor(52, 152, 219),    # Blue for default nodes
    }
    
    # Light theme
    LIGHT_THEME = {
        'background': QColor(240, 240, 240),
        'grid_main': QColor(150, 150, 150),
        'grid_sub': QColor(200, 200, 200),
        'text': QColor(50, 50, 50),
        'node_background': QColor(255, 255, 255),
        'node_border': QColor(100, 100, 100),
        'node_selected': QColor(0, 120, 212),
    }
    
    # Dark theme
    DARK_THEME = {
        'background': QColor(45, 45, 45),
        'grid_main': QColor(120, 120, 120),
        'grid_sub': QColor(80, 80, 80),
        'text': QColor(220, 220, 220),
        'node_background': QColor(60, 60, 60),
        'node_border': QColor(150, 150, 150),
        'node_selected': QColor(0, 150, 255),
    }
