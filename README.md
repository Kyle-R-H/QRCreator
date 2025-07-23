# Description
Quick QR code generator

## How to use
### Versions
**Exe Version:**
Simply copy the exe (QRCreator_x.exe) to your local system and run. It may trigger your ad blocker, I promise it's safe.

**Python Version:**
Just have python installed as well as pip packages (imports at top of the file)(pip install package_name, google if needed) and run.

### Folders
#### V1 - Single QR
Contains exe and .py for doing 1 QR code at a time

#### V2 - Excel
Contains exe and .py for converting all text in 1st column of excel file.

# Terminal Commands for python file:
### Create exe:
pyinstaller --onefile --noconsole QRCreator.py

pyinstaller --onefile --windowed --clean  QRCreator.py
