# Config
PROLOG_COMPILER := swipl
PROLOG_FLAGS := -O
PYTHON := python3
DATA_DIR := data
SRC_DIR := src
SCRIPTS_DIR := scripts
API_CACHE := $(DATA_DIR)/api_cache.db
FILTERED_ROUTES := $(DATA_DIR)/filtered_routes.txt
GRADED := $(DATA_DIR)/graded.txt

# Default target
.PHONY: all clean cities users prepinfo filter apiinfo getlist

all: getlist

# --- 1. Preprocess data ---
cities: $(DATA_DIR)/cities.pl

$(DATA_DIR)/cities.pl: $(DATA_DIR)/iata_airports.csv
	@echo "[PY] Converting CSV to Prolog..."
	@$(PYTHON) $(SCRIPTS_DIR)/csv_to_prolog.py $< $@

users: $(DATA_DIR)/users.pl

$(DATA_DIR)/users.pl: $(DATA_DIR)/input.json
	@echo "[PY] Converting JSON to Prolog..."
	@$(PYTHON) $(SCRIPTS_DIR)/json_to_prolog.py $< $@

prepinfo: cities users
	@echo "[PL] Checked cities and users facts."

# --- 2. Filter destinations using Prolog ---
filter: prepinfo
	@echo "[PL] Filtering candidate routes..."
	@$(PROLOG_COMPILER) -g "export_routes" -t halt $(SRC_DIR)/filter_rules.pl > $(FILTERED_ROUTES)

# --- 3. API Calls + Cache to SQLite ---
apiinfo: filter
	@echo "[PY] Fetching API data into SQLite cache..."
	@$(PYTHON) $(SCRIPTS_DIR)/fetch_flights.py --input $(FILTERED_ROUTES) --output $(API_CACHE)

# --- 4. Grade + Rank the destinations ---
getlist: apiinfo
	@echo "[PY] Grading and scoring destinations..."
	@$(PYTHON) $(SCRIPTS_DIR)/score_and_rank.py --input $(API_CACHE) --output $(GRADED)

# --- Clean ---
clean:
	@rm -f $(DATA_DIR)/*.pl $(DATA_DIR)/*.txt $(GRADED) $(FILTERED_ROUTES) $(API_CACHE)
	@echo "Cleaned all generated files."
