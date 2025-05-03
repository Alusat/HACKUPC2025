import csv
from collections import defaultdict

CSV_PATH = "data/iata_airports_and_locations_with_vibes.csv"

def count_duplicates(csv_path: str):
    name_counts = defaultdict(int)

    # Read all en-GB names and count occurrences
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("en-GB", "").strip()
            if name:
                name_counts[name] += 1

    # Filter duplicates
    duplicates = {name: count for name, count in name_counts.items() if count > 1}

    print(f"\nTotal unique names: {len(name_counts)}")
    print(f"Names with duplicates: {len(duplicates)}\n")
    for name, count in sorted(duplicates.items(), key=lambda x: -x[1]):
        print(f"{name}: {count} entries")

if __name__ == "__main__":
    count_duplicates(CSV_PATH)
