##main_tcg_exract.py
##main-gui-tkinter.py
#build_exe.py (for converting it into exe file)

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from main_tcg_extract import TCGCSVScraperGUI


class ModernButton(tk.Canvas):
    """Custom modern button with gradient and hover effects"""
    def __init__(self, parent, text, command, bg_color, hover_color, icon="", **kwargs):
        super().__init__(parent, height=50, highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text = text
        self.icon = icon
        self.is_enabled = True
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        self.draw_button(bg_color)
        
    def draw_button(self, color):
        self.delete('all')
        width = self.winfo_width() if self.winfo_width() > 1 else 200
        height = 50
        
        # Rounded rectangle with shadow effect
        radius = 10
        
        # Shadow - FIXED: Use standard 6-digit hex color
        shadow_offset = 2
        shadow_color = '#1a1a1a'
        self.create_arc(shadow_offset, shadow_offset, radius*2+shadow_offset, radius*2+shadow_offset, 
                       start=90, extent=90, fill=shadow_color, outline=shadow_color)
        self.create_arc(width-radius*2+shadow_offset, shadow_offset, width+shadow_offset, radius*2+shadow_offset, 
                       start=0, extent=90, fill=shadow_color, outline=shadow_color)
        self.create_arc(shadow_offset, height-radius*2+shadow_offset, radius*2+shadow_offset, height+shadow_offset, 
                       start=180, extent=90, fill=shadow_color, outline=shadow_color)
        self.create_arc(width-radius*2+shadow_offset, height-radius*2+shadow_offset, width+shadow_offset, height+shadow_offset, 
                       start=270, extent=90, fill=shadow_color, outline=shadow_color)
        self.create_rectangle(radius+shadow_offset, shadow_offset, width-radius+shadow_offset, height+shadow_offset, 
                            fill=shadow_color, outline=shadow_color)
        self.create_rectangle(shadow_offset, radius+shadow_offset, width+shadow_offset, height-radius+shadow_offset, 
                            fill=shadow_color, outline=shadow_color)
        
        # Main button
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, 0, width, radius*2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, height-radius*2, width, height, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(radius, 0, width-radius, height, fill=color, outline=color)
        self.create_rectangle(0, radius, width, height-radius, fill=color, outline=color)
        
        # Text with icon
        text_color = '#ffffff' if self.is_enabled else '#7d7d7d'
        display_text = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(width/2, height/2, text=display_text, fill=text_color, 
                        font=('Segoe UI', 11, 'bold'))
    
    def _on_enter(self, event):
        if self.is_enabled:
            self.draw_button(self.hover_color)
            self.config(cursor='hand2')
    
    def _on_leave(self, event):
        if self.is_enabled:
            self.draw_button(self.bg_color)
    
    def _on_click(self, event):
        if self.is_enabled and self.command:
            # Click animation
            self.draw_button(self.hover_color)
            self.after(100, lambda: self.draw_button(self.bg_color) if self.is_enabled else None)
            self.command()
    
    def set_enabled(self, enabled):
        self.is_enabled = enabled
        color = self.bg_color if enabled else '#2d2d2d'
        self.draw_button(color)
        self.config(cursor='hand2' if enabled else 'arrow')


class ScrollableFrame(tk.Frame):
    """A scrollable frame that works with tkinter"""
    def __init__(self, parent, bg_color, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create the scrollable frame inside the canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        # Add the scrollable frame to the canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind canvas resize to adjust inner frame width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Mouse wheel binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_canvas_configure(self, event):
        """Resize the inner frame to match canvas width"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


class TCGScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCG Card Scraper Pro")
        self.root.geometry("1100x850")
        self.root.configure(bg='#0a0e1a')
        
        # Minimum window size
        self.root.minsize(900, 600)
        
        # Center window on screen
        self.center_window()
        
        self.scraper_thread = None
        self.is_running = False
        
        # Configure style
        self.setup_styles()
        
        # Create GUI
        self.create_widgets()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color palette
        bg_dark = '#0a0e1a'
        bg_medium = '#141824'
        bg_light = '#1e2332'
        border_color = '#2a3142'
        text_color = '#e6eaef'
        accent_color = '#6366f1'
        
        style.configure('TFrame', background=bg_dark)
        style.configure('Card.TFrame', background=bg_medium, relief='flat')
        style.configure('TLabel', background=bg_dark, foreground=text_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 28, 'bold'), foreground=accent_color)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 12), foreground='#9ca3af')
        
    def create_widgets(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#0a0e1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Header Section with gradient effect
        header_frame = tk.Frame(main_frame, bg='#0a0e1a')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_container = tk.Frame(header_frame, bg='#0a0e1a')
        title_container.pack()
        
        title = tk.Label(title_container, text="🎴 TCG Card Scraper Pro", 
                        bg='#0a0e1a', fg='#6366f1',
                        font=('Segoe UI', 32, 'bold'))
        title.pack()
        
        subtitle = tk.Label(title_container, text="Professional card data extraction and image downloading tool", 
                           bg='#0a0e1a', fg='#9ca3af',
                           font=('Segoe UI', 12))
        subtitle.pack(pady=(8, 0))
        
        # Divider
        divider = tk.Frame(header_frame, bg='#2a3142', height=2)
        divider.pack(fill=tk.X, pady=(15, 0))
        
        # Content area with cards - using PanedWindow for resizable columns
        content_paned = tk.PanedWindow(main_frame, bg='#0a0e1a', orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left column - SCROLLABLE
        left_column_outer = tk.Frame(content_paned, bg='#0a0e1a', width=500)
        content_paned.add(left_column_outer, stretch="always")
        
        # Create scrollable frame for left column
        self.left_scrollable = ScrollableFrame(left_column_outer, bg_color='#0a0e1a')
        self.left_scrollable.pack(fill=tk.BOTH, expand=True)
        left_column = self.left_scrollable.scrollable_frame
        
        # Input Card
        input_card = self.create_card(left_column, "📋 Input Configuration")
        input_card.pack(fill=tk.X, pady=(0, 20))
        
        # Category IDs
        self.category_entry = self.create_input_row(input_card, "Category IDs", "85", 
                                                     "e.g., 1, 3, 85 (comma-separated)")
        
        # Group IDs
        self.group_entry = self.create_input_row(input_card, "Group IDs (Optional)", "", 
                                                  "e.g., 24721, 24653 (leave empty for all)")
        
        # Output Folder
        self.create_folder_selector(input_card)
        
        # Download Settings Card
        download_card = self.create_card(left_column, "📷 Download Settings")
        download_card.pack(fill=tk.X, pady=(0, 20))
        
        self.create_download_settings(download_card)
        
        # Right column - NOT scrollable, fixed
        right_column = tk.Frame(content_paned, bg='#0a0e1a', width=500)
        content_paned.add(right_column, stretch="always")
        
        # Progress Card
        progress_card = self.create_card(right_column, "📊 Progress Monitor")
        progress_card.pack(fill=tk.X, pady=(0, 20))
        
        self.create_progress_section(progress_card)
        
        # Console Card
        console_card = self.create_card(right_column, "💻 Console Output")
        console_card.pack(fill=tk.BOTH, expand=True)
        
        self.create_console(console_card)
        
        # Control Buttons at the bottom - OUTSIDE content area, always visible
        self.create_control_buttons(main_frame)
        
        # Initial messages
        self.append_log("=" * 60 + "\n", "cyan")
        self.append_log("🎉 Welcome to TCG Card Scraper Pro!\n", "cyan")
        self.append_log("=" * 60 + "\n\n", "cyan")
        self.append_log("📌 Quick Start Guide:\n", "lightgreen")
        self.append_log("   1. Configure your Category and Group IDs\n", "white")
        self.append_log("   2. Select output folder location\n", "white")
        self.append_log("   3. Choose image download preferences\n", "white")
        self.append_log("   4. Click 'START SCRAPING' to begin\n\n", "white")
        self.append_log("✨ Ready to scrape!\n\n", "green")
        
    def create_card(self, parent, title):
        """Create an enhanced card-style container"""
        # Card container with border
        card_border = tk.Frame(parent, bg='#2a3142', bd=0)
        card_border.pack(fill=tk.X)
        
        card = tk.Frame(card_border, bg='#141824')
        card.pack(fill=tk.X, padx=1, pady=1)
        
        # Title bar with accent
        title_bar = tk.Frame(card, bg='#1e2332', height=50)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        # Accent line
        accent_line = tk.Frame(title_bar, bg='#6366f1', width=4)
        accent_line.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(title_bar, text=title, bg='#1e2332', fg='#e6eaef',
                              font=('Segoe UI', 13, 'bold'), anchor='w')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Content area
        content = tk.Frame(card, bg='#141824')
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        card.content = content
        return card
    
    def create_input_row(self, parent, label_text, default_value, placeholder):
        """Create an enhanced input row"""
        row_frame = tk.Frame(parent.content, bg='#141824')
        row_frame.pack(fill=tk.X, pady=10)
        
        label = tk.Label(row_frame, text=label_text, bg='#141824', fg='#9ca3af',
                        font=('Segoe UI', 10, 'bold'), anchor='w')
        label.pack(anchor=tk.W, pady=(0, 8))
        
        entry_container = tk.Frame(row_frame, bg='#1e2332', bd=0)
        entry_container.pack(fill=tk.X)
        
        entry = tk.Entry(entry_container, bg='#1e2332', fg='#e6eaef',
                        font=('Segoe UI', 11), relief='flat', insertbackground='#6366f1',
                        bd=0)
        entry.pack(fill=tk.X, padx=15, pady=12)
        entry.insert(0, default_value)
        
        # Placeholder hint
        hint = tk.Label(row_frame, text=placeholder, bg='#141824', fg='#6b7280',
                       font=('Segoe UI', 9), anchor='w')
        hint.pack(anchor=tk.W, pady=(5, 0))
        
        return entry
    
    def create_folder_selector(self, parent):
        """Create folder selection section"""
        row_frame = tk.Frame(parent.content, bg='#141824')
        row_frame.pack(fill=tk.X, pady=10)
        
        label = tk.Label(row_frame, text="Output Folder", bg='#141824', fg='#9ca3af',
                        font=('Segoe UI', 10, 'bold'), anchor='w')
        label.pack(anchor=tk.W, pady=(0, 8))
        
        folder_container = tk.Frame(row_frame, bg='#141824')
        folder_container.pack(fill=tk.X)
        
        entry_frame = tk.Frame(folder_container, bg='#1e2332')
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.folder_entry = tk.Entry(entry_frame, bg='#1e2332', fg='#e6eaef',
                                     font=('Segoe UI', 11), relief='flat', 
                                     insertbackground='#6366f1', bd=0)
        self.folder_entry.pack(fill=tk.X, padx=15, pady=12)
        self.folder_entry.insert(0, os.path.expanduser('~/Desktop'))
        
        browse_btn = tk.Button(folder_container, text="📁 Browse", command=self.browse_folder,
                              bg='#6366f1', fg='white', font=('Segoe UI', 10, 'bold'),
                              relief='flat', cursor='hand2', padx=25, pady=12,
                              activebackground='#4f46e5', activeforeground='white')
        browse_btn.pack(side=tk.LEFT)
    
    def create_download_settings(self, parent):
        """Create download settings section with toggle"""
        # Download Images Toggle
        toggle_frame = tk.Frame(parent.content, bg='#141824')
        toggle_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.download_images_var = tk.BooleanVar(value=True)
        
        # Custom toggle button
        toggle_container = tk.Frame(toggle_frame, bg='#1e2332')
        toggle_container.pack(fill=tk.X, pady=10, padx=0)
        
        toggle_label_frame = tk.Frame(toggle_container, bg='#1e2332')
        toggle_label_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        icon_label = tk.Label(toggle_label_frame, text="📷", bg='#1e2332', 
                             font=('Segoe UI', 16))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        text_label = tk.Label(toggle_label_frame, text="Download Card Images", 
                             bg='#1e2332', fg='#e6eaef',
                             font=('Segoe UI', 11, 'bold'))
        text_label.pack(side=tk.LEFT)
        
        # Toggle switch
        toggle_switch = tk.Checkbutton(toggle_container, 
                                      variable=self.download_images_var,
                                      command=self.toggle_image_size,
                                      bg='#1e2332', fg='#6366f1', 
                                      selectcolor='#1e2332',
                                      font=('Segoe UI', 12), 
                                      cursor='hand2',
                                      activebackground='#1e2332', 
                                      activeforeground='#6366f1',
                                      relief='flat',
                                      bd=0,
                                      highlightthickness=0)
        toggle_switch.pack(side=tk.RIGHT, padx=20)
        
        # Image Size Selection (initially visible) - FIXED: Use a dedicated container
        self.size_frame_container = tk.Frame(parent.content, bg='#141824')
        self.size_frame_container.pack(fill=tk.X, pady=(0, 10))
        
        self.size_frame = tk.Frame(self.size_frame_container, bg='#141824')
        self.size_frame.pack(fill=tk.X)
        
        size_label = tk.Label(self.size_frame, text="Image Resolution", 
                             bg='#141824', fg='#9ca3af',
                             font=('Segoe UI', 10, 'bold'), anchor='w')
        size_label.pack(anchor=tk.W, pady=(0, 8))
        
        size_options_frame = tk.Frame(self.size_frame, bg='#141824')
        size_options_frame.pack(fill=tk.X)
        
        self.image_size_var = tk.StringVar(value="_400w")
        
        # Radio button style options
        sizes = [
            ("Low (200x200)", "_200w"),
            ("Medium (400x400)", "_400w"),
            ("High (1000x1000)", "_in_1000x1000")
        ]
        
        for i, (text, value) in enumerate(sizes):
            rb_container = tk.Frame(size_options_frame, bg='#1e2332')
            rb_container.pack(fill=tk.X, pady=5)
            
            rb = tk.Radiobutton(rb_container, text=text, variable=self.image_size_var,
                               value=value, bg='#1e2332', fg='#e6eaef',
                               selectcolor='#1e2332', activebackground='#1e2332',
                               activeforeground='#6366f1', font=('Segoe UI', 10),
                               cursor='hand2', relief='flat', bd=0,
                               highlightthickness=0)
            rb.pack(anchor=tk.W, padx=15, pady=10)
    
    def create_progress_section(self, parent):
        """Create enhanced progress section"""
        progress_frame = tk.Frame(parent.content, bg='#141824')
        progress_frame.pack(fill=tk.X, pady=10)
        
        # Status label
        self.progress_var = tk.StringVar(value="Ready to start")
        status_label = tk.Label(progress_frame, textvariable=self.progress_var,
                               bg='#141824', fg='#9ca3af', 
                               font=('Segoe UI', 10, 'bold'))
        status_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Progress bar container
        progress_container = tk.Frame(progress_frame, bg='#1e2332', height=30)
        progress_container.pack(fill=tk.X)
        progress_container.pack_propagate(False)
        
        # Custom progress bar
        self.progress_canvas = tk.Canvas(progress_container, bg='#1e2332', 
                                        height=30, highlightthickness=0)
        self.progress_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.progress_percent = 0
        self.draw_progress_bar()
        
        # Statistics frame
        stats_frame = tk.Frame(progress_frame, bg='#141824')
        stats_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.stats_labels = {}
        stats = [
            ("Groups", "0"),
            ("Products", "0"),
            ("Images", "0")
        ]
        
        for label, value in stats:
            stat_container = tk.Frame(stats_frame, bg='#1e2332')
            stat_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            value_label = tk.Label(stat_container, text=value, bg='#1e2332', 
                                  fg='#6366f1', font=('Segoe UI', 18, 'bold'))
            value_label.pack(pady=(10, 5))
            
            label_text = tk.Label(stat_container, text=label, bg='#1e2332', 
                                 fg='#9ca3af', font=('Segoe UI', 9))
            label_text.pack(pady=(0, 10))
            
            self.stats_labels[label.lower()] = value_label
    
    def draw_progress_bar(self):
        """Draw custom progress bar"""
        self.progress_canvas.delete('all')
        width = self.progress_canvas.winfo_width() if self.progress_canvas.winfo_width() > 1 else 400
        height = 30
        
        # Background
        self.progress_canvas.create_rectangle(0, 0, width, height, fill='#1e2332', outline='')
        
        # Progress fill
        if self.progress_percent > 0:
            progress_width = (width * self.progress_percent) / 100
            self.progress_canvas.create_rectangle(0, 0, progress_width, height, 
                                                 fill='#6366f1', outline='')
        
        # Percentage text
        text_color = '#e6eaef' if self.progress_percent > 50 else '#9ca3af'
        self.progress_canvas.create_text(width/2, height/2, 
                                        text=f"{self.progress_percent:.1f}%",
                                        fill=text_color, font=('Segoe UI', 11, 'bold'))
    
    def create_console(self, parent):
        """Create enhanced console"""
        console_container = tk.Frame(parent.content, bg='#0a0e1a')
        console_container.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(console_container, height=15,
                                                 bg='#0a0e1a', fg='#e6eaef',
                                                 font=('Consolas', 10), wrap=tk.WORD,
                                                 relief='flat', insertbackground='#6366f1',
                                                 bd=0, padx=10, pady=10)
        self.console.pack(fill=tk.BOTH, expand=True)
    
    def create_control_buttons(self, parent):
        """Create enhanced control buttons - FIXED: Always visible at bottom"""
        # Use a dedicated frame that doesn't expand, always at bottom
        button_frame = tk.Frame(parent, bg='#0a0e1a', height=80)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        button_frame.pack_propagate(False)  # Don't shrink
        
        # Inner container for centering
        btn_container = tk.Frame(button_frame, bg='#0a0e1a')
        btn_container.pack(expand=True)
        
        # Start button (green)
        self.start_btn = ModernButton(btn_container, "START SCRAPING", 
                                      self.start_scraping, '#10b981', '#059669',
                                      icon="▶")
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.start_btn.config(width=200)
        
        # Stop button (red)
        self.stop_btn = ModernButton(btn_container, "STOP", 
                                     self.stop_scraping, '#ef4444', '#dc2626',
                                     icon="⏹")
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.stop_btn.config(width=150)
        self.stop_btn.set_enabled(False)
        
        # Reset button (blue)
        self.reset_btn = ModernButton(btn_container, "RESET", 
                                      self.reset_fields, '#6366f1', '#4f46e5',
                                      icon="🔄")
        self.reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.reset_btn.config(width=150)
        
        # Bind resize event
        self.root.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        """Redraw UI elements on window resize"""
        if hasattr(self, 'start_btn'):
            self.start_btn.draw_button(self.start_btn.bg_color)
            self.stop_btn.draw_button(self.stop_btn.bg_color if self.stop_btn.is_enabled else '#2d2d2d')
            self.reset_btn.draw_button(self.reset_btn.bg_color)
        if hasattr(self, 'progress_canvas'):
            self.draw_progress_bar()
    
    def toggle_image_size(self):
        """Show/hide image size options based on download toggle - FIXED"""
        if self.download_images_var.get():
            self.size_frame.pack(fill=tk.X)  # Pack inside the container
            self.append_log("✅ Image downloading enabled\n", "green")
        else:
            self.size_frame.pack_forget()  # Forget only the inner frame, not container
            self.append_log("⚠️  Image downloading disabled\n", "yellow")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.append_log(f"📁 Output folder set to: {folder}\n", "cyan")
    
    def reset_fields(self):
        """Reset all fields to default values"""
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, "85")
        self.group_entry.delete(0, tk.END)
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, os.path.expanduser('~/Desktop'))
        self.download_images_var.set(True)
        self.image_size_var.set("_400w")
        # FIXED: Use the correct frame reference
        self.size_frame.pack(fill=tk.X)
        self.console.delete(1.0, tk.END)
        self.progress_percent = 0
        self.draw_progress_bar()
        self.progress_var.set("Ready to start")
        
        # Reset statistics
        for label in self.stats_labels.values():
            label.config(text="0")
        
        self.append_log("🔄 All fields reset to default values\n\n", "yellow")
    
    def append_log(self, message, color="white"):
        """Add colored message to console"""
        color_map = {
            "white": "#e6eaef",
            "cyan": "#22d3ee",
            "green": "#10b981",
            "lightgreen": "#4ade80",
            "yellow": "#fbbf24",
            "orange": "#f97316",
            "red": "#ef4444"
        }
        
        tag_name = f"color_{color}"
        if tag_name not in self.console.tag_names():
            self.console.tag_config(tag_name, foreground=color_map.get(color, color_map["white"]))
        
        self.console.insert(tk.END, message, tag_name)
        self.console.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total):
        """Update progress bar and statistics"""
        if total > 0:
            self.progress_percent = (current / total) * 100
            self.draw_progress_bar()
            self.progress_var.set(f"Processing: {current}/{total} groups ({self.progress_percent:.1f}%)")
            self.stats_labels['groups'].config(text=str(current))
        self.root.update_idletasks()
    
    def start_scraping(self):
        """Start the scraping process"""
        # Validate inputs
        category_ids = [c.strip() for c in self.category_entry.get().split(',') if c.strip()]
        if not category_ids:
            messagebox.showerror("⚠️ Input Error", "Please enter at least one Category ID.")
            return
        
        group_ids_text = self.group_entry.get().strip()
        group_ids = [g.strip() for g in group_ids_text.split(',') if g.strip()] if group_ids_text else None
        
        output_folder = self.folder_entry.get().strip()
        if not output_folder or not os.path.exists(output_folder):
            messagebox.showerror("⚠️ Folder Error", "Please select a valid output folder.")
            return
        
        # Get image download settings
        download_images = self.download_images_var.get()
        image_size = self.image_size_var.get() if download_images else None
        
        # Clear console
        self.console.delete(1.0, tk.END)
        self.progress_percent = 0
        self.draw_progress_bar()
        self.progress_var.set("Initializing scraper...")
        
        # Reset statistics
        for label in self.stats_labels.values():
            label.config(text="0")
        
        # Update button states
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.reset_btn.set_enabled(False)
        
        # Log start
        self.append_log("=" * 60 + "\n", "cyan")
        self.append_log("🚀 Starting scraping process...\n", "cyan")
        self.append_log("=" * 60 + "\n\n", "cyan")
        self.append_log(f"📋 Category IDs: {', '.join(category_ids)}\n", "white")
        if group_ids:
            self.append_log(f"📦 Group IDs: {', '.join(group_ids)}\n", "white")
        self.append_log(f"📁 Output folder: {output_folder}\n", "white")
        self.append_log(f"📷 Download images: {'Yes' if download_images else 'No'}\n", "white")
        if download_images:
            self.append_log(f"🖼️  Image resolution: {image_size}\n", "white")
        self.append_log("\n")
        
        # Start scraper in thread
        self.is_running = True
        self.scraper_thread = threading.Thread(
            target=self.run_scraper,
            args=(category_ids, group_ids, output_folder, download_images, image_size),
            daemon=True
        )
        self.scraper_thread.start()
    
    def run_scraper(self, category_ids, group_ids, output_folder, download_images, image_size):
        """Run scraper in separate thread"""
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
            self.thread_safe_log(f"\n❌ ERROR: {str(e)}\n", "red")
            self.root.after(0, self.scraping_finished, False, f"Error: {str(e)}", {})
    
    def thread_safe_log(self, message, color="white"):
        """Thread-safe logging"""
        self.root.after(0, self.append_log, message, color)
    
    def thread_safe_progress(self, current, total):
        """Thread-safe progress update"""
        self.root.after(0, self.update_progress, current, total)
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.append_log("\n" + "=" * 60 + "\n", "yellow")
        self.append_log("⚠️  STOPPING SCRAPER - Please wait...\n", "yellow")
        self.append_log("=" * 60 + "\n\n", "yellow")
        self.is_running = False
        self.stop_btn.set_enabled(False)
        self.progress_var.set("Stopping...")
    
    def scraping_finished(self, success, message, stats):
        """Handle scraping completion"""
        self.start_btn.set_enabled(True)
        self.stop_btn.set_enabled(False)
        self.reset_btn.set_enabled(True)
        
        # Update statistics
        if stats:
            self.stats_labels['groups'].config(text=str(stats.get('groups', 0)))
            self.stats_labels['products'].config(text=str(stats.get('products', 0)))
            self.stats_labels['images'].config(text=str(stats.get('images_downloaded', 0)))
        
        if success:
            self.progress_var.set("✅ Completed Successfully!")
            self.progress_percent = 100
            self.draw_progress_bar()
            
            self.append_log("\n" + "=" * 60 + "\n", "green")
            self.append_log("✅ SCRAPING COMPLETED SUCCESSFULLY!\n", "green")
            self.append_log("=" * 60 + "\n\n", "green")
            
            details = f"""✅ Scraping completed successfully!

📊 Final Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
💾 Output File:
• CSV file: {stats.get('csv_file')}
"""
            
            messagebox.showinfo("✅ Success", details)
        else:
            self.progress_var.set("❌ Failed")
            self.append_log("\n" + "=" * 60 + "\n", "red")
            self.append_log("❌ SCRAPING FAILED\n", "red")
            self.append_log("=" * 60 + "\n\n", "red")
            messagebox.showerror("❌ Error", f"Scraping failed:\n\n{message}")


def main():
    root = tk.Tk()
    app = TCGScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()







