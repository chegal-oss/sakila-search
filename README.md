# Sakila Film Search

CLI application for searching films in the `sakila` database with filters by category, release period, and title.

## Requirements

- Python 3.14
- access to MySQL
- access to MongoDB

## Installation

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows `cmd`:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Environment Configuration

The project reads environment variables from the `.env` file.

Minimum required variables:

```env
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=your-database-name
DB_USER=your-mysql-user
DB_PASSWORD=your-mysql-password
MONGO_URI=mongodb://your-user:your-password@your-host/?readPreference=primary&ssl=false&authMechanism=DEFAULT&authSource=your-auth-db
MONGO_DATABASE=your-mongo-database
MONGO_COLLECTION=your-mongo-collection
```

## Run

macOS / Linux:

```bash
source .venv/bin/activate
python main.py
```

Windows `cmd`:

```bat
.venv\Scripts\activate.bat
python main.py
```

## Features

- shows film categories
- shows release periods
- allows searching by film title
- displays paginated results
- supports search history storage in MongoDB
