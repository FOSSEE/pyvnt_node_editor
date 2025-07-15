"""
Patch module to modify the behavior of the PyVNT parser.
This patch changes where PLY stores its generated files.
"""
import os
import sys

def patch_parser():
    """
    Patch the PLY parser in PyVNT to store generated files in a local directory
    instead of the package directory.
    """
    try:
        from pyvnt.Converter.PlyParser.Parser import OpenFoamParser
        
        # Create a directory for parser output if it doesn't exist
        parser_output_dir = os.path.join(os.path.dirname(__file__), 'parser')
        os.makedirs(parser_output_dir, exist_ok=True)
        
        # Override the parser's outputdir to use our local directory
        if hasattr(OpenFoamParser, 'lexer') and hasattr(OpenFoamParser.lexer, '__class__'):
            OpenFoamParser.lexer.__class__.outputdir = parser_output_dir
            
        if hasattr(OpenFoamParser, 'parser') and hasattr(OpenFoamParser.parser, '__class__'):
            OpenFoamParser.parser.__class__.outputdir = parser_output_dir
            OpenFoamParser.parser.__class__.tabmodule = 'parsetab'
            OpenFoamParser.parser.__class__.debugfile = os.path.join(parser_output_dir, 'parser.out')
        
        return True
    except (ImportError, AttributeError):
        return False
