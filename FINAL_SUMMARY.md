# workspace_app — Current Status

This package contains a native Python/PySide6/SQLite desktop accounting application.
The React files are a documentation/web-preview stub and are not the main desktop UI.

## Repairs

- Fixed the PySide6 QFont enum usage in `main.py`.
- Fixed the POS table `SelectionBehavior` enum.
- Removed the self-referential totals layout.
- Reworked `_totals_row()` so its QHBoxLayout is explicitly attached to the supplied parent layout while keeping the existing `(label, value)` return contract.
- Adjusted login-to-main-window creation order to avoid Qt last-window lifetime issues.
- Added the application icon.
- Updated `build.bat` to use Python 3.11.x and `venv311`.

## What has been verified

- All Python source files pass syntax/AST parsing.
- The known faulty Qt calls are corrected by static inspection.

## What still requires Windows validation

The Linux repair environment cannot execute the native Windows/PySide6 GUI or produce/test a Windows EXE.
Therefore the following must be validated on Windows:

1. `python -m pytest -q`
2. `python main.py`
3. Login and open Dashboard/POS/Sales/Purchases/Inventory/Customers/Suppliers/Reports/Settings.
4. `python -m PyInstaller --clean --noconfirm app.spec`
5. Confirm `dist\AccountingSystem.exe` runs.

## Expected EXE

`dist\AccountingSystem.exe`

## Environment

Use Python 3.11.x because `requirements.txt` pins PySide6 6.7.3.
