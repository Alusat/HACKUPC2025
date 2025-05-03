import json
from pathlib import Path
import sys # To potentially write errors to stderr

def force_quote(s):
    """
    Encloses a string in single quotes for Prolog,
    escaping any internal single quotes by doubling them.
    Handles non-string inputs by converting them first (use with caution).
    """
    if not isinstance(s, str):
        # If we get something other than a string, convert it.
        # This might hide errors if the input JSON format is wrong.
        s = str(s)
    # Escape internal single quotes by replacing ' with ''
    escaped_s = s.replace("'", "''")
    # Enclose the result in single quotes
    return f"'{escaped_s}'"

def convert_to_prolog(json_data, output_path):
    """
    Converts traveler data from a JSON object to Prolog facts,
    grouping facts by predicate and ensuring all city/vibe names
    are single-quoted.
    """
    # Initialize lists for each type of fact
    prefs_rules = []
    cities_rules = []
    dests_rules = []
    budgets_rules = []

    # Check if the main 'travelers' key exists
    if "travelers" not in json_data or not isinstance(json_data["travelers"], list):
        print("Warning: 'travelers' key missing or not a list in JSON data.", file=sys.stderr)
        travelers_list = []
    else:
        travelers_list = json_data["travelers"]

    # Iterate through travelers ONCE, appending facts to respective lists
    for i, traveler in enumerate(travelers_list):
        # Use travelerNumber if present, otherwise use index+1 for uniqueness
        traveler_num = traveler.get('travelerNumber', i + 1)
        traveler_id = f"user{traveler_num}"

        # --- 1. User preference rule ---
        vibes = traveler.get("preferredVibes", [])
        if isinstance(vibes, list) and vibes: # Ensure it's a non-empty list
            # Create a Prolog-compatible list string, quoting EACH vibe atom using force_quote
            try:
                prolog_vibes_list = '[' + ', '.join([force_quote(v) for v in vibes]) + ']'
                prefs_rules.append(f"user_preference({traveler_id}, {prolog_vibes_list}).")
            except Exception as e:
                print(f"Warning: Skipping vibes for {traveler_id} due to error: {e}", file=sys.stderr)


        # --- 2. Origin city rule ---
        start_city = traveler.get('startingPoint')
        if start_city and isinstance(start_city, str): # Ensure it's a non-empty string
            # Use force_quote for ALL city names
            cities_rules.append(f"user_city({traveler_id}, {force_quote(start_city)}).")
        # Optional: Add a warning if startingPoint is missing?
        # else:
        #    print(f"Warning: Missing 'startingPoint' for {traveler_id}", file=sys.stderr)


        # --- 3. Preferred destination rule ---
        pref_dest = traveler.get('preferredDestination')
        if pref_dest and isinstance(pref_dest, str): # Ensure it's a non-empty string
             # Use force_quote for ALL city names
            dests_rules.append(f"user_dest({traveler_id}, {force_quote(pref_dest)}).")


        # --- 4. Budget rule (if exists) ---
        budget = traveler.get("budgetRange")
        # Check if budget exists, is a dict, and has both min and max keys with numeric values
        if (budget and isinstance(budget, dict) and
                "min" in budget and isinstance(budget["min"], (int, float)) and
                "max" in budget and isinstance(budget["max"], (int, float))):
            min_budget = budget["min"]
            max_budget = budget["max"]
            budgets_rules.append(f"user_budget({traveler_id}, {min_budget}, {max_budget}).")
        # Optional: Add a warning if budget format is wrong?
        # elif "budgetRange" in traveler: # If key exists but format is wrong
        #    print(f"Warning: Invalid 'budgetRange' format for {traveler_id}: {traveler['budgetRange']}", file=sys.stderr)


    # --- Combine the lists into the final structure with blank lines ---
    all_rules = []
    if prefs_rules:
        all_rules.extend(prefs_rules)
        all_rules.append("") # Add blank line separator
    if cities_rules:
        all_rules.extend(cities_rules)
        all_rules.append("")
    if dests_rules:
        all_rules.extend(dests_rules)
        all_rules.append("")
    if budgets_rules:
        all_rules.extend(budgets_rules)
        # No blank line needed after the last block

    # Remove trailing blank line if the last block was empty but others weren't
    while all_rules and all_rules[-1] == "":
        all_rules.pop()

    # --- Write to file ---
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f: # Specify UTF-8 encoding
            f.write("% User data generated from JSON\n")
            f.write("% Facts are grouped by predicate.\n")
            f.write("% All city and vibe names are quoted.\n\n") # Header and initial blank line
            if not all_rules:
                 f.write("% No traveler data found or processed.\n")
            else:
                f.write("\n".join(all_rules))
                f.write("\n") # Ensure trailing newline at the end of the file
        return True # Indicate success
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}", file=sys.stderr)
        return False # Indicate failure

# --- Main execution block ---
if __name__ == "__main__":
    # Define paths (adjust if needed)
    # Assumes this script is run from a directory where 'i_json' and 'data' are accessible
    # Often relative paths like these are better determined relative to the script's location:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent # Assumes script is in 'src' or similar, and 'data'/'i_json' are in parent

    # Default input/output paths - MODIFY IF YOUR STRUCTURE IS DIFFERENT
    # It's often better to pass these as command-line arguments
    default_output_pl_filename = "users.pl"

    input_json_path = "../i_json/user_info.json"
    output_pl_path = base_dir / "data" / default_output_pl_filename

    print(f"--- Prolog Fact Generator ---")
    print(f"Attempting to read JSON from: {input_json_path}")
    print(f"Attempting to write Prolog to: {output_pl_path}")

    input_data = None
    try:
        with open(input_json_path, 'r', encoding="utf-8") as f_json: # Specify UTF-8 encoding
            input_data = json.load(f_json)
        print(f"Successfully read JSON data.")

    except FileNotFoundError:
        print(f"Error: Input JSON file not found at '{input_json_path}'", file=sys.stderr)
        sys.exit(1) # Exit with error code
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{input_json_path}'. Invalid JSON format: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"An unexpected error occurred during file reading: {e}", file=sys.stderr)
         sys.exit(1)

    # Proceed only if input_data was loaded
    if input_data is not None:
        print(f"Generating Prolog facts...")
        success = convert_to_prolog(input_data, output_pl_path)

        if success:
            print(f"Successfully generated '{output_pl_path}'")
        else:
            print(f"Failed to generate Prolog file.", file=sys.stderr)
            sys.exit(1)
    else:
         print(f"Could not proceed without valid input data.", file=sys.stderr)
         sys.exit(1)