"""
AI Dev IDE (optimized for shorter prompts)
- Project tree (left), editor tabs (center), AI chat (right), AI+Script outputs (bottom)
- Settings window: API/model, live color pickers, cursor color, test LLM, GitHub settings
- Persist settings to ~/.ai_dev_ide_settings.json
- Closable tabs (right-click / Ctrl+W)
- Syntax highlighting for Python (basic)
- Editor actions: undo/redo, find/replace, go-to-line, select-all
- Auto-fix with LLM, test-run integration preserved
- Progress tracking for all AI operations
- GitHub integration with README.md and PORTFOLIO.md management
- Optimized prompt length with file summarization
"""

import os
import json
import threading
import tempfile
import subprocess
import difflib
import re
import socket
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext, colorchooser

try:
    import requests
except ImportError:
    requests = None

# project imports (must exist)
try:
    from agents import planner, coder, tester, summarizer
    from core.project_state import PROJECT_STATE
    from core.dependencies import infer_dependencies, write_requirements, install_requirements
    from core.llm import call_llm
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create dummy functions for missing modules
    class DummyModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: print(f"Dummy function called: {name}")
    
    planner = DummyModule()
    coder = DummyModule()
    tester = DummyModule()
    summarizer = DummyModule()
    PROJECT_STATE = {'plan': {'files': []}}
    
    def call_llm(*args, **kwargs):
        return "Dummy LLM response: Install required modules to use AI features."
    
    def infer_dependencies(*args, **kwargs):
        return []
    
    def write_requirements(*args, **kwargs):
        pass
    
    def install_requirements(*args, **kwargs):
        pass

# GitHub imports
try:
    from github.repo import create_github_repo
    from github.git_ops import git_init_and_push, git_commit
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("GitHub modules not available. GitHub features disabled.")

# Settings file
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")

# Default theme
DEFAULT_THEME = {
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
}

# Built-in theme presets
THEME_PRESETS = {
    "Dark": DEFAULT_THEME.copy(),
    "Light": {
        "BG": "#f3f3f3",
        "FG": "#1e1e1e",
        "BTN": "#e0e0e0",
        "BTN_ACTIVE": "#0078d4",
        "PANEL_BG": "#ffffff",
        "EDITOR_BG": "#ffffff",
        "OUTPUT_BG": "#f5f5f5",
        "CURSOR": "#000000",
        "FRAME_BG": "#e5e5e5",
        "LABEL_BG": "#e5e5e5",
        "TREE_BG": "#ffffff",
        "TREE_FG": "#1e1e1e",
        "TREE_SELECT": "#cce8ff",
        "FONT_FAMILY": "Consolas",
        "FONT_SIZE": 11,
        "PROGRESS_BG": "#cce5cc",
        "PROGRESS_FG": "#006400"
    }
}

# ---------------- File Management Helpers ----------------
class FileManager:
    """Manages file content and hashing for efficient AI prompts"""
    
    def __init__(self):
        self.file_hashes = {}  # relpath -> hash
        self.file_summaries = {}  # relpath -> summary
    
    def get_file_hash(self, content):
        """Get hash of file content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def summarize_file(self, content, max_lines=30):
        """Create a summary of file content"""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        # Keep first 15 lines and last 15 lines
        summary_lines = lines[:15] + ["\n... [truncated - file too long] ...\n"] + lines[-15:]
        return '\n'.join(summary_lines)
    
    def summarize_python_file(self, content, max_chars=2000):
        """Summarize Python file by keeping important parts"""
        if len(content) <= max_chars:
            return content
        
        # For Python files, keep:
        # 1. Imports
        # 2. Class/function definitions
        # 3. First 10 lines of each function
        
        lines = content.split('\n')
        important_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            # Keep imports
            if line_stripped.startswith(('import ', 'from ')):
                important_lines.append(line)
            # Keep class/function definitions
            elif line_stripped.startswith(('def ', 'class ', '@')):
                important_lines.append(line)
            # Keep comments that look important
            elif line_stripped.startswith('#') and any(keyword in line_stripped.lower() 
                                                      for keyword in ['todo', 'fixme', 'note', 'important']):
                important_lines.append(line)
        
        # If we still have too many lines, truncate
        if len('\n'.join(important_lines)) > max_chars:
            # Just take the most important parts
            result = []
            char_count = 0
            for line in important_lines:
                if char_count + len(line) > max_chars:
                    break
                result.append(line)
                char_count += len(line) + 1
            
            result.append("\n... [truncated for brevity] ...")
            return '\n'.join(result)
        
        return '\n'.join(important_lines) if important_lines else content[:max_chars] + "\n... [truncated] ..."
    
    def get_optimized_content(self, relpath, content):
        """Get optimized content for AI prompts"""
        file_ext = os.path.splitext(relpath)[1].lower()
        
        if file_ext == '.py':
            return self.summarize_python_file(content, max_chars=1500)
        elif file_ext in ['.txt', '.md', '.rst']:
            return content[:2000] + ("..." if len(content) > 2000 else "")
        else:
            # For other files, use general truncation
            return content[:1000] + ("..." if len(content) > 1000 else "")
    
    def should_send_full_file(self, relpath, content, is_modified=False):
        """Determine if we should send full file or summary"""
        current_hash = self.get_file_hash(content)
        
        # If file hasn't changed and we have a summary, use summary
        if relpath in self.file_hashes and self.file_hashes[relpath] == current_hash:
            if relpath in self.file_summaries and not is_modified:
                return False  # Use summary
        
        # Update hash and summary
        self.file_hashes[relpath] = current_hash
        self.file_summaries[relpath] = self.get_optimized_content(relpath, content)
        
        return True  # Send optimized content

# ---------------- util helpers ----------------
file_manager = FileManager()

def save_project_files(files_dict, project_dir):
    os.makedirs(project_dir, exist_ok=True)
    for fname, content in files_dict.items():
        fpath = os.path.join(project_dir, fname)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

def run_script_capture(path, timeout=60, cwd=None):
    try:
        proc = subprocess.run(["python", path], capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "stdout": e.stdout or "", "stderr": f"Timeout: {e}", "returncode": 1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": 1}

def run_pytest_capture(cwd, timeout=120):
    try:
        proc = subprocess.run(["python", "-m", "pytest", "-q", "--disable-warnings"], capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "stdout": e.stdout or "", "stderr": f"Timeout: {e}", "returncode": 1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": 1}

def compute_estimate_from_diff(old_text, new_text):
    diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines()))
    changed = 0
    for line in diff:
        if line.startswith("+") or line.startswith("-"):
            if line.startswith("+++ ") or line.startswith("--- "):
                continue
            changed += 1
    seconds = max(2, min(600, changed * 2))
    if seconds < 60:
        return f"{seconds} seconds"
    mins = seconds // 60
    sec = seconds % 60
    return f"{mins}m {sec}s"

# ---------------- persistence ----------------
def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                theme = data.get("theme", {})
                # merge defaults (ensures new theme keys are added)
                t = DEFAULT_THEME.copy()
                t.update(theme)
                data["theme"] = t
                # Load custom presets if they exist
                if "custom_presets" not in data:
                    data["custom_presets"] = {}
                # Ensure GitHub token exists
                if "github_token" not in data:
                    data["github_token"] = ""
                # Add API provider settings
                if "api_provider" not in data:
                    data["api_provider"] = "ollama"
                if "huggingface_token" not in data:
                    data["huggingface_token"] = ""
                if "huggingface_model" not in data:
                    data["huggingface_model"] = "microsoft/CodeGPT-small-py"
                if "huggingface_api_url" not in data:
                    data["huggingface_api_url"] = "https://router.huggingface.co"  # FIXED: Updated endpoint
                if "replicate_token" not in data:
                    data["replicate_token"] = ""
                if "together_token" not in data:
                    data["together_token"] = ""
                if "openrouter_token" not in data:
                    data["openrouter_token"] = ""
                if "deepinfra_token" not in data:
                    data["deepinfra_token"] = ""
                return data
        except Exception:
            pass
    # default settings
    return {
        "api_provider": "ollama",
        "api_url": "http://localhost:11434/api/generate",
        "model": "tinyllama:1.1b",
        "huggingface_token": "",
        "huggingface_model": "microsoft/CodeGPT-small-py",
        "huggingface_api_url": "https://router.huggingface.co",  # FIXED: Updated endpoint
        "replicate_token": "",
        "together_token": "",
        "openrouter_token": "",
        "deepinfra_token": "",
        "github_token": "",
        "theme": DEFAULT_THEME.copy(),
        "custom_presets": {},
        "prompt_optimization": {
            "max_files": 3,
            "max_chars_per_file": 1000,
            "use_summaries": True,
            "send_only_modified": False
        }
    }

def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

# ---------------- syntax highlighting ----------------
PY_KEYWORDS = set([
    "def","return","if","elif","else","for","while","import","from","as","class",
    "try","except","finally","with","lambda","pass","break","continue","in","is",
    "and","or","not","None","True","False","yield","async","await","global","nonlocal","assert","raise"
])
PY_BUILTINS = set(dir(__builtins__))

def simple_highlight(text_widget):
    # remove all tags
    text_widget.tag_remove("kw", "1.0", "end")
    text_widget.tag_remove("str", "1.0", "end")
    text_widget.tag_remove("cmt", "1.0", "end")
    text_widget.tag_remove("num", "1.0", "end")
    text_widget.tag_remove("builtin", "1.0", "end")
    txt = text_widget.get("1.0", "end-1c")
    if not txt:
        return
    # comments (single-line #)
    for m in re.finditer(r"#.*", txt):
        start = f"1.0+{m.start()}c"; end = f"1.0+{m.end()}c"
        text_widget.tag_add("cmt", start, end)
    # strings (single and double)
    for m in re.finditer(r"(?s)(?:'[^'\\]*(?:\\.[^'\\]*)*'|\"[^\"\\]*(?:\\.[^\"\\]*)*\")", txt):
        start = f"1.0+{m.start()}c"; end = f"1.0+{m.end()}c"
        text_widget.tag_add("str", start, end)
    # numbers
    for m in re.finditer(r"\b\d+(\.\d+)?\b", txt):
        start = f"1.0+{m.start()}c"; end = f"1.0+{m.end()}c"
        text_widget.tag_add("num", start, end)
    # keywords & builtins (word boundaries)
    for m in re.finditer(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", txt):
        w = m.group(0)
        tag = None
        if w in PY_KEYWORDS:
            tag = "kw"
        elif w in PY_BUILTINS:
            tag = "builtin"
        if tag:
            start = f"1.0+{m.start()}c"; end = f"1.0+{m.end()}c"
            text_widget.tag_add(tag, start, end)

# ---------------- main GUI ----------------
class AIDevIDE:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.theme = self.settings["theme"]
        self.prompt_opts = self.settings.get("prompt_optimization", {
            "max_files": 5,
            "max_chars_per_file": 1500,
            "use_summaries": True,
            "send_only_modified": False
        })
        
        self.root.title("AI Dev IDE - Optimized Prompts")
        self.root.geometry("1200x900")
        self.root.configure(bg=self.theme["BG"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("AIDev.TButton", foreground=self.theme["FG"], background=self.theme["BTN"])
        self.style.map("AIDev.TButton", background=[("active", self.theme["BTN_ACTIVE"]), ("pressed", self.theme["BTN_ACTIVE"])])

        # Status bar at the top
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill="x", padx=6, pady=(6,4))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", font=(self.theme["FONT_FAMILY"], 10))
        self.status_label.pack(side="left", fill="x", expand=True)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side="right", padx=(6,0))
        
        self.progress_text = ttk.Label(self.status_frame, text="", font=(self.theme["FONT_FAMILY"], 9))
        self.progress_text.pack(side="right", padx=(0,6))

        # Top controls
        top = ttk.Frame(root)
        top.pack(fill="x", padx=6, pady=(0,4))
        ttk.Button(top, text="Settings", style="AIDev.TButton", command=self.open_settings).pack(side="left")
        ttk.Button(top, text="Open Project", style="AIDev.TButton", command=self.open_existing_project).pack(side="left", padx=6)
        ttk.Button(top, text="New Project", style="AIDev.TButton", command=self.new_project).pack(side="left", padx=6)
        if GITHUB_AVAILABLE:
            ttk.Button(top, text="Push to GitHub", style="AIDev.TButton", command=self.push_to_github).pack(side="left", padx=6)
        ttk.Label(top, text=" ", background=self.theme["BG"]).pack(side="left", expand=True)
        ttk.Button(top, text="Setup Free APIs", style="AIDev.TButton", 
                command=self.run_setup_guide).pack(side="left", padx=6)

        # main panes
        main_pane = ttk.Panedwindow(root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=6, pady=4)

        # Left: tree
        left_frame = ttk.Frame(main_pane, width=240)
        main_pane.add(left_frame, weight=1)
        ttk.Label(left_frame, text="Project Tree").pack(anchor="nw", padx=6, pady=(6,0))
        self.tree = ttk.Treeview(left_frame)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Center: editors
        center_frame = ttk.Frame(main_pane)
        main_pane.add(center_frame, weight=3)
        self.notebook = ttk.Notebook(center_frame)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)
        self.editor_tabs = {}   # relpath -> Text widget
        self.tab_id_map = {}    # tab_id -> relpath

        # Welcome tab (closable)
        wtext = scrolledtext.ScrolledText(self.notebook, height=6, bg=self.theme["EDITOR_BG"], fg=self.theme["FG"], font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        wtext.insert("1.0", "Welcome — double click files in the project tree to open them.\nRight-click a tab to close it. Ctrl+W closes current tab.\n\nUse AI agents to build projects with optimized prompts.")
        wtext.configure(state="disabled")
        self.notebook.add(wtext, text="Welcome")

        # Right: AI panel
        right_frame = ttk.Frame(main_pane, width=360)
        main_pane.add(right_frame, weight=1)
        
        # AI Agents section
        agents_frame = ttk.LabelFrame(right_frame, text="AI Agents", padding=6)
        agents_frame.pack(fill="x", padx=6, pady=(6,4))
        
        agents_grid = ttk.Frame(agents_frame)
        agents_grid.pack(fill="x")
        
        ttk.Button(agents_grid, text="Plan", style="AIDev.TButton", 
                  command=lambda: self.run_agent("plan", "Create a project plan")).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(agents_grid, text="Code", style="AIDev.TButton", 
                  command=lambda: self.run_agent("code", "Generate code for planned project")).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(agents_grid, text="Test", style="AIDev.TButton", 
                  command=lambda: self.run_agent("test", "Generate tests")).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(agents_grid, text="Summarize", style="AIDev.TButton", 
                  command=lambda: self.run_agent("summarize", "Create project summary")).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        agents_grid.columnconfigure(0, weight=1)
        agents_grid.columnconfigure(1, weight=1)

        # File selection with optimization info
        file_frame = ttk.Frame(right_frame)
        file_frame.pack(fill="x", padx=6, pady=(8,0))
        
        ttk.Label(file_frame, text="Files for AI:").pack(side="left")
        ttk.Label(file_frame, text="(Ctrl+click to select multiple)", foreground="#888888", 
                 font=(self.theme["FONT_FAMILY"], 9)).pack(side="left", padx=(4,0))
        
        self.file_listbox = tk.Listbox(right_frame, selectmode="extended", height=8, bg=self.theme["PANEL_BG"], fg=self.theme["FG"])
        self.file_listbox.pack(fill="x", padx=6, pady=4)
        
        # Selection info label
        self.selection_info = ttk.Label(right_frame, text="0 files selected", foreground="#888888", 
                                       font=(self.theme["FONT_FAMILY"], 9))
        self.selection_info.pack(anchor="w", padx=6, pady=(0,4))
        self.file_listbox.bind("<<ListboxSelect>>", self.update_selection_info)

        ttk.Label(right_frame, text="AI Chat / Task (be specific):").pack(anchor="nw", padx=6)
        self.chat_text = scrolledtext.ScrolledText(right_frame, height=6, bg=self.theme["EDITOR_BG"], fg=self.theme["FG"], 
                                                  font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        self.chat_text.pack(fill="both", padx=6, pady=4, expand=False)
        self.chat_text.insert("1.0", "What would you like me to help with?")
        
        chat_ctrl = ttk.Frame(right_frame)
        chat_ctrl.pack(fill="x", padx=6, pady=(0,6))
        self.explain_changes_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(chat_ctrl, text="Explain changes", variable=self.explain_changes_var).pack(side="left")
        ttk.Button(chat_ctrl, text="Send to AI", style="AIDev.TButton", command=self.send_chat_to_ai).pack(side="right")
        
        # AI Response Actions Frame
        ai_actions_frame = ttk.Frame(right_frame)
        ai_actions_frame.pack(fill="x", padx=6, pady=(0,6))
        ttk.Button(ai_actions_frame, text="Apply AI Changes", style="AIDev.TButton", 
                  command=self.apply_ai_changes).pack(side="left", padx=(0,6))
        ttk.Button(ai_actions_frame, text="Save Changes to Script", style="AIDev.TButton", 
                  command=self.save_changes_to_script).pack(side="left")
        
        ttk.Label(right_frame, text="AI response / What changed:").pack(anchor="nw", padx=6)
        self.what_changed = scrolledtext.ScrolledText(right_frame, height=6, bg=self.theme["EDITOR_BG"], fg=self.theme["FG"], 
                                                     font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        self.what_changed.pack(fill="both", padx=6, pady=(0,6), expand=False)
        self.what_changed.configure(state="disabled")
        
        # Store AI suggested changes
        self.ai_suggested_changes = {}
        self.file_modification_times = {}  # Track when files were last modified

        # Bottom outputs
        bottom_pane = ttk.Panedwindow(root, orient="horizontal")
        bottom_pane.pack(fill="both", padx=6, pady=(0,6))
        ai_out_frame = ttk.Frame(bottom_pane)
        bottom_pane.add(ai_out_frame, weight=1)
        ttk.Label(ai_out_frame, text="AI Output").pack(anchor="nw", padx=6, pady=(4,0))
        self.ai_output = scrolledtext.ScrolledText(ai_out_frame, height=10, bg=self.theme["OUTPUT_BG"], fg=self.theme["FG"], 
                                                  font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        self.ai_output.pack(fill="both", expand=True, padx=6, pady=6)
        script_out_frame = ttk.Frame(bottom_pane)
        bottom_pane.add(script_out_frame, weight=1)
        ttk.Label(script_out_frame, text="Script / Test Output").pack(anchor="nw", padx=6, pady=(4,0))
        self.script_output = scrolledtext.ScrolledText(script_out_frame, height=10, bg=self.theme["OUTPUT_BG"], fg=self.theme["FG"], 
                                                      font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        self.script_output.pack(fill="both", expand=True, padx=6, pady=6)

        # right-click tab menu + keyboard close binding
        self.tab_menu = tk.Menu(root, tearoff=0)
        self.tab_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.notebook.bind("<Button-3>", self.on_tab_right_click)
        root.bind_all("<Control-w>", lambda e: self.close_current_tab())

        # internal state
        self.project_path = None
        self.open_files = set()
        self.settings_window = None
        self.is_running_agent = False
        self.ai_suggested_changes = {}
        
        # Ensure custom_presets exists
        if "custom_presets" not in self.settings:
            self.settings["custom_presets"] = {}

        # apply theme settings (colors etc.)
        self.apply_theme()

    # ---------------- File Selection Info ----------------
    def update_selection_info(self, event=None):
        """Update selection count info"""
        count = len(self.file_listbox.curselection())
        max_files = self.prompt_opts.get("max_files", 5)
        
        if count > max_files:
            self.selection_info.config(text=f"{count} files selected (only {max_files} will be sent)", 
                                      foreground="#ff6600")
        else:
            self.selection_info.config(text=f"{count} files selected", 
                                      foreground="#888888")

    # ---------------- Optimized File Reading ----------------
    def get_optimized_file_content(self, relpath, is_modified=False):
        """Get optimized file content for AI prompts"""
        if not self.project_path:
            return "<no project>"
            
        path = os.path.join(self.project_path, relpath)
        
        # Check if file is open in editor (most recent)
        if relpath in self.editor_tabs:
            content = self.editor_tabs[relpath].get("1.0", "end-1c")
            source = "editor"
        else:
            # Read from disk
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                source = "disk"
            except Exception:
                return "<could not read>"
        
        # Check file size
        file_size = len(content)
        max_chars = self.prompt_opts.get("max_chars_per_file", 1500)
        
        # If file is small enough, return as-is
        if file_size <= max_chars:
            return content
        
        # Optimize based on file type
        file_ext = os.path.splitext(relpath)[1].lower()
        
        if file_ext == '.py':
            # For Python files, keep structure and important parts
            return self._optimize_python_file(content, max_chars)
        elif file_ext in ['.md', '.txt', '.rst']:
            # For text files, keep beginning and end
            return self._optimize_text_file(content, max_chars)
        else:
            # For other files, just truncate
            return content[:max_chars] + f"\n\n... [file truncated, {file_size} chars total] ..."

    def _optimize_python_file(self, content, max_chars):
        """Optimize Python file content"""
        lines = content.split('\n')
        
        # If small enough, return as-is
        if len(content) <= max_chars:
            return content
        
        # Keep imports, class/function definitions, and key sections
        important_lines = []
        in_important_section = False
        
        for line in lines:
            stripped = line.strip()
            
            # Always keep imports and definitions
            if stripped.startswith(('import ', 'from ', 'def ', 'class ', '@')):
                important_lines.append(line)
                in_important_section = True
            # Keep comments with TODO/FIXME
            elif stripped.startswith('#') and any(word in stripped.lower() for word in ['todo', 'fixme', 'note', 'warning']):
                important_lines.append(line)
            # Keep lines in important sections (after definitions)
            elif in_important_section and stripped and not stripped.startswith('#'):
                important_lines.append(line)
            # End important section on empty line
            elif in_important_section and not stripped:
                important_lines.append(line)
                in_important_section = False
        
        optimized = '\n'.join(important_lines)
        
        # If still too long, truncate
        if len(optimized) > max_chars:
            # Try to keep the structure
            lines = optimized.split('\n')
            kept_lines = []
            char_count = 0
            
            for line in lines:
                if char_count + len(line) > max_chars - 100:  # Leave room for truncation message
                    break
                kept_lines.append(line)
                char_count += len(line) + 1
            
            kept_lines.append(f"\n# ... [file optimized for AI, {len(content)} chars total] ...")
            optimized = '\n'.join(kept_lines)
        
        return optimized

    def _optimize_text_file(self, content, max_chars):
        """Optimize text file content"""
        if len(content) <= max_chars:
            return content
        
        # For text files, keep first and last parts
        half = max_chars // 2
        optimized = content[:half] + f"\n\n... [middle of file omitted] ...\n\n" + content[-half:]
        
        if len(optimized) > max_chars:
            # Fallback to simple truncation
            optimized = content[:max_chars] + f"\n\n... [file truncated, {len(content)} chars total] ..."
        
        return optimized

    # ---------------- progress tracking ----------------
    def update_progress(self, message, show_progress_bar=True):
        """Update progress status in the UI"""
        self.root.after(0, lambda: self._update_progress_ui(message, show_progress_bar))
    
    def _update_progress_ui(self, message, show_progress_bar):
        self.status_label.config(text=message)
        self.progress_text.config(text=message[:40] + "..." if len(message) > 40 else message)
        
        if show_progress_bar:
            if not self.progress_bar.cget('mode') == 'indeterminate':
                self.progress_bar.config(mode='indeterminate')
            if not self.progress_bar.winfo_ismapped():
                self.progress_bar.pack(side="right", padx=(6,0))
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def clear_progress(self):
        """Clear progress indicators"""
        self.root.after(0, self._clear_progress_ui)
    
    def _clear_progress_ui(self):
        self.status_label.config(text="Ready")
        self.progress_text.config(text="")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    # ---------------- GitHub Integration ----------------
    def push_to_github(self):
        """Push the current project to GitHub"""
        if not GITHUB_AVAILABLE:
            messagebox.showerror("GitHub Not Available", "GitHub modules are not installed.")
            return
            
        if not self.project_path:
            messagebox.showinfo("No Project", "Please open or create a project first.")
            return
            
        token = self.settings.get("github_token", "")
        if not token:
            messagebox.showinfo("GitHub Token Required", 
                              "Please set your GitHub token in Settings first.")
            self.open_settings()
            return
            
        default_name = os.path.basename(self.project_path) if self.project_path else "ai-project"
        repo_name = simpledialog.askstring("GitHub Repository", 
                                          "Enter repository name:", 
                                          initialvalue=default_name)
        if not repo_name:
            return
            
        private = messagebox.askyesno("Repository Visibility", 
                                     "Make repository private?")
        
        # Ensure README.md and PORTFOLIO.md exist
        self.ensure_project_docs()
        
        def worker():
            try:
                self.update_progress("Creating GitHub repository...", True)
                
                os.environ["GITHUB_TOKEN"] = token
                
                self.log_ai(f"Creating GitHub repository '{repo_name}'...")
                clone_url = create_github_repo(repo_name, private)
                
                self.update_progress("Initializing git repository...", True)
                
                git_init_and_push(self.project_path, clone_url)
                
                self.update_progress("Project pushed to GitHub successfully!", False)
                self.log_ai(f"Project successfully pushed to GitHub: {clone_url}")
                
                messagebox.showinfo("Success", 
                                  f"Project pushed to GitHub successfully!\n\n"
                                  f"Repository: {repo_name}\n"
                                  f"URL: {clone_url}\n"
                                  f"Private: {'Yes' if private else 'No'}")
                                  
            except Exception as e:
                self.update_progress(f"GitHub error: {str(e)[:50]}...", False)
                self.log_ai(f"GitHub error: {e}")
                messagebox.showerror("GitHub Error", f"Failed to push to GitHub:\n\n{str(e)}")
                
        threading.Thread(target=worker, daemon=True).start()

    def ensure_project_docs(self):
        """Ensure README.md and PORTFOLIO.md exist in the project"""
        if not self.project_path:
            return
            
        # Check and create README.md if missing
        readme_path = os.path.join(self.project_path, "README.md")
        if not os.path.exists(readme_path):
            self.update_progress("Creating README.md...", True)
            with open(readme_path, "w", encoding="utf-8") as f:
                project_name = os.path.basename(self.project_path)
                f.write(f"# {project_name}\n\n")
                f.write("## Project Overview\n\n")
                f.write("This project was created using AI Dev IDE.\n")
            self.log_ai("Created README.md")
        
        # Check and create PORTFOLIO.md if missing
        portfolio_path = os.path.join(self.project_path, "PORTFOLIO.md")
        if not os.path.exists(portfolio_path):
            self.update_progress("Creating PORTFOLIO.md...", True)
            with open(portfolio_path, "w", encoding="utf-8") as f:
                project_name = os.path.basename(self.project_path)
                f.write(f"# {project_name} - Portfolio\n\n")
                f.write("## Project Description\n\n")
                f.write("AI-generated project demonstrating modern development practices.\n")
            self.log_ai("Created PORTFOLIO.md")
            
        self._refresh_file_listbox()

    def test_github_connection(self):
        """Test GitHub connection with provided token"""
        token = self.settings.get("github_token", "")
        if not token:
            messagebox.showinfo("No Token", "Please enter a GitHub token first.")
            return False
            
        try:
            self.update_progress("Testing GitHub connection...", True)
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json"
            }
            
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("login", "Unknown")
                self.update_progress(f"GitHub connected as {username}", False)
                self.log_ai(f"GitHub connection successful. User: {username}")
                messagebox.showinfo("GitHub Test", 
                                  f"Connection successful!\n\n"
                                  f"Username: {username}")
                return True
            else:
                self.update_progress("GitHub connection failed", False)
                self.log_ai(f"GitHub connection failed: {response.status_code}")
                messagebox.showerror("GitHub Test Failed", 
                                   f"Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.update_progress("GitHub connection error", False)
            self.log_ai(f"GitHub connection error: {e}")
            messagebox.showerror("GitHub Test Failed", f"Error: {str(e)}")
            return False

    # ---------------- AI Changes Management ----------------
    def apply_ai_changes(self):
        """Apply AI suggested changes stored in self.ai_suggested_changes"""
        if not self.ai_suggested_changes:
            messagebox.showinfo("No Changes", "No AI changes to apply.")
            return
            
        if not self.project_path:
            messagebox.showinfo("No Project", "Please open or create a project first.")
            return
            
        applied = 0
        for fname, new_content in self.ai_suggested_changes.items():
            try:
                rel = fname
                full = os.path.join(self.project_path, rel)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                
                # Save the content
                with open(full, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                
                # Update editor if open
                if rel in self.editor_tabs:
                    txt = self.editor_tabs[rel]
                    txt.delete("1.0", "end")
                    txt.insert("1.0", new_content)
                    simple_highlight(txt)
                
                applied += 1
                self.log_ai(f"Applied changes to: {rel}")
                
            except Exception as e:
                self.log_ai(f"Error applying changes to {fname}: {e}")
        
        if applied > 0:
            messagebox.showinfo("Changes Applied", f"Applied {applied} file(s) from AI suggestions.")
            self._refresh_file_listbox()
            self.ai_suggested_changes = {}
        else:
            messagebox.showinfo("No Changes Applied", "No changes were applied.")

    def run_setup_guide(self):
        """Run the free API setup guide"""
        import subprocess
        import sys
        
        try:
            # Try to run the setup script
            subprocess.Popen([sys.executable, "setup_free_apis.py"])
        except Exception as e:
            messagebox.showinfo("Setup Guide", 
                            "To set up free APIs:\n\n"
                            "1. Get a Hugging Face token:\n"
                            "   https://huggingface.co/settings/tokens\n\n"
                            "2. In this app, go to Settings\n"
                            "3. Select 'huggingface' as API Provider\n"
                            "4. Paste your token\n"
                            "5. Use model: microsoft/CodeGPT-small-py")

    def save_changes_to_script(self):
        """Save the current script changes to file"""
        if not self.project_path:
            messagebox.showinfo("No Project", "Please open or create a project first.")
            return
            
        sel = self.notebook.select()
        if not sel:
            messagebox.showinfo("No File", "Please open a file to save.")
            return
            
        rel = self.tab_id_map.get(sel)
        if not rel:
            messagebox.showinfo("No File", "Please open a file to save.")
            return
            
        txt = self.editor_tabs.get(rel)
        if not txt:
            messagebox.showinfo("No Editor", "File not found in editors.")
            return
            
        content = txt.get("1.0", "end-1c")
        full = os.path.join(self.project_path, rel)
        
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(content)
            
            self.log_ai(f"Saved changes to: {rel}")
            messagebox.showinfo("Saved", f"Changes saved to {rel}")
            
        except Exception as e:
            self.log_ai(f"Error saving {rel}: {e}")
            messagebox.showerror("Save Error", f"Failed to save {rel}:\n\n{str(e)}")

    # ---------------- Optimized AI Chat ----------------
    def send_chat_to_ai(self):
        """Send chat to AI with optimized prompts"""
        prompt_text = self.chat_text.get("1.0", "end-1c").strip()
        if not prompt_text or prompt_text == "What would you like me to help with?":
            messagebox.showinfo("No Prompt", "Please enter a prompt for the AI.")
            return
        
        if self.is_running_agent:
            messagebox.showinfo("Busy", "Please wait for current operation to complete.")
            return
            
        sel_indices = self.file_listbox.curselection()
        if not sel_indices:
            # If no files selected, use a minimal prompt
            header = f"User request: {prompt_text}\n\n"
            header += "No specific files provided. Please provide general guidance or ask for clarification.\n"
        else:
            # Apply optimization limits
            max_files = self.prompt_opts.get("max_files", 5)
            selected_files = [self.file_listbox.get(i) for i in sel_indices[:max_files]]
            
            if len(sel_indices) > max_files:
                self.log_ai(f"Note: Only sending {max_files} of {len(sel_indices)} selected files for optimization.")
            
            # Build optimized context
            files_context = {}
            total_chars = 0
            max_total_chars = 8000  # Total character limit for all files
            
            for rel in selected_files:
                if total_chars > max_total_chars:
                    self.log_ai(f"Note: Stopped adding files due to total size limit ({total_chars} chars)")
                    break
                
                content = self.get_optimized_file_content(rel)
                files_context[rel] = content
                total_chars += len(content)
            
            # Build optimized prompt
            header = f"User request: {prompt_text}\n\n"
            header += f"Project context: Working on {len(files_context)} file(s), total ~{total_chars} characters.\n\n"
            
            if files_context:
                header += "Files (optimized for context):\n"
                for fname, content in files_context.items():
                    char_count = len(content)
                    lines = content.count('\n') + 1
                    header += f"\n--- {fname} ({lines} lines, {char_count} chars) ---\n{content}\n"
            
            header += "\nInstructions:\n"
            header += "1. Provide specific, actionable changes\n"
            header += "2. If making code changes, return JSON with filename->new_content\n"
            header += "3. Include a brief explanation after the JSON\n"
            header += "4. Keep responses concise and focused\n"
        
        # Get provider settings
        api_provider = self.settings.get("api_provider", "ollama")
        api_url = self.settings.get("api_url", "")
        model = self.settings.get("model", "")
        huggingface_token = self.settings.get("huggingface_token", "")
        huggingface_model = self.settings.get("huggingface_model", "microsoft/CodeGPT-small-py")
        huggingface_api_url = self.settings.get("huggingface_api_url", "https://router.huggingface.co")  # FIXED
        replicate_token = self.settings.get("replicate_token", "")
        together_token = self.settings.get("together_token", "")
        openrouter_token = self.settings.get("openrouter_token", "")
        deepinfra_token = self.settings.get("deepinfra_token", "")
        
        self.is_running_agent = True
        self.update_progress(f"Sending to AI via {api_provider}...", True)
        
        def worker():
            try:
                self.log_ai(f"Sending optimized prompt ({len(header)} chars) via {api_provider}...")
                
                # Use the new call_llm with provider parameters
                resp = call_llm(
                    prompt=header,
                    api_provider=api_provider,
                    api_url=api_url,
                    model=model,
                    huggingface_token=huggingface_token,
                    huggingface_model=huggingface_model,
                    huggingface_api_url=huggingface_api_url,  # ADDED
                    replicate_token=replicate_token,
                    together_token=together_token,
                    openrouter_token=openrouter_token,
                    deepinfra_token=deepinfra_token,
                    timeout=180,
                    progress_callback=lambda msg: self.update_progress(f"AI: {msg}", True)
                )
                
                self.log_ai(f"AI response received ({len(resp) if resp else 0} chars)")
                
                # Parse the response
                start = resp.find("{")
                explanation = ""
                
                if start != -1:
                    try:
                        # Try to extract JSON
                        json_text = resp[start:]
                        # Simple JSON extraction - find matching braces
                        brace_count = 0
                        end_pos = start
                        for i, char in enumerate(resp[start:]):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_pos = start + i + 1
                                    break
                        
                        if end_pos > start:
                            json_str = resp[start:end_pos]
                            js = json.loads(json_str)
                            
                            # Store suggested changes
                            self.ai_suggested_changes = js
                            
                            # Extract explanation
                            explanation = resp[end_pos:].strip()
                            
                            # Update what_changed box
                            self.what_changed.configure(state="normal")
                            self.what_changed.delete("1.0", "end")
                            self.what_changed.insert("end", f"AI suggested changes for {len(js)} file(s):\n\n")
                            for fname in js.keys():
                                self.what_changed.insert("end", f"• {fname}\n")
                            self.what_changed.insert("end", f"\nExplanation:\n{explanation}\n\n")
                            self.what_changed.insert("end", "Click 'Apply AI Changes' to apply.")
                            self.what_changed.see("end")
                            self.what_changed.configure(state="disabled")
                            
                            self.update_progress(f"AI ready - {len(js)} file(s) suggested", False)
                        else:
                            raise json.JSONDecodeError("No valid JSON found", json_text, 0)
                            
                    except Exception as e:
                        self.log_ai(f"Note: Could not parse JSON from AI response: {e}")
                        explanation = resp
                        self.what_changed.configure(state="normal")
                        self.what_changed.delete("1.0", "end")
                        self.what_changed.insert("end", f"AI Response:\n\n{resp}")
                        self.what_changed.configure(state="disabled")
                        self.update_progress("AI completed (text response)", False)
                else:
                    explanation = resp
                    self.what_changed.configure(state="normal")
                    self.what_changed.delete("1.0", "end")
                    self.what_changed.insert("end", f"AI Response:\n\n{resp}")
                    self.what_changed.configure(state="disabled")
                    self.update_progress("AI completed (text response)", False)
                    
            except Exception as e:
                self.log_ai(f"LLM error: {e}")
                self.update_progress(f"AI error: {str(e)[:50]}...", False)
                messagebox.showerror("AI Error", f"LLM call failed: {e}")
            finally:
                self.is_running_agent = False
                self.clear_progress()
                
        threading.Thread(target=worker, daemon=True).start()

    # ---------------- theme / ui ----------------
    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["BG"])
        
        # Configure ttk styles
        self.style.configure("AIDev.TButton", foreground=t["FG"], background=t["BTN"])
        self.style.map("AIDev.TButton", background=[("active", t["BTN_ACTIVE"]), ("pressed", t["BTN_ACTIVE"])])
        self.style.configure("TFrame", background=t.get("FRAME_BG", t["BG"]))
        self.style.configure("TLabel", background=t.get("LABEL_BG", t["BG"]), foreground=t["FG"])
        self.style.configure("TNotebook", background=t.get("FRAME_BG", t["BG"]))
        self.style.configure("TNotebook.Tab", background=t["BTN"], foreground=t["FG"])
        self.style.map("TNotebook.Tab", background=[("selected", t.get("FRAME_BG", t["BG"]))])
        self.style.configure("TLabelframe", background=t.get("FRAME_BG", t["BG"]))
        self.style.configure("TLabelframe.Label", background=t.get("FRAME_BG", t["BG"]), foreground=t["FG"])
        
        # Configure Treeview colors
        self.style.configure("Treeview", 
                           background=t.get("TREE_BG", t["PANEL_BG"]), 
                           foreground=t.get("TREE_FG", t["FG"]),
                           fieldbackground=t.get("TREE_BG", t["PANEL_BG"]))
        self.style.map("Treeview", 
                      background=[("selected", t.get("TREE_SELECT", t["BTN_ACTIVE"]))],
                      foreground=[("selected", t["FG"])])
        
        # Configure Progressbar
        self.style.configure("Horizontal.TProgressbar",
                           background=t.get("PROGRESS_BG", "#0b5c0b"),
                           troughcolor=t.get("BG", "#1e1f23"),
                           bordercolor=t.get("FG", "#d6d6d6"),
                           lightcolor=t.get("PROGRESS_FG", "#00ff00"),
                           darkcolor=t.get("PROGRESS_BG", "#0b5c0b"))
        
        # Update widget colors
        for widget in (self.ai_output, self.script_output, self.chat_text, self.what_changed):
            try:
                widget.configure(bg=t["OUTPUT_BG"] if widget in (self.ai_output, self.script_output) else t["EDITOR_BG"], 
                               fg=t["FG"], insertbackground=t["CURSOR"])
            except Exception:
                pass
        try:
            self.file_listbox.configure(bg=t["PANEL_BG"], fg=t["FG"], selectbackground=t["BTN_ACTIVE"])
        except Exception:
            pass
        for rel, txt in list(self.editor_tabs.items()):
            try:
                txt.configure(bg=t["EDITOR_BG"], fg=t["FG"], insertbackground=t["CURSOR"])
                self.configure_highlight_tags(txt)
                simple_highlight(txt)
            except Exception:
                pass
        self.configure_global_tags()

    def configure_global_tags(self):
        for txt in list(self.editor_tabs.values()):
            self.configure_highlight_tags(txt)

    def configure_highlight_tags(self, text_widget):
        try:
            text_widget.tag_config("kw", foreground="#569CD6")
            text_widget.tag_config("str", foreground="#CE9178")
            text_widget.tag_config("cmt", foreground="#6A9955")
            text_widget.tag_config("num", foreground="#B5CEA8")
            text_widget.tag_config("builtin", foreground="#C586C0")
        except Exception:
            pass

    # ---------------- AI Agents ----------------
    def run_agent(self, agent_type, default_prompt):
        """Run an AI agent with progress tracking"""
        if self.is_running_agent:
            messagebox.showinfo("Agent Busy", "Another agent is already running. Please wait.")
            return
        
        if not self.project_path:
            messagebox.showinfo("No Project", "Please open or create a project first.")
            return
        
        prompt = simpledialog.askstring(f"{agent_type.capitalize()} Agent", 
                                       f"Enter goal for {agent_type} agent:", 
                                       initialvalue=default_prompt)
        if not prompt:
            return
        
        self.is_running_agent = True
        self.update_progress(f"Starting {agent_type} agent...", True)
        
        def worker():
            try:
                api_provider = self.settings.get("api_provider", "ollama")
                api_url = self.settings.get("api_url", "")
                model = self.settings.get("model", "")
                huggingface_token = self.settings.get("huggingface_token", "")
                huggingface_model = self.settings.get("huggingface_model", "microsoft/CodeGPT-small-py")
                huggingface_api_url = self.settings.get("huggingface_api_url", "https://router.huggingface.co")  # FIXED
                replicate_token = self.settings.get("replicate_token", "")
                together_token = self.settings.get("together_token", "")
                openrouter_token = self.settings.get("openrouter_token", "")
                deepinfra_token = self.settings.get("deepinfra_token", "")
                
                if agent_type == "plan":
                    self.update_progress("Planning project...", True)
                    # FIXED: Pass correct number of arguments
                    plan = planner.planner_agent(prompt, api_url, model)
                    self.update_progress(f"Plan created with {len(plan.get('files', []))} files", False)
                    self.log_ai(f"Planner completed: {plan.get('goal', 'No goal')}")
                    
                elif agent_type == "code":
                    self.update_progress("Generating code...", True)
                    files = PROJECT_STATE.get('plan', {}).get('files', ['main.py'])
                    for i, fname in enumerate(files):
                        self.update_progress(f"Generating {fname} ({i+1}/{len(files)})...", True)
                        # FIXED: Pass correct number of arguments
                        coder.coder_agent(self.project_path, api_url, model)
                    self.update_progress(f"Generated {len(files)} files", False)
                    self.log_ai(f"Coder completed: Generated {len(files)} files")
                    self._refresh_file_listbox()
                    
                elif agent_type == "test":
                    self.update_progress("Generating tests...", True)
                    # FIXED: Pass correct number of arguments
                    tester.tester_agent(self.project_path, api_url, model)
                    self.update_progress("Tests generated", False)
                    self.log_ai("Tester completed: Tests generated")
                    self._refresh_file_listbox()
                    
                elif agent_type == "summarize":
                    self.update_progress("Creating summary...", True)
                    # FIXED: Pass correct number of arguments
                    summarizer.summarizer_agent(self.project_path, api_url, model)
                    self.update_progress("Summary created", False)
                    self.log_ai("Summarizer completed")
                    
                messagebox.showinfo("Agent Complete", f"{agent_type.capitalize()} agent completed successfully!")
                
            except Exception as e:
                self.update_progress(f"Error in {agent_type} agent", False)
                self.log_ai(f"{agent_type.capitalize()} agent error: {e}")
                messagebox.showerror("Agent Error", f"{agent_type.capitalize()} agent failed: {e}")
            finally:
                self.is_running_agent = False
                self.clear_progress()
        
        threading.Thread(target=worker, daemon=True).start()

    # ---------------- project tree ----------------
    def new_project(self):
        """Create a new project"""
        folder = filedialog.askdirectory(title="Select Folder for New Project")
        if not folder:
            return
        
        project_name = simpledialog.askstring("Project Name", "Enter project name:")
        if not project_name:
            project_name = "new_project"
        
        project_path = os.path.join(folder, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Create basic structure
        with open(os.path.join(project_path, "README.md"), "w") as f:
            f.write(f"# {project_name}\n\nCreated with AI Dev IDE\n")
        
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write("# Main file\nprint('Hello from AI Dev IDE')")
        
        # Create PORTFOLIO.md
        with open(os.path.join(project_path, "PORTFOLIO.md"), "w") as f:
            f.write(f"# {project_name} - Portfolio\n\n")
            f.write("## Project Description\n\n")
            f.write("This project was created using AI Dev IDE.\n")
        
        self.project_path = project_path
        self.open_existing_project()
        self.log_ai(f"Created new project: {project_name}")

    def open_existing_project(self):
        folder = filedialog.askdirectory(title="Select Project Folder")
        if not folder:
            return
        self.project_path = folder
        # clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        root_node = self.tree.insert("", "end", text=os.path.basename(folder), open=True, values=(folder,))
        self._populate_tree(root_node, folder, folder)
        # clear editor tabs (leave Welcome removable)
        for tab in list(self.notebook.tabs()):
            self.notebook.forget(tab)
        self.editor_tabs.clear()
        self.tab_id_map.clear()
        # re-add Welcome
        wtext = scrolledtext.ScrolledText(self.notebook, height=6, bg=self.theme["EDITOR_BG"], fg=self.theme["FG"], font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]))
        wtext.insert("1.0", "Welcome — double click files in the project tree to open them.\nRight-click a tab to close it. Ctrl+W closes current tab.")
        wtext.configure(state="disabled")
        self.notebook.add(wtext, text="Welcome")
        self._refresh_file_listbox()
        # ensure README and PORTFOLIO exist
        self.ensure_project_docs()
        self.log_ai(f"Loaded project: {folder}")
        self.apply_theme()

    def _populate_tree(self, parent_node, folder_path, base_path):
        try:
            entries = sorted(os.listdir(folder_path))
        except Exception:
            return
        for name in entries:
            full = os.path.join(folder_path, name)
            if os.path.isdir(full):
                node = self.tree.insert(parent_node, "end", text=name, open=False, values=(full,))
                self._populate_tree(node, full, base_path)
            else:
                self.tree.insert(parent_node, "end", text=name, values=(full,))

    def on_tree_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        vals = self.tree.item(item_id, "values")
        if not vals: return
        full = vals[0]
        if os.path.isdir(full):
            cur = self.tree.item(item_id, "open")
            self.tree.item(item_id, open=not cur)
            return
        rel = os.path.relpath(full, self.project_path) if self.project_path else full
        # if already open, select it
        for tid, r in self.tab_id_map.items():
            if r == rel:
                try:
                    self.notebook.select(tid)
                    return
                except Exception:
                    break
        # open file
        try:
            with open(full, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            messagebox.showerror("Open file", str(e)); return
        self._open_file_tab(rel, content)
        self._refresh_file_listbox()

    # ---------------- editor tabs ----------------
    def _open_file_tab(self, relpath, content):
        txt = scrolledtext.ScrolledText(self.notebook, bg=self.theme["EDITOR_BG"], fg=self.theme["FG"], 
                                       font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"]), 
                                       wrap="none", undo=True, insertbackground=self.theme["CURSOR"])
        txt.insert("1.0", content)
        # bindings for editor features
        txt.bind("<<Modified>>", lambda e, t=txt: self.on_text_modified(t))
        txt.bind("<KeyRelease>", lambda e, t=txt: simple_highlight(t))
        txt.bind("<Control-f>", lambda e, t=txt: self.open_find_dialog(t))
        txt.bind("<Control-F>", lambda e, t=txt: self.open_find_dialog(t))
        txt.bind("<Control-g>", lambda e, t=txt: self.goto_line_dialog(t))
        txt.bind("<Control-G>", lambda e, t=txt: self.goto_line_dialog(t))
        txt.bind("<Control-z>", lambda e: txt.edit_undo())
        txt.bind("<Control-y>", lambda e: txt.edit_redo())
        txt.bind("<Control-a>", lambda e, t=txt: (t.tag_add("sel", "1.0", "end"), "break"))
        self.notebook.add(txt, text=relpath)
        tabs = self.notebook.tabs()
        tab_id = tabs[-1]
        self.editor_tabs[relpath] = txt
        self.tab_id_map[tab_id] = relpath
        self.configure_highlight_tags(txt)
        simple_highlight(txt)
        self.apply_theme()

    def _refresh_file_listbox(self):
        self.file_listbox.delete(0, tk.END)
        if not self.project_path:
            return
        for root_dir, _, files in os.walk(self.project_path):
            for f in files:
                rel = os.path.relpath(os.path.join(root_dir, f), self.project_path)
                self.file_listbox.insert(tk.END, rel)

    # ---------------- tab management ----------------
    def on_tab_right_click(self, event):
        try:
            self.tab_menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def close_current_tab(self):
        sel = self.notebook.select()
        if not sel:
            return
        title = self.notebook.tab(sel, "text")
        try:
            rel = self.tab_id_map.get(sel)
            self.notebook.forget(sel)
            if sel in self.tab_id_map:
                del self.tab_id_map[sel]
            if rel and rel in self.editor_tabs:
                del self.editor_tabs[rel]
        except Exception:
            pass

    # ---------------- settings window ----------------
    def open_settings(self):
        if self.settings_window and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            return
        self.settings_window = tk.Toplevel(self.root)
        sw = self.settings_window
        sw.title("Settings")
        sw.geometry("700x850")
        sw.configure(bg=self.theme.get("FRAME_BG", self.theme["BG"]))
        sw.protocol("WM_DELETE_WINDOW", lambda: self._close_settings(save=True))
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(sw, bg=self.theme.get("FRAME_BG", self.theme["BG"]), highlightthickness=0)
        scrollbar = ttk.Scrollbar(sw, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0,8))
        
        # Prompt Optimization Section (NEW)
        ttk.Label(scrollable_frame, text="Prompt Optimization:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(12,4))
        
        # Max files to send
        max_files_frame = ttk.Frame(scrollable_frame)
        max_files_frame.pack(fill="x", padx=8, pady=4)
        ttk.Label(max_files_frame, text="Max files to send:").pack(side="left", padx=(0,6))
        self.max_files_var = tk.IntVar(value=self.prompt_opts.get("max_files", 5))
        max_files_spin = ttk.Spinbox(max_files_frame, from_=1, to=20, textvariable=self.max_files_var, width=5)
        max_files_spin.pack(side="left")
        ttk.Label(max_files_frame, text="(reduces prompt size)", foreground="#888888").pack(side="left", padx=(6,0))
        
        # Max chars per file
        max_chars_frame = ttk.Frame(scrollable_frame)
        max_chars_frame.pack(fill="x", padx=8, pady=4)
        ttk.Label(max_chars_frame, text="Max chars per file:").pack(side="left", padx=(0,6))
        self.max_chars_var = tk.IntVar(value=self.prompt_opts.get("max_chars_per_file", 1500))
        max_chars_spin = ttk.Spinbox(max_chars_frame, from_=500, to=5000, increment=500, 
                                    textvariable=self.max_chars_var, width=5)
        max_chars_spin.pack(side="left")
        ttk.Label(max_chars_frame, text="(truncates large files)", foreground="#888888").pack(side="left", padx=(6,0))
        
        # Use summaries
        self.use_summaries_var = tk.BooleanVar(value=self.prompt_opts.get("use_summaries", True))
        ttk.Checkbutton(scrollable_frame, text="Use intelligent file summaries", 
                       variable=self.use_summaries_var).pack(anchor="w", padx=8, pady=4)
        
        # Send only modified files
        self.send_modified_var = tk.BooleanVar(value=self.prompt_opts.get("send_only_modified", False))
        ttk.Checkbutton(scrollable_frame, text="Send only modified files", 
                       variable=self.send_modified_var).pack(anchor="w", padx=8, pady=4)
        
        # Optimization info
        info_text = "💡 These settings help reduce prompt size and improve AI response time."
        ttk.Label(scrollable_frame, text=info_text, foreground="#888888", 
                 wraplength=650).pack(anchor="w", padx=8, pady=(4,0))
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        # Theme Presets Section
        ttk.Label(scrollable_frame, text="Theme Presets:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(4,4))
        
        preset_frame = ttk.Frame(scrollable_frame)
        preset_frame.pack(fill="x", padx=8, pady=4)
        
        all_presets = list(THEME_PRESETS.keys()) + list(self.settings.get("custom_presets", {}).keys())
        
        ttk.Label(preset_frame, text="Load Preset:").pack(side="left", padx=(0,6))
        preset_var = tk.StringVar(value="Dark")
        preset_dropdown = ttk.Combobox(preset_frame, textvariable=preset_var, values=all_presets, state="readonly", width=20)
        preset_dropdown.pack(side="left", padx=6)
        
        def load_preset():
            preset_name = preset_var.get()
            if preset_name in THEME_PRESETS:
                self.theme = THEME_PRESETS[preset_name].copy()
            elif preset_name in self.settings.get("custom_presets", {}):
                self.theme = self.settings["custom_presets"][preset_name].copy()
            else:
                messagebox.showerror("Error", f"Preset '{preset_name}' not found")
                return
            self.settings["theme"] = self.theme
            self.apply_theme()
            self._close_settings(save=True)
            self.root.after(100, self.open_settings)
        
        ttk.Button(preset_frame, text="Load", style="AIDev.TButton", command=load_preset).pack(side="left", padx=6)
        
        # Save custom preset
        save_preset_frame = ttk.Frame(scrollable_frame)
        save_preset_frame.pack(fill="x", padx=8, pady=4)
        
        ttk.Label(save_preset_frame, text="Save Current as:").pack(side="left", padx=(0,6))
        preset_name_entry = ttk.Entry(save_preset_frame, width=20)
        preset_name_entry.pack(side="left", padx=6)
        
        def save_custom_preset():
            name = preset_name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a preset name")
                return
            if name in THEME_PRESETS:
                messagebox.showerror("Error", f"Cannot overwrite built-in preset '{name}'")
                return
            if "custom_presets" not in self.settings:
                self.settings["custom_presets"] = {}
            self.settings["custom_presets"][name] = self.theme.copy()
            save_settings(self.settings)
            messagebox.showinfo("Success", f"Preset '{name}' saved!")
            preset_name_entry.delete(0, tk.END)
            all_presets = list(THEME_PRESETS.keys()) + list(self.settings.get("custom_presets", {}).keys())
            preset_dropdown['values'] = all_presets
        
        ttk.Button(save_preset_frame, text="Save Preset", style="AIDev.TButton", command=save_custom_preset).pack(side="left", padx=6)
        
        def delete_custom_preset():
            preset_name = preset_var.get()
            if preset_name in THEME_PRESETS:
                messagebox.showerror("Error", "Cannot delete built-in presets")
                return
            if preset_name not in self.settings.get("custom_presets", {}):
                messagebox.showerror("Error", f"Preset '{preset_name}' not found")
                return
            if messagebox.askyesno("Confirm", f"Delete preset '{preset_name}'?"):
                del self.settings["custom_presets"][preset_name]
                save_settings(self.settings)
                all_presets = list(THEME_PRESETS.keys()) + list(self.settings.get("custom_presets", {}).keys())
                preset_dropdown['values'] = all_presets
                preset_var.set("Dark")
                messagebox.showinfo("Success", f"Preset '{preset_name}' deleted")
        
        ttk.Button(save_preset_frame, text="Delete", style="AIDev.TButton", command=delete_custom_preset).pack(side="left", padx=6)
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        # API Provider Section
        ttk.Label(scrollable_frame, text="API Provider:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(12,4))

        provider_frame = ttk.Frame(scrollable_frame)
        provider_frame.pack(fill="x", padx=8, pady=4)

        self.api_provider_var = tk.StringVar(value=self.settings.get("api_provider", "ollama"))

        ttk.Label(provider_frame, text="Select Provider:").pack(side="left", padx=(0,6))
        provider_dropdown = ttk.Combobox(
            provider_frame, 
            textvariable=self.api_provider_var,
            values=["ollama", "huggingface", "replicate", "together", "openrouter", "deepinfra"],
            state="readonly",
            width=15
        )
        provider_dropdown.pack(side="left", padx=6)

        # Provider info label
        provider_info = ttk.Label(scrollable_frame, text="", foreground="#888888", wraplength=650)
        provider_info.pack(anchor="w", padx=8, pady=(0,8))

        def update_provider_info(*args):
            provider = self.api_provider_var.get()
            info_text = {
                "ollama": "📍 Local models. Requires Ollama installation.",
                "huggingface": "✅ Recommended! Free API. Get token at huggingface.co/settings/tokens",
                "replicate": "⚡ $5 free credits. Get token at replicate.com/account",
                "together": "🤝 Free credits. Get token at api.together.xyz/settings/api-keys",
                "openrouter": "🌐 Free models. Get token at openrouter.ai/keys",
                "deepinfra": "🚀 Free tier. Get token at deepinfra.com/dash/api_keys"
            }.get(provider, "")
            provider_info.config(text=info_text)

        self.api_provider_var.trace("w", update_provider_info)
        update_provider_info()

        # Provider-specific frames
        self.provider_frames = {}

        # Ollama frame
        ollama_frame = ttk.LabelFrame(scrollable_frame, text="Ollama Settings", padding=6)
        self.provider_frames["ollama"] = ollama_frame

        ttk.Label(ollama_frame, text="API URL:").pack(anchor="w", padx=4, pady=(4,0))
        self.api_url_var = tk.StringVar(value=self.settings.get("api_url", "http://localhost:11434/api/generate"))
        api_ent = ttk.Entry(ollama_frame, textvariable=self.api_url_var, width=70)
        api_ent.pack(fill="x", padx=4, pady=4)

        ttk.Label(ollama_frame, text="Model:").pack(anchor="w", padx=4, pady=(4,0))
        self.model_var = tk.StringVar(value=self.settings.get("model", "tinyllama:1.1b"))
        model_ent = ttk.Entry(ollama_frame, textvariable=self.model_var, width=40)
        model_ent.pack(fill="x", padx=4, pady=4)

        # Hugging Face frame
        hf_frame = ttk.LabelFrame(scrollable_frame, text="Hugging Face Settings", padding=6)
        self.provider_frames["huggingface"] = hf_frame

        ttk.Label(hf_frame, text="API URL:").pack(anchor="w", padx=4, pady=(4,0))  # ADDED
        self.hf_api_url_var = tk.StringVar(value=self.settings.get("huggingface_api_url", "https://router.huggingface.co"))  # FIXED
        hf_api_ent = ttk.Entry(hf_frame, textvariable=self.hf_api_url_var, width=70)
        hf_api_ent.pack(fill="x", padx=4, pady=4)

        ttk.Label(hf_frame, text="API Token:").pack(anchor="w", padx=4, pady=(4,0))
        self.hf_token_var = tk.StringVar(value=self.settings.get("huggingface_token", ""))
        hf_token_ent = ttk.Entry(hf_frame, textvariable=self.hf_token_var, width=60, show="*")
        hf_token_ent.pack(fill="x", padx=4, pady=4)

        def toggle_hf_token():
            if hf_token_ent.cget('show') == '*':
                hf_token_ent.config(show='')
                toggle_hf_btn.config(text="Hide")
            else:
                hf_token_ent.config(show='*')
                toggle_hf_btn.config(text="Show")

        toggle_hf_btn = ttk.Button(hf_frame, text="Show", command=toggle_hf_token)
        toggle_hf_btn.pack(anchor="w", padx=4, pady=(0,4))

        ttk.Label(hf_frame, text="Model ID:").pack(anchor="w", padx=4, pady=(4,0))
        self.hf_model_var = tk.StringVar(value=self.settings.get("huggingface_model", "microsoft/CodeGPT-small-py"))
        hf_model_ent = ttk.Entry(hf_frame, textvariable=self.hf_model_var, width=60)
        hf_model_ent.pack(fill="x", padx=4, pady=4)

        hf_models = [
            "microsoft/CodeGPT-small-py",
            "codellama/CodeLlama-7b-hf",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "google/gemma-7b-it",
            "HuggingFaceH4/zephyr-7b-beta"
        ]

        ttk.Label(hf_frame, text="Quick select:", foreground="#888888").pack(anchor="w", padx=4, pady=(4,0))
        ttk.Combobox(hf_frame, textvariable=self.hf_model_var, values=hf_models, state="readonly", width=50).pack(fill="x", padx=4, pady=4)

        # Show/hide frames
        def show_provider_frame(provider):
            for frame_name, frame in self.provider_frames.items():
                frame.pack_forget()
            if provider in self.provider_frames:
                self.provider_frames[provider].pack(fill="x", padx=8, pady=4)

        show_provider_frame(self.api_provider_var.get())
        self.api_provider_var.trace("w", lambda *args: show_provider_frame(self.api_provider_var.get()))
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        # GitHub Configuration Section
        ttk.Label(scrollable_frame, text="GitHub Configuration:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(4,4))
        
        ttk.Label(scrollable_frame, text="GitHub Token (for repository creation):").pack(anchor="w", padx=8, pady=(8,0))
        github_frame = ttk.Frame(scrollable_frame)
        github_frame.pack(fill="x", padx=8, pady=4)
        
        self.github_token_var = tk.StringVar(value=self.settings.get("github_token", ""))
        github_ent = ttk.Entry(github_frame, textvariable=self.github_token_var, width=50, show="*")
        github_ent.pack(side="left", fill="x", expand=True, padx=(0,6))
        
        def toggle_token_visibility():
            if github_ent.cget('show') == '*':
                github_ent.config(show='')
                show_btn.config(text="Hide")
            else:
                github_ent.config(show='*')
                show_btn.config(text="Show")
        
        show_btn = ttk.Button(github_frame, text="Show", style="AIDev.TButton", command=toggle_token_visibility)
        show_btn.pack(side="left", padx=(0,6))
        
        test_github_btn = ttk.Button(github_frame, text="Test Connection", style="AIDev.TButton", command=self.test_github_connection)
        test_github_btn.pack(side="left")
        
        help_text = "Get a token from: https://github.com/settings/tokens\nRequired scopes: repo"
        help_label = ttk.Label(scrollable_frame, text=help_text, foreground="#888888", font=(self.theme["FONT_FAMILY"], 9))
        help_label.pack(anchor="w", padx=8, pady=(0,8))
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        # LLM Test Section
        ttk.Label(scrollable_frame, text="LLM Test:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(4,4))
        
        def test_llm():
            api_provider = self.api_provider_var.get()
            api_url = self.api_url_var.get().strip()
            model = self.model_var.get().strip()
            hf_token = self.hf_token_var.get().strip()
            hf_model = self.hf_model_var.get().strip()
            hf_api_url = self.hf_api_url_var.get().strip()  # ADDED
            
            if api_provider == "ollama":
                if not api_url:
                    messagebox.showerror("Error", "Please enter an API URL for Ollama")
                    return
                if not model:
                    messagebox.showerror("Error", "Please enter a model name for Ollama")
                    return
            elif api_provider == "huggingface":
                if not hf_token:
                    messagebox.showerror("Error", "Please enter a Hugging Face token")
                    return
                if not hf_model:
                    messagebox.showerror("Error", "Please enter a model ID for Hugging Face")
                    return
                    
            self.update_progress("Testing LLM connection...", True)
            try:
                # Import call_llm here to avoid circular imports
                from core.llm import call_llm
                
                resp = call_llm(
                    prompt="Say 'Hello' in a creative way",
                    api_provider=api_provider,
                    api_url=api_url if api_provider == "ollama" else hf_api_url,  # FIXED
                    model=model if api_provider == "ollama" else hf_model,
                    huggingface_token=hf_token if api_provider == "huggingface" else "",
                    huggingface_model=hf_model if api_provider == "huggingface" else "",
                    huggingface_api_url=hf_api_url if api_provider == "huggingface" else "",  # ADDED
                    timeout=30
                )
                self.log_ai("LLM test response: " + (resp[:200] if isinstance(resp, str) else str(resp)))
                self.update_progress("LLM test successful!", False)
                messagebox.showinfo("LLM Test", "LLM responded successfully!")
            except Exception as e:
                error_msg = str(e)
                self.log_ai("LLM error: " + error_msg)
                self.update_progress("LLM test failed", False)
                messagebox.showerror("LLM Test Failed", error_msg)
        
        def diagnose_connection():
            api_provider = self.api_provider_var.get()
            
            if api_provider != "ollama":
                messagebox.showinfo("Diagnostics", f"Diagnostics currently only available for Ollama. For {api_provider}, please check their documentation.")
                return
                
            api_url = self.api_url_var.get().strip()
            base_url = api_url.replace('/api/generate', '') if '/api/generate' in api_url else api_url.replace('/api/chat', '')
            
            self.update_progress("Running connection diagnostics...", True)
            self.log_ai("=== Connection Diagnostics ===")
            
            # Test 1: Basic connectivity
            self.log_ai("Test 1: Checking if Ollama is running...")
            try:
                import socket
                host = "127.0.0.1" if "127.0.0.1" in api_url else "localhost"
                port = 11434
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    self.log_ai(f"✓ Port {port} is open and accepting connections")
                else:
                    self.log_ai(f"✗ Port {port} is NOT accepting connections (error code: {result})")
                    self.log_ai("  → Run 'ollama serve' in a terminal")
                    self.update_progress("Diagnostics complete", False)
                    return
            except Exception as e:
                self.log_ai(f"✗ Socket test failed: {e}")
                self.update_progress("Diagnostics complete", False)
                return
            
            # Test 2: API endpoint
            self.log_ai("Test 2: Checking API endpoint...")
            try:
                r = requests.get(f"{base_url}/api/tags", timeout=5)
                if r.status_code == 200:
                    self.log_ai(f"✓ API endpoint responding")
                    models = r.json().get('models', [])
                    self.log_ai(f"  Available models: {', '.join([m['name'] for m in models])}")
                else:
                    self.log_ai(f"✗ API returned status {r.status_code}")
            except Exception as e:
                self.log_ai(f"✗ API endpoint failed: {e}")
                self.update_progress("Diagnostics complete", False)
                return
            
            # Test 3: Model availability
            model_name = self.model_var.get().strip()
            self.log_ai(f"Test 3: Checking if model '{model_name}' exists...")
            try:
                r = requests.get(f"{base_url}/api/tags", timeout=5)
                models_data = r.json()
                available = [model['name'] for model in models_data.get('models', [])]
                if any(model_name in model_name_avail or model_name_avail.startswith(model_name) for model_name_avail in available):
                    self.log_ai(f"✓ Model '{model_name}' is available")
                else:
                    self.log_ai(f"✗ Model '{model_name}' NOT found")
                    self.log_ai(f"  → Run: ollama pull {model_name}")
                    self.log_ai(f"  → Or use one of: {', '.join(available)}")
            except Exception as e:
                self.log_ai(f"✗ Model check failed: {e}")
            
            self.log_ai("=== Diagnostics Complete ===")
            self.update_progress("Diagnostics complete", False)
            messagebox.showinfo("Diagnostics", "Diagnostics complete.")
        
        test_frame = ttk.Frame(scrollable_frame)
        test_frame.pack(fill="x", padx=8, pady=6)
        ttk.Button(test_frame, text="Test Connection", style="AIDev.TButton", command=test_llm).pack(side="left", padx=(0,6))
        ttk.Button(test_frame, text="Run Diagnostics", style="AIDev.TButton", command=diagnose_connection).pack(side="left")
        
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        # Color pickers
        ttk.Label(scrollable_frame, text="Custom Theme Colors:", font=(self.theme["FONT_FAMILY"], self.theme["FONT_SIZE"], "bold")).pack(anchor="w", padx=8, pady=(4,4))
        colors_frame = ttk.Frame(scrollable_frame)
        colors_frame.pack(fill="both", padx=8, pady=8)
        def add_color_row(label_text, key):
            row = ttk.Frame(colors_frame)
            row.pack(fill="x", pady=6)
            ttk.Label(row, text=label_text, width=18).pack(side="left")
            sw_preview = tk.Label(row, width=4, relief="sunken", bg=self.theme[key])
            sw_preview.pack(side="left", padx=6)
            def choose():
                col = colorchooser.askcolor(title=f"Choose {label_text}", initialcolor=self.theme[key])[1]
                if col:
                    self.theme[key] = col
                    sw_preview.configure(bg=col)
                    self.apply_theme()
                    self.settings["theme"] = self.theme
            btn = ttk.Button(row, text="Choose", style="AIDev.TButton", command=choose)
            btn.pack(side="left", padx=6)
        add_color_row("Window background", "BG")
        add_color_row("Text (FG)", "FG")
        add_color_row("Editor background", "EDITOR_BG")
        add_color_row("Button color", "BTN")
        add_color_row("Button active", "BTN_ACTIVE")
        
        def choose_cursor():
            col = colorchooser.askcolor(title="Choose Cursor Color", initialcolor=self.theme["CURSOR"])[1]
            if col:
                self.theme["CURSOR"] = col
                self.apply_theme()
                self.settings["theme"] = self.theme
        ttk.Button(scrollable_frame, text="Choose Cursor Color", style="AIDev.TButton", command=choose_cursor).pack(padx=8, pady=(4,8), anchor="w")
        
        # Apply / save / close
        def apply_settings():
            # Save provider settings
            self.settings["api_provider"] = self.api_provider_var.get()
            self.settings["api_url"] = self.api_url_var.get().strip()
            self.settings["model"] = self.model_var.get().strip()
            self.settings["huggingface_token"] = self.hf_token_var.get().strip()
            self.settings["huggingface_model"] = self.hf_model_var.get().strip()
            self.settings["huggingface_api_url"] = self.hf_api_url_var.get().strip()  # ADDED
            self.settings["github_token"] = self.github_token_var.get().strip()
            self.settings["theme"] = self.theme
            # Save prompt optimization settings
            self.settings["prompt_optimization"] = {
                "max_files": self.max_files_var.get(),
                "max_chars_per_file": self.max_chars_var.get(),
                "use_summaries": self.use_summaries_var.get(),
                "send_only_modified": self.send_modified_var.get()
            }
            self.prompt_opts = self.settings["prompt_optimization"]
            save_settings(self.settings)
            self.apply_theme()
            messagebox.showinfo("Settings", "Settings saved.")
        def apply_and_close():
            apply_settings()
            self._close_settings(save=False)
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill="x", padx=8, pady=8)
        ttk.Button(btn_frame, text="Apply", style="AIDev.TButton", command=apply_settings).pack(side="right", padx=6)
        ttk.Button(btn_frame, text="Apply and Close", style="AIDev.TButton", command=apply_and_close).pack(side="right", padx=6)

    def _close_settings(self, save=True):
        if save:
            # Save provider settings
            if hasattr(self, 'api_provider_var'):
                self.settings["api_provider"] = self.api_provider_var.get()
            if hasattr(self, 'api_url_var'):
                self.settings["api_url"] = self.api_url_var.get().strip()
            if hasattr(self, 'model_var'):
                self.settings["model"] = self.model_var.get().strip()
            if hasattr(self, 'hf_token_var'):
                self.settings["huggingface_token"] = self.hf_token_var.get().strip()
            if hasattr(self, 'hf_model_var'):
                self.settings["huggingface_model"] = self.hf_model_var.get().strip()
            if hasattr(self, 'hf_api_url_var'):  # ADDED
                self.settings["huggingface_api_url"] = self.hf_api_url_var.get().strip()
            if hasattr(self, 'github_token_var'):
                self.settings["github_token"] = self.github_token_var.get().strip()
            self.settings["theme"] = self.theme
            if "custom_presets" not in self.settings:
                self.settings["custom_presets"] = {}
            save_settings(self.settings)
        try:
            self.settings_window.destroy()
        except Exception:
            pass
        self.settings_window = None

    # ---------------- save/run/tests/fixes ----------------
    def save_all_open_files(self):
        if not self.project_path:
            self.project_path = tempfile.mkdtemp(prefix="ai_project_")
        saved = {}
        for rel, txt in self.editor_tabs.items():
            content = txt.get("1.0", "end-1c")
            full = os.path.join(self.project_path, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(content)
            saved[rel] = content
        self.log_ai(f"Saved {len(saved)} open files")
        return saved

    def save_and_run(self):
        self.update_progress("Saving files...", True)
        saved = self.save_all_open_files()
        sel = self.file_listbox.curselection()
        if sel:
            rel = self.file_listbox.get(sel[0])
            target = os.path.join(self.project_path, rel)
        else:
            try:
                target_rel = PROJECT_STATE.get("plan", {}).get("entrypoint", "main.py")
            except Exception:
                target_rel = "main.py"
            target = os.path.join(self.project_path, target_rel)
            if not os.path.exists(target):
                pyfiles = []
                for root_dir, _, files in os.walk(self.project_path):
                    for f in files:
                        if f.endswith(".py"):
                            pyfiles.append(os.path.join(root_dir, f))
                if pyfiles:
                    target = pyfiles[0]
        if not os.path.exists(target):
            self.log_script(f"Target script not found: {target}")
            self.update_progress("Script not found", False)
            return
        def worker():
            self.update_progress(f"Running {os.path.basename(target)}...", True)
            self.log_script(f"Running {target} ...")
            res = run_script_capture(target, cwd=self.project_path)
            self.log_script(res.get("stdout", ""))
            self.log_script(res.get("stderr", ""))
            if not res["ok"]:
                self.log_ai("Script failed.")
                self.update_progress("Script failed", False)
            else:
                self.log_ai("Run OK.")
                self.update_progress("Script executed successfully", False)
        threading.Thread(target=worker, daemon=True).start()

    def run_tests_and_show(self):
        if not self.project_path:
            messagebox.showinfo("No project", "Open or create a project first.")
            return
            
        def worker():
            self.update_progress("Running tests...", True)
            self.log_script("Running pytest ...")
            res = run_pytest_capture(self.project_path)
            self.log_script(res.get("stdout", ""))
            self.log_script(res.get("stderr", ""))
            tests_running = []
            stdout = res.get("stdout", "")
            for line in stdout.splitlines():
                if "::" in line:
                    tests_running.append(line.strip())
                if line.strip().startswith("collected"):
                    tests_running.append(line.strip())
            if tests_running:
                self.log_ai("Tests seen: " + "; ".join(tests_running))
            self.update_progress(f"Tests completed", False)
        threading.Thread(target=worker, daemon=True).start()

    def auto_generate_tests(self):
        if not self.project_path:
            messagebox.showinfo("No project", "Open or create a project first.")
            return
            
        self.run_agent("test", "Generate tests for the current project")

    def suggest_fixes(self):
        if not self.project_path:
            messagebox.showinfo("No project", "Open or create a project first.")
            return
            
        if self.is_running_agent:
            messagebox.showinfo("Busy", "Please wait for current operation to complete.")
            return
            
        error_log = self.script_output.get("1.0", "end-1c").strip()
        if not error_log:
            self.log_ai("No script output to use for fixes. Run a script first.")
            return
            
        # Optimize error log
        if len(error_log) > 2000:
            error_log = error_log[:2000] + "\n... [error log truncated] ..."
            
        sel = [self.file_listbox.get(i) for i in self.file_listbox.curselection()] or list(self.editor_tabs.keys())
        
        # Apply optimization limits
        max_files = self.prompt_opts.get("max_files", 5)
        selected_files = sel[:max_files]
        
        if len(sel) > max_files:
            self.log_ai(f"Note: Only analyzing {max_files} of {len(sel)} files for optimization.")
        
        # Build optimized context
        files_context = {}
        total_chars = 0
        max_total_chars = 6000
        
        for rel in selected_files:
            if total_chars > max_total_chars:
                self.log_ai(f"Note: Stopped adding files due to size limit")
                break
            
            content = self.get_optimized_file_content(rel)
            files_context[rel] = content
            total_chars += len(content)
        
        prompt = "Fix these errors:\n\n"
        prompt += error_log + "\n\n"
        prompt += f"Files ({len(files_context)} files, ~{total_chars} chars):\n"
        
        for k, v in files_context.items():
            prompt += f"\n--- {k} ---\n{v}\n"
        
        prompt += "\nProvide fixes as JSON mapping filename->new_content, then explanation."
        
        # Get provider settings
        api_provider = self.settings.get("api_provider", "ollama")
        api_url = self.settings.get("api_url", "")
        model = self.settings.get("model", "")
        huggingface_token = self.settings.get("huggingface_token", "")
        huggingface_model = self.settings.get("huggingface_model", "microsoft/CodeGPT-small-py")
        huggingface_api_url = self.settings.get("huggingface_api_url", "https://router.huggingface.co")  # FIXED
        replicate_token = self.settings.get("replicate_token", "")
        together_token = self.settings.get("together_token", "")
        openrouter_token = self.settings.get("openrouter_token", "")
        deepinfra_token = self.settings.get("deepinfra_token", "")
        
        self.is_running_agent = True
        self.update_progress("Analyzing errors...", True)
        
        def worker():
            try:
                self.log_ai(f"Requesting fixes (optimized prompt: {len(prompt)} chars)...")
                # Use the new call_llm with provider parameters
                resp = call_llm(
                    prompt=prompt,
                    api_provider=api_provider,
                    api_url=api_url,
                    model=model,
                    huggingface_token=huggingface_token,
                    huggingface_model=huggingface_model,
                    huggingface_api_url=huggingface_api_url,  # ADDED
                    replicate_token=replicate_token,
                    together_token=together_token,
                    openrouter_token=openrouter_token,
                    deepinfra_token=deepinfra_token,
                    timeout=240,
                    progress_callback=lambda msg: self.update_progress(f"AI Fixes: {msg}", True)
                )
                
                start = resp.find("{")
                if start == -1:
                    self.what_changed.configure(state="normal")
                    self.what_changed.delete("1.0", "end")
                    self.what_changed.insert("end", resp)
                    self.what_changed.configure(state="disabled")
                    self.update_progress("AI completed (no JSON)", False)
                    return
                
                # Try to extract JSON
                json_text = resp[start:]
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(json_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    json_str = json_text[:end_pos]
                    js = json.loads(json_str)
                    
                    self.ai_suggested_changes = js
                    
                    explanation = resp[start + len(json_str):].strip()
                    
                    self.what_changed.configure(state="normal")
                    self.what_changed.delete("1.0", "end")
                    self.what_changed.insert("end", f"AI suggested fixes for {len(js)} file(s):\n\n")
                    for fname in js.keys():
                        self.what_changed.insert("end", f"• {fname}\n")
                    self.what_changed.insert("end", f"\nExplanation:\n{explanation}\n\n")
                    self.what_changed.insert("end", "Click 'Apply AI Changes' to apply.")
                    self.what_changed.see("end")
                    self.what_changed.configure(state="disabled")
                    
                    self.update_progress(f"AI fixes ready - {len(js)} file(s)", False)
                    
                else:
                    self.what_changed.configure(state="normal")
                    self.what_changed.insert("end", "Could not parse AI response:\n\n" + resp)
                    self.what_changed.configure(state="disabled")
                    self.update_progress("AI completed (parse error)", False)
                    
            except Exception as e:
                self.log_ai(f"LLM error: {e}")
                self.update_progress(f"AI error", False)
                messagebox.showerror("AI Error", f"LLM call failed: {e}")
            finally:
                self.is_running_agent = False
                self.clear_progress()
        threading.Thread(target=worker, daemon=True).start()

    def _auto_fix_from_error(self, error_text):
        self.script_output.insert("end", "\n[Auto-fix initiated]\n")
        self.script_output.see("end")
        self.suggest_fixes()

    # ---------------- exports & dependencies ----------------
    def export_project(self):
        folder = filedialog.askdirectory(title="Export Project")
        if not folder:
            return
            
        self.update_progress("Exporting project...", True)
        saved = self.save_all_open_files()
        save_project_files(saved, folder)
        deps = infer_dependencies([os.path.join(self.project_path, f) for f in saved.keys()]) if self.project_path else []
        if deps:
            write_requirements(os.path.join(folder, "requirements.txt"), deps)
            if messagebox.askyesno("Install dependencies?", f"Detected {len(deps)} dependencies. Install now?"):
                self.update_progress("Installing dependencies...", True)
                install_requirements(folder)
        self.log_ai(f"Exported project to {folder}")
        self.update_progress("Project exported successfully", False)

    # ---------------- editor helpers (find/replace/goto) ----------------
    def open_find_dialog(self, text_widget=None):
        if text_widget is None:
            sel = self.notebook.select()
            text_widget = self.editor_tabs.get(self.tab_id_map.get(sel)) if sel else None
        if text_widget is None:
            messagebox.showinfo("Find", "Open a file to search in.")
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Find and Replace")
        ttk.Label(dlg, text="Find:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        find_ent = ttk.Entry(dlg, width=40)
        find_ent.grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(dlg, text="Replace:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        replace_ent = ttk.Entry(dlg, width=40)
        replace_ent.grid(row=1, column=1, padx=6, pady=6)
        def do_find():
            text_widget.tag_remove("find", "1.0", "end")
            needle = find_ent.get()
            if not needle:
                return
            idx = "1.0"
            while True:
                idx = text_widget.search(needle, idx, nocase=1, stopindex="end")
                if not idx:
                    break
                end = f"{idx}+{len(needle)}c"
                text_widget.tag_add("find", idx, end)
                idx = end
            text_widget.tag_config("find", background="#444444", foreground=self.theme["FG"])
        def do_replace():
            s = text_widget.get("1.0", "end-1c")
            s2 = s.replace(find_ent.get(), replace_ent.get())
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", s2)
            simple_highlight(text_widget)
        ttk.Button(dlg, text="Find", style="AIDev.TButton", command=do_find).grid(row=2, column=0, padx=6, pady=8)
        ttk.Button(dlg, text="Replace All", style="AIDev.TButton", command=do_replace).grid(row=2, column=1, padx=6, pady=8)

    def goto_line_dialog(self, text_widget=None):
        if text_widget is None:
            sel = self.notebook.select()
            text_widget = self.editor_tabs.get(self.tab_id_map.get(sel)) if sel else None
        if text_widget is None:
            messagebox.showinfo("Go to line", "Open a file first.")
            return
        ln = simpledialog.askinteger("Go to line", "Line number:", minvalue=1)
        if not ln:
            return
        text_widget.mark_set("insert", f"{ln}.0")
        text_widget.see(f"{ln}.0")

    # ---------------- text modified handler -> highlight ----------------
    def on_text_modified(self, text_widget):
        try:
            simple_highlight(text_widget)
            text_widget.edit_modified(False)
        except Exception:
            pass

    # ---------------- logging helpers ----------------
    def log_ai(self, *parts):
        try:
            self.ai_output.insert("end", " ".join(map(str, parts)) + "\n")
            self.ai_output.see("end")
        except Exception:
            pass

    def log_script(self, *parts):
        try:
            self.script_output.insert("end", " ".join(map(str, parts)) + "\n")
            self.script_output.see("end")
        except Exception:
            pass

    # ---------------- app close ----------------
    def on_close(self):
        self.settings["theme"] = self.theme
        save_settings(self.settings)
        try:
            self.root.destroy()
        except Exception:
            pass

# ---------------- run ----------------
def main():
    root = tk.Tk()
    app = AIDevIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()

    
"""
Make it so that this script provides a meaningful backtest on both the csv data files and the pkl ai models to see if it will return a profit in a real market. Only edit the 3_backtest.py script because all the other models are built using other scripts.
"""