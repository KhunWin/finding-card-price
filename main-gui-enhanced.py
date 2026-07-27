import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from main_tcg_extract import TCGCSVScraperGUI


class ModernButton(tk.Canvas):
    """Custom modern button with gradient and hover effects"""
    def __init__(self, parent, text, command, bg_color, hover_color, **kwargs):
        super().__init__(parent, height=45, highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text = text
        self.is_enabled = True
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        self.draw_button(bg_color)
        
    def draw_button(self, color):
        self.delete('all')
        width = self.winfo_width() if self.winfo_width() > 1 else 200
        height = 45
        
        # Rounded rectangle
        radius = 8
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, 0, width, radius*2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, height-radius*2, width, height, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(radius, 0, width-radius, height, fill=color, outline=color)
        self.create_rectangle(0, radius, width, height-radius, fill=color, outline=color)
        
        # Text
        text_color = '#ffffff' if self.is_enabled else '#7d7d7d'
        self.create_text(width/2, height/2, text=self.text, fill=text_color, 
                        font=('Arial', 12, 'bold'))
    
    def _on_enter(self, event):
        if self.is_enabled:
            self.draw_button(self.hover_color)
    
    def _on_leave(self, event):
        if self.is_enabled:
            self.draw_button(self.bg_color)
    
    def _on_click(self, event):
        if self.is_enabled and self.command:
            self.command()
    
    def set_enabled(self, enabled):
        self.is_enabled = enabled
        color = self.bg_color if enabled else '#3d3d3d'
        self.draw_button(color)
        self.config(cursor='hand2' if enabled else 'arrow')


class TCGScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎴 TCG Card Scraper")
        self.root.geometry("1000x750")
        self.root.configure(bg='#0d1117')
        
        self.scraper_thread = None
        self.is_running = False
        
        # Configure style
        self.setup_styles()
        
        # Create GUI
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_dark = '#0d1117'
        bg_medium = '#161b22'
        bg_light = '#21262d'
        border_color = '#30363d'
        text_color = '#c9d1d9'
        accent_color = '#58a6ff'
        
        style.configure('TFrame', background=bg_dark)
        style.configure('Card.TFrame', background=bg_medium, relief='flat')
        style.configure('TLabel', background=bg_dark, foreground=text_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground=accent_color)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground='#8b949e')
        style.configure('CardTitle.TLabel', background=bg_medium, foreground=text_color, 
                       font=('Segoe UI', 12, 'bold'))
        style.configure('TCheckbutton', background=bg_medium, foreground=text_color, 
                       font=('Segoe UI', 10))
        
        # Entry style
        style.configure('Modern.TEntry', fieldbackground=bg_light, foreground=text_color,
                       bordercolor=border_color, lightcolor=border_color, darkcolor=border_color)
        
    def create_widgets(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#0d1117')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Header Section
        header_frame = tk.Frame(main_frame, bg='#0d1117')
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title = ttk.Label(header_frame, text="🎴 TCG Card Scraper", style='Title.TLabel')
        title.pack()
        
        subtitle = ttk.Label(header_frame, text="Extract card data and images from TCG databases", 
                            style='Subtitle.TLabel')
        subtitle.pack(pady=(5, 0))
        
        # Input Card
        input_card = self.create_card(main_frame, "📋 Input Parameters")
        input_card.pack(fill=tk.X, pady=(0, 15))
        
        # Category IDs
        self.create_input_row(input_card, "Category IDs:", "85", 
                             "e.g., 1, 3, 85 (comma-separated)")
        self.category_entry = input_card.entry
        
        # Group IDs
        self.create_input_row(input_card, "Group IDs:", "", 
                             "e.g., 24721, 24653 (leave empty for all)")
        self.group_entry = input_card.entry
        
        # Settings Card
        settings_card = self.create_card(main_frame, "⚙️ Settings")
        settings_card.pack(fill=tk.X, pady=(0, 15))
        
        # Output Folder
        folder_frame = tk.Frame(settings_card, bg='#161b22')
        folder_frame.pack(fill=tk.X, padx=20, pady=8)
        
        tk.Label(folder_frame, text="Output Folder:", bg='#161b22', fg='#c9d1d9',
                font=('Segoe UI', 10), width=15, anchor='w').pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_entry = tk.Entry(folder_frame, bg='#21262d', fg='#c9d1d9',
                                     font=('Segoe UI', 10), relief='flat', 
                                     insertbackground='#c9d1d9')
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.folder_entry.insert(0, os.path.expanduser('~/Desktop'))
        
        browse_btn = tk.Button(folder_frame, text="📁 Browse", command=self.browse_folder,
                              bg='#238636', fg='white', font=('Segoe UI', 9, 'bold'),
                              relief='flat', cursor='hand2', padx=15, pady=8)
        browse_btn.pack(side=tk.LEFT)
        
        # Download Images Section
        download_frame = tk.Frame(settings_card, bg='#161b22')
        download_frame.pack(fill=tk.X, padx=20, pady=12)
        
        self.download_images_var = tk.BooleanVar(value=True)
        download_cb = tk.Checkbutton(download_frame, text="📷 Download Images", 
                                    variable=self.download_images_var,
                                    command=self.toggle_image_size,
                                    bg='#161b22', fg='#c9d1d9', selectcolor='#21262d',
                                    font=('Segoe UI', 10, 'bold'), cursor='hand2',
                                    activebackground='#161b22', activeforeground='#58a6ff')
        download_cb.pack(side=tk.LEFT)
        
        # Image Size
        size_frame = tk.Frame(settings_card, bg='#161b22')
        size_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
        
        tk.Label(size_frame, text="Image Resolution:", bg='#161b22', fg='#c9d1d9',
                font=('Segoe UI', 10), width=15, anchor='w').pack(side=tk.LEFT, padx=(0, 10))
        
        self.image_size_var = tk.StringVar(value="_400w (400 width)")
        self.image_size_combo = ttk.Combobox(size_frame, textvariable=self.image_size_var,
                                            values=["_200w (200 width)", "_400w (400 width)", 
                                                   "_in_1000x1000 (1000x1000)"],
                                            state="readonly", font=('Segoe UI', 10))
        self.image_size_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.image_size_combo.current(1)
        
        # Progress Section
        progress_card = self.create_card(main_frame, "📊 Progress")
        progress_card.pack(fill=tk.X, pady=(0, 15))
        
        progress_content = tk.Frame(progress_card, bg='#161b22')
        progress_content.pack(fill=tk.X, padx=20, pady=12)
        
        self.progress_var = tk.StringVar(value="Ready to start")
        progress_label = tk.Label(progress_content, textvariable=self.progress_var,
                                 bg='#161b22', fg='#8b949e', font=('Segoe UI', 9))
        progress_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.progress_bar = ttk.Progressbar(progress_content, mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X)
        
        # Console Card
        console_card = self.create_card(main_frame, "💻 Console Output")
        console_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        console_content = tk.Frame(console_card, bg='#161b22')
        console_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.console = scrolledtext.ScrolledText(console_content, height=12,
                                                 bg='#0d1117', fg='#c9d1d9',
                                                 font=('Consolas', 9), wrap=tk.WORD,
                                                 relief='flat', insertbackground='#c9d1d9')
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Control Buttons
        button_frame = tk.Frame(main_frame, bg='#0d1117')
        button_frame.pack(fill=tk.X)
        
        # Create custom buttons
        btn_container = tk.Frame(button_frame, bg='#0d1117')
        btn_container.pack(fill=tk.X)
        
        self.start_btn = ModernButton(btn_container, "▶  START SCRAPING", 
                                      self.start_scraping, '#238636', '#2ea043')
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.stop_btn = ModernButton(btn_container, "⏹  STOP", 
                                     self.stop_scraping, '#da3633', '#e04649')
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.stop_btn.set_enabled(False)
        
        self.reset_btn = ModernButton(btn_container, "🔄  RESET", 
                                      self.reset_fields, '#1f6feb', '#388bfd')
        self.reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind resize event to redraw buttons
        self.root.bind('<Configure>', self._on_resize)
        
        # Initial messages
        self.append_log("🎉 Welcome to TCG Card Scraper!\n", "cyan")
        self.append_log("Configure your settings above and click 'START SCRAPING' to begin.\n\n", "white")
        
    def _on_resize(self, event):
        """Redraw buttons on window resize"""
        if hasattr(self, 'start_btn'):
            self.start_btn.draw_button(self.start_btn.bg_color)
            self.stop_btn.draw_button(self.stop_btn.bg_color if self.stop_btn.is_enabled else '#3d3d3d')
            self.reset_btn.draw_button(self.reset_btn.bg_color)
    
    def create_card(self, parent, title):
        """Create a card-style container"""
        card = tk.Frame(parent, bg='#161b22', relief='flat')
        
        title_frame = tk.Frame(card, bg='#161b22')
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        title_label = tk.Label(title_frame, text=title, bg='#161b22', fg='#c9d1d9',
                              font=('Segoe UI', 12, 'bold'), anchor='w')
        title_label.pack(side=tk.LEFT)
        
        return card
    
    def create_input_row(self, parent, label_text, default_value, placeholder):
        """Create an input row with label and entry"""
        row_frame = tk.Frame(parent, bg='#161b22')
        row_frame.pack(fill=tk.X, padx=20, pady=8)
        
        label = tk.Label(row_frame, text=label_text, bg='#161b22', fg='#c9d1d9',
                        font=('Segoe UI', 10), width=15, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row_frame, bg='#21262d', fg='#c9d1d9',
                        font=('Segoe UI', 10), relief='flat', insertbackground='#c9d1d9')
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        entry.insert(0, default_value)
        
        parent.entry = entry  # Store reference
        return entry
    
    def toggle_image_size(self):
        """Enable/disable image size selection based on download checkbox"""
        if self.download_images_var.get():
            self.image_size_combo.config(state="readonly")
            self.append_log("✅ Image downloading enabled.\n", "green")
        else:
            self.image_size_combo.config(state="disabled")
            self.append_log("⚠️  Image downloading disabled.\n", "yellow")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def reset_fields(self):
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, "85")
        self.group_entry.delete(0, tk.END)
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, os.path.expanduser('~/Desktop'))
        self.download_images_var.set(True)
        self.image_size_combo.current(1)
        self.image_size_combo.config(state="readonly")
        self.console.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.progress_var.set("Ready to start")
        self.append_log("🔄 Fields reset to default values.\n\n", "yellow")
    
    def append_log(self, message, color="white"):
        color_map = {
            "white": "#c9d1d9",
            "cyan": "#58a6ff",
            "green": "#3fb950",
            "lightgreen": "#7ee787",
            "yellow": "#d29922",
            "orange": "#f0883e",
            "red": "#f85149"
        }
        
        tag_name = f"color_{color}"
        if tag_name not in self.console.tag_names():
            self.console.tag_config(tag_name, foreground=color_map.get(color, color_map["white"]))
        
        self.console.insert(tk.END, message, tag_name)
        self.console.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total):
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_bar['maximum'] = total
            self.progress_bar['value'] = current
            self.progress_var.set(f"Processing: {current}/{total} groups ({progress_percent:.1f}%)")
        self.root.update_idletasks()
    
    def start_scraping(self):
        # Validate inputs
        category_ids = [c.strip() for c in self.category_entry.get().split(',') if c.strip()]
        if not category_ids:
            messagebox.showerror("Input Error", "Please enter at least one Category ID.")
            return
        
        group_ids_text = self.group_entry.get().strip()
        group_ids = [g.strip() for g in group_ids_text.split(',') if g.strip()] if group_ids_text else None
        
        output_folder = self.folder_entry.get().strip()
        if not output_folder or not os.path.exists(output_folder):
            messagebox.showerror("Folder Error", "Please select a valid output folder.")
            return
        
        # Get image size value
        size_text = self.image_size_var.get()
        if '_200w' in size_text:
            image_size = '_200w'
        elif '_400w' in size_text:
            image_size = '_400w'
        else:
            image_size = '_in_1000x1000'
        
        # Clear console
        self.console.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.progress_var.set("Starting scraper...")
        
        # Update button states
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.reset_btn.set_enabled(False)
        
        # Start scraper in thread
        self.is_running = True
        self.scraper_thread = threading.Thread(
            target=self.run_scraper,
            args=(category_ids, group_ids, output_folder, self.download_images_var.get(), image_size),
            daemon=True
        )
        self.scraper_thread.start()
    
    def run_scraper(self, category_ids, group_ids, output_folder, download_images, image_size):
        try:
            scraper = TCGCSVScraperGUI(
                category_ids=category_ids,
                group_ids=group_ids,
                output_folder=output_folder,
                app_name='TCGScraperGUI',
                download_images=download_images,
                image_size=image_size,
                log_callback=self.thread_safe_log,
                progress_callback=self.thread_safe_progress,
                is_running_callback=lambda: self.is_running
            )
            stats = scraper.scrape_data()
            self.root.after(0, self.scraping_finished, True, "Scraping completed successfully!", stats)
        except Exception as e:
            self.thread_safe_log(f"❌ Error: {str(e)}\n", "red")
            self.root.after(0, self.scraping_finished, False, f"Error: {str(e)}", {})
    
    def thread_safe_log(self, message, color="white"):
        self.root.after(0, self.append_log, message, color)
    
    def thread_safe_progress(self, current, total):
        self.root.after(0, self.update_progress, current, total)
    
    def stop_scraping(self):
        self.append_log("\n⚠️  Stopping scraper... Please wait.\n", "yellow")
        self.is_running = False
        self.stop_btn.set_enabled(False)
    
    def scraping_finished(self, success, message, stats):
        self.start_btn.set_enabled(True)
        self.stop_btn.set_enabled(False)
        self.reset_btn.set_enabled(True)
        self.progress_var.set("✅ Completed" if success else "❌ Failed")
        
        if success:
            details = f"""✅ Scraping completed successfully!

📊 Statistics:
• Groups processed: {stats.get('groups', 0)}
• Products scraped: {stats.get('products', 0)}
• API requests made: {stats.get('requests', 0)}
• Time elapsed: {stats.get('time', 0) / 60:.2f} minutes
"""
            
            if self.download_images_var.get():
                details += f"""
📷 Image Downloads:
• Downloaded: {stats.get('images_downloaded', 0)}
• Failed: {stats.get('images_failed', 0)}
• Location: {os.path.join(self.folder_entry.get(), 'downloaded_images')}
"""
            
            if stats.get('csv_file'):
                details += f"""
💾 Output:
• CSV file: {stats.get('csv_file')}
"""
            
            messagebox.showinfo("✅ Scraping Complete", details)
        else:
            messagebox.showerror("❌ Error", f"Scraping failed:\n{message}")


def main():
    root = tk.Tk()
    app = TCGScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
