"""
Theme Management Utilities
"""
import json
import os

class ThemeManager:
    def __init__(self, settings_path=None):
        self.settings_path = settings_path or os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")
        self.default_themes = self.load_default_themes()
        
    def load_default_themes(self):
        """Load default theme presets"""
        return {
            "Dark": {
                "BG": "#1e1f23",
                "FG": "#d6d6d6",
                "BTN": "#555555",
                "BTN_ACTIVE": "#ff6600",
                "PANEL_BG": "#161618",
                "EDITOR_BG": "#0f1113",
                "OUTPUT_BG": "#0b0c0d",
                "CURSOR": "#ffffff",
                "FRAME_BG": "#2d2d30",
                "LABEL_BG": "#2d2d30",
                "TREE_BG": "#1e1e1e",
                "TREE_FG": "#d4d4d4",
                "TREE_SELECT": "#094771",
                "FONT_FAMILY": "Consolas",
                "FONT_SIZE": 11,
                "PROGRESS_BG": "#0b5c0b",
                "PROGRESS_FG": "#00ff00"
            },
            "Light": {
                "BG": "#f3f3f3",
                "FG": "#1e1e1e",
                "BTN": "#e0e0e0",
                "BTN_ACTIVE": "#0078d4",
                "PANEL_BG": "#ffffff",
                "EDITOR_BG": "#ffffff",
                "OUTPUT_BG": "#f0f0f0",
                "CURSOR": "#000000",
                "FRAME_BG": "#e1e1e1",
                "LABEL_BG": "#e1e1e1",
                "TREE_BG": "#ffffff",
                "TREE_FG": "#1e1e1e",
                "TREE_SELECT": "#cce5ff",
                "FONT_FAMILY": "Consolas",
                "FONT_SIZE": 11,
                "PROGRESS_BG": "#d4edda",
                "PROGRESS_FG": "#155724"
            },
            "Blue": {
                "BG": "#1a1d29",
                "FG": "#e1e1e6",
                "BTN": "#3a3f5b",
                "BTN_ACTIVE": "#5a86ff",
                "PANEL_BG": "#161822",
                "EDITOR_BG": "#0d1017",
                "OUTPUT_BG": "#0a0c14",
                "CURSOR": "#ffffff",
                "FRAME_BG": "#252936",
                "LABEL_BG": "#252936",
                "TREE_BG": "#1e2029",
                "TREE_FG": "#c8c8d0",
                "TREE_SELECT": "#2d5399",
                "FONT_FAMILY": "Consolas",
                "FONT_SIZE": 11,
                "PROGRESS_BG": "#1a3c6e",
                "PROGRESS_FG": "#4fc3f7"
            },
            "Green": {
                "BG": "#1e231e",
                "FG": "#d6e6d6",
                "BTN": "#3a4a3a",
                "BTN_ACTIVE": "#4caf50",
                "PANEL_BG": "#161a16",
                "EDITOR_BG": "#0f130f",
                "OUTPUT_BG": "#0b0f0b",
                "CURSOR": "#ffffff",
                "FRAME_BG": "#2d332d",
                "LABEL_BG": "#2d332d",
                "TREE_BG": "#1e231e",
                "TREE_FG": "#c8d6c8",
                "TREE_SELECT": "#2d5a2d",
                "FONT_FAMILY": "Consolas",
                "FONT_SIZE": 11,
                "PROGRESS_BG": "#1b5e20",
                "PROGRESS_FG": "#69f0ae"
            }
        }
    
    def get_theme(self, theme_name):
        """Get theme by name"""
        return self.default_themes.get(theme_name, self.default_themes["Dark"])
    
    def save_custom_theme(self, theme_name, theme_data):
        """Save custom theme"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            if 'custom_themes' not in settings:
                settings['custom_themes'] = {}
            
            settings['custom_themes'][theme_name] = theme_data
            
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return True
        except:
            return False
    
    def load_custom_themes(self):
        """Load custom themes"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                return settings.get('custom_themes', {})
        except:
            return {}
    
    def delete_custom_theme(self, theme_name):
        """Delete custom theme"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                
                if 'custom_themes' in settings and theme_name in settings['custom_themes']:
                    del settings['custom_themes'][theme_name]
                    
                    with open(self.settings_path, 'w') as f:
                        json.dump(settings, f, indent=2)
                    
                    return True
        except:
            pass
        return False
    
    def export_theme(self, theme_data, file_path):
        """Export theme to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(theme_data, f, indent=2)
            return True
        except:
            return False
    
    def import_theme(self, file_path):
        """Import theme from file"""
        try:
            with open(file_path, 'r') as f:
                theme_data = json.load(f)
            return theme_data
        except:
            return None