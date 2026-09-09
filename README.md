# نظام المحاسبة وإدارة الأعمال
# Accounting & Business Management System

A professional Windows desktop accounting application built with Python, PySide6, and SQLite.

## Phase 1 — Production Foundation

This is Phase 1 of the project. It establishes the production-quality local core that all future business modules will build upon.

### What's Included

✅ **Native PySide6 Desktop Application**
- Login window with Arabic RTL support
- Main window with sidebar navigation
- Dashboard, Users, Audit Log, Backup, Settings pages
- Status bar with system information
- Arabic/English language framework

✅ **SQLite Database**
- WAL mode for better concurrency
- Foreign key enforcement
- Transaction support
- Schema versioning
- Safe initialization

✅ **Migration System**
- SQL-based migrations
- Automatic version tracking
- Safe, repeatable upgrades
- Located in `database/migrations/`

✅ **Authentication & Security**
- bcrypt password hashing (12 rounds)
- Session management with expiration
- Role-based permissions (6 roles)
- Audit logging for all auth events
- Default admin user creation

✅ **Repository Layer**
- UserRepository
- AuditRepository
- OutboxRepository (sync foundation)
- SettingsRepository

✅ **Service Layer**
- AuthService (login, logout, session validation, password change)
- BackupService (create, restore, validate backups)

✅ **Outbox Foundation**
- Durable outbox table for future cloud sync
- Operation tracking with retry support
- Status management (pending → syncing → synced/failed)

✅ **Backup & Restore**
- Safe SQLite backup using backup API
- Restore with safety backup
- Backup validation
- Backup listing and deletion

✅ **Configuration**
- Application data stored in `%APPDATA%\AccountingSystem\`
- User preferences persisted
- Database outside installation directory

✅ **Logging**
- Rotating file logs
- Console output for development
- Structured log format

✅ **Testing**
- Database tests
- Authentication tests
- Migration tests
- Backup/restore tests

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Windows 10/11

### Installation

```bash
# Clone or extract the project
cd project

# Run the build script (creates venv, installs deps, runs tests, builds EXE)
build.bat
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate application icon (optional but recommended)
python generate_icon.py

# Run the application
python main.py

# Run tests
python -m pytest tests/ -v
```

### Default Login

```
Username: admin
Password: admin123
```

⚠️ **IMPORTANT**: Change the default password immediately after first login!

## Project Structure

```
project/
├── app/
│   ├── ui/                  # PySide6 desktop interface
│   │   ├── login_window.py  # Login screen
│   │   ├── main_window.py   # Main application window
│   │   └── styles.py        # Application theming
│   ├── services/            # Application services
│   │   ├── auth_service.py  # Authentication logic
│   │   └── backup_service.py # Backup/restore
│   ├── domain/              # Business entities
│   │   └── models.py        # Data models
│   ├── repositories/        # Data access layer
│   │   ├── user_repo.py     # User CRUD
│   │   ├── audit_repo.py    # Audit log
│   │   ├── outbox_repo.py   # Sync outbox
│   │   └── settings_repo.py # Settings
│   ├── database/            # Database layer
│   │   ├── connection.py    # SQLite connection
│   │   └── migrations.py    # Migration manager
│   ├── security/            # Security
│   │   ├── passwords.py     # Password hashing
│   │   └── permissions.py   # Role-based permissions
│   ├── config/              # Configuration
│   │   └── settings.py      # App settings
│   └── utils/               # Utilities
│       ├── i18n.py          # Internationalization
│       └── logging_config.py # Logging setup
├── database/
│   └── migrations/          # SQL migration files
│       ├── 001_initial.sql  # Core tables
│       └── 002_outbox.sql   # Sync outbox
├── tests/                   # Test suite
│   ├── test_database.py     # Database tests
│   ├── test_auth.py         # Auth tests
│   ├── test_backup.py       # Backup tests
│   └── test_migrations.py   # Migration tests
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── build.bat                # Windows build script
├── app.spec                 # PyInstaller specification
├── version_info.txt         # EXE version info
└── README.md                # This file
```

## Architecture

```
PySide6 UI (app/ui/)
    ↓
Application Services (app/services/)
    ↓
Domain / Business Logic (app/domain/)
    ↓
Repositories (app/repositories/)
    ↓
SQLite Database (app/database/)
```

### Data Flow

```
User Action
    ↓
UI Layer (PySide6)
    ↓
Service Layer (business logic)
    ↓
Repository Layer (data access)
    ↓
SQLite (persistence)
    ↓
Outbox (future sync)
```

## Data Storage

User data is stored outside the application installation directory:

```
%APPDATA%\AccountingSystem\
├── data\
│   ├── app.db           # Main database
│   └── preferences.json # User preferences
├── backups\             # Database backups
├── logs\                # Application logs
│   └── app.log
└── exports\             # Data exports
```

This ensures that application updates never delete user data.

## Roles & Permissions

| Role | Description |
|------|-------------|
| Owner | Full system access |
| Admin | System administration |
| Manager | Business operations |
| Cashier | Sales operations |
| Accountant | Financial reporting |
| Inventory | Stock management |

## Technology Stack

- **Python 3.10+** — Core language
- **PySide6** — Desktop GUI framework
- **SQLite** — Local database
- **bcrypt** — Password hashing
- **PyInstaller** — EXE packaging
- **pytest** — Testing

All dependencies have prebuilt Windows wheels. No C++ compiler or Visual Studio required.

## Building the EXE

```bash
build.bat
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Run the test suite
4. Build the EXE using PyInstaller
5. Place the result in `dist\AccountingSystem.exe`

## Next Steps (Phase 2)

Phase 2 will add the business modules:
- Point of Sale (POS)
- Sales Management
- Purchase Management
- Inventory Management
- Customer Management
- Supplier Management
- Reports & Analytics

## License

Copyright (c) 2024. All rights reserved.
