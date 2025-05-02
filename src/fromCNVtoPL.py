import csv

def csv_to_prolog(input_csv, output_pl):
    with open(input_csv, 'r') as csvfile, open(output_pl, 'w') as prologfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and format the city name (using IATA code as fallback)
            city_name = row['en-GB'].strip() if row['en-GB'] != 'null' else row['IATA']
            city_name = city_name.replace("'", "")  # Remove apostrophes that might break Prolog syntax
            
            # Handle latitude/longitude
            lat = row['latitude']
            long = row['longitude']
            
            # Handle vibes - convert "null" to empty list, otherwise split
            vibes = [] if row['vibes'] == 'null' else row['vibes'].split(',')
            
            # Write Prolog facts
            prologfile.write(f"city('{city_name}').\n")
            prologfile.write(f"city_iata('{city_name}', '{row['IATA']}').\n")
            prologfile.write(f"city_lat('{city_name}', {lat}).\n")
            prologfile.write(f"city_long('{city_name}', {long}).\n")
            
            # Write vibes only if they exist
            if vibes:
                # Convert vibes to Prolog list format: [vibe1, vibe2]
                vibes_str = '[' + ', '.join(vibes) + ']'
                prologfile.write(f"has_vibes('{city_name}', {vibes_str}).\n")
            
            prologfile.write("\n")  # Add blank line between cities

# Usage
csv_to_prolog('../data/iata_airports_and_locations_with_vibes.csv', 'cities.pl')