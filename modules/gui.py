# modules/gui.py

import tkinter as tk
import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import threading
import webbrowser
import subprocess
import os
import time
import sys
from tkinter import filedialog
from tkinter import font as tkfont
import queue
from .logger import Logger
from .serial_handler import SerialHandler
from .flasher import Flasher
from .updater import Updater
from .config_manager import ConfigManager
from .utils import get_icon_path, get_main_folder
from .usb_name_changer import USBNameChanger, USBNameChangerFTDI
from tkinter import messagebox
from .device_manager import DeviceManager


class GUI:
    def __init__(self, root, is_admin_func):
        self.root = root
        self.is_admin = is_admin_func
        """
        Initialize the GUI.
        """
        self.root = root
        self.root.title("MAKCU v2.1")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.task_queue = queue.Queue()
        self.process_queue()
        self.device_manager = DeviceManager()

        # Internal state
        self.is_connected = False
        self.current_mode = "Normal"
        self.theme_is_dark = True
        self.command_history = []
        self.history_position = -1
        self.available_ports = []
        self.port_mapping = {}
        self.is_devkit_mode = False
        self.is_online = False
        self.is_offline = True

        # Configure grid weights for the main window
        self.root.grid_rowconfigure(0, weight=0)  # Marquee row
        self.root.grid_rowconfigure(1, weight=0)  # MCU status row
        self.root.grid_rowconfigure(2, weight=0)  # Buttons row
        self.root.grid_rowconfigure(3, weight=0)  # Icons row
        self.root.grid_rowconfigure(4, weight=0)  # Text input row
        self.root.grid_rowconfigure(5, weight=1)  # Output terminal row

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # Create output logger
        log_file_path = os.path.join(get_main_folder(), 'log.txt')
        self.output_text = self.create_output_box()
        self.logger = Logger(self.output_text, self.root, log_file_path=log_file_path)

        # Set theme
        if self.theme_is_dark:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

        self.define_theme_colors()

        # Initialize ConfigManager and download config
        self.config_manager = ConfigManager(self.logger, progress_callback=self.update_progress)
        
        # Initialize both USB changers (CH343 and FTDI)
        self.ch343_changer = USBNameChanger(self.logger, self.is_admin)
        self.ftdi_changer  = USBNameChangerFTDI(self.logger, self.is_admin)

        # Schedule driver install only once (CH343 requires it)
        self.root.after(500, self.ch343_changer.ensure_driver_installed)

        # Still only need one mismatch check (applies to CH340-named devices)
        self.root.after(1500, self._check_ch340_mismatch)


        # Restore window position from config
        self.restore_window_position()

        # Build GUI components
        self.create_marquee_label()       # Row 0
        self.create_mcu_status_label()    # Row 1
        self.create_buttons()             # Row 2
        self.create_flash_buttons()       # Integrated into row 2
        self.update_flash_buttons_text()  # Initialize flash buttons' text
        self.create_icons()               # Row 3
        self.create_text_input()          # Row 4


        # Device select dropdown
        self.selected_device_var = tk.StringVar()
        device_names = [d['name'] for d in self.device_manager.devices]
        default_value = device_names[0] if device_names else "No Devices"
        self.device_dropdown = tk.OptionMenu(self.root, self.selected_device_var, default_value, *device_names)
        self.device_dropdown.grid(row=1, column=2, padx=5, pady=5, sticky="e")

        def connect_selected_device():
            name = self.selected_device_var.get()
            profile = next((d for d in self.device_manager.devices if d['name'] == name), None)
            if profile:
                self.serial_handler.connect_device_profile(profile)
                self.logger.terminal_print(f"Connected to {name}")
            else:
                self.logger.terminal_print("Device profile not found.")

        def flash_selected_device():
            name = self.selected_device_var.get()
            profile = next((d for d in self.device_manager.devices if d['name'] == name), None)
            if profile:
                self.flasher.flash_device_profile(profile)
            else:
                self.logger.terminal_print("Device profile not found.")

        connect_btn = tk.Button(self.root, text="Connect device", command=connect_selected_device)
        connect_btn.grid(row=2, column=2, padx=5, pady=5, sticky="e")
        flash_btn = tk.Button(self.root, text="Flash firmware", command=flash_selected_device)
        flash_btn.grid(row=3, column=2, padx=5, pady=5, sticky="e")

        self.make_window_draggable()

        # Hide buttons initially
        self.control_button.grid_remove()
        self.makcu_button.grid_remove()

        # Device Manager tab
        self.create_device_manager_tab()
    def create_device_manager_tab(self):
        def open_device_manager():
            win = tk.Toplevel(self.root)
            win.title("Device Manager")
            win.geometry("700x600")
            frame = tk.Frame(win)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Known devices
            tk.Label(frame, text="Known devices:", font=("Helvetica", 12, "bold")).pack(anchor="w")
            known = self.device_manager.find_connected_devices()
            for dev in known:
                tk.Label(frame, text=f"{dev['name']} ({dev['port']})", fg="green").pack(anchor="w")

            # Unknown devices
            tk.Label(frame, text="\nUnknown devices:", font=("Helvetica", 12, "bold")).pack(anchor="w")
            unknown = self.device_manager.detect_unknown_devices()
            
            # Store unknown devices for easy access
            unknown_devices_list = []
            for dev in unknown:
                dev_label = tk.Label(frame, text=f"VID: {dev['vid']} PID: {dev['pid']} Port: {dev['port']} {dev['description']}", fg="red")
                dev_label.pack(anchor="w")
                unknown_devices_list.append(dev)

            # Add device form
            tk.Label(frame, text="\nAdd new device:", font=("Helvetica", 12, "bold")).pack(anchor="w")
            form_frame = tk.Frame(frame)
            form_frame.pack(anchor="w")
            tk.Label(form_frame, text="Name:").grid(row=0, column=0)
            name_entry = tk.Entry(form_frame)
            name_entry.grid(row=0, column=1)
            
            # VID field with copy button
            tk.Label(form_frame, text="VID:").grid(row=1, column=0)
            vid_entry = tk.Entry(form_frame)
            vid_entry.grid(row=1, column=1)
            
            # PID field with copy button
            tk.Label(form_frame, text="PID:").grid(row=2, column=0)
            pid_entry = tk.Entry(form_frame)
            pid_entry.grid(row=2, column=1)
            
            # Helper: Copy VID/PID from unknown device
            def copy_from_unknown():
                if unknown_devices_list:
                    # Create selection window
                    sel_win = tk.Toplevel(win)
                    sel_win.title("Select Device")
                    sel_win.geometry("500x300")
                    tk.Label(sel_win, text="Select device to copy VID/PID:", font=("Helvetica", 10, "bold")).pack(pady=5)
                    
                    listbox = tk.Listbox(sel_win, font=("Courier", 9))
                    listbox.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    for dev in unknown_devices_list:
                        listbox.insert(tk.END, f"VID: {dev['vid']} PID: {dev['pid']} - {dev['description']}")
                    
                    def select_device():
                        selection = listbox.curselection()
                        if selection:
                            idx = selection[0]
                            selected_dev = unknown_devices_list[idx]
                            vid_entry.delete(0, tk.END)
                            vid_entry.insert(0, selected_dev['vid'])
                            pid_entry.delete(0, tk.END)
                            pid_entry.insert(0, selected_dev['pid'])
                            if selected_dev['description']:
                                name_entry.delete(0, tk.END)
                                name_entry.insert(0, selected_dev['description'])
                            sel_win.destroy()
                    
                    tk.Button(sel_win, text="Copy to Form", command=select_device).pack(pady=5)
                else:
                    feedback_label.config(text="No unknown devices found. Plug in your device.", fg="orange")
            
            copy_btn = tk.Button(form_frame, text="📋 Copy from Unknown Devices", command=copy_from_unknown, bg="#4CAF50", fg="white")
            copy_btn.grid(row=1, column=2, rowspan=2, padx=5, sticky="ns")
            
            tk.Label(form_frame, text="Features (comma separated):").grid(row=3, column=0)
            features_entry = tk.Entry(form_frame)
            features_entry.grid(row=3, column=1)
            tk.Label(form_frame, text="Protocol:").grid(row=4, column=0)
            protocol_entry = tk.Entry(form_frame)
            protocol_entry.grid(row=4, column=1)

            # Firmware info
            tk.Label(form_frame, text="Firmware version:").grid(row=5, column=0)
            fw_version_entry = tk.Entry(form_frame)
            fw_version_entry.grid(row=5, column=1)
            tk.Label(form_frame, text="Firmware URL:").grid(row=6, column=0)
            fw_url_entry = tk.Entry(form_frame)
            fw_url_entry.grid(row=6, column=1)
            tk.Label(form_frame, text="Flash method:").grid(row=7, column=0)
            flash_method_entry = tk.Entry(form_frame)
            flash_method_entry.grid(row=7, column=1)
            tk.Label(form_frame, text="Firmware changelog:").grid(row=8, column=0)
            fw_changelog_entry = tk.Entry(form_frame)
            fw_changelog_entry.grid(row=8, column=1)

            # Protocol info
            tk.Label(form_frame, text="Baudrate:").grid(row=9, column=0)
            baudrate_entry = tk.Entry(form_frame)
            baudrate_entry.grid(row=9, column=1)
            tk.Label(form_frame, text="Handshake:").grid(row=10, column=0)
            handshake_entry = tk.Entry(form_frame)
            handshake_entry.grid(row=10, column=1)
            tk.Label(form_frame, text="Command set (komma gescheiden):").grid(row=11, column=0)
            commandset_entry = tk.Entry(form_frame)
            commandset_entry.grid(row=11, column=1)

            def auto_fetch():
                vid = vid_entry.get().strip().upper()
                pid = pid_entry.get().strip().upper()
                if not vid or not pid:
                    feedback_label.config(text="Please enter VID and PID first.", fg="red")
                    return
                
                # Try to find device in USB ports to get description
                import serial.tools.list_ports
                device_found = False
                for port in serial.tools.list_ports.comports():
                    if str(port.vid).upper() == vid and str(port.pid).upper() == pid:
                        device_found = True
                        # Auto-fill name from USB description if available
                        if port.description and not name_entry.get():
                            name_entry.delete(0, tk.END)
                            name_entry.insert(0, port.description)
                        feedback_label.config(text=f"Device found on {port.device}. Please fill remaining fields.", fg="green")
                        break
                
                if not device_found:
                    feedback_label.config(text="Device not found on USB. Fill fields manually.", fg="orange")


            feedback_label = tk.Label(frame, text="", fg="red")
            feedback_label.pack(anchor="w")

            def add_device():
                name = name_entry.get().strip()
                vid = vid_entry.get().strip().upper()
                pid = pid_entry.get().strip().upper()
                features = [f.strip() for f in features_entry.get().split(",") if f.strip()]
                protocol = protocol_entry.get().strip() or "standard"
                fw_version = fw_version_entry.get().strip()
                fw_url = fw_url_entry.get().strip()
                flash_method = flash_method_entry.get().strip()
                fw_changelog = [c.strip() for c in fw_changelog_entry.get().split(",") if c.strip()]
                baudrate = baudrate_entry.get().strip()
                handshake = handshake_entry.get().strip()
                command_set = [c.strip() for c in commandset_entry.get().split(",") if c.strip()]
                info = {
                    "type": "mouse",
                    "name": name,
                    "vid": vid,
                    "pid": pid,
                    "features": features,
                    "serial_protocol": protocol,
                    "firmware": {
                        "version": fw_version,
                        "url": fw_url,
                        "flash_method": flash_method,
                        "changelog": fw_changelog
                    },
                    "protocol_info": {
                        "baudrate": int(baudrate) if baudrate.isdigit() else baudrate,
                        "handshake": handshake,
                        "command_set": command_set
                    }
                }
                valid, msg = self.device_manager.validate_device_info(info)
                if valid:
                    self.device_manager.add_device(info)
                    feedback_label.config(text=f"Added: {name} VID:{vid} PID:{pid}", fg="blue")
                else:
                    feedback_label.config(text=msg, fg="red")

            def test_device():
                vid = vid_entry.get().strip().upper()
                pid = pid_entry.get().strip().upper()
                if vid and pid:
                    ok, msg = self.device_manager.test_device(vid, pid)
                    feedback_label.config(text=msg, fg="green" if ok else "red")
                else:
                    feedback_label.config(text="Enter VID and PID to test.", fg="red")

            fetch_btn = tk.Button(form_frame, text="Auto-fetch device data", command=auto_fetch)
            fetch_btn.grid(row=12, column=0, columnspan=2, pady=5)
            add_btn = tk.Button(form_frame, text="Add Device", command=add_device)
            add_btn.grid(row=13, column=0, columnspan=2, pady=5)
            test_btn = tk.Button(form_frame, text="Test device", command=test_device)
            test_btn.grid(row=14, column=0, columnspan=2, pady=5)

        device_manager_btn = ctk.CTkButton(self.root, text="Device Manager", command=open_device_manager)
        device_manager_btn.grid(row=2, column=1, padx=5, pady=5, sticky="n")

        # Handlers
        self.serial_handler = SerialHandler(self.logger, self.update_mcu_status, self.root)
        self.flasher = Flasher(self.logger, self.serial_handler, self.config_manager)
        self.main_folder = get_main_folder()

        # Create Updater and run check
        self.updater = Updater(self.logger, self.config_manager, self.flasher)
        self.updater.check_for_updates()

        # Start serial monitoring
        self.serial_handler.start_monitoring()

        # Schedule marquee initialization after update check
        def check_update_and_init_marquee():
            if self.updater.update_check_complete.is_set():
                # Set online/offline status after update check
                self.is_offline = self.updater.is_offline
                if self.is_offline:
                    self.online_offline_button.configure(text="Offline")
                else:
                    self.online_offline_button.configure(text="Online")
                self.fetch_and_display_welcome_message()
            else:
                self.root.after(100, check_update_and_init_marquee)

        self.root.after(100, check_update_and_init_marquee)

        # Bind the window resize event to adjust the marquee
        self.root.bind("<Configure>", self.on_window_resize)
        
    def process_queue(self):
        """Check the queue for tasks and execute them in the main thread."""
        try:
            while True:
                task = self.task_queue.get_nowait()  # Get a task if available
                task()  # Run the task (e.g., update_gui)
        except queue.Empty:
            pass  # No tasks left in the queue
        # Schedule the next check in 100ms
        self.root.after(100, self.process_queue)
        
    
    def update_progress(self, filename, status):
        def update_gui():
            if filename == "all" and status == "starting":
                self.logger.terminal_print("Downloading files...")
            elif filename == "all" and status == "complete":
                self.logger.terminal_print("Download complete")
                self.fetch_and_display_welcome_message()
            else:
                self.logger.terminal_print(f"Download {filename}: {status}")

        # Send the task to the main thread via the queue
        
        self.task_queue.put(update_gui)
        
    def restore_window_position(self):
        """
        Restore the window position from the config.json file.
        """
        window_position = self.config_manager.get_config_value("window_position", None)
        if window_position and isinstance(window_position, dict):
            x = window_position.get("x", 100)
            y = window_position.get("y", 100)
            # Ensure the position is within the screen bounds
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = max(0, min(x, screen_width - 800))
            y = max(0, min(y, screen_height - 600))
            self.root.geometry(f"800x600+{x}+{y}")
            #self.logger.terminal_print(f"Restored window position to x={x}, y={y}")
        else:
            # Default position if no saved position
            self.root.geometry("800x600+100+100")
            #self.logger.terminal_print("No saved window position, using default (100, 100)")
            
    def save_window_position(self):
        """
        Save the current window position to config.json.
        """
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.config_manager.set_config_value("window_position", {"x": x, "y": y})
            self.logger.terminal_print(f"Saved window position: x={x}, y={y}")
        except Exception as e:
            self.logger.terminal_print(f"Failed to save window position: {e}")
        
    # -------------------------------------------------------------
    # Output terminal
    # -------------------------------------------------------------
    def create_output_box(self):
        output_text = ctk.CTkTextbox(self.root, state="disabled", font=("Helvetica", 12))
        output_text.grid(row=5, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="nsew")
        return output_text

    # -------------------------------------------------------------
    # Marquee label at row=0
    # -------------------------------------------------------------
    # In the create_marquee_label method, change the anchor to "center"
    def create_marquee_label(self):
        """
        Create the marquee label that spans all three columns in row 0.
        """
        self.marquee_label = ctk.CTkLabel(
            self.root,
            text="",
            text_color="white",
            bg_color="black",
            font=("Courier", 12),
            anchor="center"  # Center text for balanced appearance
        )
        self.marquee_label.grid(row=0, column=0, columnspan=3, padx=0, pady=0, sticky="ew")

        # Initialize marquee variables
        self.marquee_text = ""
        self.full_message = ""
        self.marquee_position = 0
        self.display_length = 20
        self.marquee_speed = 50

    # -------------------------------------------------------------
    # MCU Status Label at row=1
    # -------------------------------------------------------------
    def create_mcu_status_label(self):
        """
        Create the MCU status label positioned in row 1, column 1.
        """
        self.label_mcu = ctk.CTkLabel(
            self.root,
            text="MCU disconnected",
            text_color="blue",
            font=("Helvetica", 12),
            anchor="w"
        )
        self.label_mcu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # -------------------------------------------------------------
    # Buttons at row=2
    # -------------------------------------------------------------
    def create_buttons(self):
        """
        Create the left and right button frames in row 2.
        """
        button_bg = "#1f1f1f" if self.theme_is_dark else "#d3d3d3"
        button_fg = "white" if self.theme_is_dark else "black"

        # Left button frame
        self.left_button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_button_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        for i in range(5):  # Adjusted for USB toggle button
            self.left_button_frame.grid_rowconfigure(i, weight=0, minsize=40)
        self.left_button_frame.grid_columnconfigure(0, weight=1)

        initial_theme_text = "Light Mode" if self.theme_is_dark else "Dark Mode"
        self.theme_button = ctk.CTkButton(
            self.left_button_frame,
            text=initial_theme_text,
            command=self.change_theme,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.theme_button.grid(row=0, column=0, padx=0, pady=5, sticky="w")

        self.open_log_button = ctk.CTkButton(
            self.left_button_frame,
            text="User Logs",
            command=self.open_log,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.open_log_button.grid(row=1, column=0, padx=0, pady=5, sticky="w")

        self.clear_log_button = ctk.CTkButton(
            self.left_button_frame,
            text="Clear Log",
            command=self.clear_terminal,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.clear_log_button.grid(row=2, column=0, padx=0, pady=5, sticky="w")

        # New USB Name Toggle Button (replacing hidden placeholder)
        self.usb_name_toggle_button = ctk.CTkButton(
            self.left_button_frame,
            text="Toggle CH340/CH343",
            command=self.toggle_usb_name,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.usb_name_toggle_button.grid(row=3, column=0, padx=0, pady=5, sticky="w")

        # Right button frame
        self.right_button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.right_button_frame.grid(row=2, column=2, padx=5, pady=5, sticky="ne")
        for i in range(5):
            self.right_button_frame.grid_rowconfigure(i, weight=0, minsize=40)
        self.right_button_frame.grid_columnconfigure(0, weight=1)

        self.online_offline_button = ctk.CTkButton(
            self.right_button_frame,
            text="Online",
            command=self.toggle_online_offline,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.online_offline_button.grid(row=0, column=0, padx=0, pady=5, sticky="e")

        self.makcu_button = ctk.CTkButton(
            self.right_button_frame,
            text="MAKCU",
            command=self.toggle_makcu_mode,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.makcu_button.grid(row=1, column=0, padx=0, pady=5, sticky="e")
        
        self.control_button = ctk.CTkButton(
            self.right_button_frame,
            text="Test",
            command=self.test_button_function,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.control_button.grid(row=2, column=0, padx=0, pady=5, sticky="e")

        self.quit_button = ctk.CTkButton(
            self.right_button_frame,
            text="Quit",
            command=self.quit_application,
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.quit_button.grid(row=3, column=0, padx=0, pady=5, sticky="e")

    def create_flash_buttons(self):
        """
        Create the flash buttons in row 2, within button frames.
        """
        button_bg = "#1f1f1f" if self.theme_is_dark else "#d3d3d3"
        button_fg = "white" if self.theme_is_dark else "black"

        # Left flash button in left button frame (row 4)
        self.left_flash_button = ctk.CTkButton(
            self.left_button_frame,
            text="Flash Left",
            command=lambda: self.handle_flash('left'),
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.left_flash_button.grid(row=4, column=0, padx=0, pady=5, sticky="w")
        self.left_flash_button.grid_remove()

        # Right flash button in right button frame (row 4)
        self.right_flash_button = ctk.CTkButton(
            self.right_button_frame,
            text="Flash Right",
            command=lambda: self.handle_flash('right'),
            fg_color=button_bg,
            text_color=button_fg,
            border_color=button_fg,
            border_width=1,
            font=("Helvetica", 12)
        )
        self.right_flash_button.grid(row=4, column=0, padx=0, pady=5, sticky="e")
        self.right_flash_button.grid_remove()

    def update_flash_buttons_text(self):
        """
        Update the flash buttons' text based on Devkit mode.
        """
        if self.is_devkit_mode:
            self.left_flash_button.configure(text="Flash Top Right")
            self.right_flash_button.configure(text="Flash Bottom Right")
        else:
            self.left_flash_button.configure(text="USB1 Flash")
            self.right_flash_button.configure(text="USB3 Flash")

    def create_icons(self):
        """
        Create Discord and GitHub icons in row 3.
        """
        icon_size = (20, 20)
        discord_icon_path = get_icon_path("Discord.png")
        github_icon_path = get_icon_path("GitHub.png")

        if not os.path.exists(discord_icon_path):
            self.logger.terminal_print(f"Discord icon not found at {discord_icon_path}")
        if not os.path.exists(github_icon_path):
            self.logger.terminal_print(f"GitHub icon not found at {github_icon_path}")

        try:
            discord_pil_image = Image.open(discord_icon_path).resize(icon_size)
            github_pil_image = Image.open(github_icon_path).resize(icon_size)
        except Exception as e:
            self.logger.terminal_print(f"Error loading icons: {e}")
            discord_pil_image = Image.new('RGBA', icon_size, (255, 255, 255, 0))
            github_pil_image = Image.new('RGBA', icon_size, (255, 255, 255, 0))

        self.discord_icon = CTkImage(discord_pil_image, size=icon_size)
        self.github_icon = CTkImage(github_pil_image, size=icon_size)

        self.github_icon_label = ctk.CTkLabel(self.root, image=self.github_icon, text="")
        self.github_icon_label.grid(row=4, column=0, padx=(70, 0), pady=5, sticky="w")
        self.github_icon_label.bind("<Button-1>", lambda event: webbrowser.open("https://github.com/terrafirma2021/MAKCM"))
        self.github_icon_label.bind("<Enter>", lambda event: self.github_icon_label.configure(cursor="hand2"))
        self.github_icon_label.bind("<Leave>", lambda event: self.github_icon_label.configure(cursor=""))

        self.discord_icon_label = ctk.CTkLabel(self.root, image=self.discord_icon, text="")
        self.discord_icon_label.grid(row=4, column=2, padx=(0, 70), pady=5, sticky="e")
        self.discord_icon_label.bind("<Button-1>", lambda event: webbrowser.open("https://discord.gg/6TJBVtdZbq"))
        self.discord_icon_label.bind("<Enter>", lambda event: self.discord_icon_label.configure(cursor="hand2"))
        self.discord_icon_label.bind("<Leave>", lambda event: self.discord_icon_label.configure(cursor=""))

        self.discord_icon_label.image = self.discord_icon
        self.github_icon_label.image = self.github_icon

    def create_text_input(self):
        input_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        input_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
    
        self.text_input = ctk.CTkEntry(
            input_frame,
            font=("Helvetica", 12),
            placeholder_text="Press up arrow to view input history",
            placeholder_text_color="gray"
        )
        self.text_input.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        self.text_input.bind("<FocusIn>", self.clear_placeholder)
        self.text_input.bind("<FocusOut>", self.add_placeholder)
        self.text_input.bind("<Return>", self.send_input)
        self.text_input.bind("<KP_Enter>", self.send_input)
        self.text_input.bind("<Up>", self.handle_history)
        self.text_input.bind("<Down>", self.handle_history)

    def clear_placeholder(self, event=None):
        """
        Clear the placeholder text when the input field gains focus.
        """
        if self.text_input.get() == "Press up arrow to view input history":
            self.text_input.delete(0, ctk.END)
            self.text_input.configure(text_color="black")

    def add_placeholder(self, event=None):
        """
        Add the placeholder text back if the input field is empty when it loses focus.
        """
        if not self.text_input.get():
            self.text_input.insert(0, "Press up arrow to view input history")
            self.text_input.configure(text_color="gray")

    def define_theme_colors(self):
        """
        Define and apply theme colors based on the current theme setting.
        """
        if self.theme_is_dark:
            root_bg = "black"
            button_bg = "#1f1f1f"
            button_fg = "white"
            marquee_bg = "black"
            marquee_fg = "white"
            dropdown_bg = "black"
            dropdown_fg = "white"
            dropdown_selected_bg = "#333333"
        else:
            root_bg = "white"
            button_bg = "#d3d3d3"
            button_fg = "black"
            marquee_bg = "white"
            marquee_fg = "black"
            dropdown_bg = "white"
            dropdown_fg = "black"
            dropdown_selected_bg = "#a9a9a9"

        self.root.configure(bg=root_bg)
        if hasattr(self, 'marquee_label'):
            self.marquee_label.configure(bg_color=marquee_bg, text_color=marquee_fg)

        self.dropdown_bg = dropdown_bg
        self.dropdown_fg = dropdown_fg
        self.dropdown_selected_bg = dropdown_selected_bg

        buttons = [
            getattr(self, 'theme_button', None),
            getattr(self, 'quit_button', None),
            getattr(self, 'control_button', None),
            getattr(self, 'open_log_button', None),
            getattr(self, 'clear_log_button', None),
            getattr(self, 'makcu_button', None),
            getattr(self, 'online_offline_button', None),
            getattr(self, 'left_flash_button', None),
            getattr(self, 'right_flash_button', None),
            getattr(self, 'usb_name_toggle_button', None),  # Added USB toggle button
        ]

        for btn in buttons:
            if btn:
                btn.configure(fg_color=button_bg, text_color=button_fg, border_color=button_fg, border_width=1)

        self.output_text.configure(fg_color=root_bg, text_color=button_fg)

    def change_theme(self):
        """
        Toggle between dark and light themes.
        """
        if self.theme_is_dark:
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="Light Mode")

        self.theme_is_dark = not self.theme_is_dark
        self.define_theme_colors()

    def update_mcu_status(self):
        """
        Update the MCU status label based on the connection status
        and show/hide buttons appropriately.
        """
        def update_status():
            if self.serial_handler.is_connected:
                changer = self._active_changer()  # ← Selects CH343 or FTDI
                if self.serial_handler.current_mode == "Normal":
                    status_color = "#0acc1e"  # Green
                    mode_text = "Normal"
                    self.clear_log_button.grid()
                    self.makcu_button.grid()
                    self.usb_name_toggle_button.grid()  # Show in Normal mode

                    device_name, com_port = changer.get_device_info()
                    if device_name:
                        mcu_status = f"MAKCU Connected in {mode_text} mode on {com_port} {device_name}"
                    else:
                        mcu_status = f"MAKCU Connected in {mode_text} mode on {self.serial_handler.com_port}"

                else:
                    status_color = "#bf0a37"  # Red
                    mode_text = "Flash"
                    self.clear_log_button.grid()
                    self.makcu_button.grid()
                    self.usb_name_toggle_button.grid_remove()

                    mcu_status = f"MAKCU Connected in {mode_text} mode on {self.serial_handler.com_port}"

                if self.serial_handler.current_mode == "Flash" or self.is_devkit_mode:
                    self.show_flash_buttons()
                else:
                    self.hide_flash_buttons()
            else:
                mcu_status = "MCU disconnected"
                status_color = "#1860db"
                self.clear_log_button.grid_remove()
                self.makcu_button.grid_remove()
                self.usb_name_toggle_button.grid_remove()
                self.hide_flash_buttons()

            self.label_mcu.configure(text=mcu_status, text_color=status_color)

        self.root.after(0, update_status)


    def _install_driver(self):
        """
        Background thread: Installs driver only. Does not modify the device name.
        """
        if self.usb_changer.ensure_driver_installed():
            self.logger.terminal_print("Driver installation complete.")
        else:
            self.logger.terminal_print("Driver installation failed.")
        self.task_queue.put(self.update_mcu_status)  # UI update safely
        
    def _check_ch340_mismatch(self):
        changer = self._active_changer()  # ← Selects CH343 or FTDI
        device_name, com_port = changer.get_device_info()
        if device_name and com_port and device_name.startswith(changer.target_desc):
            expected = f"{changer.target_desc} ({com_port})"
            if device_name != expected:
                self.logger.terminal_print(f"Auto-fixing CH340 name mismatch: {device_name} → {expected}")
                changer.update_registry_name(expected, com_port)
    


    def _set_custom_name_in_thread(self, new_name):
        """
        Background thread: Sets custom name safely (no device uninstall).
        """
        success = self.usb_changer.set_custom_name(new_name)
        if success:
            self.logger.terminal_print(f"USB name changed to {new_name}")
        else:
            self.logger.terminal_print("Failed to change USB name.")
        self.task_queue.put(self.update_mcu_status)

    def _restore_original_name_thread(self):
        """
        Background thread: Restores default CH343 name by uninstalling the device.
        """
        success = self.usb_changer.restore_original_name()
        if success:
            self.logger.terminal_print("\nChanging USB name, please wait...\nUSB name restored to USB-Enhanced-SERIAL CH343")
        else:
            self.logger.terminal_print("Failed to restore original USB name.")
        self.task_queue.put(self.update_mcu_status)

    def _active_changer(self):
        """Return whichever USBNameChanger currently has a matching VID/PID on the bus."""
        for ch in (self.ch343_changer, self.ftdi_changer):
            if ch.is_device_connected():
                return ch
        return self.ch343_changer   # fallback so code paths don’t break


    def toggle_usb_name(self, auto_install_driver: bool = False):
        """
        Toggle between the adapter's factory name (CH343 or FTDI)
        and the CH340-style custom name.
        """
        import re

        changer = self._active_changer()          # ← helper added earlier
        device_name, com_port = changer.get_device_info()
        if device_name is None:
            self.logger.terminal_print("Device not found. Please insert the device.")
            return

        # Strip the "(COMxx)" suffix if present
        match     = re.match(r"^(.*) \(COM\d+\)$", device_name)
        base_name = match.group(1) if match else device_name

        want_custom  = base_name == changer.default_name      # switch to CH340 style
        want_restore = base_name.startswith(changer.target_desc)  # back to factory

        # ────────────────────────────────────── safety pop-ups ─────────────────────────────────────
        if want_custom:
            proceed = messagebox.askyesno(
                title="Static COM-Port Warning",
                message=(
                    "WARNING: This will pin your COM-port inside the FriendlyName.\n"
                    "If Windows later re-assigns another COM number you must rename it again.\n\n"
                    "Continue?"
                ),
                icon=messagebox.WARNING,
            )
            if not proceed:
                self.logger.terminal_print("USB-name change cancelled by user.")
                return
        elif want_restore:
            messagebox.showinfo(
                title="Device Reconnection Required",
                message=(
                    "The device will be reset to its original name.\n"
                    "Unplug and re-plug it afterwards so Windows re-enumerates correctly."
                ),
            )

        # ────────────────────────────────── privilege / connection checks ──────────────────────────
        if not self.is_admin():
            if messagebox.askyesno(
                "Admin Privileges Required",
                "This action needs admin rights. Restart as Administrator?"
            ):
                from main import run_as_admin
                run_as_admin()
            else:
                self.logger.terminal_print("Operation cancelled – admin rights required.")
            return

        if not self.serial_handler.is_connected:
            self.logger.terminal_print("Device not connected. Connect first.")
            return

        # ───────────────────────────────── correct CH340 names already set ─────────────────────────
        if base_name.startswith(changer.target_desc):
            expected = f"{changer.target_desc} ({com_port})"
            if device_name != expected:
                self.logger.terminal_print(f"Fixing FriendlyName mismatch: {device_name} → {expected}")
                changer.update_registry_name(expected, com_port)

        # ───────────────────────────────────── perform the toggle ──────────────────────────────────
        if want_custom:
            threading.Thread(
                target=changer.set_custom_name,
                args=(changer.target_desc,),
                daemon=True,
            ).start()

        elif want_restore:
            threading.Thread(
                target=changer.restore_original_name,
                daemon=True,
            ).start()

        else:
            self.logger.terminal_print(f"Name '{base_name}' not recognised – toggle skipped.")



    def toggle_online_offline(self):
        """
        Toggle the online/offline mode manually.
        """
        self.is_offline = not self.is_offline
        self.updater.is_offline = self.is_offline
        if self.is_offline:
            self.online_offline_button.configure(text="Offline")
        else:
            self.online_offline_button.configure(text="Online")

    def send_input(self, event=None):
        """
        Send the entered command via the serial connection.
        """
        command = self.text_input.get().strip()
        if command:
            if not self.serial_handler.is_connected or not self.serial_handler.serial_open:
                self.logger.terminal_print("Connect to Device first")
            else:
                command += "\r"
                self.text_input.delete(0, ctk.END)
                try:
                    self.serial_handler.serial_connection.write(command.encode())
                    self.logger.terminal_print(f"Sent command: {command.strip()}")
                    if len(self.command_history) >= 20:
                        self.command_history.pop(0)
                    self.command_history.append(command.strip())
                    self.history_position = -1
                except Exception as e:
                    self.logger.terminal_print(f"Failed to send command: {e}")
        return "break"

    def clear_terminal(self):
        """
        Clear the output terminal.
        """
        self.output_text.configure(state="normal")
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state="disabled")

    def open_log(self):
        """
        Open the log file in the system's file explorer.
        """
        log_file_path = os.path.join(self.main_folder, 'log.txt')
        self.open_file_explorer(log_file_path)

    def open_file_explorer(self, file_path):
        """
        Open the system's file explorer at the given file path.
        """
        if os.path.exists(file_path):
            try:
                if sys.platform == "win32":
                    subprocess.Popen(['explorer', '/select,', file_path])
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', '-R', file_path])
                else:
                    subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
            except Exception as e:
                self.logger.terminal_print(f"Failed to open file explorer: {e}")
        else:
            self.logger.terminal_print("File does not exist.")

    def handle_flash(self, firmware_key):
        """
        Handle flashing for the specified side or firmware key, using pre-downloaded
        or online files.
        """
        info = self.config_manager.get_firmware_info(firmware_key)
        if not info:
            self.logger.terminal_print(
                f"No firmware file found for direction: {firmware_key}"
            )
            return
        filename = info["filename"]

        if self.updater.is_offline or not self.config_manager.is_online_status():
            self.logger.terminal_print(
                "Offline mode detected. Please select your .bin file."
            )
            self.offline_flash_dialog()
        else:
            self.logger.terminal_print(f"Attempting to flash {filename}")
            self.flasher.download_and_flash(firmware_key)

    def offline_flash_dialog(self):
        """
        Prompts the user for a local .bin firmware file and flashes it.
        """
        self.logger.terminal_print("Offline mode: Select your local firmware .bin file.")
        selected_file = filedialog.askopenfilename(
            title="Select .bin file for flashing",
            initialdir=self.main_folder,
            filetypes=[("Firmware Binary", "*.bin"), ("All Files", "*.*")]
        )
        if selected_file:
            self.logger.terminal_print(f"Selected firmware: {selected_file}")
            self.flasher.flash_local_bin(selected_file)
        else:
            self.logger.terminal_print("No firmware file selected. Aborting flash.")

    def test_button_function(self):
        """
        Perform test actions based on the current mode.
        """
        if self.serial_handler.current_mode == "Normal":
            self.test_normal_mode()
        elif self.serial_handler.current_mode == "Flash":
            self.test_flash_mode()

    def test_normal_mode(self):
        """
        Test function in Normal mode.
        """
        if self.serial_handler.is_connected:
            if self.serial_handler.serial_connection and self.serial_handler.serial_connection.is_open:
                try:
                    serial_command = "km.move(50,50)\r"
                    self.serial_handler.serial_connection.write(serial_command.encode())
                    self.logger.terminal_print("Mouse move command sent, did mouse move?")
                except Exception as e:
                    self.logger.terminal_print(f"Error sending command: {e}")
            else:
                self.logger.terminal_print("Serial connection is not open.")
        else:
            self.logger.terminal_print("Serial connection is not established. Please connect first.")

    def test_flash_mode(self):
        """
        Test function in Flash mode.
        """
        self.logger.terminal_print("Test function is disabled in Flash mode.")

    def toggle_makcu_mode(self):
        """
        Toggle between MAKCU and Devkit modes.
        """
        if self.is_devkit_mode:
            self.is_devkit_mode = False
            self.makcu_button.configure(text="MAKCU")
            self.hide_flash_buttons()
        else:
            self.is_devkit_mode = True
            self.makcu_button.configure(text="Devkit")
            self.show_flash_buttons()
        self.update_flash_buttons_text()

    def show_flash_buttons(self):
        """
        Show the flash buttons and update their texts.
        """
        self.left_flash_button.grid()
        self.right_flash_button.grid()
        self.update_flash_buttons_text()

    def hide_flash_buttons(self):
        """
        Hide the flash buttons.
        """
        self.left_flash_button.grid_remove()
        self.right_flash_button.grid_remove()

    def fetch_and_display_welcome_message(self):
        """
        Fetch the welcome message and start the marquee in the main thread.
        """
        try:
            marquee_message = self.config_manager.get_config_value("message", "Welcome to MAKCU!")
            self.marquee_text = marquee_message + "    "
            self.start_marquee()
        except Exception as e:
            self.logger.terminal_print(f"Error fetching welcome message: {e}")
            self.set_offline_marquee()

    def start_marquee(self):
        """
        Initialize the marquee to start scrolling.
        """
        if not self.marquee_text:
            return
        self.update_full_message()
        self.marquee_position = 0
        self.animate_marquee()

    def animate_marquee(self):
        """
        Scroll the marquee text from right to left smoothly using Tkinter's event loop.
        """
        if not self.marquee_text:
            return
        start_idx = self.marquee_position
        end_idx = start_idx + self.display_length
        visible_message = self.full_message[start_idx:end_idx]
        if len(visible_message) < self.display_length:
            visible_message += " " * (self.display_length - len(visible_message))
        self.marquee_label.configure(text=visible_message)
        total_length = len(self.marquee_text) + self.display_length
        self.marquee_position = (self.marquee_position + 1) % total_length
        self.root.after(self.marquee_speed, self.animate_marquee)

    def update_full_message(self):
        """
        Recalculate the full message with minimal padding for smooth scrolling.
        """
        self.display_length = self.get_display_length()
        if self.display_length is None:
            self.display_length = 50
        self.full_message = self.marquee_text + " " * self.display_length
        self.marquee_position = 0

    def get_display_length(self):
        self.root.update_idletasks()
        label_width = self.marquee_label.winfo_width()
        font = tkfont.Font(font=self.marquee_label.cget("font"))
        avg_char_width = font.measure("W")
        if avg_char_width == 0:
            return 50
        calculated_length = max(int(label_width / avg_char_width), 10)
        return calculated_length

    def set_offline_marquee(self):
        """
        Set the marquee to display an offline message.
        """
        offline_message = "You are offline, manual flashing supported    "
        self.marquee_text = offline_message
        self.start_marquee()

    def handle_history(self, event):
        """
        Navigate through the command history using up/down arrows.
        """
        if not self.command_history:
            return "break"
        if event.keysym == "Up":
            if self.history_position < len(self.command_history) - 1:
                self.history_position += 1
                command = self.command_history[-self.history_position - 1]
                self.text_input.delete(0, ctk.END)
                self.text_input.insert(0, command)
        elif event.keysym == "Down":
            if self.history_position > 0:
                self.history_position -= 1
                command = self.command_history[-self.history_position - 1]
                self.text_input.delete(0, ctk.END)
                self.text_input.insert(0, command)
            elif self.history_position == 0:
                self.history_position = -1
                self.text_input.delete(0, ctk.END)
        return "break"

    def show_history_menu(self):
        """
        Show a dropdown menu of command history.
        """
        if not self.command_history:
            return
        if self.history_dropdown and tk.Toplevel.winfo_exists(self.history_dropdown):
            return
        self.history_dropdown = tk.Toplevel(self.root)
        self.history_dropdown.wm_overrideredirect(True)
        self.history_dropdown.configure(bg=self.dropdown_bg)
        self.root.update_idletasks()
        input_x = self.text_input.winfo_rootx()
        input_y = self.text_input.winfo_rooty() + self.text_input.winfo_height()
        input_width = self.text_input.winfo_width()
        self.history_dropdown.wm_geometry(f"{input_width}x200+{input_x}+{input_y}")
        frame = tk.Frame(self.history_dropdown, bg=self.dropdown_bg, bd=1, relief="solid")
        frame.pack(fill="both", expand=True)
        self.history_listbox = tk.Listbox(
            frame,
            selectmode=tk.SINGLE,
            height=10,
            bg=self.dropdown_bg,
            fg=self.dropdown_fg,
            selectbackground=self.dropdown_selected_bg,
            font=("Helvetica", 12)
        )
        for cmd in reversed(self.command_history):
            self.history_listbox.insert(tk.END, cmd)
        self.history_listbox.pack(side="left", fill="both", expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)
        self.history_listbox.bind("<MouseWheel>", lambda event: self.history_listbox.yview_scroll(int(-1*(event.delta/120)), "units"))
        self.history_listbox.bind("<Button-4>", lambda event: self.history_listbox.yview_scroll(-1, "units"))
        self.history_listbox.bind("<Button-5>", lambda event: self.history_listbox.yview_scroll(1, "units"))
        self.root.bind("<Button-1>", self.on_click_outside)
        self.history_listbox.focus_set()

    def update_history_dropdown(self):
        """
        Update the history dropdown with the latest commands.
        """
        if self.history_dropdown and tk.Toplevel.winfo_exists(self.history_dropdown):
            self.history_listbox.delete(0, tk.END)
            for cmd in reversed(self.command_history):
                self.history_listbox.insert(tk.END, cmd)

    def on_history_select(self, event):
        """
        Handle selection of a command from the history dropdown.
        """
        selected_indices = self.history_listbox.curselection()
        if selected_indices:
            selected_command = self.history_listbox.get(selected_indices[0])
            self.select_history_command(selected_command)
            self.hide_history_dropdown()

    def on_click_outside(self, event):
        """
        Hide the history dropdown if clicked outside.
        """
        if self.history_dropdown:
            x1 = self.history_dropdown.winfo_rootx()
            y1 = self.history_dropdown.winfo_rooty()
            x2 = x1 + self.history_dropdown.winfo_width()
            y2 = y1 + self.history_dropdown.winfo_height()
            if not (x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2):
                self.hide_history_dropdown()

    def hide_history_dropdown(self):
        """
        Hide and destroy the history dropdown.
        """
        if self.history_dropdown and tk.Toplevel.winfo_exists(self.history_dropdown):
            self.history_dropdown.destroy()
            self.history_dropdown = None
            self.root.unbind("<Button-1>")

    def select_history_command(self, command):
        """
        Insert the selected command into the text input.
        """
        self.text_input.delete(0, ctk.END)
        self.text_input.insert(0, command)

    def make_window_draggable(self):
        """
        Enable dragging the window by clicking and holding only on the marquee label.
        """
        def start_drag(event):
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.window_start_x = self.root.winfo_x()
            self.window_start_y = self.root.winfo_y()
    
        def drag_window(event):
            delta_x = event.x_root - self.drag_start_x
            delta_y = event.y_root - self.drag_start_y
            new_x = self.window_start_x + delta_x
            new_y = self.window_start_y + delta_y
            self.root.geometry(f"+{new_x}+{new_y}")
    
        self.marquee_label.bind("<Button-1>", start_drag)
        self.marquee_label.bind("<B1-Motion>", drag_window)

    def quit_application(self):
        """
        Safely exit the application, ensuring all threads and connections are closed.
        """
        try:
            self.save_window_position()
            self.serial_handler.monitoring_active = False
            self.serial_handler.stop_monitoring()
            self.logger.stop()
            if self.flasher.is_flashing:
                self.logger.terminal_print("Flashing in progress. Please wait...")
                while self.flasher.is_flashing:
                    time.sleep(0.1)
        except Exception as e:
            self.logger.terminal_print(f"Error during shutdown: {e}")
        finally:
            self.root.quit()
            self.root.destroy()

    def on_window_resize(self, event):
        """
        Handle window resize events to adjust marquee display length.
        """
        new_display_length = self.get_display_length()
        if new_display_length != self.display_length:
            self.display_length = new_display_length
            self.update_full_message()