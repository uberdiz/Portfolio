"""
Output Panels Module
"""
import tkinter as tk
from tkinter import ttk
import datetime

class OutputPanels:
    def __init__(self, parent_panedwindow, app):
        self.app = app
        self.setup_panels(parent_panedwindow)

    def setup_panels(self, parent):
        # AI Output panel
        self.ai_frame = ttk.LabelFrame(parent, text="AI Output", padding=10)
        parent.add(self.ai_frame, weight=1)
        
        self.ai_output = tk.Text(self.ai_frame, wrap="word")
        self.ai_output.pack(fill="both", expand=True)
        
        ai_scrollbar = ttk.Scrollbar(self.ai_frame, command=self.ai_output.yview)
        ai_scrollbar.pack(side="right", fill="y")
        self.ai_output.configure(yscrollcommand=ai_scrollbar.set)
        
        # Script Output panel
        self.script_frame = ttk.LabelFrame(parent, text="Script Output", padding=10)
        parent.add(self.script_frame, weight=1)
        
        self.script_output = tk.Text(self.script_frame, wrap="word")
        self.script_output.pack(fill="both", expand=True)
        
        script_scrollbar = ttk.Scrollbar(self.script_frame, command=self.script_output.yview)
        script_scrollbar.pack(side="right", fill="y")
        self.script_output.configure(yscrollcommand=script_scrollbar.set)
        
        # Clear buttons
        button_frame_ai = ttk.Frame(self.ai_frame)
        button_frame_ai.pack(fill="x", pady=(5, 0))
        ttk.Button(button_frame_ai, text="Clear", command=self.clear_ai_output).pack(side="right")
        
        button_frame_script = ttk.Frame(self.script_frame)
        button_frame_script.pack(fill="x", pady=(5, 0))
        ttk.Button(button_frame_script, text="Clear", command=self.clear_script_output).pack(side="right")

    def log_ai(self, message):
        """Log to AI output"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.ai_output.insert("end", formatted)
        self.ai_output.see("end")

    def log_script(self, message):
        """Log to script output"""
        self.script_output.insert("end", message)
        self.script_output.see("end")

    def clear_ai_output(self):
        """Clear AI output"""
        self.ai_output.delete("1.0", "end")

    def clear_script_output(self):
        """Clear script output"""
        self.script_output.delete("1.0", "end")

    def apply_theme(self, theme):
        """Apply theme to output panels"""
        self.ai_output.configure(
            bg=theme["OUTPUT_BG"],
            fg=theme["FG"],
            insertbackground=theme["CURSOR"]
        )
        self.script_output.configure(
            bg=theme["OUTPUT_BG"],
            fg=theme["FG"],
            insertbackground=theme["CURSOR"]
        )