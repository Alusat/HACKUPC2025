import json
from pathlib import Path

def convert_to_prolog(json_data, output_path):
    prolog_rules = []
    
    for traveler in json_data["travelers"]:
        traveler_id = f"user{traveler['travelerNumber']}"
        vibes = traveler["preferredVibes"]  # Keep original names (e.g., "art_and_culture")
        
        # User preference rule
        prolog_rules.append(f"user_preference({traveler_id}, {vibes}).")
        
        # Origin/destination rules
        prolog_rules.append(f"user_city({traveler_id}, '{traveler['startingPoint']}').")
        if traveler["preferredDestination"]:
            prolog_rules.append(f"user_dest({traveler_id}, '{traveler['preferredDestination']}').")
        
        # Budget rule (if exists)
        if "budgetRange" in traveler:
            min_budget = traveler["budgetRange"]["min"]
            max_budget = traveler["budgetRange"]["max"]
            prolog_rules.append(f"user_budget({traveler_id}, {min_budget}, {max_budget}).")
    
    # Write to file
    with open(output_path, "w") as f:
        f.write("% User preferences generated from JSON\n")
        f.write("\n".join(prolog_rules))

if __name__ == "__main__":
    # Example input (replace with actual JSON loading)
    input_json = json.loads(open("input.json").read())
    output_path = Path("data/users.pl")
    convert_to_prolog(input_json, output_path)
    print(f"Generated {output_path}")