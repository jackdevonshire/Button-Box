"""
Minimal schema migrations for the SQLite database.

db.create_all() creates missing tables but never changes existing ones, so columns added after a database was first
created are added here. The schema version is stored in the settings table; each migration runs once, in order.
Migrations must be safe to run on a freshly created database too (where create_all already made the new columns).
"""
from sqlalchemy import inspect, text

SCHEMA_VERSION_KEY = "SchemaVersion"


def add_column_if_missing(db, table, column, definition):
    columns = [c["name"] for c in inspect(db.engine).get_columns(table)]
    if column not in columns:
        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def migration_1_bindings(db):
    # Configuration buttons become bindings with modifiers, gestures and an enabled flag
    add_column_if_missing(db, "configuration_button", "modifiers", "JSON NOT NULL DEFAULT '[]'")
    add_column_if_missing(db, "configuration_button", "gesture", "VARCHAR NOT NULL DEFAULT 'single'")
    add_column_if_missing(db, "configuration_button", "enabled", "BOOLEAN NOT NULL DEFAULT 1")
    add_column_if_missing(db, "configuration", "display_lines", "JSON")


MIGRATIONS = [
    migration_1_bindings,
]


def run_migrations(db):
    from app.core.models import Setting

    version_setting = db.session.get(Setting, SCHEMA_VERSION_KEY)
    if version_setting is None:
        version_setting = Setting(key=SCHEMA_VERSION_KEY, value="0", visible=False)
        db.session.add(version_setting)

    current_version = int(version_setting.value)
    for version, migration in enumerate(MIGRATIONS, start=1):
        if version > current_version:
            print(f"Running database migration {version}: {migration.__name__}")
            migration(db)
            version_setting.value = str(version)
            db.session.commit()

    db.session.commit()
