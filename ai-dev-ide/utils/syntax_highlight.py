"""
Syntax Highlighting Utilities
"""
import tkinter as tk
import re

class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
        
    def setup_tags(self):
        """Setup syntax highlighting tags"""
        # Python
        self.text_widget.tag_configure("keyword", foreground="#ff6600", font=("Consolas", 11, "bold"))
        self.text_widget.tag_configure("string", foreground="#6aab73")
        self.text_widget.tag_configure("comment", foreground="#6a9955", font=("Consolas", 11, "italic"))
        self.text_widget.tag_configure("function", foreground="#dcdcaa")
        self.text_widget.tag_configure("number", foreground="#b5cea8")
        self.text_widget.tag_configure("builtin", foreground="#569cd6")
        
        # JSON
        self.text_widget.tag_configure("json_key", foreground="#9cdcfe")
        self.text_widget.tag_configure("json_string", foreground="#ce9178")
        self.text_widget.tag_configure("json_number", foreground="#b5cea8")
        self.text_widget.tag_configure("json_boolean", foreground="#569cd6")
        
        # Markdown
        self.text_widget.tag_configure("md_header", foreground="#569cd6", font=("Consolas", 11, "bold"))
        self.text_widget.tag_configure("md_bold", foreground="#dcdcaa", font=("Consolas", 11, "bold"))
        self.text_widget.tag_configure("md_italic", foreground="#dcdcaa", font=("Consolas", 11, "italic"))
        self.text_widget.tag_configure("md_code", foreground="#ce9178", background="#1e1e1e")
        
    def highlight_python(self, event=None):
        """Highlight Python syntax"""
        # Remove previous tags
        for tag in ["keyword", "string", "comment", "function", "number", "builtin"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
        
        # Get text
        text = self.text_widget.get("1.0", "end-1c")
        
        # Keywords
        python_keywords = [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
            'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
            'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        
        # Find and tag keywords
        for keyword in python_keywords:
            pattern = r'\b' + keyword + r'\b'
            self.highlight_pattern(pattern, "keyword")
        
        # Strings
        self.highlight_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "string")
        self.highlight_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "string")
        self.highlight_pattern(r'"""[^"]*"""', "string", regex_flags=re.DOTALL)
        self.highlight_pattern(r"'''[^']*'''", "string", regex_flags=re.DOTALL)
        
        # Comments
        self.highlight_pattern(r'#.*$', "comment", regex_flags=re.MULTILINE)
        
        # Functions
        self.highlight_pattern(r'\bdef\s+(\w+)', "function")
        
        # Numbers
        self.highlight_pattern(r'\b\d+\.?\d*\b', "number")
        
        # Builtins
        builtins = ['print', 'len', 'range', 'list', 'dict', 'set', 'str', 'int', 'float']
        for builtin in builtins:
            pattern = r'\b' + builtin + r'\b'
            self.highlight_pattern(pattern, "builtin")
    
    def highlight_json(self, event=None):
        """Highlight JSON syntax"""
        # Remove previous tags
        for tag in ["json_key", "json_string", "json_number", "json_boolean"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
        
        # Keys
        self.highlight_pattern(r'"([^"]+)"\s*:', "json_key")
        
        # Strings (values)
        self.highlight_pattern(r':\s*"([^"]+)"', "json_string")
        
        # Numbers
        self.highlight_pattern(r':\s*(\d+\.?\d*)', "json_number")
        
        # Booleans and null
        self.highlight_pattern(r':\s*(true|false|null)', "json_boolean", regex_flags=re.IGNORECASE)
    
    def highlight_markdown(self, event=None):
        """Highlight Markdown syntax"""
        # Remove previous tags
        for tag in ["md_header", "md_bold", "md_italic", "md_code"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
        
        # Headers
        self.highlight_pattern(r'^#+.+$', "md_header", regex_flags=re.MULTILINE)
        
        # Bold
        self.highlight_pattern(r'\*\*.+?\*\*', "md_bold")
        self.highlight_pattern(r'__.+?__', "md_bold")
        
        # Italic
        self.highlight_pattern(r'\*.+?\*', "md_italic")
        self.highlight_pattern(r'_.+?_', "md_italic")
        
        # Code
        self.highlight_pattern(r'`.+?`', "md_code")
        self.highlight_pattern(r'```[\s\S]*?```', "md_code")
    
    def highlight_pattern(self, pattern, tag, regex_flags=0):
        """Highlight a regex pattern with a tag"""
        text = self.text_widget.get("1.0", "end-1c")
        matches = re.finditer(pattern, text, regex_flags)
        
        for match in matches:
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add(tag, start, end)
    
    def auto_highlight(self, filename):
        """Auto-detect language and highlight"""
        if filename.endswith('.py'):
            self.highlight_python()
        elif filename.endswith('.json'):
            self.highlight_json()
        elif filename.endswith('.md'):
            self.highlight_markdown()