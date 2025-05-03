# Makefile for creating the Prolog city recommender executable

# --- Variables ---

# The SWI-Prolog interpreter command
PROLOG = swipl

# The main Prolog script containing the program logic
MAIN_SCRIPT = filter_rules.pl

# The Prolog data files (facts/beliefs)
DATA_CITIES = ../data/cities.pl
DATA_USERS = ../data/users.pl

# The name of the output executable file
EXECUTABLE = recommend

# Flags for creating a standalone executable using SWI-Prolog
# --goal=main : Specifies the entry point predicate (main/0). Change if yours is different.
# --stand_alone=true : Creates an executable that bundles the runtime.
# -o $(EXECUTABLE) : Specifies the output file name.
# -c ... : Specifies the source/data files to compile/consult into the executable.
PROLOG_FLAGS = --goal=main --stand_alone=true

# --- Targets ---

# Default target: build the executable.
# Typing 'make' or 'make all' will run this.
all: $(EXECUTABLE)

# Rule to build the executable file.
# This target depends on the main script and the data files. If any of them
# change, running 'make' will rebuild the executable.
$(EXECUTABLE): $(MAIN_SCRIPT) $(DATA_CITIES) $(DATA_USERS)
	@echo "Building Prolog executable '$(EXECUTABLE)'..."
	$(PROLOG) $(PROLOG_FLAGS) -o $(EXECUTABLE) -c $(MAIN_SCRIPT) $(DATA_CITIES) $(DATA_USERS)
	@echo "'$(EXECUTABLE)' created successfully."
	@echo "You can now run it using: ./$(EXECUTABLE)"

# Target to clean up generated files.
# Typing 'make clean' will run this.
clean:
	@echo "Cleaning up..."
	rm -f $(EXECUTABLE)
	@echo "Removed '$(EXECUTABLE)'."

# Declare phony targets. These are targets that don't represent actual files.
# This prevents 'make' from getting confused if a file named 'all' or 'clean' exists.
.PHONY: all clean