"""
Settings Window Module
"""
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json

class SettingsWindow:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.settings = app.settings.copy()
        
    def show(self):
        """Show the settings window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.geometry("700x750")
        self.window.configure(bg=self.app.theme["BG"])
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_ai_tab(notebook)
        self.create_github_tab(notebook)
        self.create_theme_tab(notebook)
        self.create_advanced_tab(notebook)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side="left", padx=5)
    
    def create_ai_tab(self, notebook):
        """Create AI settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="AI")
        
        # API Provider
        ttk.Label(frame, text="API Provider:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.provider_var = tk.StringVar(value=self.settings.get("api_provider", "ollama"))
        providers = ["ollama", "huggingface", "openai", "anthropic"]
        ttk.Combobox(frame, textvariable=self.provider_var, values=providers, state="readonly").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # API URL
        ttk.Label(frame, text="API URL:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.api_url_var = tk.StringVar(value=self.settings.get("api_url", "http://localhost:11434/api/generate"))
        ttk.Entry(frame, textvariable=self.api_url_var, width=50).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Model
        ttk.Label(frame, text="Model:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_var = tk.StringVar(value=self.settings.get("model", "tinyllama:1.1b"))
        ttk.Entry(frame, textvariable=self.model_var, width=30).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Hugging Face Token (only for huggingface provider)
        ttk.Label(frame, text="Hugging Face Token:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.hf_token_var = tk.StringVar(value=self.settings.get("huggingface_token", ""))
        hf_entry = ttk.Entry(frame, textvariable=self.hf_token_var, width=40, show="*")
        hf_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        def toggle_hf_token():
            hf_entry.config(show="" if hf_entry.cget('show') == '*' else '*')
        
        ttk.Button(frame, text="Show/Hide", command=toggle_hf_token).grid(row=3, column=2, padx=5)
        
        # Optimizations
        ttk.Label(frame, text="Prompt Optimizations:").grid(row=4, column=0, sticky="w", padx=10, pady=10)
        
        self.max_files_var = tk.IntVar(value=self.settings.get("max_files", 5))
        ttk.Checkbutton(frame, text="Limit files sent to AI", variable=self.max_files_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=2)
        
        self.summarize_files_var = tk.BooleanVar(value=self.settings.get("summarize_files", True))
        ttk.Checkbutton(frame, text="Summarize large files", variable=self.summarize_files_var).grid(row=6, column=0, columnspan=2, sticky="w", padx=20, pady=2)
    
    def create_github_tab(self, notebook):
        """Create GitHub settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="GitHub")
        
        ttk.Label(frame, text="GitHub Token:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.github_token_var = tk.StringVar(value=self.settings.get("github_token", ""))
        github_entry = ttk.Entry(frame, textvariable=self.github_token_var, width=40, show="*")
        github_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        def toggle_github_token():
            github_entry.config(show="" if github_entry.cget('show') == '*' else '*')
        
        ttk.Button(frame, text="Show/Hide", command=toggle_github_token).grid(row=0, column=2, padx=5)
        
        ttk.Label(frame, text="Default Repo Name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.repo_name_var = tk.StringVar(value=self.settings.get("default_repo_name", ""))
        ttk.Entry(frame, textvariable=self.repo_name_var, width=30).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.private_repo_var = tk.BooleanVar(value=self.settings.get("private_repo", False))
        ttk.Checkbutton(frame, text="Create private repositories by default", variable=self.private_repo_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
    
    def create_theme_tab(self, notebook):
        """Create theme settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Theme")
        
        # Theme presets
        ttk.Label(frame, text="Theme Preset:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.theme_preset_var = tk.StringVar(value="Dark")
        presets = ["Dark", "Light", "Blue", "Green", "Purple"]
        ttk.Combobox(frame, textvariable=self.theme_preset_var, values=presets, state="readonly").grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text="Apply Preset", command=self.apply_theme_preset).grid(row=0, column=2, padx=5)
        
        # Color pickers
        colors = [
            ("Background", "BG"),
            ("Text", "FG"),
            ("Editor Background", "EDITOR_BG"),
            ("Button", "BTN"),
            ("Active Button", "BTN_ACTIVE"),
            ("Cursor", "CURSOR")
        ]
        
        self.color_vars = {}
        for i, (label, key) in enumerate(colors):
            ttk.Label(frame, text=f"{label}:").grid(row=i+2, column=0, sticky="w", padx=10, pady=5)
            
            color_var = tk.StringVar(value=self.app.theme.get(key, "#000000"))
            self.color_vars[key] = color_var
            
            color_frame = tk.Frame(frame, bg=color_var.get(), width=30, height=20, relief="solid")
            color_frame.grid(row=i+2, column=1, padx=10, pady=5, sticky="w")
            
            ttk.Button(frame, text="Pick", command=lambda k=key, f=color_frame: self.pick_color(k, f)).grid(row=i+2, column=2, padx=5)
    
    def create_advanced_tab(self, notebook):
        """Create advanced settings tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Advanced")
        
        # Timeout settings
        ttk.Label(frame, text="AI Timeout (seconds):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.timeout_var = tk.IntVar(value=self.settings.get("timeout", 120))
        ttk.Spinbox(frame, from_=30, to=600, textvariable=self.timeout_var, width=10).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Max response length
        ttk.Label(frame, text="Max Response Length:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.max_response_var = tk.IntVar(value=self.settings.get("max_response", 4000))
        ttk.Spinbox(frame, from_=500, to=20000, textvariable=self.max_response_var, width=10).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Auto-save
        self.autosave_var = tk.BooleanVar(value=self.settings.get("autosave", True))
        ttk.Checkbutton(frame, text="Auto-save before running", variable=self.autosave_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Clear logs on run
        self.clear_logs_var = tk.BooleanVar(value=self.settings.get("clear_logs", False))
        ttk.Checkbutton(frame, text="Clear logs before running", variable=self.clear_logs_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)
    
    def pick_color(self, key, frame):
        """Pick a color for theme element"""
        color = colorchooser.askcolor(title=f"Choose {key} color", initialcolor=frame.cget("bg"))[1]
        if color:
            frame.config(bg=color)
            self.color_vars[key].set(color)
    
    def apply_theme_preset(self):
        """Apply theme preset"""
        preset = self.theme_preset_var.get()
        presets = {
            "Dark": {
                "BG": "#1e1f23", "FG": "#d6d6d6", "EDITOR_BG": "#0f1113",
                "BTN": "#555555", "BTN_ACTIVE": "#ff6600", "CURSOR": "#ffffff"
            },
            "Light": {
                "BG": "#f3f3f3", "FG": "#1e1e1e", "EDITOR_BG": "#ffffff",
                "BTN": "#e0e0e0", "BTN_ACTIVE": "#0078d4", "CURSOR": "#000000"
            },
            "Blue": {
                "BG": "#1a1d29", "FG": "#e1e1e6", "EDITOR_BG": "#0d1017",
                "BTN": "#3a3f5b", "BTN_ACTIVE": "#5a86ff", "CURSOR": "#ffffff"
            }
        }
        
        if preset in presets:
            for key, value in presets[preset].items():
                if key in self.color_vars:
                    self.color_vars[key].set(value)
            messagebox.showinfo("Theme Applied", f"{preset} theme applied to preview")
    
    def test_connection(self):
        """Test AI connection"""
        from core.llm import test_llm_connection
        
        api_provider = self.provider_var.get()
        api_url = self.api_url_var.get()
        model = self.model_var.get()
        token = self.hf_token_var.get() if api_provider == "huggingface" else None
        
        if not api_url or not model:
            messagebox.showerror("Error", "Please fill in API URL and Model")
            return
        
        try:
            success, message = test_llm_connection(api_provider, api_url, model, token)
            if success:
                messagebox.showinfo("Success", f"Connection successful!\n\nResponse: {message[:200]}...")
            else:
                messagebox.showerror("Error", f"Connection failed:\n\n{message}")
        except Exception as e:
            messagebox.showerror("Error", f"Test failed: {str(e)}")
    
    def save_settings(self):
        """Save all settings"""
        # AI Settings
        self.settings.update({
            "api_provider": self.provider_var.get(),
            "api_url": self.api_url_var.get(),
            "model": self.model_var.get(),
            "huggingface_token": self.hf_token_var.get(),
            "max_files": self.max_files_var.get(),
            "summarize_files": self.summarize_files_var.get()
        })
        
        # GitHub Settings
        self.settings.update({
            "github_token": self.github_token_var.get(),
            "default_repo_name": self.repo_name_var.get(),
            "private_repo": self.private_repo_var.get()
        })
        
        # Theme Settings
        theme = {}
        for key, var in self.color_vars.items():
            theme[key] = var.get()
        self.settings["theme"] = theme
        
        # Advanced Settings
        self.settings.update({
            "timeout": self.timeout_var.get(),
            "max_response": self.max_response_var.get(),
            "autosave": self.autosave_var.get(),
            "clear_logs": self.clear_logs_var.get()
        })
        
        # Update app
        self.app.save_settings(self.settings)
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
        self.window.destroy()
    
    def on_close(self):
        """Handle window close"""
        if messagebox.askyesno("Save Settings", "Do you want to save changes before closing?"):
            self.save_settings()
        else:
            self.window.destroy()