"""
Advanced Theme Engine - Complete control over all GUI colors
"""
import tkinter as tk
from tkinter import ttk
import json

class ThemeEngine:
    def __init__(self, root):
        self.root = root
        self.styles = {}
        self.color_map = {}
    
    def define_color_roles(self):
        """Define every color role in the application"""
        return {
            # Window areas
            "window_bg": "Background color of main window",
            "frame_bg": "Background of panels and frames",
            "border_color": "Border color for frames",
            
            # Text areas
            "editor_bg": "Code editor background",
            "editor_fg": "Code editor text color",
            "editor_cursor": "Cursor color in editor",
            "editor_selection": "Selected text background",
            "editor_gutter": "Line number gutter background",
            "editor_gutter_fg": "Line number color",
            
            # Tree/List views
            "tree_bg": "Project tree background",
            "tree_fg": "Project tree text color",
            "tree_selection": "Selected item background",
            "tree_hover": "Hover color for tree items",
            
            # Buttons
            "button_bg": "Default button background",
            "button_fg": "Default button text color",
            "button_hover": "Button hover color",
            "button_active": "Active/pressed button color",
            "button_disabled": "Disabled button color",
            
            # Text widgets (non-editor)
            "text_bg": "Chat/output text background",
            "text_fg": "Chat/output text color",
            
            # Syntax highlighting
            "syntax_keyword": "Keywords (def, class, if)",
            "syntax_string": "String literals",
            "syntax_comment": "Comments",
            "syntax_function": "Function names",
            "syntax_number": "Numbers",
            "syntax_builtin": "Built-in functions",
            
            # Status bar
            "status_bg": "Status bar background",
            "status_fg": "Status bar text color",
            
            # Tabs
            "tab_bg": "Tab background",
            "tab_fg": "Tab text color",
            "tab_selected": "Selected tab color",
            "tab_hover": "Tab hover color",
            
            # Scrollbars
            "scrollbar_bg": "Scrollbar background",
            "scrollbar_fg": "Scrollbar slider color",
            "scrollbar_hover": "Scrollbar hover color",
        }
    
    def normalize_theme(self, theme_data):
        """
        Ensure a theme has all required keys, mapping legacy keys when needed.
        """
        # Start with defaults
        base = self.create_dark_theme()
        
        # Detect legacy (uppercase) themes and translate
        if any(k.isupper() for k in theme_data.keys()):
            theme_data = self._from_legacy(theme_data)
        
        # Merge provided over defaults
        merged = {**base, **theme_data}
        self.color_map = merged
        return merged
    
    def _from_legacy(self, legacy_theme):
        """Convert older theme keys to the new role names."""
        mapping = {
            "BG": "window_bg",
            "FRAME_BG": "frame_bg",
            "LABEL_BG": "frame_bg",
            "FG": "text_fg",
            "BTN": "button_bg",
            "BTN_ACTIVE": "button_active",
            "PANEL_BG": "frame_bg",
            "EDITOR_BG": "editor_bg",
            "CURSOR": "editor_cursor",
            "TREE_BG": "tree_bg",
            "TREE_FG": "tree_fg",
            "TREE_SELECT": "tree_selection",
            "OUTPUT_BG": "text_bg",
            "PROGRESS_BG": "button_active",
            "PROGRESS_FG": "button_fg",
        }
        converted = {}
        for key, value in legacy_theme.items():
            new_key = mapping.get(key, key.lower())
            converted[new_key] = value
        return converted
    
    def to_legacy_theme(self):
        """Provide legacy-style keys for existing widgets."""
        cm = self.color_map or self.create_dark_theme()
        return {
            "BG": cm.get("window_bg", "#1e1f23"),
            "FG": cm.get("text_fg", "#d6d6d6"),
            "BTN": cm.get("button_bg", "#555555"),
            "BTN_ACTIVE": cm.get("button_active", "#ff6600"),
            "PANEL_BG": cm.get("frame_bg", "#161618"),
            "EDITOR_BG": cm.get("editor_bg", "#0f1113"),
            "OUTPUT_BG": cm.get("text_bg", "#0b0c0d"),
            "CURSOR": cm.get("editor_cursor", "#ffffff"),
            "FRAME_BG": cm.get("frame_bg", "#2d2d30"),
            "LABEL_BG": cm.get("frame_bg", "#2d2d30"),
            "TREE_BG": cm.get("tree_bg", "#1e1e1e"),
            "TREE_FG": cm.get("tree_fg", "#d4d4d4"),
            "TREE_SELECT": cm.get("tree_selection", "#094771"),
            "FONT_FAMILY": "Consolas",
            "FONT_SIZE": 11,
            "PROGRESS_BG": cm.get("button_active", "#0b5c0b"),
            "PROGRESS_FG": cm.get("button_fg", "#00ff00"),
        }
    
    def apply_theme(self, theme_data):
        """Apply theme to all tkinter and ttk widgets"""
        self.color_map = theme_data
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Frame styles
        style.configure(
            "TFrame",
            background=self.get_color("frame_bg"),
            borderwidth=1,
            relief="flat"
        )
        
        # Label styles
        style.configure(
            "TLabel",
            background=self.get_color("frame_bg"),
            foreground=self.get_color("text_fg"),
            font=("Consolas", 10)
        )
        
        # Button styles with state variations
        style.configure(
            "TButton",
            background=self.get_color("button_bg"),
            foreground=self.get_color("button_fg"),
            borderwidth=1,
            relief="raised"
        )
        
        style.map(
            "TButton",
            background=[
                ('active', self.get_color("button_hover")),
                ('pressed', self.get_color("button_active")),
                ('disabled', self.get_color("button_disabled"))
            ],
            foreground=[('disabled', self.get_color("button_disabled"))]
        )
        
        # Entry styles
        style.configure(
            "TEntry",
            fieldbackground=self.get_color("editor_bg"),
            foreground=self.get_color("editor_fg"),
            insertcolor=self.get_color("editor_cursor"),
            borderwidth=1,
            relief="sunken"
        )
        
        # Notebook (Tabs) styles
        style.configure("TNotebook", background=self.get_color("tab_bg"), borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.get_color("tab_bg"),
            foreground=self.get_color("tab_fg"),
            padding=[10, 5],
            borderwidth=1
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ('selected', self.get_color("tab_selected")),
                ('active', self.get_color("tab_hover"))
            ],
            foreground=[('selected', self.get_color("text_fg"))]
        )
        
        # Scrollbar styles
        style.configure(
            "Vertical.TScrollbar",
            background=self.get_color("scrollbar_bg"),
            troughcolor=self.get_color("frame_bg"),
            bordercolor=self.get_color("border_color"),
            arrowcolor=self.get_color("text_fg"),
            width=12
        )
        
        style.configure(
            "Horizontal.TScrollbar",
            background=self.get_color("scrollbar_bg"),
            troughcolor=self.get_color("frame_bg"),
            bordercolor=self.get_color("border_color"),
            arrowcolor=self.get_color("text_fg"),
            width=12
        )
        
        # Treeview styles (Project Tree)
        style.configure(
            "Treeview",
            background=self.get_color("tree_bg"),
            foreground=self.get_color("tree_fg"),
            fieldbackground=self.get_color("tree_bg"),
            borderwidth=0
        )
        
        style.map(
            "Treeview",
            background=[('selected', self.get_color("tree_selection"))]
        )
        
        style.configure(
            "Treeview.Heading",
            background=self.get_color("frame_bg"),
            foreground=self.get_color("text_fg"),
            relief="flat"
        )
        
        # Progressbar styles
        style.configure(
            "Horizontal.TProgressbar",
            background=self.get_color("button_active"),
            troughcolor=self.get_color("frame_bg"),
            bordercolor=self.get_color("border_color"),
            lightcolor=self.get_color("button_hover"),
            darkcolor=self.get_color("button_bg")
        )
        
        # LabelFrame styles
        style.configure(
            "TLabelframe",
            background=self.get_color("frame_bg"),
            foreground=self.get_color("text_fg"),
            bordercolor=self.get_color("border_color"),
            borderwidth=2,
            relief="groove"
        )
        
        style.configure(
            "TLabelframe.Label",
            background=self.get_color("frame_bg"),
            foreground=self.get_color("text_fg")
        )
        
        # Apply to root window
        self.root.configure(bg=self.get_color("window_bg"))
        
        # Update all existing widgets (placeholder)
        self.update_all_widgets()
    
    def get_color(self, role, default="#000000"):
        """Get color for a role with fallback"""
        return self.color_map.get(role, default)
    
    def update_all_widgets(self):
        """Update all existing widgets with new theme"""
        # Widgets will update when explicitly themed by components.
        pass
    
    def create_theme_from_preset(self, preset_name):
        """Create a complete theme from preset name"""
        presets = {
            "Dark": self.create_dark_theme(),
            "Light": self.create_light_theme(),
            "Blue": self.create_blue_theme(),
            "Green": self.create_green_theme(),
            "Solarized": self.create_solarized_theme(),
        }
        return presets.get(preset_name, self.create_dark_theme())
    
    def create_dark_theme(self):
        """Dark theme matching your screenshot"""
        return {
            "window_bg": "#1e1f23",
            "frame_bg": "#161618",
            "border_color": "#2d2d30",
            
            "editor_bg": "#0f1113",
            "editor_fg": "#d6d6d6",
            "editor_cursor": "#ffffff",
            "editor_selection": "#094771",
            "editor_gutter": "#1e1e1e",
            "editor_gutter_fg": "#858585",
            
            "tree_bg": "#1e1e1e",
            "tree_fg": "#d4d4d4",
            "tree_selection": "#094771",
            "tree_hover": "#2a2d2e",
            
            "button_bg": "#555555",
            "button_fg": "#d6d6d6",
            "button_hover": "#666666",
            "button_active": "#ff6600",
            "button_disabled": "#333333",
            
            "text_bg": "#161618",
            "text_fg": "#d6d6d6",
            
            "syntax_keyword": "#ff6600",
            "syntax_string": "#6aab73",
            "syntax_comment": "#6a9955",
            "syntax_function": "#dcdcaa",
            "syntax_number": "#b5cea8",
            "syntax_builtin": "#569cd6",
            
            "status_bg": "#1e1f23",
            "status_fg": "#d6d6d6",
            
            "tab_bg": "#2d2d30",
            "tab_fg": "#d6d6d6",
            "tab_selected": "#1e1f23",
            "tab_hover": "#3d3d40",
            
            "scrollbar_bg": "#555555",
            "scrollbar_fg": "#888888",
            "scrollbar_hover": "#ff6600",
        }
    
    def create_light_theme(self):
        """Light theme variant"""
        return {
            "window_bg": "#f3f3f3",
            "frame_bg": "#ffffff",
            "border_color": "#e0e0e0",
            
            "editor_bg": "#ffffff",
            "editor_fg": "#1e1e1e",
            "editor_cursor": "#000000",
            "editor_selection": "#cce5ff",
            "editor_gutter": "#f3f3f3",
            "editor_gutter_fg": "#6b6b6b",
            
            "tree_bg": "#ffffff",
            "tree_fg": "#1e1e1e",
            "tree_selection": "#cce5ff",
            "tree_hover": "#e6e6e6",
            
            "button_bg": "#e0e0e0",
            "button_fg": "#1e1e1e",
            "button_hover": "#d5d5d5",
            "button_active": "#0078d4",
            "button_disabled": "#b0b0b0",
            
            "text_bg": "#ffffff",
            "text_fg": "#1e1e1e",
            
            "syntax_keyword": "#0078d4",
            "syntax_string": "#0b8a00",
            "syntax_comment": "#6a9955",
            "syntax_function": "#d17b00",
            "syntax_number": "#098658",
            "syntax_builtin": "#005fb8",
            
            "status_bg": "#f3f3f3",
            "status_fg": "#1e1e1e",
            
            "tab_bg": "#e0e0e0",
            "tab_fg": "#1e1e1e",
            "tab_selected": "#ffffff",
            "tab_hover": "#d5d5d5",
            
            "scrollbar_bg": "#d0d0d0",
            "scrollbar_fg": "#a0a0a0",
            "scrollbar_hover": "#0078d4",
        }
    
    def create_blue_theme(self):
        """Blue theme variant"""
        return {
            "window_bg": "#1a1d29",
            "frame_bg": "#161822",
            "border_color": "#252936",
            
            "editor_bg": "#0d1017",
            "editor_fg": "#e1e1e6",
            "editor_cursor": "#ffffff",
            "editor_selection": "#2d5399",
            "editor_gutter": "#1e2029",
            "editor_gutter_fg": "#8795b5",
            
            "tree_bg": "#1e2029",
            "tree_fg": "#c8c8d0",
            "tree_selection": "#2d5399",
            "tree_hover": "#242736",
            
            "button_bg": "#3a3f5b",
            "button_fg": "#e1e1e6",
            "button_hover": "#4a5173",
            "button_active": "#5a86ff",
            "button_disabled": "#2b2f44",
            
            "text_bg": "#161822",
            "text_fg": "#e1e1e6",
            
            "syntax_keyword": "#5a86ff",
            "syntax_string": "#6aab73",
            "syntax_comment": "#6a9955",
            "syntax_function": "#dcdcaa",
            "syntax_number": "#b5cea8",
            "syntax_builtin": "#4fc3f7",
            
            "status_bg": "#1a1d29",
            "status_fg": "#e1e1e6",
            
            "tab_bg": "#252936",
            "tab_fg": "#e1e1e6",
            "tab_selected": "#1a1d29",
            "tab_hover": "#2f3446",
            
            "scrollbar_bg": "#3a3f5b",
            "scrollbar_fg": "#5a86ff",
            "scrollbar_hover": "#5a86ff",
        }
    
    def create_green_theme(self):
        """Green theme variant"""
        return {
            "window_bg": "#1e231e",
            "frame_bg": "#161a16",
            "border_color": "#2d332d",
            
            "editor_bg": "#0f130f",
            "editor_fg": "#d6e6d6",
            "editor_cursor": "#ffffff",
            "editor_selection": "#2d5a2d",
            "editor_gutter": "#1e231e",
            "editor_gutter_fg": "#9ab59a",
            
            "tree_bg": "#1e231e",
            "tree_fg": "#c8d6c8",
            "tree_selection": "#2d5a2d",
            "tree_hover": "#243024",
            
            "button_bg": "#3a4a3a",
            "button_fg": "#d6e6d6",
            "button_hover": "#455645",
            "button_active": "#4caf50",
            "button_disabled": "#2b332b",
            
            "text_bg": "#161a16",
            "text_fg": "#d6e6d6",
            
            "syntax_keyword": "#4caf50",
            "syntax_string": "#6aab73",
            "syntax_comment": "#6a9955",
            "syntax_function": "#dcdcaa",
            "syntax_number": "#b5cea8",
            "syntax_builtin": "#69f0ae",
            
            "status_bg": "#1e231e",
            "status_fg": "#d6e6d6",
            
            "tab_bg": "#2d332d",
            "tab_fg": "#d6e6d6",
            "tab_selected": "#1e231e",
            "tab_hover": "#364036",
            
            "scrollbar_bg": "#3a4a3a",
            "scrollbar_fg": "#69f0ae",
            "scrollbar_hover": "#4caf50",
        }
    
    def create_solarized_theme(self):
        """Solarized-like variant"""
        return {
            "window_bg": "#002b36",
            "frame_bg": "#073642",
            "border_color": "#586e75",
            
            "editor_bg": "#002b36",
            "editor_fg": "#93a1a1",
            "editor_cursor": "#93a1a1",
            "editor_selection": "#073642",
            "editor_gutter": "#073642",
            "editor_gutter_fg": "#657b83",
            
            "tree_bg": "#073642",
            "tree_fg": "#93a1a1",
            "tree_selection": "#586e75",
            "tree_hover": "#0b3a45",
            
            "button_bg": "#586e75",
            "button_fg": "#fdf6e3",
            "button_hover": "#657b83",
            "button_active": "#b58900",
            "button_disabled": "#3c4c52",
            
            "text_bg": "#073642",
            "text_fg": "#93a1a1",
            
            "syntax_keyword": "#b58900",
            "syntax_string": "#2aa198",
            "syntax_comment": "#586e75",
            "syntax_function": "#cb4b16",
            "syntax_number": "#6c71c4",
            "syntax_builtin": "#268bd2",
            
            "status_bg": "#002b36",
            "status_fg": "#93a1a1",
            
            "tab_bg": "#073642",
            "tab_fg": "#93a1a1",
            "tab_selected": "#002b36",
            "tab_hover": "#0b3a45",
            
            "scrollbar_bg": "#586e75",
            "scrollbar_fg": "#93a1a1",
            "scrollbar_hover": "#b58900",
        }



