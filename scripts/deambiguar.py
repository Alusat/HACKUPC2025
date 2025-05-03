import csv

INPUT_CSV = "data/iata_airports_and_locations_with_vibes.csv"
OUTPUT_CSV = "data/iata_airports_and_locations_with_vibes_disambiguated.csv"

def append_iata_to_name(input_path: str, output_path: str):
    with open(input_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if "en-GB" not in fieldnames or "IATA" not in fieldnames:
            raise ValueError("CSV must contain 'en-GB' and 'IATA' columns")

        rows = []
        for row in reader:
            name = row["en-GB"].strip()
            iata = row["IATA"].strip()
            if name and iata:
                row["en-GB"] = f"{name} ({iata})"
            rows.append(row)

    with open(output_path, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Updated CSV written to: {output_path}")

if __name__ == "__main__":
    append_iata_to_name(INPUT_CSV, OUTPUT_CSV)
