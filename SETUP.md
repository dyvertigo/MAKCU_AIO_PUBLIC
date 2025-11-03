# Quick Setup Guide

## Just Want to Run It?

### For Users (No Coding)
1. Download the `.exe` file from [Releases](https://github.com/dyvertigo/MAKCU_AIO_PUBLIC/releases)
2. Run it (choose Wizard or Advanced version)
3. That's it! ✅

---

##  For Developers

### Quick Start (5 steps)

```powershell
# 1. Clone
git clone https://github.com/dyvertigo/MAKCU_AIO_PUBLIC.git
cd MAKCU_AIO_PUBLIC

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run it!
python main.py              # Advanced interface
# or
python main_wizard.py       # Beginner wizard
```

**That's it!** The app works out of the box.

### Optional: Virtual Environment

If you want isolation (recommended):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Building Executables

Want to create `.exe` files?

```powershell
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build (choose one or both)
pyinstaller --onefile --noconsole --uac-admin --name MAKCU_Advanced main.py
pyinstaller --onefile --noconsole --uac-admin --name MAKCU_Wizard main_wizard.py

# 3. Find your .exe files in the dist/ folder
```



---

## Common Issues

**"Module not found"**  
→ Run: `pip install -r requirements.txt`

**Build fails**  
→ Run: `pip install --upgrade pyinstaller`

**Antivirus blocks .exe**  
→ Add exception for the `dist/` folder

---

## Need More Help?

- Check the [README.md](README.md) for features overview
- See [CONTRIBUTING.md](CONTRIBUTING.md) for code guidelines
- Open an [Issue](https://github.com/dyvertigo/MAKCU_AIO_PUBLIC/issues) if stuck

