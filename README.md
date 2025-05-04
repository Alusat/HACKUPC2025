# ✈️ Smart Travel Matcher

This project builds a semantic travel destination recommender. It processes user preferences, filters city data via logic rules, queries the Skyscanner API, and returns ranked flight results — all with a clean front-end display.

---

## 🧠 Pipeline Overview
![pipeline](https://github.com/user-attachments/assets/700a2d1b-768f-47ff-95a8-3b8342a02b6f)

```text

🗂 Project Structure

Raw Data + Preferences: The system starts with a tagged CSV of destinations and a user input JSON containing preferences like weather, vibe, and origin.

Preprocessing:

Disambiguates city names by appending IATA codes (e.g., Barcelona (BCN))

Converts input into Prolog-readable facts

Ontology Filtering:

Uses Prolog logic rules to eliminate non-matching destinations

Flight Queries:

Calls the Skyscanner API to get real-time flight prices and availability for the filtered IATA codes

Scoring:

Ranks destinations based on a mix of factors: vibe match, budget, flight time, and more

Display:

The frontend shows the top-ranked options in a user-friendly interface

📦 Setup
bash
Copiar
Editar
git clone https://github.com/your-org/travel-matcher.git
cd travel-matcher
pip install -r requirements.txt
🧪 Run Preprocessing
bash
Copiar
Editar
python preprocess/append_iata.py
python preprocess/prepare_prolog_facts.py
🧠 Run Prolog Filtering
bash
Copiar
Editar
swipl -s prolog/ontology.pl -g main
🌍 Call Flights & Rank
bash
Copiar
Editar
python api/skyscanner_query.py
python api/scoring.py
🖥 Launch Frontend
bash
Copiar
Editar
python frontend/main.py  # or `npm start` if using a JS frontend
✨ Example Output
json
Copiar
Editar
[
  {
    "destination": "Lisbon (LIS)",
    "price": 103.25,
    "vibe_match": 0.92
  },
  {
    "destination": "Nice (NCE)",
    "price": 118.40,
    "vibe_match": 0.89
  }
]
📌 Notes
City names are disambiguated using the format: City (IATA)

Prolog filtering is deterministic due to this disambiguation

Currently focused on en-GB naming; other locales can be added later

🤝 Contributing
Feel free to open issues or submit pull requests to improve the pipeline, scoring logic, or ontology expressiveness.

📄 License
MIT License. See LICENSE file for details.

vbnet
Copiar
Editar
