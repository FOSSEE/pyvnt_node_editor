"""
Path and case management utilities for OpenFOAM Case Generator
"""

import os
import shutil
from typing import Dict, List, Tuple, Optional
from pathlib import Path


def resolve_case_path(user_input: str, default_output_dir: str) -> str:
    """
    Resolve case path from user input - handles both case names and full paths
    
    Args:
        user_input (str): Either just case name, directory path, or path with filename
        default_output_dir (str): Default output directory for cases
    
    Returns:
        str: Full path to case directory
    """
    if not user_input.strip():
        raise ValueError("Case name or path cannot be empty")
    
    user_input = user_input.strip()
    
    # Check if user_input is a full path (contains path separators or is absolute)
    if os.path.isabs(user_input) or ('\\' in user_input or '/' in user_input):
        # User provided a path - could be directory or directory + filename
        return os.path.abspath(user_input)
    else:
        # User provided just a case name - use default output directory
        return os.path.join(default_output_dir, user_input)


def ensure_case_structure(case_path: str) -> None:
    """
    Ensure OpenFOAM case directory structure exists
    
    Args:
        case_path (str): Path to case directory
    """
    required_dirs = ['system', 'constant', '0']
    
    # Create case directory first
    os.makedirs(case_path, exist_ok=True)
    
    # Create required subdirectories
    for dir_name in required_dirs:
        dir_path = os.path.join(case_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)


class CaseManager:
    """
    Manages OpenFOAM case directories and file operations
    """
    
    def __init__(self, case_path: str):
        self.case_path = os.path.abspath(case_path)
        self.system_dir = os.path.join(self.case_path, 'system')
        self.constant_dir = os.path.join(self.case_path, 'constant')
        self.zero_dir = os.path.join(self.case_path, '0')
        
        # Valid OpenFOAM folders
        self.valid_folders = ['system', 'constant', '0']
    
    def case_exists(self) -> bool:
        """Check if case directory already exists"""
        return os.path.exists(self.case_path)
    
    def get_existing_files(self, folder: str) -> List[str]:
        """
        Get list of existing files in specified folder
        
        Args:
            folder (str): Folder name ('system', 'constant', '0')
            
        Returns:
            List[str]: List of existing filenames
        """
        if folder not in self.valid_folders:
            raise ValueError(f"Invalid folder '{folder}'. Must be one of: {self.valid_folders}")
        
        folder_path = os.path.join(self.case_path, folder)
        if not os.path.exists(folder_path):
            return []
        
        return [f for f in os.listdir(folder_path) 
                if os.path.isfile(os.path.join(folder_path, f))]
    
    def get_case_info(self) -> Dict[str, List[str]]:
        """
        Get information about existing case structure
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping folder names to file lists
        """
        case_info = {}
        for folder in self.valid_folders:
            case_info[folder] = self.get_existing_files(folder)
        return case_info
    
    def file_exists(self, folder: str, filename: str) -> bool:
        """
        Check if specific file exists in folder
        
        Args:
            folder (str): Folder name ('system', 'constant', '0')
            filename (str): Name of file to check
            
        Returns:
            bool: True if file exists
        """
        if folder not in self.valid_folders:
            return False
        
        file_path = os.path.join(self.case_path, folder, filename)
        return os.path.exists(file_path)
    
    def backup_existing_file(self, folder: str, filename: str) -> Optional[str]:
        """
        Create backup of existing file before overwriting
        
        Args:
            folder (str): Folder name ('system', 'constant', '0')
            filename (str): Name of file to backup
            
        Returns:
            Optional[str]: Path to backup file if created, None otherwise
        """
        if not self.file_exists(folder, filename):
            return None
        
        file_path = os.path.join(self.case_path, folder, filename)
        backup_path = f"{file_path}.backup"
        
        # If backup already exists, create numbered backup
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{file_path}.backup.{counter}"
            counter += 1
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            return None
    
    def add_file_to_folder(self, folder: str, filename: str, content: str, 
                          overwrite: bool = False, create_backup: bool = True) -> Tuple[bool, str]:
        """
        Add file to specified folder
        
        Args:
            folder (str): Target folder ('system', 'constant', '0')
            filename (str): Name of file to create
            content (str): File content
            overwrite (bool): Whether to overwrite existing files
            create_backup (bool): Whether to create backup of existing files
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if folder not in self.valid_folders:
            return False, f"Invalid folder '{folder}'. Must be one of: {self.valid_folders}"
        
        # Ensure case structure exists
        ensure_case_structure(self.case_path)
        
        file_path = os.path.join(self.case_path, folder, filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            if not overwrite:
                return False, f"File '{filename}' already exists in '{folder}' folder. Enable overwrite to replace."
            
            # Create backup if requested
            if create_backup:
                backup_path = self.backup_existing_file(folder, filename)
                if backup_path:
                    backup_name = os.path.basename(backup_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Successfully wrote '{filename}' to '{folder}' folder"
        except Exception as e:
            return False, f"Error writing file '{filename}': {str(e)}"
    
    def get_folder_for_file(self, filename: str, socket_label: str = "") -> str:
        """
        Determine appropriate folder for a file based on filename and socket label
        
        Args:
            filename (str): Name of the file
            socket_label (str): Label from the socket connection
            
        Returns:
            str: Appropriate folder name ('system', 'constant', '0')
        """
        # Define file categories
        file_categories = {
            "system": [
                "controldict", "fvsolution", "fvschemes", "blockmeshdict", 
                "decomposepardict", "snappyhexmeshdict", "meshing"
            ],
            "constant": [
                "transportproperties", "turbulenceproperties", "thermophysicalproperties",
                "transport", "turbulence", "thermophysical", "properties"
            ],
            "0": [
                "p", "u", "t", "k", "omega", "epsilon", "nut", "alphat", 
                "velocity", "pressure", "temperature", "field"
            ]
        }
        
        filename_lower = filename.lower()
        socket_label_lower = socket_label.lower()
        
        # Check socket label for direct folder mapping
        if "system" in socket_label_lower:
            return "system"
        elif "constant" in socket_label_lower:
            return "constant"
        elif "initial" in socket_label_lower or "(0/)" in socket_label_lower or "0/" in socket_label_lower:
            return "0"
        
        # Check against known file categories
        for folder, keywords in file_categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return folder
        
        # Default to system for unknown files
        return "system"


def validate_case_name(case_name: str) -> Tuple[bool, str]:
    """
    Validate case name for filesystem compatibility
    
    Args:
        case_name (str): Case name to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not case_name or not case_name.strip():
        return False, "Case name cannot be empty"
    
    case_name = case_name.strip()
    
    # Check for invalid characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        if char in case_name:
            return False, f"Case name cannot contain '{char}'"
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if case_name.upper() in reserved_names:
        return False, f"'{case_name}' is a reserved name"
    
    # Check length
    if len(case_name) > 255:
        return False, "Case name is too long (max 255 characters)"
    
    return True, ""


def get_case_summary(case_path: str) -> Dict[str, any]:
    """
    Get summary information about an existing case
    
    Args:
        case_path (str): Path to case directory
        
    Returns:
        Dict[str, any]: Case summary information
    """
    manager = CaseManager(case_path)
    
    summary = {
        'path': case_path,
        'exists': manager.case_exists(),
        'folders': {},
        'total_files': 0
    }
    
    if summary['exists']:
        case_info = manager.get_case_info()
        summary['folders'] = case_info
        summary['total_files'] = sum(len(files) for files in case_info.values())
    
    return summary

def parse_case_input(user_input: str, default_output_dir: str) -> dict:
    """
    Parse user input to extract case directory and optional filename
    
    Args:
        user_input (str): User input (case name, directory, or directory/filename)
        default_output_dir (str): Default output directory
        
    Returns:
        dict: {
            'case_path': str,           # Directory for the case
            'suggested_filename': str,  # Filename if detected, None otherwise
            'input_type': str          # 'case_name', 'directory', or 'directory_with_file'
        }
    """
    if not user_input.strip():
        raise ValueError("Input cannot be empty")
    
    user_input = user_input.strip()
    
    # Determine if it's a path or just a name
    is_path = os.path.isabs(user_input) or ('\\' in user_input or '/' in user_input)
    
    if not is_path:
        # Just a case name
        return {
            'case_path': os.path.join(default_output_dir, user_input),
            'suggested_filename': None,
            'input_type': 'case_name'
        }
    
    # It's a path - resolve it
    full_path = os.path.abspath(user_input)
    
    # Check if it includes a filename
    basename = os.path.basename(full_path)
    
    # Consider it a filename if:
    # 1. Has an extension, OR
    # 2. Doesn't end with path separator AND contains a dot (but not just at start)
    has_extension = bool(os.path.splitext(basename)[1])
    looks_like_file = (not user_input.endswith(('\\', '/')) and 
                      '.' in basename and 
                      not basename.startswith('.') and
                      len(basename.split('.')) == 2)  # Simple filename.ext pattern
    
    if has_extension or looks_like_file:
        # Path includes filename
        case_path = os.path.dirname(full_path)
        suggested_filename = os.path.splitext(basename)[0]  # Remove extension
        return {
            'case_path': case_path,
            'suggested_filename': suggested_filename,
            'input_type': 'directory_with_file'
        }
    else:
        # Path is just directory
        return {
            'case_path': full_path,
            'suggested_filename': None,
            'input_type': 'directory'
        }
