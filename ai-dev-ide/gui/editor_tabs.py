"""
Editor Tabs Module
"""
import os
import re
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import threading

class EditorTabs(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_file = None
        self.open_files = {}  # filename -> (tab_id, text_widget)
        self.setup_notebook()

    def setup_notebook(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Bind events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.bind("<Button-3>", self.show_tab_menu)
        
        # Tab context menu
        self.tab_menu = tk.Menu(self, tearoff=0)
        self.tab_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.tab_menu.add_command(label="Save Tab", command=self.save_current_file)
        self.tab_menu.add_command(label="Close All", command=self.close_all_tabs)

    def open_file(self, file_path):
        """Open a file in new tab"""
        # Check if already open
        for filename, (tab_id, _) in self.open_files.items():
            if filename == file_path:
                self.notebook.select(tab_id)
                return
        
        # Create new tab
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True)
        
        # Text widget with scrollbars
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(text_frame)
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Text widget
        text_widget = tk.Text(text_frame, 
                             wrap="none",
                             undo=True,
                             yscrollcommand=y_scrollbar.set,
                             xscrollcommand=x_scrollbar.set,
                             font=(self.app.theme["FONT_FAMILY"], self.app.theme["FONT_SIZE"]))
        text_widget.pack(side="left", fill="both", expand=True)
        
        y_scrollbar.config(command=text_widget.yview)
        x_scrollbar.config(command=text_widget.xview)
        
        # Load file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert("1.0", content)
        except Exception as e:
            text_widget.insert("1.0", f"# Error reading file: {e}")
        
        # Apply basic theme colors immediately
        text_widget.configure(
            bg=self.app.theme["EDITOR_BG"],
            fg=self.app.theme["FG"],
            insertbackground=self.app.theme["CURSOR"],
            selectbackground=self.app.theme["TREE_SELECT"]
        )
        
        # Add to notebook
        tab_id = self.notebook.add(frame, text=os.path.basename(file_path))
        self.open_files[file_path] = (tab_id, text_widget)
        self.notebook.select(tab_id)
        
        # Apply syntax highlighting
        self.apply_basic_syntax_highlighting(file_path, text_widget)

    def apply_basic_syntax_highlighting(self, file_path, text_widget):
        """Apply basic syntax highlighting"""
        # Basic Python highlighting
        if file_path.endswith('.py'):
            text_widget.tag_configure("keyword", foreground="#ff6600")
            text_widget.tag_configure("string", foreground="#6aab73")
            text_widget.tag_configure("comment", foreground="#6a9955")
            text_widget.tag_configure("function", foreground="#dcdcaa")
            
            # Simple keyword matching
            keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 
                       'import', 'from', 'return', 'pass', 'break', 'continue', 'with', 'as',
                       'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is']
            
            content = text_widget.get("1.0", "end-1c")
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Comments
                if '#' in line:
                    comment_start = line.find('#')
                    text_widget.tag_add("comment", f"{i+1}.{comment_start}", f"{i+1}.end")
                
                # Keywords
                for keyword in keywords:
                    for match in re.finditer(r'\b' + keyword + r'\b', line):
                        start = match.start()
                        end = match.end()
                        text_widget.tag_add("keyword", f"{i+1}.{start}", f"{i+1}.{end}")
                
                # Strings
                for match in re.finditer(r'["\'](?:[^"\\]|\\.)*["\']', line):
                    start = match.start()
                    end = match.end()
                    text_widget.tag_add("string", f"{i+1}.{start}", f"{i+1}.{end}")
            
            # Could add more sophisticated highlighting here

    def on_tab_changed(self, event):
        """Handle tab change"""
        tab_id = self.notebook.select()
        if tab_id:
            for filename, (tid, text_widget) in self.open_files.items():
                if tid == tab_id:
                    self.current_file = filename
                    break

    def show_tab_menu(self, event):
        """Show tab context menu"""
        tab_id = self.notebook.identify(event.x, event.y)
        if tab_id:
            self.notebook.select(tab_id)
            self.tab_menu.post(event.x_root, event.y_root)

    def close_current_tab(self):
        """Close current tab"""
        tab_id = self.notebook.select()
        if tab_id:
            # Find filename for this tab
            filename_to_remove = None
            for filename, (tid, _) in self.open_files.items():
                if tid == tab_id:
                    filename_to_remove = filename
                    break
            
            if filename_to_remove:
                del self.open_files[filename_to_remove]
                self.notebook.forget(tab_id)

    def save_current_file(self):
        """Save current file"""
        tab_id = self.notebook.select()
        if tab_id and self.current_file:
            for filename, (tid, text_widget) in self.open_files.items():
                if tid == tab_id:
                    content = text_widget.get("1.0", "end-1c")
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.app.log_ai(f"Saved: {os.path.basename(filename)}")
                    except Exception as e:
                        self.app.log_ai(f"Error saving {filename}: {e}")

    def close_all_tabs(self):
        """Close all open tabs"""
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.open_files.clear()

    def get_current_file(self):
        """Get current file path"""
        return self.current_file

    def get_open_files(self):
        """Get all open files"""
        return list(self.open_files.keys())

    def save_all_files(self, project_path):
        """Save all open files"""
        saved = []
        for filename, (tab_id, text_widget) in self.open_files.items():
            content = text_widget.get("1.0", "end-1c")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved.append(filename)
            except Exception as e:
                self.app.log_ai(f"Error saving {filename}: {e}")
        return saved

    def update_file_content(self, filename, new_content):
        """Update file content if open"""
        if filename in self.open_files:
            tab_id, text_widget = self.open_files[filename]
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", new_content)

    def apply_theme(self, theme):
        """Apply theme to editors"""
        for filename, (tab_id, text_widget) in self.open_files.items():
            text_widget.configure(
                bg=theme["EDITOR_BG"],
                fg=theme["FG"],
                insertbackground=theme["CURSOR"],
                selectbackground=theme["TREE_SELECT"]
            )