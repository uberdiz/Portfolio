"""
Free API Setup Guide for AI Dev IDE
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

class SetupGuide:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Free API Setup Guide")
        self.window.geometry("600x500")
        self.window.configure(bg="#f0f0f0")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title = tk.Label(self.window, text="🚀 Free API Setup Guide", 
                        font=("Arial", 18, "bold"), bg="#f0f0f0")
        title.pack(pady=20)
        
        # Instructions frame
        frame = ttk.LabelFrame(self.window, text="Step-by-Step Guide", padding=20)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Steps
        steps = [
            ("1. Get Hugging Face Token", 
             "Visit huggingface.co and create an account.\nGet your API token from Settings > Access Tokens.",
             "https://huggingface.co/settings/tokens"),
            
            ("2. Configure in AI Dev IDE", 
             "In Settings > AI tab:\n- Select 'huggingface' as API Provider\n- Paste your token\n- Use model: microsoft/CodeGPT-small-py", None),
            
            ("3. Alternative: Ollama (Local)", 
             "Install Ollama from ollama.ai\nRun: ollama pull codellama\nUse API URL: http://localhost:11434/api/generate",
             "https://ollama.ai"),
            
            ("4. Alternative: OpenAI (Paid)", 
             "Get API key from platform.openai.com\nSelect 'openai' provider and paste key",
             "https://platform.openai.com/api-keys"),
        ]
        
        for i, (step_title, description, url) in enumerate(steps):
            step_frame = ttk.Frame(frame)
            step_frame.pack(fill="x", pady=10)
            
            # Step number
            num_label = tk.Label(step_frame, text=f"●", font=("Arial", 14), 
                                fg="#007acc", bg="#f0f0f0")
            num_label.pack(side="left", padx=(0, 10))
            
            # Step content
            content_frame = ttk.Frame(step_frame)
            content_frame.pack(side="left", fill="x", expand=True)
            
            title_label = tk.Label(content_frame, text=step_title, 
                                  font=("Arial", 12, "bold"), bg="#f0f0f0", 
                                  anchor="w", justify="left")
            title_label.pack(anchor="w")
            
            desc_label = tk.Label(content_frame, text=description, 
                                 font=("Arial", 10), bg="#f0f0f0", 
                                 anchor="w", justify="left", wraplength=500)
            desc_label.pack(anchor="w", pady=(2, 0))
            
            # Link button if URL exists
            if url:
                link_btn = ttk.Button(content_frame, text="Open Link",
                                     command=lambda u=url: webbrowser.open(u))
                link_btn.pack(anchor="w", pady=(5, 0))
        
        # Test button
        test_frame = ttk.Frame(self.window)
        test_frame.pack(pady=20)
        
        ttk.Button(test_frame, text="Test Hugging Face Connection", 
                  command=self.test_huggingface).pack(side="left", padx=5)
        
        ttk.Button(test_frame, text="Close", 
                  command=self.window.destroy).pack(side="left", padx=5)
    
    def test_huggingface(self):
        """Test Hugging Face connection"""
        messagebox.showinfo("Test Connection", 
                          "After configuring your token in Settings:\n"
                          "1. Go to AI Dev IDE Settings\n"
                          "2. Click 'Test Connection'\n"
                          "3. If successful, you'll see 'Hello' response")
    
    def run(self):
        """Run the setup guide"""
        self.window.mainloop()

if __name__ == "__main__":
    guide = SetupGuide()
    guide.run()