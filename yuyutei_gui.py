"""
Yuyu-Tei GUI - Tkinter interface for Yuyu-Tei scraper
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from datetime import datetime
from pathlib import Path

# Import the Yuyu-Tei scraper
yuyu_tei_path = os.path.join(os.path.dirname(__file__), 'yuyu_tei')
if yuyu_tei_path not in sys.path:
    sys.path.append(yuyu_tei_path)
from yuyu_tei.yuyu_tei_wrapper import YuyuTeiWrapper
from product_key.product_keys_supabase import SupabaseProductKeyManager as ProductKeyManager



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
        radius = 10
        shadow_offset = 2
        shadow_color = '#1a1a1a'
        
        # Shadow
        self.create_arc(shadow_offset, shadow_offset, radius*2+shadow_offset, radius*2+shadow_offset, 
                       start=90, extent=90, fill=shadow_color, outline=shadow_color)
        self.create_rectangle(radius+shadow_offset, shadow_offset, width-radius+shadow_offset, height+shadow_offset, 
                            fill=shadow_color, outline=shadow_color)
        
        # Main button
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_rectangle(radius, 0, width-radius, height, fill=color, outline=color)
        self.create_rectangle(0, radius, width, height-radius, fill=color, outline=color)
        
        text_color = '#ffffff' if self.is_enabled else '#7d7d7d'
        display_text = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(width/2, height/2, text=display_text, fill=text_color, 
                        font=('Segoe UI', 11, 'bold'))
    
    def _on_enter(self, event):
        if self.is_enabled:
            self.draw_button(self.hover_color)
    
    def _on_leave(self, event):
        self.draw_button(self.bg_color)
    
    def _on_click(self, event):
        if self.is_enabled and self.command:
            self.command()
    
    def enable(self):
        self.is_enabled = True
        self.draw_button(self.bg_color)
    
    def disable(self):
        self.is_enabled = False
        self.draw_button('#3d3d3d')


class YuyuTeiGUI:
    """GUI for Yuyu-Tei scraper"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Yuyu-Tei Card Scraper")
        self.root.geometry("1000x800")
        self.root.configure(bg='#1e1e1e')
        
        self.is_running = False
        self.scraper_thread = None
        self.output_folder = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.key_manager = ProductKeyManager()

        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#2d2d2d', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🎯 Yuyu-Tei Card Scraper",
            font=('Segoe UI', 20, 'bold'), fg='#00d4ff', bg='#2d2d2d')
        title_label.pack(pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel
        left_panel = tk.Frame(main_container, bg='#2d2d2d', width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        self.setup_input_fields(left_panel)
        
        # Right panel
        right_panel = tk.Frame(main_container, bg='#1e1e1e')
        right_panel.pack(side='right', fill='both', expand=True)
        self.setup_log_area(right_panel)
        
        self.setup_control_buttons()
    
    def setup_input_fields(self, parent):
        padding_frame = tk.Frame(parent, bg='#2d2d2d')
        padding_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Category ID
        self.create_label(padding_frame, "📁 Category ID (ws,wsr,..):")
        self.category_id_entry = self.create_entry(padding_frame, "ws")
        
        # Group IDs
        self.create_label(padding_frame, "📋 Group IDs (comma-separated):")
        self.group_ids_entry = self.create_entry(padding_frame, "dcext1.0, dc")
        
        # Output folder
        self.create_label(padding_frame, "📂 Output Folder:")
        folder_frame = tk.Frame(padding_frame, bg='#2d2d2d')
        folder_frame.pack(fill='x', pady=(0, 15))
        
        self.output_folder_label = tk.Label(folder_frame, text=self.output_folder,
            font=('Segoe UI', 9), fg='#b0b0b0', bg='#3d3d3d', anchor='w', padx=10, relief='flat', height=2)
        self.output_folder_label.pack(side='left', fill='x', expand=True)
        
        browse_btn = tk.Button(folder_frame, text="📁", font=('Segoe UI', 10), bg='#0078d4',
            fg='white', activebackground='#005a9e', relief='flat', cursor='hand2', width=4,
            command=self.browse_output_folder)
        browse_btn.pack(side='right', padx=(5, 0))
        
        # Download images
        self.create_label(padding_frame, "⚙️ Options:")
        options_frame = tk.Frame(padding_frame, bg='#2d2d2d')
        options_frame.pack(fill='x', pady=(0, 15))
        
        self.download_images_var = tk.BooleanVar(value=True)
        download_images_check = tk.Checkbutton(options_frame, text="Download Images",
            variable=self.download_images_var, font=('Segoe UI', 10), fg='#e0e0e0', bg='#2d2d2d',
            activebackground='#2d2d2d', selectcolor='#3d3d3d', cursor='hand2')
        download_images_check.pack(anchor='w')
    
    def create_label(self, parent, text):
        label = tk.Label(parent, text=text, font=('Segoe UI', 11, 'bold'),
            fg='#00d4ff', bg='#2d2d2d', anchor='w')
        label.pack(fill='x', pady=(10, 5))
        return label
    
    def create_entry(self, parent, placeholder=""):
        entry = tk.Entry(parent, font=('Segoe UI', 10), bg='#3d3d3d',
            fg='#e0e0e0', insertbackground='#00d4ff', relief='flat', bd=5)
        entry.pack(fill='x', pady=(0, 15))
        if placeholder:
            entry.insert(0, placeholder)
        return entry
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.output_folder_label.config(text=folder)
            self.append_log(f"📂 Output folder: {folder}\n", "cyan")
    
    def setup_log_area(self, parent):
        log_label = tk.Label(parent, text="📝 Activity Log", font=('Segoe UI', 12, 'bold'),
            fg='#00d4ff', bg='#1e1e1e', anchor='w')
        log_label.pack(fill='x', pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 4))

        self.card_status_var = tk.StringVar(value="")
        card_status_label = tk.Label(
            parent,
            textvariable=self.card_status_var,
            font=('Segoe UI', 9),
            fg='#b0b0b0',
            bg='#1e1e1e',
            anchor='w',
        )
        card_status_label.pack(fill='x', pady=(0, 6))
        
        log_frame = tk.Frame(parent, bg='#0d1117', relief='flat', bd=1)
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9), bg='#0d1117',
            fg='#e0e0e0', insertbackground='#00d4ff', relief='flat', wrap='word', state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.log_text.tag_config('white', foreground='#e0e0e0')
        self.log_text.tag_config('green', foreground='#00ff00')
        self.log_text.tag_config('red', foreground='#ff4444')
        self.log_text.tag_config('yellow', foreground='#ffff00')
        self.log_text.tag_config('cyan', foreground='#00d4ff')
        self.log_text.tag_config('orange', foreground='#ff9500')
        self.log_text.tag_config('lightgreen', foreground='#90EE90')
    
    def setup_control_buttons(self):
        button_frame = tk.Frame(self.root, bg='#1e1e1e', height=80)
        button_frame.pack(fill='x', padx=20, pady=(10, 20))
        button_frame.pack_propagate(False)
        
        self.start_btn = ModernButton(button_frame, text="Start Scraping", command=self.start_scraping,
            bg_color='#00b894', hover_color='#00a083', icon='▶', width=200)
        self.start_btn.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.stop_btn = ModernButton(button_frame, text="Stop", command=self.stop_scraping,
            bg_color='#d63031', hover_color='#b71c1c', icon='⬛', width=200)
        self.stop_btn.pack(side='left', fill='both', expand=True, padx=5)
        self.stop_btn.disable()
        
        # Upload button
        # upload_btn = ModernButton(button_frame, text="Upload", command=self.open_upload_window,
        #     bg_color='#8b5cf6', hover_color='#7c3aed', icon='📤', width=200)
        # upload_btn.pack(side='left', fill='both', expand=True, padx=5)

        self.upload_btn = ModernButton(button_frame, text="Upload", command=self.open_upload_window,
            bg_color='#8b5cf6', hover_color='#7c3aed', icon='📤', width=200)
        self.upload_btn.pack(side='left', fill='both', expand=True, padx=5)
        
        # Back button
        back_btn = ModernButton(button_frame, text="Back", command=self.go_back_to_selection,
            bg_color='#6b7280', hover_color='#4b5563', icon='◀', width=200)
        back_btn.pack(side='left', fill='both', expand=True, padx=5)
        
        clear_btn = ModernButton(button_frame, text="Clear Log", command=self.clear_log,
            bg_color='#636e72', hover_color='#4a5458', icon='🗑', width=200)
        clear_btn.pack(side='right', fill='both', expand=True, padx=(5, 0))
    
    def append_log(self, message, color='white'):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message, color)
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def update_card_status(self, current, total):
        """Update the small status label below the progress bar."""
        if total and total > 0:
            pct = int(current / total * 100)
            self.card_status_var.set(f"  Card {current}/{total}  ({pct}%)")
        else:
            self.card_status_var.set("")
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')
        self.progress_var.set(0)
    
    def validate_inputs(self):
        category_id = self.category_id_entry.get().strip()
        group_ids_text = self.group_ids_entry.get().strip()
        
        if not category_id:
            messagebox.showerror("Error", "Please enter a Category ID")
            return None
        
        if not group_ids_text:
            messagebox.showerror("Error", "Please enter at least one Group ID")
            return None
        
        group_ids = [gid.strip() for gid in group_ids_text.split(',') if gid.strip()]
        
        if not group_ids:
            messagebox.showerror("Error", "Please enter valid Group IDs")
            return None
        
        return {
            'category_id': category_id,
            'group_ids': group_ids,
            'output_folder': self.output_folder,
            'download_images': self.download_images_var.get()
        }
    
    def start_scraping(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        params = self.validate_inputs()
        if not params:
            return
        
        self.is_running = True
        self.start_btn.disable()
        self.stop_btn.enable()
        
        self.clear_log()
        self.card_status_var.set("")
        self.append_log("=" * 60 + "\n", "cyan")
        self.append_log("🎯 YUYU-TEI SCRAPER STARTED\n", "green")
        self.append_log("=" * 60 + "\n", "cyan")
        self.append_log(f"📁 Category ID: {params['category_id']}\n", "white")
        self.append_log(f"📋 Group IDs: {', '.join(params['group_ids'])}\n", "white")
        self.append_log(f"📂 Output Folder: {params['output_folder']}\n", "white")
        self.append_log(f"📷 Download Images: {'Yes' if params['download_images'] else 'No'}\n", "white")
        self.append_log("=" * 60 + "\n\n", "cyan")
        
        self.scraper_thread = threading.Thread(target=self.run_scraper, args=(params,), daemon=True)
        self.scraper_thread.start()
    
    def run_scraper(self, params):
        try:
            wrapper = YuyuTeiWrapper(
                category_id=params['category_id'],
                group_ids=params['group_ids'],
                output_folder=params['output_folder'],
                download_images=params['download_images'],
                log_callback=self.append_log,
                progress_callback=self.update_progress,
                card_progress_callback=self.update_card_status,
                is_running_callback=lambda: self.is_running
            )
            
            stats = wrapper.scrape_all()

            self.append_log("\n" + "=" * 60 + "\n", "cyan")
            if self.is_running:
                self.append_log("✓ SCRAPING COMPLETED SUCCESSFULLY\n", "green")
            else:
                self.append_log("⚠️ SCRAPING STOPPED (partial data saved)\n", "yellow")
            self.append_log("=" * 60 + "\n", "cyan")
            self.append_log(f"Groups Processed: {stats['groups']}\n", "white")
            self.append_log(f"Total Cards: {stats['cards']}\n", "white")
            if params['download_images']:
                self.append_log(f"Images Downloaded: {stats['images_downloaded']}\n", "white")
                self.append_log(f"Images Failed: {stats['images_failed']}\n", "white")
            self.append_log(f"Time Elapsed: {stats['time']:.2f} seconds\n", "white")
            # List every per-group Excel file if available, else fall back to
            # the single legacy key so old results still display correctly.
            excel_files = stats.get('excel_files') or []
            if excel_files:
                self.append_log("Excel Files:\n", "white")
                for ef in excel_files:
                    self.append_log(f"  • {ef}\n", "white")
            else:
                self.append_log(f"Excel File: {stats.get('excel_file', 'N/A')}\n", "white")
            self.append_log("=" * 60 + "\n", "cyan")

            files_summary = "\n".join(excel_files) if excel_files else stats.get('excel_file', 'N/A')
            if self.is_running:
                messagebox.showinfo("Success", f"Scraping completed!\n\n"
                                              f"Groups: {stats['groups']}\n"
                                              f"Cards: {stats['cards']}\n"
                                              f"Time: {stats['time']:.2f}s\n"
                                              f"Files:\n{files_summary}")
            else:
                messagebox.showinfo("Partial Save", f"Scraping was stopped.\n\n"
                                                    f"Partial data ({stats['cards']} cards) saved.\n"
                                                    f"Re-run with the same settings to resume.\n\n"
                                                    f"Files:\n{files_summary}")
        
        except Exception as e:
            self.append_log(f"\n❌ ERROR: {str(e)}\n", "red")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.is_running = False
            self.start_btn.enable()
            self.stop_btn.disable()
            self.update_progress(0)
            self.card_status_var.set("")
    
    def stop_scraping(self):
        if not self.is_running:
            return
        
        self.append_log("\n⚠️ Stopping scraper...\n", "yellow")
        self.is_running = False
        self.stop_btn.disable()
        
        if self.scraper_thread and self.scraper_thread.is_alive():
            self.scraper_thread.join(timeout=2)
        
        self.append_log("⬛ Scraper stopped\n", "orange")
        self.start_btn.enable()
        self.update_progress(0)


    # def open_upload_window(self):
    #     """Open the upload window for Yuyu-Tei data"""
    #     from upload_window import UploadWindow
    #     UploadWindow(self.root, source='yuyutei')
    


    def open_upload_window(self):
        """Open the upload window for Yuyu-Tei data with product key validation"""
        # Check product key access for upload
        if not self.key_manager.has_upload_access():
            # Check if user has scraping-only key
            if self.key_manager.has_scraping_access():
                # User has scraping key, prompt them to enter Full Access key
                response = messagebox.askyesno(
                    "🔑 Full Access Key Required",
                    "Your current key only allows scraping.\n\n"
                    "To use the Upload feature, you need a Full Access key.\n\n"
                    "Would you like to enter a Full Access key now?"
                )
                
                if not response:
                    return
                
                # Prompt for Full Access key
                key = simpledialog.askstring(
                    "🔑 Enter Full Access Key",
                    "Please enter your Full Access product key:\n\n"
                    "Full Access Key format: FULL-XXXX-XXXX-XXXX-XXXX",
                    parent=self.root
                )
                
                if not key:
                    messagebox.showwarning("⚠️ Cancelled", "Full Access key is required to use the upload feature.")
                    return
                
                # Activate the key
                success, key_type, message = self.key_manager.activate_key(key)
                
                if not success:
                    messagebox.showerror("❌ Invalid Key", message)
                    return
                
                # Check if it's a full access key
                if key_type != self.key_manager.KEY_TYPE_FULL:
                    messagebox.showerror(
                        "❌ Wrong Key Type",
                        "This key only allows scraping.\n\n"
                        "To use the Upload feature, you need a Full Access key (FULL-XXXX-XXXX-XXXX-XXXX)."
                    )
                    return
                
                # Show success message
                messagebox.showinfo("✅ Key Activated", "Full Access key activated successfully!\n\nYou can now use both Scraping and Upload features.")
                self.append_log("🔑 Full Access key activated\n", "green")
            else:
                # No key activated yet, prompt for full access key
                key = simpledialog.askstring(
                    "🔑 Full Access Key Required",
                    "Please enter your Full Access product key to use the upload feature:\n\n"
                    "Full Access Key format: FULL-XXXX-XXXX-XXXX-XXXX",
                    parent=self.root
                )
                
                if not key:
                    messagebox.showwarning("⚠️ Cancelled", "Full Access key is required to use the upload feature.")
                    return
                
                # Activate the key
                success, key_type, message = self.key_manager.activate_key(key)
                
                if not success:
                    messagebox.showerror("❌ Invalid Key", message)
                    return
                
                # Check if it's a full access key
                if key_type != self.key_manager.KEY_TYPE_FULL:
                    messagebox.showerror(
                        "❌ Wrong Key Type",
                        "This key only allows scraping.\n\n"
                        "To use the Upload feature, you need a Full Access key (FULL-XXXX-XXXX-XXXX-XXXX)."
                    )
                    return
                
                # Show success message
                messagebox.showinfo("✅ Key Activated", "Full Access key activated successfully!\n\nYou can now use both Scraping and Upload features.")
                self.append_log("🔑 Full Access key activated\n", "green")
        
        # Open upload window (Yuyu-Tei source)
        from upload_window import UploadWindow
        UploadWindow(self.root, source='yuyutei')

    def go_back_to_selection(self):
        """Return to the selection window"""
        if messagebox.askyesno("Confirm", "Are you sure you want to go back to the selection window?"):
            self.root.destroy()
            from selection_window import SelectionWindow
            import main_gui_tkinter 
            root = tk.Tk()
            
            # Set application icon
            try:
                icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
                if os.path.exists(icon_path):
                    root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Could not set icon: {e}")
            
            SelectionWindow(root, main_gui_tkinter.launch_tcg_gui, main_gui_tkinter.launch_yuyutei_gui)
            root.mainloop()



def main():
    root = tk.Tk()
    
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Could not set icon: {e}")
    
    app = YuyuTeiGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

