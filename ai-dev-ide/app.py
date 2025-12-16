"""
Main GUI for AI Dev IDE - Refactored and Modular
"""
import os
import sys
import tkinter as tk
from tkinter import ttk

# Add module paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import modular components
from gui.settings_window import SettingsWindow
from gui.project_tree import ProjectTree
from gui.editor_tabs import EditorTabs
from gui.ai_panel import AIPanel
from gui.output_panels import OutputPanels
from core.file_manager import FileManager
from core.project_state import PROJECT_STATE
from core.llm import call_llm
from agents.summarizer import summarizer_agent
from agents.fixer import fixer_agent
from core.theme_engine import ThemeEngine

# Try to import GitHub modules
try:
    from github.repo import create_github_repo
    from github.git_ops import git_init_and_push
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Settings file
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")

def load_settings():
    """Load settings from file and ensure all theme keys exist"""
    import json
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
        except:
            loaded_settings = {}
    else:
        loaded_settings = {}
    
    loaded_settings["theme"] = loaded_settings.get("theme", {})
    return loaded_settings

def save_settings(settings):
    """Save settings to file"""
    import json
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except:
        pass

class AIDevIDE:
    def __init__(self, root, settings=None, theme_engine=None):
        self.root = root
        self.settings = settings or load_settings()
        
        # Initialize theme engine first
        self.theme_engine = theme_engine or ThemeEngine(root)
        theme_data = self.settings.get("theme", self.theme_engine.create_dark_theme())
        normalized_theme = self.theme_engine.normalize_theme(theme_data)
        self.theme_engine.apply_theme(normalized_theme)
        self.theme = self.theme_engine.to_legacy_theme()
        
        # Initialize components
        self.file_manager = FileManager()
        self.project_path = None
        self.is_running_agent = False
        self.ai_suggested_changes = {}
        
        # Setup GUI
        self.setup_gui()
        self.apply_theme_to_all()
        
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root.title("AI Dev IDE - Modular")
        self.root.geometry("1200x900")
        self.root.configure(bg=self.theme["BG"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create main frames
        self.setup_menu()
        self.setup_status_bar()
        self.setup_main_panes()
        self.setup_bottom_panes()
        
    def setup_menu(self):
        """Setup the top menu/controls"""
        from tkinter import Menu
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_existing_project)
        file_menu.add_separator()
        file_menu.add_command(label="Save All", command=self.save_all_open_files)
        file_menu.add_command(label="Export Project", command=self.export_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H")
        edit_menu.add_command(label="Go to Line", accelerator="Ctrl+G")
        
        # AI menu
        ai_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Plan Project", command=lambda: self.run_agent("plan"))
        ai_menu.add_command(label="Generate Code", command=lambda: self.run_agent("code"))
        ai_menu.add_command(label="Generate Tests", command=lambda: self.run_agent("test"))
        ai_menu.add_command(label="Summarize Project", command=lambda: self.run_agent("summarize"))
        ai_menu.add_separator()
        ai_menu.add_command(label="Fix Errors", command=self.suggest_fixes)
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self.open_settings)
        tools_menu.add_command(label="Run Script", command=self.save_and_run)
        tools_menu.add_command(label="Run Tests", command=self.run_tests_and_show)
        if GITHUB_AVAILABLE:
            tools_menu.add_command(label="Push to GitHub", command=self.push_to_github)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill="x", padx=6, pady=(6,4))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", font=(self.theme["FONT_FAMILY"], 10))
        self.status_label.pack(side="left", fill="x", expand=True)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side="right", padx=(6,0))
        
        self.progress_text = ttk.Label(self.status_frame, text="", font=(self.theme["FONT_FAMILY"], 9))
        self.progress_text.pack(side="right", padx=(0,6))
    
    def setup_main_panes(self):
        """Setup the main panes (tree, editor, AI panel)"""
        import tkinter as tk
        from tkinter import ttk
        
        # Main horizontal panes
        main_pane = ttk.Panedwindow(self.root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=6, pady=4)
        
        # Left: Project tree
        left_frame = ttk.Frame(main_pane, width=240)
        main_pane.add(left_frame, weight=1)
        self.project_tree = ProjectTree(left_frame, self)
        self.project_tree.pack(fill="both", expand=True)
        
        # Center: Editor tabs
        center_frame = ttk.Frame(main_pane)
        main_pane.add(center_frame, weight=3)
        self.editor_tabs = EditorTabs(center_frame, self)
        self.editor_tabs.pack(fill="both", expand=True)
        
        # Right: AI panel
        right_frame = ttk.Frame(main_pane, width=360)
        main_pane.add(right_frame, weight=1)
        self.ai_panel = AIPanel(right_frame, self)
        self.ai_panel.pack(fill="both", expand=True)
    
    def setup_bottom_panes(self):
        """Setup bottom output panes"""
        bottom_pane = ttk.Panedwindow(self.root, orient="horizontal")
        bottom_pane.pack(fill="both", padx=6, pady=(0,6))
        
        self.output_panels = OutputPanels(bottom_pane, self)
    
    def apply_theme_to_all(self):
        """Apply theme to all components"""
        # Refresh legacy theme snapshot for existing widgets
        self.theme = self.theme_engine.to_legacy_theme()
        self.root.configure(bg=self.theme["BG"])
        
        # Configure ttk style for frames, labels, buttons, etc.
        style = ttk.Style()
        style.configure("TFrame", background=self.theme["FRAME_BG"])
        style.configure("TLabel", background=self.theme["LABEL_BG"], foreground=self.theme["FG"])
        style.configure("TButton", background=self.theme["BTN"])
        style.map("TButton", background=[('active', self.theme["BTN_ACTIVE"])])
        style.configure("TLabelFrame", background=self.theme["FRAME_BG"], foreground=self.theme["FG"])
        style.configure("TNotebook", background=self.theme["FRAME_BG"])
        style.configure("TNotebook.Tab", background=self.theme["PANEL_BG"], foreground=self.theme["FG"])
        
        # Apply to specific components
        if hasattr(self, 'project_tree'):
            self.project_tree.apply_theme(self.theme)
        if hasattr(self, 'editor_tabs'):
            self.editor_tabs.apply_theme_to_all()
        if hasattr(self, 'ai_panel'):
            self.ai_panel.apply_theme(self.theme)
        if hasattr(self, 'output_panels'):
            self.output_panels.apply_theme(self.theme)
        if hasattr(self, 'status_frame'):
            self.status_frame.configure(style="TFrame")
            self.status_label.configure(style="TLabel")
            self.progress_text.configure(style="TLabel")
    
    def update_progress(self, message, show_progress_bar=True):
        """Update progress status"""
        self.root.after(0, lambda: self._update_progress_ui(message, show_progress_bar))
    
    def _update_progress_ui(self, message, show_progress_bar):
        self.status_label.config(text=message)
        self.progress_text.config(text=message[:40] + "..." if len(message) > 40 else message)
        
        if show_progress_bar:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
    
    def clear_progress(self):
        """Clear progress indicators"""
        self.status_label.config(text="Ready")
        self.progress_text.config(text="")
        self.progress_bar.stop()
    
    # Project methods
    def new_project(self):
        """Create a new project"""
        from tkinter import filedialog, simpledialog
        import os
        
        folder = filedialog.askdirectory(title="Select Folder for New Project")
        if not folder:
            return
        
        project_name = simpledialog.askstring("Project Name", "Enter project name:")
        if not project_name:
            project_name = "new_project"
        
        self.project_path = os.path.join(folder, project_name)
        os.makedirs(self.project_path, exist_ok=True)
        
        # Create basic files
        with open(os.path.join(self.project_path, "README.md"), "w") as f:
            f.write(f"# {project_name}\n\nCreated with AI Dev IDE\n")
        
        with open(os.path.join(self.project_path, "main.py"), "w") as f:
            f.write('# Main file\nprint("Hello from AI Dev IDE")')
        
        with open(os.path.join(self.project_path, "PORTFOLIO.md"), "w") as f:
            f.write(f"# {project_name} - Portfolio\n\n## Project Description\n\nThis project was created using AI Dev IDE.\n")
        
        # Load the new project
        self.project_tree.load_project(self.project_path)
        self.log_ai(f"Created new project: {project_name}")
    
    def open_existing_project(self):
        """Open an existing project"""
        from tkinter import filedialog
        import os
        
        folder = filedialog.askdirectory(title="Select Project Folder")
        if not folder:
            return
        
        self.project_path = folder
        self.project_tree.load_project(folder)
        # Only ensure docs after user selects folder, not at startup
        self.ensure_project_docs()
        self.log_ai(f"Loaded project: {folder}")
    
    def ensure_project_docs(self):
        """Ensure README.md and PORTFOLIO.md exist"""
        if not self.project_path:
            return
        
        import os
        
        # Check and create README.md
        readme_path = os.path.join(self.project_path, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                project_name = os.path.basename(self.project_path)
                f.write(f"# {project_name}\n\n## Project Overview\n\nThis project was created using AI Dev IDE.\n")
            self.log_ai("Created README.md")
        
        # Check and create PORTFOLIO.md
        portfolio_path = os.path.join(self.project_path, "PORTFOLIO.md")
        if not os.path.exists(portfolio_path):
            with open(portfolio_path, "w", encoding="utf-8") as f:
                project_name = os.path.basename(self.project_path)
                f.write(f"# {project_name} - Portfolio\n\n## Project Description\n\nAI-generated project demonstrating modern development practices.\n")
            self.log_ai("Created PORTFOLIO.md")
    
    # Agent methods
    def run_agent(self, agent_type):
        """Run an AI agent"""
        if self.is_running_agent:
            self.show_message("Agent Busy", "Another agent is already running. Please wait.")
            return
        
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        from tkinter import simpledialog
        
        prompts = {
            "plan": "Create a project plan",
            "code": "Generate code for planned project",
            "test": "Generate tests",
            "summarize": "Create project summary"
        }
        
        prompt = simpledialog.askstring(
            f"{agent_type.capitalize()} Agent",
            f"Enter goal for {agent_type} agent:",
            initialvalue=prompts.get(agent_type, "")
        )
        
        if not prompt:
            return
        
        self.is_running_agent = True
        self.update_progress(f"Starting {agent_type} agent...", True)
        
        import threading
        
        def worker():
            try:
                api_url = self.settings.get("api_url", "http://localhost:11434/api/generate")
                model = self.settings.get("model", "tinyllama:1.1b")
                
                if agent_type == "plan":
                    from agents.planner import planner_agent
                    plan = planner_agent(prompt, api_url, model)
                    PROJECT_STATE['plan'] = plan
                    self.update_progress(f"Plan created with {len(plan.get('files', []))} files", False)
                    
                elif agent_type == "code":
                    from agents.coder import coder_agent
                    files = PROJECT_STATE.get('plan', {}).get('files', ['main.py'])
                    for i, fname in enumerate(files):
                        self.update_progress(f"Generating {fname} ({i+1}/{len(files)})...", True)
                        coder_agent(self.project_path, api_url, model)
                    self.update_progress(f"Generated {len(files)} files", False)
                    
                elif agent_type == "test":
                    from agents.tester import tester_agent
                    tester_agent(self.project_path, api_url, model)
                    self.update_progress("Tests generated", False)
                    
                elif agent_type == "summarize":
                    # Use the updated summarizer agent
                    summarizer_agent(self.project_path, api_url, model)
                    self.update_progress("Project summarized", False)
                    
                self.show_message("Agent Complete", f"{agent_type.capitalize()} agent completed successfully!")
                
            except Exception as e:
                self.update_progress(f"Error in {agent_type} agent", False)
                self.log_ai(f"{agent_type.capitalize()} agent error: {e}")
                self.show_message("Agent Error", f"{agent_type.capitalize()} agent failed: {e}")
            finally:
                self.is_running_agent = False
                self.clear_progress()
        
        threading.Thread(target=worker, daemon=True).start()
    
    def suggest_fixes(self):
        """Use AI to suggest fixes for errors"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        if self.is_running_agent:
            self.show_message("Busy", "Please wait for current operation to complete.")
            return
        
        error_log = self.output_panels.script_output.get("1.0", "end-1c").strip()
        if not error_log:
            self.log_ai("No script output to use for fixes. Run a script first.")
            return
        
        self.is_running_agent = True
        self.update_progress("Analyzing errors...", True)
        
        import threading
        
        def worker():
            try:
                # Get selected files
                selected_files = self.ai_panel.get_selected_files() or list(self.editor_tabs.get_open_files())
                
                # Use the fixer agent
                fixes = fixer_agent(
                    self.project_path,
                    selected_files,
                    error_log,
                    self.settings.get("api_url", ""),
                    self.settings.get("model", "")
                )
                
                if fixes:
                    self.ai_suggested_changes = fixes
                    self.ai_panel.display_suggested_changes(fixes)
                    self.update_progress(f"Found {len(fixes)} potential fixes", False)
                else:
                    self.update_progress("No fixes found", False)
                    self.show_message("No Fixes", "AI could not find any fixes for the errors.")
                    
            except Exception as e:
                self.update_progress("Fixer error", False)
                self.log_ai(f"Fixer error: {e}")
                self.show_message("Fixer Error", f"Fixer failed: {e}")
            finally:
                self.is_running_agent = False
                self.clear_progress()
        
        threading.Thread(target=worker, daemon=True).start()
    
    def apply_ai_changes(self):
        """Apply AI suggested changes"""
        if not self.ai_suggested_changes:
            self.show_message("No Changes", "No AI changes to apply.")
            return
        
        applied = 0
        for fname, new_content in self.ai_suggested_changes.items():
            try:
                full_path = os.path.join(self.project_path, fname)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                
                # Update editor if open
                if fname in self.editor_tabs.get_open_files():
                    self.editor_tabs.update_file_content(fname, new_content)
                
                applied += 1
                self.log_ai(f"Applied changes to: {fname}")
                
            except Exception as e:
                self.log_ai(f"Error applying changes to {fname}: {e}")
        
        if applied > 0:
            self.show_message("Changes Applied", f"Applied {applied} file(s) from AI suggestions.")
            self.ai_suggested_changes = {}
            self.project_tree.refresh()
        else:
            self.show_message("No Changes Applied", "No changes were applied.")
    
    # Settings
    def open_settings(self):
        """Open the settings window"""
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = SettingsWindow(self.root, self)
        self.settings_window.show()
    
    def save_settings(self, new_settings):
        """Save new settings"""
        self.settings.update(new_settings)
        theme_data = new_settings.get("theme", self.theme_engine.color_map)
        normalized = self.theme_engine.normalize_theme(theme_data)
        self.theme_engine.apply_theme(normalized)
        self.settings["theme"] = normalized
        save_settings(self.settings)
        self.apply_theme_to_all()
    
    # Utility methods
    def save_all_open_files(self):
        """Save all open files"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        saved = self.editor_tabs.save_all_files(self.project_path)
        self.log_ai(f"Saved {len(saved)} open files")
        return saved
    
    def save_and_run(self):
        """Save and run the current script"""
        self.save_all_open_files()
        
        # Get target script
        target = self.editor_tabs.get_current_file() or "main.py"
        if not os.path.exists(os.path.join(self.project_path, target)):
            self.log_script(f"Script not found: {target}")
            return
        
        import threading
        import subprocess
        
        def worker():
            self.update_progress(f"Running {target}...", True)
            try:
                result = subprocess.run(
                    ["python", target],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                self.output_panels.clear_script_output()
                self.log_script(result.stdout)
                if result.stderr:
                    self.log_script(f"Errors:\n{result.stderr}")
                
                if result.returncode == 0:
                    self.update_progress("Script executed successfully", False)
                else:
                    self.update_progress("Script failed", False)
                    
            except Exception as e:
                self.log_script(f"Error running script: {e}")
                self.update_progress("Script error", False)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def run_tests_and_show(self):
        """Run tests and show results"""
        if not self.project_path:
            self.show_message("No Project", "Please open or create a project first.")
            return
        
        import threading
        import subprocess
        
        def worker():
            self.update_progress("Running tests...", True)
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "-v"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                self.output_panels.clear_script_output()
                self.log_script(result.stdout)
                if result.stderr:
                    self.log_script(f"Test errors:\n{result.stderr}")
                
                self.update_progress("Tests completed", False)
                
            except Exception as e:
                self.log_script(f"Error running tests: {e}")
                self.update_progress("Test error", False)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def export_project(self):
        """Export the project"""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(title="Export Project")
        if not folder:
            return
        
        import shutil
        try:
            shutil.copytree(self.project_path, os.path.join(folder, os.path.basename(self.project_path)))
            self.show_message("Export Complete", f"Project exported to {folder}")
        except Exception as e:
            self.show_message("Export Error", f"Failed to export project: {e}")
    
    def push_to_github(self):
        """Push project to GitHub"""
        if not GITHUB_AVAILABLE:
            self.show_message("GitHub Not Available", "GitHub modules are not installed.")
            return
        
        # Implementation would go here
        pass
    
    # Logging methods
    def log_ai(self, message):
        """Log to AI output"""
        self.output_panels.log_ai(message)
    
    def log_script(self, message):
        """Log to script output"""
        self.output_panels.log_script(message)
    
    def show_message(self, title, message):
        """Show a message box"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    def on_close(self):
        """Handle window close"""
        self.save_settings(self.settings)
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = AIDevIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()