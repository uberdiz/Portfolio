"""
Project Tree Module
"""
import os
import tkinter as tk
from tkinter import ttk
import threading

class ProjectTree(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.project_path = None
        self.setup_tree()

    def setup_tree(self):
        # Treeview with scrollbar
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True)

        # Create Treeview
        self.tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Context menu
        self.setup_context_menu()

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_command(label="Refresh", command=self.refresh)
        
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_project(self, project_path):
        """Load project into tree"""
        self.project_path = project_path
        self.tree.delete(*self.tree.get_children())
        
        if not project_path or not os.path.exists(project_path):
            return
        
        # Add project root
        root_name = os.path.basename(project_path)
        root_id = self.tree.insert("", "end", text=root_name, open=True)
        
        # Populate in background thread
        threading.Thread(target=self.populate_tree, args=(project_path, root_id), daemon=True).start()

    def populate_tree(self, path, parent=""):
        """Populate tree with files and directories"""
        try:
            items = os.listdir(path)
            for item in sorted(items):
                full_path = os.path.join(path, item)
                rel_path = os.path.relpath(full_path, self.project_path)
                
                # Skip hidden files and __pycache__
                if item.startswith('.') or item == '__pycache__':
                    continue
                
                if os.path.isdir(full_path):
                    node_id = self.tree.insert(parent, "end", text=item, open=False)
                    # Populate subdirectories
                    self.populate_tree(full_path, node_id)
                else:
                    self.tree.insert(parent, "end", text=item, tags=("file",))
        except:
            pass

    def on_double_click(self, event):
        """Handle double click on file"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")
        
        if self.project_path:
            # Get full path
            full_path = self.get_full_path(item)
            if os.path.isfile(full_path):
                self.app.editor_tabs.open_file(full_path)

    def on_select(self, event):
        """Handle selection"""
        item = self.tree.selection()
        if item:
            text = self.tree.item(item, "text")

    def get_full_path(self, item):
        """Get full path for tree item"""
        path_parts = []
        while item:
            text = self.tree.item(item, "text")
            path_parts.append(text)
            item = self.tree.parent(item)
        path_parts.reverse()
        
        if self.project_path:
            return os.path.join(self.project_path, *path_parts)
        return os.path.join(*path_parts)

    def open_selected(self):
        """Open selected file"""
        item = self.tree.selection()[0]
        if item:
            full_path = self.get_full_path(item)
            if os.path.isfile(full_path):
                self.app.editor_tabs.open_file(full_path)

    def delete_selected(self):
        """Delete selected file/folder"""
        from tkinter import messagebox
        item = self.tree.selection()[0]
        if item:
            full_path = self.get_full_path(item)
            if messagebox.askyesno("Confirm Delete", f"Delete {os.path.basename(full_path)}?"):
                import shutil
                try:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete: {e}")

    def refresh(self):
        """Refresh tree view"""
        if self.project_path:
            self.load_project(self.project_path)

    def apply_theme(self, theme):
        """Apply theme to tree"""
        style = ttk.Style()
        style.configure("Treeview", 
                       background=theme["TREE_BG"],
                       foreground=theme["TREE_FG"],
                       fieldbackground=theme["TREE_BG"])
        style.map('Treeview', 
                 background=[('selected', theme["TREE_SELECT"])])