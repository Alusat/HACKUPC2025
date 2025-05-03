'''
import csv
import ast  # For safely evaluating string as dictionary

def csv_to_prolog(input_csv, output_pl):
    with open(input_csv, 'r') as csvfile, open(output_pl, 'w') as prologfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and format the city name
            city_name = row['en-GB'].strip() if row['en-GB'] != 'null' else row['IATA']
            city_name = city_name.replace("'", "")
            
            # Handle latitude/longitude
            lat = row['latitude']
            long = row['longitude']
            
            # Process vibes - extract only keys with value "1"
            vibes = []
            if row['vibes'] != 'null':
                try:
                    # Safely convert string to dictionary
                    vibe_dict = ast.literal_eval(row['vibes'])
                    # Get all vibes with value "1"
                    vibes = [vibe for vibe, val in vibe_dict.items() 
                            if str(val).strip() == "1"]
                except (ValueError, SyntaxError):
                    print(f"Warning: Couldn't parse vibes for {city_name}")
            
            # Write Prolog facts
            prologfile.write(f"city('{city_name}').\n")
            prologfile.write(f"city_iata('{city_name}', '{row['IATA']}').\n")
            prologfile.write(f"city_lat('{city_name}', {lat}).\n")
            prologfile.write(f"city_long('{city_name}', {long}).\n")
            
            # Write vibes if any exist
            if vibes:
                vibes_str = '[' + ', '.join(vibes) + ']'
                prologfile.write(f"has_vibes('{city_name}', {vibes_str}).\n")
            
            prologfile.write("\n")

# Example usage
csv_to_prolog('../data/iata_airports_and_locations_with_vibes.csv', 'cities.pl')
'''
import csv
import ast
from collections import defaultdict

def csv_to_prolog(input_csv, output_pl):
    # Data structures to group facts by type
    facts = {
        'city': [],
        'city_iata': [],
        'city_lat': [],
        'city_long': [],
        'has_vibes': []
    }

    with open(input_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and format the city name
            city_name = row['en-GB'].strip() if row['en-GB'] != 'null' else row['IATA']
            city_name = city_name.replace("'", "")
            
            # Store basic facts
            facts['city'].append(f"city('{city_name}').")
            facts['city_iata'].append(f"city_iata('{city_name}', '{row['IATA']}').")
            facts['city_lat'].append(f"city_lat('{city_name}', {row['latitude']}).")
            facts['city_long'].append(f"city_long('{city_name}', {row['longitude']}).")
            
            # Process vibes
            if row['vibes'] != 'null':
                try:
                    vibe_dict = ast.literal_eval(row['vibes'])
                    vibes = [vibe for vibe, val in vibe_dict.items() 
                            if str(val).strip() == "1"]
                    if vibes:
                        vibes_str = '[' + ', '.join(vibes) + ']'
                        facts['has_vibes'].append(f"has_vibes('{city_name}', {vibes_str}).")
                except (ValueError, SyntaxError):
                    print(f"Warning: Couldn't parse vibes for {city_name}")

    # Write grouped facts to file
    with open(output_pl, 'w') as prologfile:
        for fact_type in ['city', 'city_iata', 'city_lat', 'city_long', 'has_vibes']:
            prologfile.write(f"% {fact_type} facts\n")
            prologfile.write("\n".join(facts[fact_type]) + "\n\n")
            
csv_to_prolog('../data/iata_airports_and_locations_with_vibes.csv', 'newCities.pl')
