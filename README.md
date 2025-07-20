# OpenFOAM Case Generator

A professional graphical tool for creating, editing, and generating OpenFOAM case files using an intuitive node-based interface. This application streamlines the process of creating complex OpenFOAM configurations through visual programming.

## Overview

The OpenFOAM Case Generator provides a sophisticated node-based editor that enables users to:

- Visually construct OpenFOAM case structures
- Generate individual configuration files or complete case directories
- Validate configuration integrity before generation
- Organize files into appropriate OpenFOAM directory structures

## Project Structure

The project is architected into the following modules:

- `loader/`: Contains functionality for loading and parsing OpenFOAM cases
  - `case_loader.py`: Handles loading and parsing of OpenFOAM case files
  - `node_converter.py`: Converts parsed objects to visual nodes
  - `parser_patch.py`: Customizes parser behavior for improved functionality

- `nodes/`: Contains all graphical node implementations
  - `base_graphical_node.py`: Base class for all visual nodes
  - `*_graphical.py`: Specialized node implementations for various data types:
    - Container nodes (`Node_C`, `Key_C`)
    - Parameter nodes (`Int_P`, `Flt_P`, `Str_P`, `Vector_P`, etc.)
    - Output nodes for file and case folder generation

- `view/`: Contains the UI components
  - `main_window.py`: Main application window and orchestration
  - `editor_scene.py`: Scene for the node editor with grid and management
  - `editor_view.py`: Interactive view for the node editor with zoom/pan controls
  - `edge.py`: Connection edges between nodes with routing algorithms
  - `socket.py`: Connection points on nodes for data flow
  - `undo_redo_manager.py`: Command pattern implementation for edit history
  - `commands.py`: Command objects for all editable operations
  - `properties_panel.py`: The Properties Panel for editing node properties interactively
## Properties Panel

The **Properties Panel** (see `view/properties_panel.py`) is a dynamic sidebar that displays and allows editing of the properties for the currently selected node. It provides context-sensitive controls (such as text fields, spin boxes, checkboxes, and lists) that are tailored to the type of node selected. Changes made in the Properties Panel are synchronized with the node in real time, and vice versa. This enables quick, precise editing of node parameters, names, values, and other attributes without directly interacting with the node on the canvas.

**Key features:**
- Automatically updates to reflect the selected node's properties
- Supports two-way synchronization between the panel and node widgets
- Provides specialized controls for different node types (e.g., vectors, enums, lists)
- Allows editing of advanced options like element order, case names, and output filenames
- Ensures that all changes are immediately reflected in the node graph and output

The Properties Panel is essential for efficient node configuration and is a core part of the application's workflow.

- `config/`: Contains configuration-related functionality
  - `themes.py`: Theme definitions for UI customization

- `output/`: Default directory for generated OpenFOAM cases

## How It Works

### Node-Based Editing

1. **Node Creation**: Drag nodes from the Node Library panel on the left into the editor area
2. **Node Connection**: Connect nodes by dragging from output sockets to input sockets
3. **Node Configuration**: Set parameters and properties directly within each node

### Node Types

- **Container Nodes**:
  - `Node_C`: Represents an OpenFOAM dictionary structure
  - `Key_C`: Represents key-value pairs in OpenFOAM

- **Parameter Nodes**:
  - `Int_P`: Integer parameters
  - `Flt_P`: Floating-point parameters
  - `Str_P`: String parameters
  - `Vector_P`: Vector parameters
  - `Tensor_P` : tensor parameters
  - `Dim_Set_P`: Dimensional set parameters
  - `Enm_P`: Enumeration (selection) parameters
  - `List_CP`: List container parameters

- **Output Nodes**:
  - `Output`: Validates PyVNT objects and optionally generates individual OpenFOAM files
  - `Case Folder`: Generates complete OpenFOAM case directory structures from connected inputs

### New Workflow Architecture

The application uses an optimized workflow to eliminate duplicate file generation:

1. **Input Nodes → Output Node (Validation or Generation)**:
   - Connect your parameter and container nodes to an Output node
   - The Output node validates all connected PyVNT objects
   - Optionally generates individual files if needed for testing

2. **Output Node → Case Folder Node (Generation)**:
   - Connect the validated Output node to a Case Folder node
   - The Case Folder node generates the complete OpenFOAM directory structure
   - No duplicate file generation occurs

3. **Flexible Input Options**:
   - Case Folder nodes accept 1-4 input connections
   - You can connect multiple Output nodes or use partial configurations
   - Missing inputs are gracefully handled during generation

### Generation Process

When you click the "Generate" button in an Output node or "Generate File" in a Case Folder node:

1. **Validation Phase**:
   - The system checks all input connections
   - Validates the node tree structure
   - Ensures all nodes have proper names and configurations

2. **Object Construction**:
   - For Output nodes: Traverses connected node graph and validates PyVNT objects
   - For Case Folder nodes: Retrieves validated objects from connected Output nodes
   - Objects are organized into a hierarchical structure matching OpenFOAM format

3. **Output Generation**:
   - **Output Node (Standalone Mode)**:
     - Gets the output path from the text field
     - Writes the configuration to the specified location
   
   - **Output Node (Validation Mode)**:
     - Validates connected PyVNT objects without file generation
     - Displays validation status and prepares objects for Case Folder consumption
   
   - **Case Folder Node**:
     - Creates the OpenFOAM directory structure (0/, constant/, system/)
     - Intelligently categorizes files into appropriate subfolders
     - Generates each file with proper formatting

4. **Status Update**:
   - Success/failure status is displayed
   - Generated file count and locations are reported

## Getting Started

1. Ensure you have Python 3.10+ installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Dependencies

- **PyQt6**: Provides the graphical user interface framework
- **PyVNT**: Powers the OpenFOAM file parsing and generation (included in the project)

## Working With the Application

1. **Create a New Case**: Use File > New Case to start fresh
2. **Build Your Structure**: Add nodes and connect them to define your case structure
3. **Configure Parameters**: Set values and properties within each node
4. **Generate Files**: Use output nodes to generate files or complete case structures
5. **Load Existing Cases**: Import and visualize existing OpenFOAM cases

## Navigation and Editing Controls

### Canvas Navigation
- **Zoom**: Use the mouse wheel to zoom in and out of the editor canvas
- **Pan**: Click and drag with the middle mouse button or hold Space and drag
- **Reset View**: Press Space to reset the view to default zoom and position
- **Fit Content**: Use View > Fit All to automatically frame all nodes in the view

### Node Manipulation
- **Select**: Click on a node to select it
- **Move**: Click and drag a node to reposition it
- **Delete**: Right-click a node to delete it, or select and press Delete

### Connection Management
- **Create Connection**: Click and drag from an output socket to an input socket
- **Knife Tool**: Press K or select Tools > Knife Tool to activate the connection cutting tool
  - While active, drag across connections to cut them
  - The cursor changes to indicate knife mode is active
  - Press K again or Escape to exit knife mode

### Editing History
- **Undo**: Ctrl+Z or Edit > Undo to reverse the last action
- **Redo**: Ctrl+Y or Edit > Redo to reapply undone actions
- **Limitations**:
  - Node property changes within dialogs can't be undone
  - The undo stack has a finite depth (last 20 operations)
  - Complex operations count as a single undo step

## Case Loading and Importing

The application supports loading existing OpenFOAM cases:

1. **Loading Individual Files**:
   - Use File > Load File to import a single OpenFOAM configuration file
   - The file will be parsed and converted to a node structure

2. **Loading Case Directories**:
   - Use File > Load Case Directory to import an entire OpenFOAM case
   - The system will automatically identify and parse relevant files
   - Files are organized based on the standard OpenFOAM directory structure

3. **Loading Process**:
   - Progress dialog shows parsing and node creation status
   - After loading, the scene will automatically fit to show all imported nodes
   - Connections are automatically established based on file references

4. **Loading Limitations**:
   - Complex OpenFOAM syntax may require manual adjustments
   - Very large cases may experience performance degradation
   - Custom functions and macros may not be fully supported

## Development

The application uses a model-view architecture with:
- PyVNT objects as the underlying data model
- Custom graphical nodes as the view and controller
- Signal-slot communication for event handling
