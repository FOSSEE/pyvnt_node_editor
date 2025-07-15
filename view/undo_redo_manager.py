"""Undo/Redo manager for the node editor"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional
from view.commands import Command


class UndoRedoManager(QObject):
    """Manager for undo/redo operations in the node editor"""
    
    # Signals
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)
    undo_text_changed = pyqtSignal(str)
    redo_text_changed = pyqtSignal(str)
    
    def __init__(self, max_commands: int = 100):
        super().__init__()
        self.max_commands = max_commands
        self.commands: List[Command] = []
        self.current_index = -1  # Index of the last executed command
        
        # Track if we're currently executing undo/redo to prevent recursive calls
        self._executing = False
        
    def execute_command(self, command: Command) -> bool:
        """Execute a command and add it to the undo stack"""
        if self._executing:
            return False
            
        # Execute the command
        if not command.execute():
            return False
        
        # Remove any commands after current index (they become invalid)
        if self.current_index < len(self.commands) - 1:
            self.commands = self.commands[:self.current_index + 1]
        
        # Add the new command
        self.commands.append(command)
        self.current_index += 1
        
        # Limit the number of commands
        if len(self.commands) > self.max_commands:
            self.commands.pop(0)
            self.current_index -= 1
        
        # Emit signals
        self._emit_state_changed()
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.commands) - 1
    
    def undo(self) -> bool:
        """Undo the last command"""
        if not self.can_undo() or self._executing:
            return False
        
        self._executing = True
        try:
            command = self.commands[self.current_index]
            if command.undo():
                self.current_index -= 1
                self._emit_state_changed()
                return True
            return False
        finally:
            self._executing = False
    
    def redo(self) -> bool:
        """Redo the next command"""
        if not self.can_redo() or self._executing:
            return False
        
        self._executing = True
        try:
            command = self.commands[self.current_index + 1]
            if command.redo():
                self.current_index += 1
                self._emit_state_changed()
                return True
            return False
        finally:
            self._executing = False
    
    def get_undo_text(self) -> str:
        """Get the text for the undo action"""
        if self.can_undo():
            return f"Undo {self.commands[self.current_index]}"
        return "Undo"
    
    def get_redo_text(self) -> str:
        """Get the text for the redo action"""
        if self.can_redo():
            return f"Redo {self.commands[self.current_index + 1]}"
        return "Redo"
    
    def clear(self):
        """Clear all commands"""
        self.commands.clear()
        self.current_index = -1
        self._emit_state_changed()
    
    def get_command_count(self) -> int:
        """Get the total number of commands"""
        return len(self.commands)
    
    def get_undo_count(self) -> int:
        """Get the number of commands that can be undone"""
        return self.current_index + 1
    
    def get_redo_count(self) -> int:
        """Get the number of commands that can be redone"""
        return len(self.commands) - self.current_index - 1
    
    def _emit_state_changed(self):
        """Emit signals when the state changes"""
        self.can_undo_changed.emit(self.can_undo())
        self.can_redo_changed.emit(self.can_redo())
        self.undo_text_changed.emit(self.get_undo_text())
        self.redo_text_changed.emit(self.get_redo_text())
    
    def get_commands_list(self) -> List[str]:
        """Get a list of all commands for debugging"""
        return [str(cmd) for cmd in self.commands]
    
    def begin_macro(self, description: str = "Multiple Operations"):
        """Begin a macro command (multiple operations treated as one)"""
        return MacroCommand(self, description)


class MacroCommand:
    """Context manager for grouping multiple commands into one undoable operation"""
    
    def __init__(self, manager: UndoRedoManager, description: str):
        self.manager = manager
        self.description = description
        self.commands: List[Command] = []
        self.original_executing = False
        
    def __enter__(self):
        """Start recording commands"""
        self.original_executing = self.manager._executing
        self.manager._executing = True  # Prevent individual commands from being added
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finish recording and execute as composite command"""
        self.manager._executing = self.original_executing
        
        if exc_type is None and self.commands:
            # Create and execute composite command
            from view.commands import CompositeCommand
            composite = CompositeCommand(self.commands, self.description)
            self.manager.execute_command(composite)
    
    def add_command(self, command: Command):
        """Add a command to the macro"""
        if command.execute():
            self.commands.append(command)
            return True
        return False
