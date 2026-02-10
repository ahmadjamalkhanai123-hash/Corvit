"""Seed the database with sample data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import async_session_factory
from src.database.seed import seed_database


async def main() -> None:
    print("Seeding database...")
    async with async_session_factory() as session:
        stats = await seed_database(session)
    print("Seed complete:")
    for key, count in stats.items():
        print(f"  {key}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
