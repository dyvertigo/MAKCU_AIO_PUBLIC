# Contributing to MAKCU AIO

Thank you for your interest in contributing to MAKCU AIO! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - System information (Windows version, Python version)

### Suggesting Features

1. Check if the feature has been suggested in Issues or Discussions
2. Create a new issue/discussion with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach

### Code Contributions

#### Setup Development Environment

```powershell
# Clone your fork
git clone https://github.com/dyvertigo/MAKCU_AIO_PUBLIC.git
cd MAKCU_AIO_PUBLIC

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Making Changes

1. **Create a branch** for your feature/fix:
   ```powershell
   git checkout -b feature/my-awesome-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Follow coding standards**:
   - All code must be in English (comments, variables, functions, docstrings)
   - Use meaningful variable and function names
   - Add docstrings to all functions and classes
   - Follow PEP 8 style guidelines
   - Keep functions focused and modular

3. **Code structure guidelines**:
   ```python
   def example_function(param1: str, param2: int) -> bool:
       """
       Brief description of what the function does.
       
       Args:
           param1: Description of param1
           param2: Description of param2
           
       Returns:
           Description of return value
       """
       # Implementation here
       pass
   ```

4. **Test your changes**:
   - Test both wizard and advanced interfaces
   - Test with real hardware when possible
   - Verify no errors in console/terminal
   - Check that log files don't contain errors

5. **Commit your changes**:
   ```powershell
   git add .
   git commit -m "feat: add awesome feature"
   # or
   git commit -m "fix: resolve connection issue"
   ```

   Use conventional commit format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

6. **Push to your fork**:
   ```powershell
   git push origin feature/my-awesome-feature
   ```

7. **Create Pull Request**:
   - Go to GitHub and create a PR
   - Describe what your changes do
   - Reference any related issues
   - Add screenshots if UI changes

#### Code Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged
- Your contribution will be credited

### Adding Device Profiles

If you want to add support for a new device:

1. **Test the device** thoroughly with MAKCU
2. **Use Device Manager** in the advanced interface to add the device
3. **Export the profile** as JSON
4. **Submit via Pull Request**:
   - Add the JSON file to a new PR
   - Include device name, manufacturer, and model
   - Document any special requirements or quirks

Device profile template:
```json
{
  "name": "Device Name",
  "vid": "1234",
  "pid": "5678",
  "features": ["dpi", "polling_rate", "rgb"],
  "serial_protocol": "standard",
  "firmware": {
    "version": "1.0.0",
    "url": "https://example.com/firmware.bin",
    "flash_method": "standard_flash",
    "changelog": "Initial support"
  },
  "protocol_info": {
    "baudrate": 115200,
    "handshake": "none",
    "command_set": ["standard_v1"]
  }
}
```

### Documentation

Help improve documentation:
- Fix typos and grammar
- Add missing information
- Improve clarity
- Add examples and screenshots
- Translate documentation (UI must stay in English)

## Development Guidelines

### Python Version
- Target Python 3.8+
- Test on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

### Dependencies
- Minimize external dependencies
- Document why new dependencies are needed
- Update `requirements.txt`

### File Structure
```
modules/
  ├── gui.py              # Advanced interface
  ├── wizard_gui.py       # Beginner interface
  ├── device_manager.py   # Device management
  ├── serial_handler.py   # Serial communication
  ├── flasher.py          # Firmware flashing
  ├── config_manager.py   # Configuration
  ├── logger.py           # Logging system
  ├── updater.py          # Auto-update
  ├── usb_name_changer.py # USB utilities
  └── utils.py            # Helper functions
```

### What NOT to Include

❌ Personal information (names, emails, tokens)
❌ Hardcoded credentials or API keys
❌ Large binary files
❌ IDE-specific files (.vscode, .idea)
❌ Compiled files (__pycache__, *.pyc)
❌ Log files
❌ Test/temporary files
❌ Non-English code or comments

### Security

- Never commit secrets, tokens, or credentials
- Validate all user input
- Sanitize file paths
- Use secure communication (HTTPS)
- Review dependencies for vulnerabilities

## Getting Help

- **Questions**: Use GitHub Discussions
- **Bugs**: Use GitHub Issues
- **Chat**: Join our community (link in README)

## Recognition

Contributors will be:
- Listed in the project contributors
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to MAKCU AIO! 🚀
