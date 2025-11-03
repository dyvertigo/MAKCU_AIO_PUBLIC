# main_wizard.py
# Wizard-style main entry point for MAKCU

import sys
import os
import ctypes
import customtkinter as ctk

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.wizard_gui import SetupWizard

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """Main entry point"""
    # Check admin rights
    if not is_admin():
        print("Not running as admin - some features may be limited")
    
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create root window
    root = ctk.CTk()
    
    # Create wizard
    wizard = SetupWizard(root, is_admin)
    
    # Run
    root.mainloop()

if __name__ == "__main__":
    main()
