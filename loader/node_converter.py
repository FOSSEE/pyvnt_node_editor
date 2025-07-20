"""
Module for converting PyVNT objects to visual node representations.
Provides the NodeConverter class for creating visual nodes from parsed OpenFOAM objects.
"""

# Import required modules
from PyQt6.QtCore import QObject

# Try to import PyVNT classes for type checking
try:
    from pyvnt.Container.node import Node_C
    from pyvnt.Container.key import Key_C
    from pyvnt.Container.list import List_CP
    from pyvnt.Reference.basic import Int_P, Flt_P, Enm_P, Str_P
    from pyvnt.Reference.vector import Vector_P
    from pyvnt.Reference.tensor import Tensor_P
    from pyvnt.Reference.dimension_set import Dim_Set_P
except ImportError:
    # Define dummy classes for type checking if PyVNT is not available
    class Node_C: pass
    class Key_C: pass
    class List_CP: pass
    class Int_P: pass
    class Flt_P: pass
    class Enm_P: pass
    class Str_P: pass
    class Vector_P: pass
    class Dim_Set_P: pass


class NodeConverter:
    """
    Converts pyvnt objects to visual node representations for the editor.
    """
    
    @staticmethod
    def pyvnt_to_visual_nodes(pyvnt_object, scene, position_x=0, position_y=0, spacing=50):
        """
        Convert a pyvnt object tree into visual nodes in the editor scene.
        
        Args:
            pyvnt_object: The pyvnt object to convert
            scene: The editor scene to add nodes to
            position_x: Starting X position
            position_y: Starting Y Position
            spacing: Spacing between nodes
            
        Returns:
            Dictionary with created nodes and their connections
        """
        if not pyvnt_object:
            return {'nodes': [], 'connections': []}
            
        # Keep track of converted objects to avoid duplicates
        converted_objects = {}
        
        result = NodeConverter._convert_pyvnt_recursive(
            pyvnt_object, scene, position_x, position_y, spacing, converted_objects
        )
        
        # Create the actual connections after all nodes are created
        NodeConverter._create_connections(result['connections'], scene)
        
        return result
    
    @staticmethod
    def _convert_pyvnt_recursive(pyvnt_object, scene, position_x, position_y, spacing, converted_objects):
        """
        Recursively convert PyVNT objects, avoiding duplicates.
        """
        if not pyvnt_object:
            return {'nodes': [], 'connections': []}
        
        # Check if we've already converted this object
        object_id = id(pyvnt_object)
        if object_id in converted_objects:
            return {'nodes': [converted_objects[object_id]], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Handle different pyvnt object types
        if isinstance(pyvnt_object, Node_C):
            # Compute the depth of the tree first to properly position the head node
            depth = NodeConverter._compute_tree_depth(pyvnt_object)
            # Position head node farther right based on depth
            head_x = position_x + (depth * 180)
            node_result = NodeConverter._convert_node_c_recursive(
                pyvnt_object, scene, head_x, position_y, spacing, converted_objects
            )
            result['nodes'].extend(node_result['nodes'])
            result['connections'].extend(node_result['connections'])
            
        elif isinstance(pyvnt_object, Key_C):
            node_result = NodeConverter._convert_key_c_recursive(
                pyvnt_object, scene, position_x, position_y, spacing, converted_objects
            )
            if node_result:
                result['nodes'].extend(node_result['nodes'])
                result['connections'].extend(node_result['connections'])
                
        elif isinstance(pyvnt_object, List_CP):
            node_result = NodeConverter._convert_list_cp_with_children_recursive(
                pyvnt_object, scene, position_x, position_y, spacing, converted_objects
            )
            if node_result:
                result['nodes'].extend(node_result['nodes'])
                result['connections'].extend(node_result['connections'])
                
        elif isinstance(pyvnt_object, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
            node = NodeConverter._convert_property(pyvnt_object, scene, position_x, position_y)
            if node:
                result['nodes'].append(node)
                # Mark this object as converted
                converted_objects[object_id] = node
        
        return result
    
    @staticmethod
    def _compute_tree_depth(node_object, current_depth=0):
        """
        Compute the maximum depth of the tree to properly position nodes.
        
        Args:
            node_object: The node to compute depth for
            current_depth: Current depth in the tree
            
        Returns:
            Maximum depth of the tree
        """
        if not node_object or not isinstance(node_object, Node_C):
            return current_depth
            
        max_depth = current_depth
        
        # Check children
        if hasattr(node_object, 'children'):
            for child in node_object.children:
                child_depth = NodeConverter._compute_tree_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
                
        # Check data items
        if hasattr(node_object, 'data'):
            for data_item in node_object.data:
                if isinstance(data_item, Node_C):
                    data_depth = NodeConverter._compute_tree_depth(data_item, current_depth + 1)
                    max_depth = max(max_depth, data_depth)
                    
        return max_depth
    
    @staticmethod
    def _convert_node_c(node_c, scene, x, y, spacing):
        """Convert Node_C to visual representation with connection tracking."""
        try:
            from nodes.node_c_graphical import Node_CGraphicalNode
        except ImportError:
            pass
            return {'nodes': [], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        current_y = y
        
        # Create the main Node_C visual node
        visual_node = Node_CGraphicalNode()
        if hasattr(visual_node, 'name_edit'):
            visual_node.name_edit.setText(node_c.name if hasattr(node_c, 'name') else "unnamed")
        visual_node.setPos(x, current_y)
        scene.addItem(visual_node)
        result['nodes'].append(visual_node)
        
        # Get the main node dimensions
        main_node_width, main_node_height = NodeConverter._get_node_dimensions(visual_node)
        current_y += main_node_height + 20  # Start children below with minimal padding
        
        # Convert child nodes and data
        child_x = x - 300  # Offset children to the left with tight spacing
        
        # Handle data (Key_C objects) - these should connect to the Node_C input sockets
        if hasattr(node_c, 'data'):
            for data_item in node_c.data:
                # Store the starting y position for this branch
                branch_start_y = current_y
                
                # Process the child node
                child_result = NodeConverter.pyvnt_to_visual_nodes(data_item, scene, child_x, current_y, spacing)
                result['nodes'].extend(child_result['nodes'])
                result['connections'].extend(child_result['connections'])
                
                # Create connection from child to parent Node_C
                if child_result['nodes']:
                    child_node = child_result['nodes'][0]  # First node is the main one
                    result['connections'].append({
                        'from_node': child_node,
                        'to_node': visual_node,
                        'from_socket': 'output',  # Child's output socket
                        'to_socket': 'input'      # Parent's input socket
                    })
                    
                    # Determine how much vertical space this branch took
                    # and move current_y accordingly with extra padding
                    child_width, child_height = NodeConverter._get_node_dimensions(child_node)
                    branch_height = max(child_height, spacing)
                    
                    # If this is a complex child with its own children, add more space
                    if len(child_result['nodes']) > 1:
                        # Find the bottom-most y position of all nodes in this branch
                        max_y = branch_start_y
                        for node in child_result['nodes']:
                            node_pos = node.pos()
                            node_height = NodeConverter._get_node_dimensions(node)[1]
                            node_bottom = node_pos.y() + node_height
                            max_y = max(max_y, node_bottom)
                        
                        # Set current_y to max_y plus padding
                        current_y = max_y + 30
                    else:
                        # Simple node, just add standard spacing
                        current_y = branch_start_y + branch_height + 30
                
        # Handle child nodes - these should also connect to the Node_C
        if hasattr(node_c, 'children'):
            for child in node_c.children:
                # Store the starting y position for this branch
                branch_start_y = current_y
                
                # Process the child node
                child_result = NodeConverter.pyvnt_to_visual_nodes(child, scene, child_x, current_y, spacing)
                result['nodes'].extend(child_result['nodes'])
                result['connections'].extend(child_result['connections'])
                
                # Create connection from child to parent Node_C
                if child_result['nodes']:
                    child_node = child_result['nodes'][0]  # First node is the main one
                    result['connections'].append({
                        'from_node': child_node,
                        'to_node': visual_node,
                        'from_socket': 'output',  # Child's output socket
                        'to_socket': 'input'      # Parent's input socket
                    })
                    
                    # Determine how much vertical space this branch took
                    # and move current_y accordingly with extra padding
                    child_width, child_height = NodeConverter._get_node_dimensions(child_node)
                    branch_height = max(child_height, spacing)
                    
                    # If this is a complex child with its own children, add more space
                    if len(child_result['nodes']) > 1:
                        # Find the bottom-most y position of all nodes in this branch
                        max_y = branch_start_y
                        for node in child_result['nodes']:
                            node_pos = node.pos()
                            node_height = NodeConverter._get_node_dimensions(node)[1]
                            node_bottom = node_pos.y() + node_height
                            max_y = max(max_y, node_bottom)
                        
                        # Set current_y to max_y plus padding
                        current_y = max_y + 30
                    else:
                        # Simple node, just add standard spacing
                        current_y = branch_start_y + branch_height + 30
                
        return result
    
    @staticmethod
    def _convert_key_c(key_c, scene, x, y, spacing):
        """Convert Key_C to visual representation with connection tracking."""
        try:
            from nodes.key_c_graphical import Key_CGraphicalNode
        except ImportError:
            pass
            return {'nodes': [], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Create the main Key_C visual node
        visual_node = Key_CGraphicalNode()
        if hasattr(visual_node, 'name_edit'):
            visual_node.name_edit.setText(key_c.name if hasattr(key_c, 'name') else "unnamed")
        visual_node.setPos(x, y)
        scene.addItem(visual_node)
        result['nodes'].append(visual_node)
        
        # Handle values - these should connect to the Key_C input sockets
        current_y = y + spacing
        value_x = x - 300  # Offset values to the left with tight spacing
        
        if hasattr(key_c, 'get_items'):
            try:
                items = key_c.get_items()
                for key, value in items:
                    # Convert the value to a visual node based on type
                    if isinstance(value, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
                        value_node = NodeConverter._convert_property(value, scene, value_x, current_y)
                        if value_node:
                            result['nodes'].append(value_node)
                            # Create connection from value to key
                            result['connections'].append({
                                'from_node': value_node,
                                'to_node': visual_node,
                                'from_socket': 'output',  # Value's output socket
                                'to_socket': 'input'      # Key's input socket
                            })
                            current_y += spacing
                    elif isinstance(value, List_CP):
                        # Handle List_CP values - create List_CP node and connect
                        list_result = NodeConverter._convert_list_cp_with_children(value, scene, value_x, current_y, spacing)
                        if list_result:
                            result['nodes'].extend(list_result['nodes'])
                            result['connections'].extend(list_result['connections'])
                            
                            # Connect the main list node to the key
                            if list_result['nodes']:
                                list_node = list_result['nodes'][0]  # First node is the main list
                                result['connections'].append({
                                    'from_node': list_node,
                                    'to_node': visual_node,
                                    'from_socket': 'output',
                                    'to_socket': 'input'
                                })
                            
                            # Update current_y based on the height of the list structure
                            if len(list_result['nodes']) > 1:
                                # Find the bottom-most node in the list structure
                                max_y = current_y
                                for node in list_result['nodes']:
                                    if hasattr(node, 'pos'):
                                        node_pos = node.pos()
                                        node_height = NodeConverter._get_node_dimensions(node)[1]
                                        node_bottom = node_pos.y() + node_height
                                        max_y = max(max_y, node_bottom)
                                current_y = max_y + spacing
                            else:
                                current_y += spacing
                    elif isinstance(value, (Node_C, Key_C)):
                        # Handle nested container objects
                        nested_result = NodeConverter.pyvnt_to_visual_nodes(value, scene, value_x, current_y, spacing)
                        if nested_result:
                            result['nodes'].extend(nested_result['nodes'])
                            result['connections'].extend(nested_result['connections'])
                            
                            # Connect the main nested node to the key
                            if nested_result['nodes']:
                                nested_node = nested_result['nodes'][0]  # First node is the main one
                                result['connections'].append({
                                    'from_node': nested_node,
                                    'to_node': visual_node,
                                    'from_socket': 'output',
                                    'to_socket': 'input'
                                })
                            
                            # Update current_y based on the height of the nested structure
                            if len(nested_result['nodes']) > 1:
                                # Find the bottom-most node in the nested structure
                                max_y = current_y
                                for node in nested_result['nodes']:
                                    if hasattr(node, 'pos'):
                                        node_pos = node.pos()
                                        node_height = NodeConverter._get_node_dimensions(node)[1]
                                        node_bottom = node_pos.y() + node_height
                                        max_y = max(max_y, node_bottom)
                                current_y = max_y + spacing
                            else:
                                current_y += spacing
                    elif isinstance(value, (list, tuple)):
                        # Handle raw list/tuple values by creating individual nodes
                        for i, item in enumerate(value):
                            if isinstance(item, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
                                item_node = NodeConverter._convert_property(item, scene, value_x, current_y)
                                if item_node:
                                    result['nodes'].append(item_node)
                                    result['connections'].append({
                                        'from_node': item_node,
                                        'to_node': visual_node,
                                        'from_socket': 'output',
                                        'to_socket': 'input'
                                    })
                                    current_y += spacing
                            elif isinstance(item, (Node_C, Key_C, List_CP)):
                                item_result = NodeConverter.pyvnt_to_visual_nodes(item, scene, value_x, current_y, spacing)
                                if item_result:
                                    result['nodes'].extend(item_result['nodes'])
                                    result['connections'].extend(item_result['connections'])
                                    
                                    if item_result['nodes']:
                                        item_node = item_result['nodes'][0]
                                        result['connections'].append({
                                            'from_node': item_node,
                                            'to_node': visual_node,
                                            'from_socket': 'output',
                                            'to_socket': 'input'
                                        })
                                    
                                    # Update current_y
                                    if len(item_result['nodes']) > 1:
                                        max_y = current_y
                                        for node in item_result['nodes']:
                                            if hasattr(node, 'pos'):
                                                node_pos = node.pos()
                                                node_height = NodeConverter._get_node_dimensions(node)[1]
                                                node_bottom = node_pos.y() + node_height
                                                max_y = max(max_y, node_bottom)
                                        current_y = max_y + spacing
                                    else:
                                        current_y += spacing
                            else:
                                pass
                                current_y += spacing // 2  # Small increment for unhandled items
                    else:
                        pass
                        current_y += spacing // 2  # Small increment for unhandled items
                        
            except (AttributeError, Exception):
                pass
        
        # Also check for direct value attribute (alternative way some Keys store values)
        if hasattr(key_c, 'value') and key_c.value is not None:
            try:
                value = key_c.value
                if isinstance(value, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
                    value_node = NodeConverter._convert_property(value, scene, value_x, current_y)
                    if value_node:
                        result['nodes'].append(value_node)
                        result['connections'].append({
                            'from_node': value_node,
                            'to_node': visual_node,
                            'from_socket': 'output',
                            'to_socket': 'input'
                        })
                elif isinstance(value, (Node_C, Key_C, List_CP)):
                    value_result = NodeConverter.pyvnt_to_visual_nodes(value, scene, value_x, current_y, spacing)
                    if value_result:
                        result['nodes'].extend(value_result['nodes'])
                        result['connections'].extend(value_result['connections'])
                        
                        if value_result['nodes']:
                            value_node = value_result['nodes'][0]
                            result['connections'].append({
                                'from_node': value_node,
                                'to_node': visual_node,
                                'from_socket': 'output',
                                'to_socket': 'input'
                            })
            except (AttributeError, Exception):
                pass
        
        return result
    
    @staticmethod
    def _convert_list_cp(list_cp, scene, x, y):
        """Convert List_CP to visual representation."""
        try:
            from nodes.list_cp_graphical import List_CPGraphicalNode
        except ImportError:
            return None
        
        visual_node = List_CPGraphicalNode()
        if hasattr(visual_node, 'name_edit'):
            visual_node.name_edit.setText(list_cp.name if hasattr(list_cp, 'name') else "list")
        visual_node.setPos(x, y)
        scene.addItem(visual_node)
        return visual_node
    
    @staticmethod
    def _convert_list_cp_with_children(list_cp, scene, x, y, spacing):
        """Convert List_CP with its children to visual representation with connections."""
        try:
            from nodes.list_cp_graphical import List_CPGraphicalNode
        except ImportError:
            return {'nodes': [], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Create the main List_CP visual node
        visual_node = List_CPGraphicalNode()
        
        # Set the name from the List_CP object
        if hasattr(list_cp, 'name'):
            if hasattr(visual_node, 'name_edit'):
                visual_node.name_edit.setText(list_cp.name)
        
        # Set the isNode property
        if hasattr(list_cp, 'is_a_node') and hasattr(visual_node, 'isnode_checkbox'):
            visual_node.isnode_checkbox.setChecked(list_cp.is_a_node())
            if list_cp.is_a_node():
                # Disable elements text for node lists
                if hasattr(visual_node, 'elements_text'):
                    visual_node.elements_text.setEnabled(False)
                    visual_node.elements_text.setPlaceholderText("This list contains child nodes.")
        
        # Set elements text for non-node lists
        if hasattr(list_cp, 'get_elems') and hasattr(visual_node, 'elements_text'):
            if not (hasattr(list_cp, 'is_a_node') and list_cp.is_a_node()):
                try:
                    elems = list_cp.get_elems()
                    if elems:
                        lines = []
                        for elem in elems:
                            if elem:  # Skip empty elements
                                line_values = []
                                for val in elem:
                                    if hasattr(val, 'give_val'):
                                        line_values.append(str(val.give_val()))
                                    else:
                                        line_values.append(str(val))
                                if line_values:
                                    lines.append(' '.join(line_values))
                        if lines:
                            visual_node.elements_text.setPlainText('\n'.join(lines))
                except Exception:
                    pass
        
        visual_node.setPos(x, y)
        scene.addItem(visual_node)
        result['nodes'].append(visual_node)
        
        # Handle list values/children if they exist
        current_y = y + spacing
        child_x = x - 350  # Offset children to the left with tighter spacing
        
        # Check if List_CP has children (for boundary-style lists)
        if hasattr(list_cp, 'children') and list_cp.children:
            for child in list_cp.children:
                child_result = NodeConverter.pyvnt_to_visual_nodes(child, scene, child_x, current_y, spacing)
                if child_result:
                    result['nodes'].extend(child_result['nodes'])
                    result['connections'].extend(child_result['connections'])
                    
                    # Connect child to list
                    if child_result['nodes']:
                        child_node = child_result['nodes'][0]  # First node is the main one
                        result['connections'].append({
                            'from_node': child_node,
                            'to_node': visual_node,
                            'from_socket': 'output',
                            'to_socket': 'input'
                        })
                    
                    # Update current_y based on the height of the child structure
                    if len(child_result['nodes']) > 1:
                        # Find the bottom-most node in the child structure
                        max_y = current_y
                        for node in child_result['nodes']:
                            if hasattr(node, 'pos'):
                                node_pos = node.pos()
                                node_height = NodeConverter._get_node_dimensions(node)[1]
                                node_bottom = node_pos.y() + node_height
                                max_y = max(max_y, node_bottom)
                        current_y = max_y + spacing
                    else:
                        current_y += spacing
                
        # Check if List_CP has values (for vertices/blocks-style lists)
        if hasattr(list_cp, 'values') and list_cp.values:
            # Process each value in the list
            for i, value in enumerate(list_cp.values):
                if isinstance(value, (Node_C, Key_C, List_CP)):
                    # Create visual representation for complex values
                    value_result = NodeConverter.pyvnt_to_visual_nodes(value, scene, child_x, current_y, spacing)
                    if value_result:
                        result['nodes'].extend(value_result['nodes'])
                        result['connections'].extend(value_result['connections'])
                        
                        # Connect value to list
                        if value_result['nodes']:
                            value_node = value_result['nodes'][0]
                            result['connections'].append({
                                'from_node': value_node,
                                'to_node': visual_node,
                                'from_socket': 'output',
                                'to_socket': 'input'
                            })
                        
                        # Update current_y
                        if len(value_result['nodes']) > 1:
                            max_y = current_y
                            for node in value_result['nodes']:
                                if hasattr(node, 'pos'):
                                    node_pos = node.pos()
                                    node_height = NodeConverter._get_node_dimensions(node)[1]
                                    node_bottom = node_pos.y() + node_height
                                    max_y = max(max_y, node_bottom)
                            current_y = max_y + spacing
                        else:
                            current_y += spacing
                            
                elif isinstance(value, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
                    # Create visual representation for simple values
                    value_node = NodeConverter._convert_property(value, scene, child_x, current_y)
                    if value_node:
                        result['nodes'].append(value_node)
                        result['connections'].append({
                            'from_node': value_node,
                            'to_node': visual_node,
                            'from_socket': 'output',
                            'to_socket': 'input'
                        })
                        current_y += spacing
                else:
                    # For other value types, create a simple representation
                    pass
        
        # Check if List_CP has get_items method (alternative way to access data)
        if hasattr(list_cp, 'get_items') and not (hasattr(list_cp, 'children') and list_cp.children):
            try:
                items = list_cp.get_items()
                for key, value in items:
                    if isinstance(value, (Node_C, Key_C, List_CP)):
                        # Create visual representation for complex values
                        value_result = NodeConverter.pyvnt_to_visual_nodes(value, scene, child_x, current_y, spacing)
                        if value_result:
                            result['nodes'].extend(value_result['nodes'])
                            result['connections'].extend(value_result['connections'])
                            
                            # Connect value to list
                            if value_result['nodes']:
                                value_node = value_result['nodes'][0]
                                result['connections'].append({
                                    'from_node': value_node,
                                    'to_node': visual_node,
                                    'from_socket': 'output',
                                    'to_socket': 'input'
                                })
                            
                            current_y += spacing  # Reduced spacing for items
                            
                    elif isinstance(value, (Int_P, Flt_P, Enm_P, Str_P, Vector_P, Dim_Set_P, Tensor_P)):
                        # Create visual representation for simple values
                        value_node = NodeConverter._convert_property(value, scene, child_x, current_y)
                        if value_node:
                            result['nodes'].append(value_node)
                            result['connections'].append({
                                'from_node': value_node,
                                'to_node': visual_node,
                                'from_socket': 'output',
                                'to_socket': 'input'
                            })
                            current_y += spacing
            except (AttributeError, Exception):
                pass
        
        return result
    
    @staticmethod
    def _convert_property(prop_obj, scene, x, y):
        """Convert property objects (Int_P, Flt_P, etc.) to visual representation."""
        visual_node = None
        
        try:
            if isinstance(prop_obj, Int_P):
                from nodes.int_p_graphical import Int_PGraphicalNode
                visual_node = Int_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "int_val")
                if hasattr(visual_node, 'value_spin') and hasattr(prop_obj, 'get_value'):
                    try:
                        visual_node.value_spin.setValue(int(prop_obj.get_value()))
                    except (ValueError, AttributeError):
                        pass
                
            elif isinstance(prop_obj, Flt_P):
                from nodes.flt_p_graphical import Flt_PGraphicalNode
                visual_node = Flt_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "float_val")
                if hasattr(visual_node, 'value_spin') and hasattr(prop_obj, 'get_value'):
                    try:
                        visual_node.value_spin.setValue(float(prop_obj.get_value()))
                    except (ValueError, AttributeError):
                        pass
                
            elif isinstance(prop_obj, Enm_P):
                from nodes.enm_p_graphical import Enm_PGraphicalNode
                visual_node = Enm_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "enum_val")
                
                # Set enum options and default value
                if hasattr(visual_node, 'items_list') and hasattr(prop_obj, 'get_items'):
                    try:
                        # Clear existing items selection
                        for i in range(visual_node.items_list.count()):
                            visual_node.items_list.item(i).setSelected(False)
                        
                        # Get items from the parsed enum property
                        enum_items = prop_obj.get_items()
                        default_value = prop_obj.get_value() if hasattr(prop_obj, 'get_value') else None
                        
                        # Select the matching items in the list
                        for i in range(visual_node.items_list.count()):
                            item = visual_node.items_list.item(i)
                            if item.text() in enum_items:
                                item.setSelected(True)
                        
                        # Update default options and set the default value
                        visual_node._update_default_options()
                        if default_value and hasattr(visual_node, 'default_combo'):
                            index = visual_node.default_combo.findText(default_value)
                            if index >= 0:
                                visual_node.default_combo.setCurrentIndex(index)
                    except (AttributeError, Exception):
                        pass
                
            elif isinstance(prop_obj, Str_P):
                from nodes.str_p_graphical import Str_PGraphicalNode
                visual_node = Str_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "str_val")
                if hasattr(visual_node, 'value_edit') and hasattr(prop_obj, 'get_value'):
                    try:
                        visual_node.value_edit.setText(str(prop_obj.get_value()))
                    except AttributeError:
                        pass
                
            elif isinstance(prop_obj, Vector_P):
                from nodes.vector_p_graphical import Vector_PGraphicalNode
                visual_node = Vector_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "vector_val")
                
                # Set vector components from the parsed object
                try:
                    # Vector values are typically stored as [x, y, z]
                    if hasattr(prop_obj, 'get_value'):
                        vector_values = prop_obj.get_value()
                        if isinstance(vector_values, (list, tuple)) and len(vector_values) >= 3:
                            if hasattr(visual_node, 'x_spin'):
                                visual_node.x_spin.setValue(float(vector_values[0]))
                            if hasattr(visual_node, 'y_spin'):
                                visual_node.y_spin.setValue(float(vector_values[1]))
                            if hasattr(visual_node, 'z_spin'):
                                visual_node.z_spin.setValue(float(vector_values[2]))
                except (AttributeError, ValueError, TypeError, Exception):
                    pass
                
            elif isinstance(prop_obj, Dim_Set_P):
                from nodes.dim_set_p_graphical import Dim_Set_PGraphicalNode
                visual_node = Dim_Set_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "dim_set")
                    
                # Set dimension values from the parsed object
                try:
                    # Dimension values are typically stored as [mass, length, time, temp, moles, current, luminosity]
                    if hasattr(prop_obj, 'get_value') and hasattr(visual_node, 'dim_spins'):
                        dim_values = prop_obj.get_value()
                        if isinstance(dim_values, (list, tuple)):
                            # Update each spinbox with corresponding dimension value
                            for i, value in enumerate(dim_values):
                                if i < len(visual_node.dim_spins):
                                    visual_node.dim_spins[i].setValue(int(value))
                except (AttributeError, ValueError, TypeError, Exception):
                    pass
                    
            elif isinstance(prop_obj, Tensor_P):
                from nodes.tensor_p_graphical import Tensor_PGraphicalNode
                visual_node = Tensor_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText(prop_obj.name if hasattr(prop_obj, 'name') else "tensor")
                    
                # Set tensor values from the parsed object
                try:
                    # Tensor values are typically stored as a list of Flt_P objects
                    if hasattr(prop_obj, 'value') and hasattr(visual_node, 'component_spins'):
                        tensor_values = prop_obj.value
                        if isinstance(tensor_values, list):
                            # Update tensor size first
                            if hasattr(visual_node, 'size_spin'):
                                visual_node.size_spin.setValue(len(tensor_values))
                                visual_node._update_tensor_components()
                            
                            # Set component values
                            for i, flt_p in enumerate(tensor_values):
                                if (i < len(visual_node.component_spins) and 
                                    hasattr(flt_p, 'value') and 
                                    isinstance(flt_p.value, (int, float))):
                                    visual_node.component_spins[i].setValue(float(flt_p.value))
                except (AttributeError, ValueError, TypeError, Exception):
                    pass
                
        except ImportError:
            return None
        except Exception:
            return None
            
        if visual_node:
            visual_node.setPos(x, y)
            scene.addItem(visual_node)
            
        return visual_node
    
    @staticmethod
    def _create_connections(connections, scene):
        """Create visual connections between nodes."""
        try:
            from view.edge import Edge
        except ImportError:
            pass
            return
        
        successful_connections = 0
        failed_connections = 0
        
        # Keep track of connections to avoid duplicates
        existing_connections = set()
        
        # Filter unique connections first
        unique_connections = []
        for connection in connections:
            from_node = connection['from_node']
            to_node = connection['to_node']
            
            # Create a unique key for this connection
            connection_key = (id(from_node), id(to_node))
            
            # Skip if we already processed this connection
            if connection_key in existing_connections:
                continue
                
            existing_connections.add(connection_key)
            unique_connections.append(connection)
        
        for connection in unique_connections:
            try:
                from_node = connection['from_node']
                to_node = connection['to_node']
                
                # Skip if nodes are the same (self-connection)
                if from_node == to_node:
                    continue
                
                # Ensure both nodes are in the scene before connecting
                if from_node.scene() != scene:
                    scene.addItem(from_node)
                if to_node.scene() != scene:
                    scene.addItem(to_node)
                
                # Find appropriate sockets
                from_socket = None
                to_socket = None
                
                # Get output socket from source node
                if hasattr(from_node, 'output_sockets') and from_node.output_sockets:
                    # Find an available output socket or multi-connection socket
                    for socket in from_node.output_sockets:
                        if not hasattr(socket, 'hasEdge') or not socket.hasEdge():
                            # Available socket with no connections
                            from_socket = socket
                            break
                        elif hasattr(socket, 'multi_connection') and socket.multi_connection:
                            # Multi-connection socket can have more connections
                            from_socket = socket
                            break
                    
                    # If no perfect match found, use first multi-connection socket
                    if not from_socket:
                        for socket in from_node.output_sockets:
                            if hasattr(socket, 'multi_connection') and socket.multi_connection:
                                from_socket = socket
                                break
                    
                    # If still no socket found, use the first output socket if it exists
                    if not from_socket and from_node.output_sockets:
                        from_socket = from_node.output_sockets[0]
                        
                elif hasattr(from_node, 'sockets'):
                    # Fallback: look for sockets in general
                    output_sockets = [s for s in from_node.sockets if hasattr(s, 'socket_type') and s.socket_type == 2]  # OUTPUT_SOCKET = 2
                    for socket in output_sockets:
                        if not hasattr(socket, 'hasEdge') or not socket.hasEdge():
                            from_socket = socket
                            break
                        elif hasattr(socket, 'multi_connection') and socket.multi_connection:
                            from_socket = socket
                            break
                
                # Get input socket from target node
                if hasattr(to_node, 'input_sockets') and to_node.input_sockets:
                    # Find available input socket or multi-connection socket
                    for socket in to_node.input_sockets:
                        if not hasattr(socket, 'hasEdge') or not socket.hasEdge():
                            # Available socket with no connections
                            to_socket = socket
                            break
                        elif hasattr(socket, 'multi_connection') and socket.multi_connection:
                            # Multi-connection socket can accept more connections
                            to_socket = socket
                            break
                    
                    # If no perfect match found, use first multi-connection socket
                    if not to_socket:
                        for socket in to_node.input_sockets:
                            if hasattr(socket, 'multi_connection') and socket.multi_connection:
                                to_socket = socket
                                break
                    
                    # If still no socket found, use the first input socket if it exists
                    if not to_socket and to_node.input_sockets:
                        to_socket = to_node.input_sockets[0]
                        
                elif hasattr(to_node, 'sockets'):
                    # Fallback: look for sockets in general
                    input_sockets = [s for s in to_node.sockets if hasattr(s, 'socket_type') and s.socket_type == 1]  # INPUT_SOCKET = 1
                    for socket in input_sockets:
                        if not hasattr(socket, 'hasEdge') or not socket.hasEdge():
                            to_socket = socket
                            break
                        elif hasattr(socket, 'multi_connection') and socket.multi_connection:
                            to_socket = socket
                            break
                
                # Create the connection if both sockets are available
                if from_socket and to_socket:
                    # Check if connection is allowed
                    can_connect = True
                    if hasattr(from_socket, 'canConnectTo'):
                        can_connect = from_socket.canConnectTo(to_socket)
                    
                    if can_connect:
                        # Check if this exact socket-to-socket connection already exists
                        socket_connection_exists = False
                        for edge in from_socket.edges:
                            if edge.end_socket == to_socket:
                                socket_connection_exists = True
                                break
                        
                        if not socket_connection_exists:
                            # Ensure both nodes are properly added to the scene before creating edge
                            if from_node.scene() != scene:
                                scene.addItem(from_node)
                            if to_node.scene() != scene:
                                scene.addItem(to_node)
                            
                            # Try to use undo system if available
                            if hasattr(scene, 'undo_manager'):
                                try:
                                    from view.commands import CreateEdgeCommand
                                    command = CreateEdgeCommand(scene, from_socket, to_socket)
                                    scene.undo_manager.execute_command(command)
                                    successful_connections += 1
                                except ImportError:
                                    # Fall back to direct creation
                                    edge = Edge(from_socket, to_socket, scene)
                                    scene.addItem(edge)
                                    # Ensure event filters are installed after adding to scene
                                    edge.ensure_event_filters()
                                    successful_connections += 1
                                except Exception:
                                    failed_connections += 1
                            else:
                                # Create edge directly
                                try:
                                    edge = Edge(from_socket, to_socket, scene)
                                    scene.addItem(edge)
                                    # Ensure event filters are installed after adding to scene
                                    edge.ensure_event_filters()
                                    successful_connections += 1
                                except Exception:
                                    failed_connections += 1
                        
                        failed_connections += 1
                else:
                    failed_connections += 1
            
            except Exception:
                failed_connections += 1
                continue
        

    
    @staticmethod
    def _get_node_dimensions(node_type):
        """
        Get the dimensions of a node type to properly space nodes.
        
        Args:
            node_type: The type of node (class name or instance)
            
        Returns:
            Tuple (width, height) with the node dimensions
        """
        # Default dimensions
        default_width = 300
        default_height = 150
        
        # Get actual dimensions based on node type
        if isinstance(node_type, str):
            # Handle string class names
            if "Node_C" in node_type:
                return (320, 200)
            elif "Key_C" in node_type:
                return (320, 180)
            elif "Enm_P" in node_type:
                return (280, 250)
            elif "Int_P" in node_type or "Flt_P" in node_type:
                return (260, 120)
            elif "Vector_P" in node_type:
                return (280, 180)
            elif "Str_P" in node_type:
                return (260, 120)
            elif "Dim_Set_P" in node_type:
                return (320, 220)
            elif "List_CP" in node_type:
                return (260, 120)
        else:
            # Handle instances
            try:
                class_name = type(node_type).__name__
                return NodeConverter._get_node_dimensions(class_name)
            except:
                pass
                
        return (default_width, default_height)
    
    @staticmethod
    def _convert_node_c_recursive(node_c, scene, position_x, position_y, spacing, converted_objects):
        """
        Recursively convert Node_C and its children to visual representation.
        """
        if not node_c:
            return {'nodes': [], 'connections': []}
        
        # Check if we've already converted this object
        object_id = id(node_c)
        if object_id in converted_objects:
            return {'nodes': [converted_objects[object_id]], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Convert the Node_C itself
        node_result = NodeConverter._convert_node_c(node_c, scene, position_x, position_y, spacing)
        result['nodes'].extend(node_result['nodes'])
        result['connections'].extend(node_result['connections'])
        
        # Mark this object as converted
        if result['nodes']:
            converted_objects[object_id] = result['nodes'][0]
        
        return result
    
    @staticmethod
    def _convert_key_c_recursive(key_c, scene, position_x, position_y, spacing, converted_objects):
        """
        Recursively convert Key_C and its values to visual representation.
        """
        if not key_c:
            return {'nodes': [], 'connections': []}
        
        # Check if we've already converted this object
        object_id = id(key_c)
        if object_id in converted_objects:
            return {'nodes': [converted_objects[object_id]], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Convert the Key_C itself
        key_result = NodeConverter._convert_key_c(key_c, scene, position_x, position_y, spacing)
        result['nodes'].extend(key_result['nodes'])
        result['connections'].extend(key_result['connections'])
        
        # Mark this object as converted
        if result['nodes']:
            converted_objects[object_id] = result['nodes'][0]
        
        return result
    
    @staticmethod
    def _convert_list_cp_with_children_recursive(list_cp, scene, position_x, position_y, spacing, converted_objects):
        """
        Recursively convert List_CP and its children to visual representation.
        """
        if not list_cp:
            return {'nodes': [], 'connections': []}
        
        # Check if we've already converted this object
        object_id = id(list_cp)
        if object_id in converted_objects:
            return {'nodes': [converted_objects[object_id]], 'connections': []}
        
        result = {'nodes': [], 'connections': []}
        
        # Convert the List_CP itself
        list_result = NodeConverter._convert_list_cp_with_children(list_cp, scene, position_x, position_y, spacing)
        result['nodes'].extend(list_result['nodes'])
        result['connections'].extend(list_result['connections'])
        
        # Mark this object as converted
        if result['nodes']:
            converted_objects[object_id] = result['nodes'][0]
        
        return result
    
    @staticmethod
    def _convert_raw_value(value, scene, x, y):
        """Convert raw Python values to visual nodes when not wrapped in PyVNT objects."""
        if isinstance(value, int):
            try:
                from nodes.int_p_graphical import Int_PGraphicalNode
                visual_node = Int_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText("raw_int")
                if hasattr(visual_node, 'value_spin'):
                    visual_node.value_spin.setValue(value)
                visual_node.setPos(x, y)
                scene.addItem(visual_node)
                return visual_node
            except ImportError:
                pass
                return None
        
        elif isinstance(value, float):
            try:
                from nodes.flt_p_graphical import Flt_PGraphicalNode
                visual_node = Flt_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText("raw_float")
                if hasattr(visual_node, 'value_spin'):
                    visual_node.value_spin.setValue(value)
                visual_node.setPos(x, y)
                scene.addItem(visual_node)
                return visual_node
            except ImportError:
                pass
                return None
        
        elif isinstance(value, str):
            try:
                from nodes.str_p_graphical import Str_PGraphicalNode
                visual_node = Str_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText("raw_string")
                if hasattr(visual_node, 'value_edit'):
                    visual_node.value_edit.setText(value)
                visual_node.setPos(x, y)
                scene.addItem(visual_node)
                return visual_node
            except ImportError:
                pass
                return None
        
        elif isinstance(value, (list, tuple)) and len(value) == 3:
            # Assume it's a vector if it's a 3-element list/tuple
            try:
                from nodes.vector_p_graphical import Vector_PGraphicalNode
                visual_node = Vector_PGraphicalNode()
                if hasattr(visual_node, 'name_edit'):
                    visual_node.name_edit.setText("raw_vector")
                if hasattr(visual_node, 'x_spin'):
                    visual_node.x_spin.setValue(float(value[0]))
                if hasattr(visual_node, 'y_spin'):
                    visual_node.y_spin.setValue(float(value[1]))
                if hasattr(visual_node, 'z_spin'):
                    visual_node.z_spin.setValue(float(value[2]))
                visual_node.setPos(x, y)
                scene.addItem(visual_node)
                return visual_node
            except (ImportError, ValueError, IndexError):
                return None
        
        else:
            return None
