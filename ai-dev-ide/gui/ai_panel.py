"""
AI Panel Module
"""
import tkinter as tk
from tkinter import ttk
import threading

class AIPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_panel()

    def setup_panel(self):
        # Chat display
        chat_frame = ttk.LabelFrame(self, text="AI Chat", padding=10)
        chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Chat text
        self.chat_text = tk.Text(chat_frame, height=15, wrap="word")
        self.chat_text.pack(fill="both", expand=True)
        
        # Chat scrollbar
        chat_scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        chat_scrollbar.pack(side="right", fill="y")
        self.chat_text.configure(yscrollcommand=chat_scrollbar.set)
        
        # Chat input
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=(5, 0))
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.chat_input.bind("<Return>", self.send_chat_message)
        
        ttk.Button(input_frame, text="Send", command=self.send_chat_message).pack(side="right")
        
        # Suggested changes frame
        changes_frame = ttk.LabelFrame(self, text="AI Suggestions", padding=10)
        changes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.changes_text = tk.Text(changes_frame, height=10, wrap="word")
        self.changes_text.pack(fill="both", expand=True)
        
        changes_scrollbar = ttk.Scrollbar(changes_frame, command=self.changes_text.yview)
        changes_scrollbar.pack(side="right", fill="y")
        self.changes_text.configure(yscrollcommand=changes_scrollbar.set)
        
        # Apply changes button
        button_frame = ttk.Frame(changes_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(button_frame, text="Apply Changes", command=self.app.apply_ai_changes).pack(side="left")
        ttk.Button(button_frame, text="Clear", command=self.clear_suggestions).pack(side="right")

    def send_chat_message(self, event=None):
        """Send chat message to AI"""
        message = self.chat_input.get().strip()
        if not message:
            return
        
        self.chat_input.delete(0, "end")
        self.add_chat_message("User", message)
        
        # Process in background
        threading.Thread(target=self.process_ai_response, args=(message,), daemon=True).start()

    def process_ai_response(self, message):
        """Process AI response"""
        self.app.update_progress("AI thinking...", True)
        
        try:
            # Use LLM to generate response
            from core.llm import call_llm
            api_url = self.app.settings.get("api_url", "")
            model = self.app.settings.get("model", "")
            
            prompt = f"""User message: {message}
            
Current project: {self.app.project_path if self.app.project_path else 'No project open'}
            
Provide helpful, concise response about coding, project structure, or debugging."""
            
            response = call_llm(prompt, api_url, model)
            self.add_chat_message("AI", response)
            
        except Exception as e:
            self.add_chat_message("AI", f"Error: {str(e)}")
        finally:
            self.app.clear_progress()

    def add_chat_message(self, sender, message):
        """Add message to chat"""
        self.chat_text.insert("end", f"\n{sender}: {message}\n")
        self.chat_text.see("end")

    def display_suggested_changes(self, changes):
        """Display AI suggested changes"""
        self.changes_text.delete("1.0", "end")
        
        if isinstance(changes, dict):
            for filename, content in changes.items():
                self.changes_text.insert("end", f"File: {filename}\n")
                self.changes_text.insert("end", "-" * 40 + "\n")
                # Show preview (first 500 chars)
                preview = content[:500] + ("..." if len(content) > 500 else "")
                self.changes_text.insert("end", preview + "\n\n")
        else:
            self.changes_text.insert("end", str(changes))

    def clear_suggestions(self):
        """Clear suggestions"""
        self.changes_text.delete("1.0", "end")

    def get_selected_files(self):
        """Get files selected for fixing"""
        # In a full implementation, this would get from checkboxes
        return None

    def apply_theme(self, theme):
        """Apply theme to panel"""
        self.chat_text.configure(
            bg=theme["PANEL_BG"],
            fg=theme["FG"],
            insertbackground=theme["CURSOR"]
        )
        self.changes_text.configure(
            bg=theme["PANEL_BG"],
            fg=theme["FG"],
            insertbackground=theme["CURSOR"]
        )