"""
Module for loading and parsing OpenFOAM case files.
Provides the CaseLoader class for handling OpenFOAM cases.
"""

# Import required modules
import os
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional
from .node_converter import NodeConverter
from .parser_patch import patch_parser  # Import the parser patch

# Try to import the parser
try:
    from pyvnt.Converter.PlyParser.Parser import OpenFoamParser
    from pyvnt.Container.node import Node_C
    from pyvnt.Container.key import Key_C
    from pyvnt.Container.list import List_CP
    from pyvnt.Reference.basic import Int_P, Flt_P, Enm_P, Str_P
    from pyvnt.Reference.vector import Vector_P
    from pyvnt.Reference.dimension_set import Dim_Set_P
except ImportError:
    OpenFoamParser = None
    Node_C = None
    Key_C = None
    List_CP = None
    Int_P = None
    Flt_P = None
    Enm_P = None
    Str_P = None
    Vector_P = None
    Dim_Set_P = None


class CaseLoader(QObject):
    """
    Handles loading and parsing of OpenFOAM case files using pyvnt parser.
    Converts parsed pyvnt objects into visual node representations.
    """
    
    # Signals
    loading_started = pyqtSignal(str)  # Emitted when loading starts
    loading_finished = pyqtSignal(object)  # Emitted when loading finishes with parsed tree
    loading_error = pyqtSignal(str)  # Emitted when loading fails
    progress_updated = pyqtSignal(int, str)  # Emitted to update progress (percentage, message)
    
    def __init__(self):
        super().__init__()
        # Apply the parser patch to redirect output files
        patch_parser()
        self.parser = OpenFoamParser() if OpenFoamParser else None
        
    def is_available(self) -> bool:
        """Check if the parser is available."""
        return self.parser is not None
    
    def load_case_file(self, file_path: str) -> Optional[object]:
        """
        Load a single OpenFOAM case file and parse it.
        
        Args:
            file_path (str): Path to the OpenFOAM file
            
        Returns:
            Parsed pyvnt object or None if parsing fails
        """
        if not self.parser:
            self.loading_error.emit("pyvnt parser not available")
            return None
            
        if not os.path.exists(file_path):
            self.loading_error.emit(f"File not found: {file_path}")
            return None
            
        try:
            self.loading_started.emit(file_path)
            self.progress_updated.emit(10, "Reading file...")
            
            # Use pyvnt parser to parse the file
            parsed_object = self.parser.parse_file(path=file_path)
            
            self.progress_updated.emit(100, "Parsing complete")
            self.loading_finished.emit(parsed_object)
            
            return parsed_object
            
        except Exception as e:
            error_msg = f"Failed to parse file {file_path}: {str(e)}"
            self.loading_error.emit(error_msg)
            return None
    
    def load_case_directory(self, case_path: str) -> Optional[object]:
        """
        Load an entire OpenFOAM case directory and parse all files.
        
        Args:
            case_path (str): Path to the OpenFOAM case directory
            
        Returns:
            Parsed pyvnt case tree or None if parsing fails
        """
        if not self.parser:
            self.loading_error.emit("pyvnt parser not available")
            return None
            
        if not os.path.exists(case_path) or not os.path.isdir(case_path):
            self.loading_error.emit(f"Case directory not found: {case_path}")
            return None
            
        try:
            self.loading_started.emit(case_path)
            self.progress_updated.emit(10, "Scanning case directory...")
            
            # Use pyvnt parser to parse the entire case
            parsed_case = self.parser.parse_case(case_path)
            
            self.progress_updated.emit(100, "Case loading complete")
            self.loading_finished.emit(parsed_case)
            
            return parsed_case
            
        except Exception as e:
            error_msg = f"Failed to parse case directory {case_path}: {str(e)}"
            self.loading_error.emit(error_msg)
            return None
    
    def load_from_text(self, text: str, file_type: str = 'txt') -> Optional[object]:
        """
        Load and parse OpenFOAM content from text string.
        
        Args:
            text (str): OpenFOAM file content as string
            file_type (str): File type ('txt' or 'yaml')
            
        Returns:
            Parsed pyvnt object or None if parsing fails
        """
        if not self.parser:
            self.loading_error.emit("pyvnt parser not available")
            return None
            
        try:
            self.loading_started.emit("text input")
            self.progress_updated.emit(50, "Parsing text...")
            
            # Use pyvnt parser to parse the text
            parsed_object = self.parser.parse_file(text=text, fileType=file_type)
            
            self.progress_updated.emit(100, "Text parsing complete")
            self.loading_finished.emit(parsed_object)
            
            return parsed_object
            
        except Exception as e:
            error_msg = f"Failed to parse text: {str(e)}"
            self.loading_error.emit(error_msg)
            return None

# Note: Conversion of PyVNT objects to visual nodes is now handled by the NodeConverter class
# from the loader.node_converter module
    
    # Note: All node conversion methods have been moved to the NodeConverter class
    # in loader/node_converter.py
