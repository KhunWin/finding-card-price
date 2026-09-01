"""
Selection Window - Choose between TCG and Yuyu-Tei scraper
"""
import tkinter as tk
from tkinter import ttk

class SelectionWindow:
    """Initial window to select scraping source"""
    
    def __init__(self, root, on_tcg_selected, on_yuyutei_selected):
        self.root = root
        self.on_tcg_selected = on_tcg_selected
        self.on_yuyutei_selected = on_yuyutei_selected
        
        self.root.title("Card Scraper - Select Source")
        self.root.geometry("500x600")
        self.root.configure(bg='#1e1e1e')
        
        # Center window
        self.center_window()
        
        # Title
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(pady=40)
        
        title_label = tk.Label(
            title_frame,
            text="🎴 Card Scraper",
            font=('Segoe UI', 24, 'bold'),
            fg='#00d4ff',
            bg='#1e1e1e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Choose your data source",
            font=('Segoe UI', 12),
            fg='#b0b0b0',
            bg='#1e1e1e'
        )
        subtitle_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg='#1e1e1e')
        buttons_frame.pack(pady=20)
        
        # TCG Button
        tcg_btn = tk.Button(
            buttons_frame,
            text="🌐 TCG CSV\n\nScrape from tcgcsv.com",
            font=('Segoe UI', 12, 'bold'),
            bg='#0078d4',
            fg='white',
            activebackground='#005a9e',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=20,
            height=5,
            command=self.select_tcg
        )
        tcg_btn.pack(pady=10)
        
        # Yuyu-Tei Button
        yuyutei_btn = tk.Button(
            buttons_frame,
            text="🎯 Yuyu-Tei\n\nScrape from yuyu-tei.jp",
            font=('Segoe UI', 12, 'bold'),
            bg='#00b894',
            fg='white',
            activebackground='#00a083',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=20,
            height=5,
            command=self.select_yuyutei
        )
        yuyutei_btn.pack(pady=10)
        
        # Footer
        footer_label = tk.Label(
            self.root,
            text="Select a source to begin scraping",
            font=('Segoe UI', 10),
            fg='#808080',
            bg='#1e1e1e'
        )
        footer_label.pack(side='bottom', pady=20)
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def select_tcg(self):
        """User selected TCG"""
        self.root.destroy()
        self.on_tcg_selected()
    
    def select_yuyutei(self):
        """User selected Yuyu-Tei"""
        self.root.destroy()
        self.on_yuyutei_selected()
