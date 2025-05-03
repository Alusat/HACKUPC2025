import csv
from collections import OrderedDict

def extract_unique_en_gb_ordered(input_file, output_file):
    """
    Extracts unique 'en-GB' entries from input CSV preserving original order.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output CSV file
    """
    unique_en_gb = OrderedDict()  # Maintains insertion order
    
    try:
        # Read the input CSV file
        with open(input_file, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            
            # Get header to find 'en-GB' column index if needed
            headers = next(reader)
            
            # Determine column index - either by name or position
            if 'en-GB' in headers:
                col_index = headers.index('en-GB')
            else:
                # Assume it's the 3rd field (index 2) if 'en-GB' not in headers
                col_index = 2
                print("Note: 'en-GB' not found in headers, using 3rd column (index 2)")
            
            # Collect unique entries while preserving order
            for row in reader:
                if len(row) > col_index:
                    en_gb_value = row[col_index].strip()
                    if en_gb_value:  # Only add non-empty values
                        unique_en_gb[en_gb_value] = None  # Value doesn't matter, we just want ordered keys
    
        # Write unique entries to output CSV in original order
        with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile)
            
            # Write header
            writer.writerow(['en-GB'])
            
            # Write each unique value in order of first appearance
            for value in unique_en_gb.keys():
                writer.writerow([value])
                
        print(f"Success! Found {len(unique_en_gb)} unique en-GB entries. Output written to {output_file}")
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    input_csv = "iata_airports_and_locations_with_vibes.csv" 
    output_csv = "locations.csv"  
    
    extract_unique_en_gb_ordered(input_csv, output_csv)