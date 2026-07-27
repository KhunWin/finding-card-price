import sys
import os
import threading

from numpy import extract
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QCheckBox, QComboBox, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette
import requests
import time
import json
import csv
from datetime import datetime
from urllib.parse import urlparse
import hashlib
from main_tcg_extract import TCGCSVScraperGUI  # Assuming you have a separate scraper module

class ScraperThread(QThread):
    log_signal = pyqtSignal(str, str)  # message, color
    progress_signal = pyqtSignal(int, int)  # current, total
    finished_signal = pyqtSignal(bool, str, dict)  # success, message, stats
    
    def __init__(self, category_ids, group_ids, output_folder, download_images, image_size, app_name):
        super().__init__()
        self.category_ids = category_ids
        self.group_ids = group_ids
        self.output_folder = output_folder
        self.download_images = download_images
        self.image_size = image_size
        self.app_name = app_name
        self.is_running = True
        
    def log(self, message, color="white"):
        self.log_signal.emit(message, color)
    
    def run(self):
        try:
            scraper = TCGCSVScraperGUI(
                category_ids=self.category_ids,
                group_ids=self.group_ids,
                output_folder=self.output_folder,
                app_name=self.app_name,
                download_images=self.download_images,
                image_size=self.image_size,
                log_callback=self.log,
                progress_callback=self.progress_signal,
                is_running_callback=lambda: self.is_running
            )
            stats = scraper.scrape_data()
            self.finished_signal.emit(True, "Scraping completed successfully!", stats)
        except Exception as e:
            self.log(f"Error: {str(e)}", "red")
            self.finished_signal.emit(False, f"Error: {str(e)}", {})
    
    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scraper_thread = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('TCG Card Scraper')
        self.setGeometry(100, 100, 900, 700)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #7d7d7d;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                padding: 10px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 10pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #3d3d3d;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border: 1px solid #0e639c;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0e639c;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 12px;
                font-size: 11pt;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
            }
        """)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel('🎴 TCG Card Scraper')
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Input Group
        input_group = QGroupBox('Input Parameters')
        input_layout = QVBoxLayout()
        
        # Category ID
        cat_layout = QHBoxLayout()
        cat_label = QLabel('Category IDs:')
        cat_label.setFixedWidth(120)
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText('e.g., 1, 3, 85 (comma-separated)')
        self.category_input.setText('85')
        cat_layout.addWidget(cat_label)
        cat_layout.addWidget(self.category_input)
        input_layout.addLayout(cat_layout)
        
        # Group ID
        group_layout = QHBoxLayout()
        group_label = QLabel('Group IDs:')
        group_label.setFixedWidth(120)
        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText('e.g., 24721, 24653 (comma-separated, leave empty for all)')
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_input)
        input_layout.addLayout(group_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Settings Group
        settings_group = QGroupBox('Settings')
        settings_layout = QVBoxLayout()
        
        # Output folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel('Output Folder:')
        folder_label.setFixedWidth(120)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText('Select output folder...')
        self.folder_input.setText(os.path.expanduser('~/Desktop'))
        self.folder_btn = QPushButton('Browse')
        self.folder_btn.setMaximumWidth(100)
        self.folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)
        settings_layout.addLayout(folder_layout)
        
        # Download images checkbox
        self.download_images_cb = QCheckBox('Download Images')
        self.download_images_cb.setChecked(True)
        self.download_images_cb.stateChanged.connect(self.toggle_image_size)
        settings_layout.addWidget(self.download_images_cb)
        
        # Image size
        size_layout = QHBoxLayout()
        size_label = QLabel('Image Size:')
        size_label.setFixedWidth(120)
        self.image_size_combo = QComboBox()
        self.image_size_combo.addItems(['_200w (200 width)', '_400w (400 width)', '_in_1000x1000 (1000x1000)'])
        self.image_size_combo.setCurrentIndex(1)  # Default to 400w
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.image_size_combo)
        settings_layout.addLayout(size_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%v / %m groups (%p%)')
        layout.addWidget(self.progress_bar)
        
        # Terminal/Console
        console_label = QLabel('📟 Console Output')
        console_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        layout.addWidget(console_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(250)
        layout.addWidget(self.console)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_btn = QPushButton('▶ Start Scraping')
        self.start_btn.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('⏹ Stop')
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #d13438;
            }
            QPushButton:hover {
                background-color: #e04649;
            }
            QPushButton:pressed {
                background-color: #b82d31;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #7d7d7d;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_scraping)
        button_layout.addWidget(self.stop_btn)
        
        self.reset_btn = QPushButton('🔄 Reset')
        self.reset_btn.clicked.connect(self.reset_fields)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # Initial log message
        self.append_log("Welcome to TCG Card Scraper! 🎴", "cyan")
        self.append_log("Configure your settings and click 'Start Scraping' to begin.", "white")
        
    # def toggle_image_size(self):
    #     self.image_size_combo.setEnabled(self.download_images_cb.isChecked())

    def toggle_image_size(self):
        """Enable/disable image size selection based on download checkbox"""
        is_enabled = self.download_images_cb.isChecked()
        self.image_size_combo.setEnabled(is_enabled)
        
        # Visual feedback
        if is_enabled:
            self.append_log("Image downloading enabled.", "green")
        else:
            self.append_log("Image downloading disabled.", "yellow")
            
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if folder:
            self.folder_input.setText(folder)
    
    def reset_fields(self):
        self.category_input.setText('85')
        self.group_input.setText('')
        self.folder_input.setText(os.path.expanduser('~/Desktop'))
        self.download_images_cb.setChecked(True)
        self.image_size_combo.setCurrentIndex(1)
        self.console.clear()
        self.progress_bar.setValue(0)
        self.append_log("Fields reset to default values.", "yellow")
    
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
        
        hex_color = color_map.get(color, color_map["white"])
        self.console.append(f'<span style="color: {hex_color};">{message}</span>')
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        QApplication.processEvents()
    
    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        QApplication.processEvents()
    
    def start_scraping(self):
        # Validate inputs
        category_ids = [c.strip() for c in self.category_input.text().split(',') if c.strip()]
        if not category_ids:
            QMessageBox.warning(self, 'Input Error', 'Please enter at least one Category ID.')
            return
        
        group_ids_text = self.group_input.text().strip()
        group_ids = [g.strip() for g in group_ids_text.split(',') if g.strip()] if group_ids_text else None
        
        output_folder = self.folder_input.text().strip()
        if not output_folder or not os.path.exists(output_folder):
            QMessageBox.warning(self, 'Folder Error', 'Please select a valid output folder.')
            return
        
        # Get image size value
        size_text = self.image_size_combo.currentText()
        if '_200w' in size_text:
            image_size = '_200w'
        elif '_400w' in size_text:
            image_size = '_400w'
        else:
            image_size = '_in_1000x1000'
        
        # Clear console
        self.console.clear()
        self.progress_bar.setValue(0)
        
        # Disable start button, enable stop button
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.reset_btn.setEnabled(False)
        
        # Start scraper thread
        self.scraper_thread = ScraperThread(
            category_ids=category_ids,
            group_ids=group_ids,
            output_folder=output_folder,
            download_images=self.download_images_cb.isChecked(),
            image_size=image_size,
            app_name='TCGScraperGUI'
        )
        self.scraper_thread.log_signal.connect(self.append_log)
        self.scraper_thread.progress_signal.connect(self.update_progress)
        self.scraper_thread.finished_signal.connect(self.scraping_finished)
        self.scraper_thread.start()
    
    def stop_scraping(self):
        if self.scraper_thread:
            self.append_log("\n⚠ Stopping scraper... Please wait.", "yellow")
            self.scraper_thread.stop()
            self.stop_btn.setEnabled(False)
    
    def scraping_finished(self, success, message, stats):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(True)
        
        if success:
            # Show completion dialog
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle('Scraping Complete')
            
            details = f"""
✓ Scraping completed successfully!

📊 Statistics:
• Groups processed: {stats.get('groups', 0)}
• Products scraped: {stats.get('products', 0)}
• API requests made: {stats.get('requests', 0)}
• Time elapsed: {stats.get('time', 0) / 60:.2f} minutes
"""
            
            if self.download_images_cb.isChecked():
                details += f"""
📷 Image Downloads:
• Downloaded: {stats.get('images_downloaded', 0)}
• Failed: {stats.get('images_failed', 0)}
• Location: {os.path.join(self.folder_input.text(), 'downloaded_images')}
"""
            
            if stats.get('csv_file'):
                details += f"""
💾 Output:
• CSV file: {stats.get('csv_file')}
"""
            
            msg.setText(details)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            QMessageBox.critical(self, 'Error', f'Scraping failed:\n{message}')

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()