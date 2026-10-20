"""Back up test.db and add the nullable user_id column if it is missing."""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("test.db")


def main():
    if not DB_PATH.is_file():
        raise SystemExit(
            f"Could not find {DB_PATH.resolve()}. Run this from the directory containing test.db."
        )

    with sqlite3.connect(DB_PATH) as connection:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "posts" not in tables:
            raise SystemExit("The database has no 'posts' table; no changes were made.")
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(posts)").fetchall()
        }

    if "user_id" in columns:
        print("No change needed: posts.user_id already exists.")
        return

    backup = DB_PATH.with_name(
        f"{DB_PATH.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{DB_PATH.suffix}"
    )
    shutil.copy2(DB_PATH, backup)
    print(f"Backup created: {backup.resolve()}")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("ALTER TABLE posts ADD COLUMN user_id CHAR(32) NULL")
        connection.commit()

    print("Migration complete. Existing posts are preserved; their owners remain unknown.")


if __name__ == "__main__":
    main()
