"""
Test script to verify the Supabase/Postgres database connection.
Run from the project root: python -m tests.test_supabase_connection
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src.*` imports resolve
# when running the script directly (python tests/test_supabase_connection.py)
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, inspect, text
from src.core.config import settings


def list_tables() -> None:
    """Connect to the Supabase Postgres database and list all schemas / tables."""

    if not settings.POSTGRES_URL:
        print("ERROR: POSTGRES_URL is not set in .env")
        print(
            "  -> Go to your Supabase dashboard: Settings > Database > Connection string"
        )
        sys.exit(1)

    print(f"Connecting to: {settings.POSTGRES_URL[:40]}...")

    try:
        engine = create_engine(settings.POSTGRES_URL, echo=False)

        # Quick sanity check – run a trivial query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("Connection successful!\n")

        inspector = inspect(engine)
        schemas = inspector.get_schema_names()

        for schema in schemas:
            tables = inspector.get_table_names(schema=schema)
            if tables:
                print(f"Schema: {schema}")
                for table in tables:
                    print(f"  - {table}")

    except ModuleNotFoundError:
        print(
            "ERROR: Missing database driver. Install one with:\n"
            "  pip install psycopg2-binary"
        )
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: Could not connect to the database.\n  {exc}")
        sys.exit(1)


if __name__ == "__main__":
    list_tables()