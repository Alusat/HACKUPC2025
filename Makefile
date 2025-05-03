# Config
PROLOG_COMPILER := swipl
PROLOG_FLAGS := -O
PYTHON := python3
DATA_DIR := data
SRC_DIR := src
SCRIPTS_DIR := scripts
API_CACHE := $(DATA_DIR)/api_cache.db
FILTERED_ROUTES := $(DATA_DIR)/filtered_routes.txt

# Targets
.PHONY: all clean run filter grade api-cache

all: $(DATA_DIR)/graded

# --- Data Generation ---
$(DATA_DIR)/cities.pl: $(DATA_DIR)/iata_airports.csv
	@echo "[PY] Converting CSV to Prolog..."
	@$(PYTHON) $(SCRIPTS_DIR)/csv_to_prolog.py $< $@

$(DATA_DIR)/users.pl: $(DATA_DIR)/input.json
	@echo "[PY] Converting JSON to Prolog..."
	@$(PYTHON) $(SCRIPTS_DIR)/json_to_prolog.py $< $@

# --- Filtering ---
filter: $(DATA_DIR)/users.pl $(DATA_DIR)/cities.pl
	@echo "[PL] Filtering candidate routes..."
	@$(PROLOG_COMPILER) -g "export_routes" -t halt $(SRC_DIR)/filter_rules.pl > $(FILTERED_ROUTES)

# --- API Cache ---
api-cache: filter
	@echo "[PY] Fetching flight data..."
	@$(PYTHON) $(SCRIPTS_DIR)/fetch_flights.py --input $(FILTERED_ROUTES) --output $(API_CACHE)

# --- Grading ---
grade: api-cache
	@echo "[PL] Compiling grading rules..."
	@$(PROLOG_COMPILER) $(PROLOG_FLAGS) -o $(DATA_DIR)/graded -c $(SRC_DIR)/grade_rules.pl

# --- Run ---
run: grade
	@echo "[PL] Running recommendations..."
	@$(DATA_DIR)/graded

# --- Clean ---
clean:
	@rm -f $(DATA_DIR)/*.pl $(DATA_DIR)/graded $(FILTERED_ROUTES) $(API_CACHE)
	@echo "Cleaned all generated files."