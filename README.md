# MAKCU AIO (All-In-One)

https://www.makcu.com/

## Features

### Two Interfaces for Every Skill Level
- **🧙‍♂️ Setup Wizard** (`main_wizard.py`) - Step-by-step guided setup for beginners
  - 5-step process for easy configuration
  - Auto-detection of devices
  - Built-in firmware update flow
- **⚡ Advanced Interface** (`main.py`) - Full-featured interface for power users
  - All options visible at once
  - Direct access to all features
  - Device Manager for adding custom devices

## Quick Start

### Prerequisites
- Windows OS
- Python 3.8+ (for development)
- USB connection to supported mouse

### Installation

#### Option 1: Use Pre-built Executable
1. Download the latest release from the Releases page
2. Extract the ZIP file
3. Run `MAKCU.exe`

#### Option 2: Run from Source
```powershell
# Clone the repository
git clone https://github.com/dyvertigo/MAKCU_AIO_PUBLIC.git
cd MAKCU_AIO_PUBLIC

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application (choose one)
python main.py          # Advanced interface
python main_wizard.py   # Beginner wizard interface
```

### First Time Setup

#### 1. Hardware Setup (MAKCU Device)

**Initial Configuration:**
1. Open the MAKCU AIO tool
2. **Hold the left button down** on your MAKCU device
3. Connect the USB cable
4. Release the button
5. Press the **USB 1** button on the device

**Repeat for right side:**
- Follow the same steps (hold button → connect → release → press USB 1)

**Install Driver:**
- Click "Install CH343 Driver" in the application (if not already installed)

#### 2. Normal MAKCU Usage

**USB Port Configuration:**
- **USB 3** = Mouse connection
- **USB 2** = COM port (serial communication)
- **USB 1** = Main PC connection

#### 3. Software Setup

1. **Launch MAKCU**: Run the executable or Python script
2. **Select Device**: Choose your device from the dropdown (or add it if not listed)
3. **Connect**: Click "Connect" to establish serial communication (uses USB 2/COM port)
4. **Configure**: Adjust settings or flash firmware as needed

## Adding New Devices

### Device Manager (Advanced Interface)
1. Click "Device Manager" button in main window
2. Use "📋 Copy from Unknown Devices" button to detect and copy VID/PID
3. Fill in device information (name, features, protocol)
4. Click "Test Device" to verify connectivity
5. Click "Add Device" to save to your local database



## Device Profile Structure

```json
{
  "name": "Example Gaming Mouse",
  "vid": "1234",
  "pid": "5678",
  "features": ["dpi", "polling_rate", "rgb", "macros"],
  "serial_protocol": "standard",
  "firmware": {
    "version": "1.0.0",
    "url": "https://example.com/firmware.bin",
    "flash_method": "standard_flash",
    "changelog": "Initial release"
  },
  "protocol_info": {
    "baudrate": 115200,
    "handshake": "none",
    "command_set": "standard_v1"
  }
}
```

## Supported Features

Device features that can be configured:
- `dpi`: Dots per inch sensitivity
- `polling_rate`: USB polling rate (Hz)
- `rgb`: RGB lighting control
- `macros`: Macro programming (future feature)
- `buttons`: Button remapping (future feature)
- `profiles`: Profile switching (future feature)



## Troubleshooting

### MAKCU Device Not Responding
**Initial setup not working?**
1. Make sure to **hold the button BEFORE** connecting the cable
2. Keep holding until the cable is fully connected
3. Then release and press USB 1
4. If still not working, try the other side first
5. Ensure CH343 driver is installed

### Device Not Detected
- Ensure mouse is plugged into **USB 3** port on MAKCU
- Check that MAKCU device is connected to PC via **USB 1**
- Try a different USB port on your PC
- Check if device is listed in Windows Device Manager
- Run application as Administrator

### Connection Failed (COM Port Issues)
- Make sure **USB 2** is connected for serial communication
- Verify correct VID/PID in device profile
- Check baudrate matches device specification (usually 115200)
- Ensure no other software is using the COM port
- Close any other serial monitor applications
- Try a different COM port in Device Manager
- Restart the application as Administrator

### Driver Issues
- Install CH343 driver using the button in the application
- If driver installation fails, run as Administrator
- Check Windows Device Manager for yellow warning icons
- Manually install driver from `assets/driver/` folder

### Flash Failed
- Verify firmware file is accessible
- Check flash method matches device requirements
- Ensure device is in bootloader mode if required
- Check device permissions and admin rights
- Try using a different USB cable or port


### Device Profile Contributions
1. Test device thoroughly with MAKCU
2. Create complete device profile using Device Manager
3. Export as JSON and include in pull request or in the discord
4. Document any device-specific quirks or requirements

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- Original MAKCU project and contributors
- CustomTkinter developers for the modern UI framework
- PySerial team for serial communication support
- CH343 driver providers
