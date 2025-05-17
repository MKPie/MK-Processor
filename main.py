#!/usr/bin/env python3
"""
MK Processor - Main Application Entry Point
Version 3.0.6
"""

import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

# Add the app directory to the python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import application modules
try:
    from app.config import get_config
    from app.gui.main_window import MainWindow
    from app.plugins.base import PluginManager
    from app.utils.error_handling import setup_exception_handling
    from update.updater import Updater
except Exception:
    # Show a clear error message if modules can't be imported
    e = sys.exc_info()[1]  # Get the exception object
    print(f"Error importing required modules: {e}")
    print(traceback.format_exc())
    if __name__ == "__main__":
        if 'PyQt5' in sys.modules:
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Module Import Error")
            msg.setText(f"Failed to import required modules: {e}")
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
        sys.exit(1)


def check_for_updates():
    """Check for application updates."""
    config = get_config()
    if not config.get("app", "check_updates", True):
        return False
    
    current_version = config.get("app", "version", "3.0.6")
    update_url = config.get("app", "update_url", "https://example.com/updates/mk_processor.json")
    
    updater = Updater(current_version, update_url)
    update_info = updater.check_for_updates()
    
    if update_info:
        return update_info
    
    return False


def main():
    """Main application entry point."""
    # Initialize the QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MK Processor")
    app.setApplicationVersion("3.0.6")
    
    # Set up global exception handling
    setup_exception_handling(app)
    
    # Check if essential directories exist
    config = get_config()
    web_folder = os.path.expanduser(config.get("google_drive", "web_folder", "~/GoogleDriveMount/Web/"))
    if not os.path.exists(web_folder):
        try:
            os.makedirs(web_folder, exist_ok=True)
        except Exception:
            e = sys.exc_info()[1]  # Get the exception object
            QMessageBox.warning(
                None, 
                "Directory Warning",
                f"Could not create web folder at {web_folder}.\n\n"
                f"Error: {str(e)}\n\n"
                "The application will continue, but functionality may be limited."
            )
    
    # Set application icon if available
    icon_path = os.path.join(app_dir, "resources", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize plugin system
    plugin_manager = PluginManager()
    plugin_manager.load_plugins()
    
    # Create main window
    window = MainWindow(plugin_manager)
    window.show()
    
    # Check for updates after window is shown (don't block startup)
    update_info = check_for_updates()
    if update_info:
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: show_update_dialog(window, update_info))
    
    # Run the application
    return app.exec_()


def show_update_dialog(parent, update_info):
    """Show a dialog offering to update the application."""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
    
    dialog = QDialog(parent)
    dialog.setWindowTitle("Update Available")
    dialog.setMinimumWidth(400)
    dialog.setMinimumHeight(300)
    
    layout = QVBoxLayout(dialog)
    
    # Version info
    layout.addWidget(QLabel(f"<h3>MK Processor {update_info.get('version')} is available!</h3>"))
    layout.addWidget(QLabel(f"You are currently using version {get_config().get('app', 'version', '3.0.6')}"))
    
    # Release notes
    layout.addWidget(QLabel("<b>Release Notes:</b>"))
    notes = QTextEdit()
    notes.setReadOnly(True)
    notes.setPlainText(update_info.get("release_notes", "No release notes available."))
    layout.addWidget(notes)
    
    # Buttons
    button_layout = QHBoxLayout()
    update_button = QPushButton("Update Now")
    later_button = QPushButton("Later")
    
    button_layout.addWidget(later_button)
    button_layout.addWidget(update_button)
    layout.addLayout(button_layout)
    
    # Connect buttons
    later_button.clicked.connect(dialog.reject)
    
    def start_update():
        dialog.accept()
        
        # Create the updater and start the update process
        updater = Updater(get_config().get("app", "version", "3.0.6"))
        update_file = updater.download_update()
        
        if update_file:
            result = updater.install_update(update_file)
            if not result:
                QMessageBox.warning(
                    parent,
                    "Update Failed",
                    "Failed to install the update. Please try again later."
                )
    
    update_button.clicked.connect(start_update)
    
    # Show the dialog
    dialog.exec_()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        e = sys.exc_info()[1]  # Get the exception object
        print(f"Unhandled application error: {e}")
        print(traceback.format_exc())
        
        try:
            # Try to show an error dialog
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Application Error")
            msg.setText(f"An unhandled error occurred: {str(e)}")
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
        except:
            # Last resort, print to console
            pass
        
        sys.exit(1)
