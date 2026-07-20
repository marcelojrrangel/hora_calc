#!/usr/bin/env python3
"""
Migra CSVs existentes para incluir coluna ID.

Uso: python scripts/migrate_csv_ids.py [data_dir]
"""
import sys
import uuid
from pathlib import Path


def migrate_file(file_path: Path) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return 0

    header = lines[0].strip()
    if header.startswith("ID;"):
        print(f"  Skipping {file_path.name} (already has ID column)")
        return 0

    new_lines = ["ID;" + header + "\n"]
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        meeting_id = uuid.uuid4().hex[:8]
        new_lines.append(f"{meeting_id};{line}\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return len(new_lines) - 1


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")

    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        sys.exit(1)

    csv_files = sorted(data_dir.glob("Horas_*.csv"))
    if not csv_files:
        print("No CSV files found.")
        return

    total_migrated = 0
    for csv_file in csv_files:
        count = migrate_file(csv_file)
        if count > 0:
            print(f"Migrated {count} meetings in {csv_file.name}")
            total_migrated += count

    print(f"\nTotal: {total_migrated} meetings migrated across {len(csv_files)} files.")


if __name__ == "__main__":
    main()
