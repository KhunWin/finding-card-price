"""
Upload Window for Boutir Product Upload
Handles the GUI and process for uploading products to Boutir
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import logging
from excel_transformer import ExcelTransformer


class UploadWindow:
    """Separate window for handling Boutir product uploads"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Upload to Boutir")
        self.window.geometry("1000x650")
        self.window.configure(bg='#0a0e1a')
        self.window.resizable(True, True)
        
        # Set window icon
        self.set_window_icon()
        
        # Center the window
        self.center_window()
        
        # Variables
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.file_path_var = tk.StringVar(value="No file selected")
        self.transformed_file_path = None
        self.upload_stop_flag = False
        self.transformer = ExcelTransformer()
        
        # Create GUI
        self.create_widgets()
    
    def set_window_icon(self):
        """Set the window icon for both title bar and taskbar"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
            else:
                # When running as PyInstaller executable, try to get from temp directory
                if getattr(sys, 'frozen', False):
                    icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
                    if os.path.exists(icon_path):
                        self.window.iconbitmap(icon_path)
        except Exception as e:
            # Icon setting failed, continue without icon
            print(f"Could not set icon for upload window: {e}")
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_card(self, parent, title):
        """Create a card-style container"""
        card_border = tk.Frame(parent, bg='#2a3142', bd=0)
        card_border.pack(fill=tk.X, pady=(0, 15))
        
        card = tk.Frame(card_border, bg='#141824')
        card.pack(fill=tk.X, padx=1, pady=1)
        
        # Title bar
        title_bar = tk.Frame(card, bg='#1e2332', height=4)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        # Accent line
        accent_line = tk.Frame(title_bar, bg='#8b5cf6', width=10)
        accent_line.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(title_bar, text=title, bg='#1e2332', fg='#e6eaef',
                              font=('Segoe UI', 12, 'bold'), anchor='w')
        title_label.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Content area
        content = tk.Frame(card, bg='#141824')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        card.content = content
        return card
    
    def create_widgets(self):
        """Create all widgets for the upload window"""
        # Main container
        main_frame = tk.Frame(self.window, bg='#0a0e1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Title
        title = tk.Label(main_frame, text="📤 Upload Products to Boutir", 
                        bg='#0a0e1a', fg='#8b5cf6',
                        font=('Segoe UI', 22, 'bold'))
        title.pack(pady=(0, 20))
        
        # Two-column layout
        columns_frame = tk.Frame(main_frame, bg='#0a0e1a')
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN - Credentials and File Selection (with canvas for scrolling)
        left_frame = tk.Frame(columns_frame, bg='#0a0e1a')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        left_canvas = tk.Canvas(left_frame, bg='#0a0e1a', highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
        left_scrollable_frame = tk.Frame(left_canvas, bg='#0a0e1a')
        
        left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        canvas_window = left_canvas.create_window((0, 0), window=left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Bind to update canvas width to match frame width
        def update_canvas_width(event):
            canvas_width = event.width
            left_canvas.itemconfig(canvas_window, width=canvas_width)
        left_canvas.bind('<Configure>', update_canvas_width)
        
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Credentials Card
        cred_card = self.create_card(left_scrollable_frame, "🔐 Boutir Credentials")
        
        # Email input
        email_label = tk.Label(cred_card.content, text="Email Address", 
                              bg='#141824', fg='#9ca3af',
                              font=('Segoe UI', 9, 'bold'), anchor='w')
        email_label.pack(anchor=tk.W, pady=(0, 5))
        
        email_container = tk.Frame(cred_card.content, bg='#1e2332')
        email_container.pack(fill=tk.X, pady=(0, 12))
        
        self.email_entry = tk.Entry(email_container, textvariable=self.email_var,
                                    bg='#1e2332', fg='#e6eaef',
                                    font=('Segoe UI', 11), relief='flat', 
                                    insertbackground='#8b5cf6', bd=0)
        self.email_entry.pack(fill=tk.X, padx=12, pady=10)
        
        # Password input
        pass_label = tk.Label(cred_card.content, text="Password", 
                             bg='#141824', fg='#9ca3af',
                             font=('Segoe UI', 9, 'bold'), anchor='w')
        pass_label.pack(anchor=tk.W, pady=(0, 5))
        
        pass_container = tk.Frame(cred_card.content, bg='#1e2332')
        pass_container.pack(fill=tk.X)
        
        self.pass_entry = tk.Entry(pass_container, textvariable=self.password_var,
                                   bg='#1e2332', fg='#e6eaef',
                                   font=('Segoe UI', 11), relief='flat', 
                                   insertbackground='#8b5cf6', bd=0, show='*')
        self.pass_entry.pack(fill=tk.X, padx=12, pady=10)
        
        # File Selection Card
        file_card = self.create_card(left_scrollable_frame, "📁 Excel File Selection")
        
        file_label = tk.Label(file_card.content, text="Select Excel File (.xlsx, .xls)", 
                             bg='#141824', fg='#9ca3af',
                             font=('Segoe UI', 9, 'bold'), anchor='w')
        file_label.pack(anchor=tk.W, pady=(0, 5))
        
        file_path_container = tk.Frame(file_card.content, bg='#1e2332')
        file_path_container.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path_entry = tk.Entry(file_path_container, textvariable=self.file_path_var,
                                        bg='#1e2332', fg='#9ca3af',
                                        font=('Segoe UI', 9), relief='flat', 
                                        state='normal', bd=0)
        self.file_path_entry.pack(fill=tk.X, padx=12, pady=10)
        self.file_path_entry.config(state='readonly')
        
        browse_file_btn = tk.Button(file_card.content, text="📂 Browse File", 
                                    command=self.browse_excel,
                                    bg='#8b5cf6', fg='white', 
                                    font=('Segoe UI', 10, 'bold'),
                                    relief='flat', cursor='hand2', 
                                    padx=20, pady=10,
                                    activebackground='#7c3aed', 
                                    activeforeground='white')
        browse_file_btn.pack(fill=tk.X)
        
        # Buttons Frame
        buttons_frame = tk.Frame(left_scrollable_frame, bg='#0a0e1a')
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Transform Excel File Button
        self.transform_btn = tk.Button(buttons_frame, text="🔄 Transform Excel File", 
                                       command=self.transform_excel,
                                       bg='#f59e0b', fg='white', 
                                       font=('Segoe UI', 12, 'bold'),
                                       relief='flat', cursor='hand2', 
                                       padx=30, pady=12,
                                       activebackground='#d97706', 
                                       activeforeground='white')
        self.transform_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Stop Button
        self.stop_btn = tk.Button(buttons_frame, text="⏹ Stop", 
                                  command=self.stop_upload,
                                  bg='#ef4444', fg='white', 
                                  font=('Segoe UI', 12, 'bold'),
                                  relief='flat', cursor='hand2', 
                                  padx=30, pady=12,
                                  activebackground='#dc2626', 
                                  activeforeground='white',
                                  state='disabled')
        self.stop_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Run Upload Button
        self.run_btn = tk.Button(buttons_frame, text="▶ RUN UPLOAD", 
                                 command=self.start_upload,
                                 bg='#10b981', fg='white', 
                                 font=('Segoe UI', 14, 'bold'),
                                 relief='flat', cursor='hand2', 
                                 padx=40, pady=15,
                                 activebackground='#059669', 
                                 activeforeground='white')
        self.run_btn.pack(fill=tk.X)
        
        # RIGHT COLUMN - Terminal
        right_frame = tk.Frame(columns_frame, bg='#0a0e1a')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Terminal Card
        terminal_card = self.create_card(right_frame, "💻 Upload Progress")
        
        self.terminal = scrolledtext.ScrolledText(terminal_card.content, height=40,
                                                  bg='#0a0e1a', fg='#10b981',
                                                  font=('Consolas', 9), wrap=tk.WORD,
                                                  relief='flat', insertbackground='#8b5cf6',
                                                  bd=0, padx=10, pady=10)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        
        # Initial message
        self.append_terminal("=" * 70 + "\n", '#22d3ee')
        self.append_terminal("📋 Ready to upload products to Boutir\n", '#22d3ee')
        self.append_terminal("=" * 70 + "\n\n", '#22d3ee')
        self.append_terminal("ℹ️  Please enter your credentials and select an Excel file\n", '#9ca3af')
        self.append_terminal("ℹ️  Click 'RUN UPLOAD' to start the process\n\n", '#9ca3af')
        
        # Mouse wheel binding for left canvas
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def browse_excel(self):
        """Browse for Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.transformed_file_path = None  # Reset transformed file
            self.append_terminal(f"✅ File selected: {file_path}\n", '#10b981')
    
    def transform_excel(self):
        """Transform Excel file to Boutir format"""
        excel_file = self.file_path_var.get()
        
        # Validation
        if excel_file == "No file selected" or not os.path.exists(excel_file):
            messagebox.showerror("Error", "Please select an Excel file first")
            return
        
        try:
            self.append_terminal("\n" + "=" * 70 + "\n", '#f59e0b')
            self.append_terminal("🔄 Starting Excel Transformation...\n", '#f59e0b')
            self.append_terminal("=" * 70 + "\n\n", '#f59e0b')
            
            # Validate input file
            is_valid, message = self.transformer.validate_input_file(excel_file)
            if not is_valid:
                self.append_terminal(f"❌ Validation failed: {message}\n", '#ef4444')
                messagebox.showerror("Validation Error", message)
                return
            
            self.append_terminal(f"✅ Input file validated\n", '#10b981')
            self.append_terminal(f"📁 Input file: {excel_file}\n", '#e6eaef')
            
            # Get output directory (same as exe/script location)
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                output_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                output_dir = os.getcwd()
            
            self.append_terminal(f"📂 Output directory: {output_dir}\n", '#e6eaef')
            self.append_terminal("\n🔄 Transforming...\n", '#f59e0b')
            
            # Transform the file
            self.transformed_file_path = self.transformer.transform(excel_file, output_dir)
            
            self.append_terminal(f"\n✅ Transformation completed!\n", '#10b981')
            self.append_terminal(f"📄 Transformed file: {self.transformed_file_path}\n", '#22d3ee')
            self.append_terminal("\n" + "=" * 70 + "\n", '#10b981')
            self.append_terminal("✅ Ready for upload! Click 'RUN UPLOAD' to proceed.\n", '#10b981')
            self.append_terminal("=" * 70 + "\n\n", '#10b981')
            
            messagebox.showinfo("Success", 
                              f"Excel file transformed successfully!\n\n"
                              f"Output file:\n{os.path.basename(self.transformed_file_path)}\n\n"
                              f"The transformed file will be used for upload.")
            
        except Exception as e:
            self.append_terminal(f"\n❌ Transformation failed: {str(e)}\n", '#ef4444')
            messagebox.showerror("Error", f"Failed to transform Excel file:\n\n{str(e)}")
    
    def stop_upload(self):
        """Stop the upload process"""
        self.upload_stop_flag = True
        self.append_terminal("\n⏹ Stop requested by user...\n", '#fbbf24')
        self.stop_btn.config(state='disabled')
    
    def append_terminal(self, message, color='#10b981'):
        """Append message to terminal with color"""
        tag_name = f"color_{color.replace('#', '')}"
        if tag_name not in self.terminal.tag_names():
            self.terminal.tag_config(tag_name, foreground=color)
        self.terminal.insert(tk.END, message, tag_name)
        self.terminal.see(tk.END)
        self.window.update_idletasks()
    
    def start_upload(self):
        """Validate inputs and start upload process"""
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        excel_file = self.file_path_var.get()
        
        # Validation
        if not email:
            messagebox.showerror("Error", "Please enter your Boutir email")
            return
        if not password:
            messagebox.showerror("Error", "Please enter your Boutir password")
            return
        if excel_file == "No file selected" or not os.path.exists(excel_file):
            messagebox.showerror("Error", "Please select a valid Excel file")
            return
        
        # Check file extension
        if not excel_file.lower().endswith(('.xlsx', '.xls')):
            messagebox.showerror("Error", "Please select an Excel file (.xlsx or .xls)")
            return
        
        # Use transformed file if available, otherwise use original
        upload_file = self.transformed_file_path if self.transformed_file_path else excel_file
        
        # Verify upload file exists
        if not os.path.exists(upload_file):
            messagebox.showerror("Error", "Upload file not found. Please transform the file first.")
            return
        
        # Clear terminal and start upload
        self.terminal.delete(1.0, tk.END)
        self.append_terminal("=" * 70 + "\n", '#22d3ee')
        self.append_terminal("🚀 Starting Upload Process\n", '#22d3ee')
        self.append_terminal("=" * 70 + "\n\n", '#22d3ee')
        self.append_terminal(f"📧 Email: {email}\n", '#e6eaef')
        
        if self.transformed_file_path:
            self.append_terminal(f"📁 Original File: {excel_file}\n", '#e6eaef')
            self.append_terminal(f"✨ Using Transformed File: {upload_file}\n", '#22d3ee')
        else:
            self.append_terminal(f"📁 Excel File: {upload_file}\n", '#e6eaef')
            self.append_terminal(f"⚠️  Warning: Using original file (not transformed)\n", '#fbbf24')
        
        self.append_terminal("\n")
        
        # Reset stop flag and enable stop button
        self.upload_stop_flag = False
        self.stop_btn.config(state='normal')
        self.run_btn.config(state='disabled')
        self.transform_btn.config(state='disabled')
        
        # Run upload in thread
        upload_thread = threading.Thread(
            target=self.run_upload_thread, 
            args=(email, password, upload_file),
            daemon=True
        )
        upload_thread.start()
    
    def run_upload_thread(self, email, password, excel_file):
        """Run the upload process in a separate thread"""
        try:
            # Check stop flag
            if self.upload_stop_flag:
                self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                return
            
            # Try Playwright first
            self.append_terminal("=" * 70 + "\n", '#8b5cf6')
            self.append_terminal("🎭 Attempting upload with Playwright...\n", '#8b5cf6')
            self.append_terminal("=" * 70 + "\n\n", '#8b5cf6')
            
            # Add web-upload-bulk to path
            sys.path.insert(0, os.path.join(os.getcwd(), 'web-upload-bulk'))
            
            try:
                from uploaders.playwright_uploader import PlaywrightUploader
                from utils.config import Config
                
                # Check stop flag
                if self.upload_stop_flag:
                    self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                    return
                
                # Update config with credentials from GUI
                Config.BOUTIR_EMAIL = email
                Config.BOUTIR_PASSWORD = password
                
                uploader = PlaywrightUploader(headless=True)
                
                # Setup logging to terminal
                self.setup_logging()
                
                success = uploader.run(excel_file)
                
                if success and not self.upload_stop_flag:
                    self.append_terminal("\n" + "=" * 70 + "\n", '#10b981')
                    self.append_terminal("✅ UPLOAD COMPLETED SUCCESSFULLY!\n", '#10b981')
                    self.append_terminal("=" * 70 + "\n", '#10b981')
                    self.window.after(0, messagebox.showinfo, "Success", 
                                     "Upload completed successfully!")
                elif self.upload_stop_flag:
                    self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                else:
                    raise Exception("Playwright upload failed")
                    
            except Exception as playwright_error:
                if self.upload_stop_flag:
                    self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                    return
                
                self.append_terminal(f"\n⚠️ Playwright failed: {str(playwright_error)}\n\n", 
                                   '#fbbf24')
                self.append_terminal("=" * 70 + "\n", '#f97316')
                self.append_terminal("🔄 Attempting upload with Selenium...\n", '#f97316')
                self.append_terminal("=" * 70 + "\n\n", '#f97316')
                
                try:
                    from uploaders.selenium_uploader import SeleniumUploader
                    from utils.config import Config
                    
                    # Check stop flag
                    if self.upload_stop_flag:
                        self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                        return
                    
                    # Update config with credentials from GUI
                    Config.BOUTIR_EMAIL = email
                    Config.BOUTIR_PASSWORD = password
                    
                    uploader = SeleniumUploader(headless=True)
                    
                    success = uploader.run(excel_file)
                    
                    if success and not self.upload_stop_flag:
                        self.append_terminal("\n" + "=" * 70 + "\n", '#10b981')
                        self.append_terminal("✅ UPLOAD COMPLETED (Selenium)!\n", '#10b981')
                        self.append_terminal("=" * 70 + "\n", '#10b981')
                        self.window.after(0, messagebox.showinfo, "Success", 
                                         "Upload completed successfully using Selenium!")
                    elif self.upload_stop_flag:
                        self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                    else:
                        raise Exception("Selenium upload failed")
                        
                except Exception as selenium_error:
                    if self.upload_stop_flag:
                        self.append_terminal("\n⏹ Upload stopped by user\n", '#fbbf24')
                        return
                    
                    self.append_terminal(f"\n❌ Selenium failed: {str(selenium_error)}\n", 
                                       '#ef4444')
                    self.append_terminal("\n" + "=" * 70 + "\n", '#ef4444')
                    self.append_terminal("❌ UPLOAD FAILED - Both methods failed\n", '#ef4444')
                    self.append_terminal("=" * 70 + "\n", '#ef4444')
                    error_msg = (f"Upload failed with both methods:\n\n"
                               f"Playwright: {str(playwright_error)}\n\n"
                               f"Selenium: {str(selenium_error)}")
                    self.window.after(0, messagebox.showerror, "Error", error_msg)
                    
        except Exception as e:
            self.append_terminal(f"\n❌ CRITICAL ERROR: {str(e)}\n", '#ef4444')
            self.window.after(0, messagebox.showerror, "Error", 
                            f"Critical error during upload:\n\n{str(e)}")
        finally:
            # Re-enable buttons
            self.window.after(0, lambda: self.run_btn.config(state='normal'))
            self.window.after(0, lambda: self.transform_btn.config(state='normal'))
            self.window.after(0, lambda: self.stop_btn.config(state='disabled'))
    
    def setup_logging(self):
        """Setup logging to redirect to terminal"""
        class TerminalHandler(logging.Handler):
            def __init__(self, terminal_window):
                super().__init__()
                self.terminal_window = terminal_window
            
            def emit(self, record):
                msg = self.format(record) + "\n"
                color = '#10b981'
                if record.levelname == 'ERROR':
                    color = '#ef4444'
                elif record.levelname == 'WARNING':
                    color = '#fbbf24'
                elif record.levelname == 'INFO':
                    color = '#22d3ee'
                self.terminal_window.window.after(0, 
                    self.terminal_window.append_terminal, msg, color)
        
        handler = TerminalHandler(self)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
