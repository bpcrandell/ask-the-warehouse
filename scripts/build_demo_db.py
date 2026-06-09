"""Build the demo warehouse. Run: python scripts/build_demo_db.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask.demo_data import DEFAULT_DB, build  # noqa: E402

if __name__ == "__main__":
    counts = build(DEFAULT_DB)
    print(f"Built {DEFAULT_DB}")
    for table, n in counts.items():
        print(f"  {table:28} {n:>6} rows")
