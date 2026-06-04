# Sakila Film Search

CLI application for searching films in the `sakila` database with filters by category, release period, and title.

## Requirements

- Python 3.14
- MySQL access is optional at runtime
- MongoDB access is optional at runtime

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

The project reads environment variables from the `.env` file when it exists.
All variables have local defaults, so importing and running the project does not require `.env`.

Optional MySQL variables:

```env
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=your-database-name
DB_USER=your-mysql-user
DB_PASSWORD=your-mysql-password
DB_CONNECT_TIMEOUT=3
```

Optional MongoDB variables:

```env
MONGO_URI=mongodb://your-user:your-password@your-host/
MONGO_DATABASE=your-mongo-database
MONGO_COLLECTION=your-mongo-collection
MONGO_TIMEOUT_MS=3000
```

## Local SQLite Copy

Create or refresh the local SQLite database:

```bash
python scripts/copy_mysql_to_sqlite.py
```

The script copies only tables used by the application: `film`, `film_category`, and `category`.
The local file is created at `data/sakila.sqlite` and is ignored by git.

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
- shows detailed film information
- uses MySQL when available and falls back to local SQLite
- stores search history in MongoDB when available and falls back to local SQLite
