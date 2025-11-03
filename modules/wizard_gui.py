# modules/wizard_gui.py

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import threading
import time
from .logger import Logger
from .serial_handler import SerialHandler
from .flasher import Flasher
from .config_manager import ConfigManager
from .device_manager import DeviceManager
from .utils import get_icon_path

class SetupWizard:
    def __init__(self, root, is_admin_func):
        self.root = root
        self.is_admin = is_admin_func
        self.root.title("MAKCU Setup Wizard")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Initialize backend
        self.logger = Logger(None, self.root)  # Pass root for logger
        self.config_manager = ConfigManager(self.logger, None)
        self.device_manager = DeviceManager()
        self.serial_handler = SerialHandler(self.logger, None, self.root)
        self.flasher = Flasher(self.logger, self.serial_handler, self.config_manager)
        
        # Wizard state
        self.current_step = 0
        self.setup_mode = None  # "2pc" or "1pc"
        self.detected_device = None
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="MAKCU Setup Wizard", 
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)
        
        # Progress indicator
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", pady=10)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Step 0/5",
            font=("Arial", 12)
        )
        self.progress_label.pack()
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # Button area
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", pady=10)
        
        self.back_btn = ctk.CTkButton(
            self.button_frame,
            text="← Back",
            command=self.previous_step,
            width=100
        )
        self.back_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            self.button_frame,
            text="Next →",
            command=self.next_step,
            width=100
        )
        self.next_btn.pack(side="right", padx=5)
        
        # Start wizard
        self.show_step(0)
    
    def clear_content(self):
        """Clear content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_step(self, step):
        """Display specific step"""
        self.current_step = step
        self.clear_content()
        
        # Update progress
        total_steps = 5
        self.progress_label.configure(text=f"Step {step}/{total_steps}")
        
        # Show/hide back button
        if step == 0:
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="left", padx=5)
        
        # Route to correct step
        if step == 0:
            self.step_welcome()
        elif step == 1:
            self.step_choose_mode()
        elif step == 2:
            self.step_connect_makcu()
        elif step == 3:
            self.step_check_firmware()
        elif step == 4:
            self.step_connect_mouse()
        elif step == 5:
            self.step_complete()
    
    def step_welcome(self):
        """Step 0: Welcome screen"""
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome to MAKCU Setup",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            self.content_frame,
            text="This wizard will guide you through setting up\nyour MAKCU mouse emulator.",
            font=("Arial", 12)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            self.content_frame,
            text="What you'll need:",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        checklist = [
            "• MAKCU device",
            "• Gaming mouse",
            "• USB cable(s)"
        ]
        
        for item in checklist:
            ctk.CTkLabel(
                self.content_frame,
                text=item,
                font=("Arial", 11)
            ).pack(anchor="w", padx=50)
        
        self.next_btn.configure(text="Start Setup →")
    
    def step_choose_mode(self):
        """Step 1: Choose setup mode"""
        ctk.CTkLabel(
            self.content_frame,
            text="Choose Your Setup Mode",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            self.content_frame,
            text="How will you use MAKCU?",
            font=("Arial", 12)
        ).pack(pady=10)
        
        # 2 PC Mode
        mode_2pc_frame = ctk.CTkFrame(self.content_frame)
        mode_2pc_frame.pack(fill="x", padx=20, pady=10)
        
        def select_2pc():
            self.setup_mode = "2pc"
            self.next_step()
        
        ctk.CTkButton(
            mode_2pc_frame,
            text="🖥️ 2 PC Setup",
            command=select_2pc,
            height=60,
            font=("Arial", 14, "bold")
        ).pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            mode_2pc_frame,
            text="Gaming PC + Streaming PC\nMouse connected to MAKCU, MAKCU to gaming PC",
            font=("Arial", 10)
        ).pack(padx=10, pady=5)
        
        # 1 PC Mode
        mode_1pc_frame = ctk.CTkFrame(self.content_frame)
        mode_1pc_frame.pack(fill="x", padx=20, pady=10)
        
        def select_1pc():
            self.setup_mode = "1pc"
            self.next_step()
        
        ctk.CTkButton(
            mode_1pc_frame,
            text="💻 Single PC Setup",
            command=select_1pc,
            height=60,
            font=("Arial", 14, "bold")
        ).pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            mode_1pc_frame,
            text="One PC for gaming and everything\nMouse → MAKCU → PC",
            font=("Arial", 10)
        ).pack(padx=10, pady=5)
        
        self.next_btn.pack_forget()  # Hide next button, they click mode buttons
    
    def step_connect_makcu(self):
        """Step 2: Connect MAKCU device"""
        ctk.CTkLabel(
            self.content_frame,
            text="Connect Your MAKCU",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        if self.setup_mode == "2pc":
            instruction = "1. Plug MAKCU into your GAMING PC via USB\n2. Wait for Windows to recognize it"
        else:
            instruction = "1. Plug MAKCU into your PC via USB\n2. Wait for Windows to recognize it"
        
        ctk.CTkLabel(
            self.content_frame,
            text=instruction,
            font=("Arial", 12)
        ).pack(pady=20)
        
        # Detection status
        self.detection_label = ctk.CTkLabel(
            self.content_frame,
            text="🔍 Waiting for MAKCU...",
            font=("Arial", 12),
            text_color="orange"
        )
        self.detection_label.pack(pady=20)
        
        # Auto-detect button
        detect_btn = ctk.CTkButton(
            self.content_frame,
            text="🔄 Check Connection",
            command=self.detect_makcu,
            height=40
        )
        detect_btn.pack(pady=10)
        
        # Disable next until detected
        self.next_btn.configure(state="disabled")
        
        # Auto-start detection
        self.root.after(500, self.detect_makcu)
    
    def detect_makcu(self):
        """Try to detect MAKCU device"""
        known = self.device_manager.find_connected_devices()
        unknown = self.device_manager.detect_unknown_devices()
        
        if known:
            # Found a known device
            self.detected_device = known[0]
            self.detection_label.configure(
                text=f"✅ Found: {self.detected_device['name']}",
                text_color="green"
            )
            self.next_btn.configure(state="normal")
        elif unknown:
            # Found unknown device - guide user to add it
            dev = unknown[0]
            self.detection_label.configure(
                text=f"⚠️ Unknown device detected\nVID: {dev['vid']} PID: {dev['pid']}",
                text_color="orange"
            )
            
            # Add quick setup button
            def quick_add():
                # Auto-add with basic config
                device_info = {
                    "name": f"MAKCU_{dev['vid']}_{dev['pid']}",
                    "vid": dev['vid'],
                    "pid": dev['pid'],
                    "features": ["serial"],
                    "serial_protocol": "standard",
                    "firmware": {
                        "version": "unknown",
                        "url": "",
                        "flash_method": "esptool",
                        "changelog": "Auto-detected"
                    },
                    "protocol_info": {
                        "baudrate": 115200,
                        "handshake": "none",
                        "command_set": ["standard_v1"]
                    }
                }
                self.device_manager.add_device(device_info)
                self.detected_device = device_info
                self.detection_label.configure(
                    text=f"✅ Device added: {device_info['name']}",
                    text_color="green"
                )
                self.next_btn.configure(state="normal")
            
            ctk.CTkButton(
                self.content_frame,
                text="Add This Device",
                command=quick_add,
                height=30
            ).pack(pady=5)
        else:
            self.detection_label.configure(
                text="❌ No device found\nMake sure MAKCU is plugged in",
                text_color="red"
            )
            self.next_btn.configure(state="disabled")
    
    def step_check_firmware(self):
        """Step 3: Check and update firmware"""
        ctk.CTkLabel(
            self.content_frame,
            text="Firmware Check",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            self.content_frame,
            text="Checking MAKCU firmware version...",
            font=("Arial", 12)
        ).pack(pady=10)
        
        # Status display
        self.fw_status_label = ctk.CTkLabel(
            self.content_frame,
            text="🔍 Checking...",
            font=("Arial", 12)
        )
        self.fw_status_label.pack(pady=20)
        
        # Progress bar
        self.fw_progress = ctk.CTkProgressBar(self.content_frame)
        self.fw_progress.pack(pady=10, padx=50, fill="x")
        self.fw_progress.set(0)
        
        # Check firmware
        self.root.after(500, self.check_firmware)
    
    def check_firmware(self):
        """Check if firmware update needed"""
        if not self.detected_device:
            self.fw_status_label.configure(text="❌ No device detected")
            return
        
        fw_info = self.detected_device.get('firmware', {})
        current_version = fw_info.get('version', 'unknown')
        
        # Check online version
        self.fw_status_label.configure(text=f"Current: {current_version}")
        self.fw_progress.set(0.5)
        
        # For now, assume update available
        if self.config_manager.is_online:
            online_version = self.config_manager.config_data.get('firmware', {}).get('left', {}).get('version', current_version)
            
            if online_version != current_version:
                self.fw_status_label.configure(
                    text=f"⚠️ Update available: {online_version}\nCurrent: {current_version}",
                    text_color="orange"
                )
                
                update_btn = ctk.CTkButton(
                    self.content_frame,
                    text="🔄 Update Firmware",
                    command=self.update_firmware,
                    height=40
                )
                update_btn.pack(pady=10)
            else:
                self.fw_status_label.configure(
                    text=f"✅ Firmware up to date ({current_version})",
                    text_color="green"
                )
                self.fw_progress.set(1.0)
                self.next_btn.configure(state="normal")
        else:
            self.fw_status_label.configure(
                text=f"⚠️ Cannot check online\nCurrent: {current_version}",
                text_color="orange"
            )
            skip_btn = ctk.CTkButton(
                self.content_frame,
                text="Skip Firmware Check",
                command=lambda: self.next_step()
            ).pack(pady=10)
    
    def update_firmware(self):
        """Flash firmware to device"""
        self.fw_status_label.configure(text="📥 Downloading firmware...")
        self.fw_progress.set(0.3)
        
        def flash_thread():
            try:
                self.flasher.flash_device_profile(self.detected_device)
                self.root.after(0, self.firmware_complete)
            except Exception as e:
                self.root.after(0, lambda: self.firmware_error(str(e)))
        
        threading.Thread(target=flash_thread, daemon=True).start()
    
    def firmware_complete(self):
        """Firmware update completed"""
        self.fw_status_label.configure(
            text="✅ Firmware updated successfully!",
            text_color="green"
        )
        self.fw_progress.set(1.0)
        self.next_btn.configure(state="normal")
    
    def firmware_error(self, error):
        """Firmware update failed"""
        self.fw_status_label.configure(
            text=f"❌ Update failed: {error}",
            text_color="red"
        )
        
        retry_btn = ctk.CTkButton(
            self.content_frame,
            text="🔄 Retry",
            command=self.update_firmware
        ).pack(pady=5)
        
        skip_btn = ctk.CTkButton(
            self.content_frame,
            text="Skip for Now",
            command=lambda: self.next_step()
        ).pack(pady=5)
    
    def step_connect_mouse(self):
        """Step 4: Connect gaming mouse"""
        ctk.CTkLabel(
            self.content_frame,
            text="Connect Your Gaming Mouse",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        if self.setup_mode == "2pc":
            instruction = "1. Plug your gaming mouse into the MAKCU device\n2. MAKCU will emulate the mouse to your gaming PC"
        else:
            instruction = "1. Plug your gaming mouse into the MAKCU device\n2. Your mouse is now running through MAKCU"
        
        ctk.CTkLabel(
            self.content_frame,
            text=instruction,
            font=("Arial", 12)
        ).pack(pady=20)
        
        # Visual diagram
        diagram_frame = ctk.CTkFrame(self.content_frame)
        diagram_frame.pack(pady=20)
        
        if self.setup_mode == "2pc":
            diagram_text = "🖱️ Mouse → 🔷 MAKCU → 💻 Gaming PC"
        else:
            diagram_text = "🖱️ Mouse → 🔷 MAKCU → 💻 PC"
        
        ctk.CTkLabel(
            diagram_frame,
            text=diagram_text,
            font=("Arial", 14, "bold")
        ).pack(padx=20, pady=20)
        
        # Test connection button
        test_btn = ctk.CTkButton(
            self.content_frame,
            text="🧪 Test Mouse Connection",
            command=self.test_mouse,
            height=40
        )
        test_btn.pack(pady=10)
        
        self.mouse_status_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=("Arial", 11)
        )
        self.mouse_status_label.pack(pady=5)
    
    def test_mouse(self):
        """Test if mouse is working through MAKCU"""
        self.mouse_status_label.configure(text="🔍 Testing mouse connection...")
        
        # Try to establish serial connection
        try:
            # Use detected device profile
            self.serial_handler.connect_device_profile(self.detected_device)
            
            self.mouse_status_label.configure(
                text="✅ Mouse connected and working!",
                text_color="green"
            )
            self.next_btn.configure(state="normal")
        except Exception as e:
            self.mouse_status_label.configure(
                text=f"⚠️ Connection issue: {str(e)}",
                text_color="orange"
            )
    
    def step_complete(self):
        """Step 5: Setup complete"""
        ctk.CTkLabel(
            self.content_frame,
            text="✅ Setup Complete!",
            font=("Arial", 20, "bold"),
            text_color="green"
        ).pack(pady=30)
        
        ctk.CTkLabel(
            self.content_frame,
            text="Your MAKCU is ready to use!",
            font=("Arial", 14)
        ).pack(pady=10)
        
        summary_frame = ctk.CTkFrame(self.content_frame)
        summary_frame.pack(pady=20, padx=30, fill="x")
        
        ctk.CTkLabel(
            summary_frame,
            text="Setup Summary:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        summary_items = [
            f"• Mode: {self.setup_mode.upper()}",
            f"• Device: {self.detected_device['name'] if self.detected_device else 'Unknown'}",
            f"• Status: ✅ Ready"
        ]
        
        for item in summary_items:
            ctk.CTkLabel(
                summary_frame,
                text=item,
                font=("Arial", 11)
            ).pack(anchor="w", padx=20, pady=2)
        
        # Finish button
        self.next_btn.configure(text="🎮 Start Gaming", command=self.finish_setup)
    
    def finish_setup(self):
        """Complete wizard and close"""
        messagebox.showinfo(
            "Setup Complete",
            "MAKCU is configured and ready!\n\nYou can now use your mouse for gaming."
        )
        self.root.quit()
    
    def next_step(self):
        """Go to next step"""
        self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
