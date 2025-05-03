import os
import json
import requests
import csv
from datetime import datetime
from time import sleep
from typing import Dict, Optional, List

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY        = os.getenv("API_KEY")
HEADERS        = {"x-api-key": API_KEY, "Content-Type": "application/json"}
INDICATIVE_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/indicative/search"

INPUT_JSON   = "data/ranked_cities_top100.json"
USER_JSON    = "data/user_info.json"
OUTPUT_JSON  = "data/final_scored.json"
AIRPORTS_CSV = "data/iata_airports_and_locations_with_vibes.csv"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_airport_mapping(csv_path: str) -> Dict[str, str]:
    """
    Build a map of exact CSV 'en-GB' airport/city names → IATA codes.
    We assume the names in user_info.json match these exactly.
    """
    mapping: Dict[str, str] = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            name = row.get('en-GB', '').strip()
            code = row.get('IATA', '').strip().upper()
            if name == "Barcelona":
                print(row)
            if name and code:
                mapping[name] = code
    return mapping


def extract_quotes(resp: Dict) -> Dict:
    return (resp or {}).get("content", {}).get("results", {}).get("quotes", {}) or {}

def get_indicative(origin: str, dest: str,
                   dep_date: Optional[datetime.date] = None,
                   ret_date: Optional[datetime.date] = None) -> Dict:
    legs = [{
        "originPlace": {"queryPlace": {"iata": origin}},
        "destinationPlace": {"queryPlace": {"iata": dest}}
    }]
    if dep_date and ret_date:
        legs[0]["fixedDate"] = {"year": dep_date.year, "month": dep_date.month, "day": dep_date.day}
        legs.append({
            "originPlace": {"queryPlace": {"iata": dest}},
            "destinationPlace": {"queryPlace": {"iata": origin}},
            "fixedDate": {"year": ret_date.year, "month": ret_date.month, "day": ret_date.day}
        })
    else:
        legs[0]["anytime"] = True

    payload = {"query": {
        "market":   "ES",
        "locale":   "en-GB",
        "currency": "EUR",
        "queryLegs": legs
    }}
    r = requests.post(INDICATIVE_URL, headers=HEADERS, json=payload, timeout=10)
    if r.status_code != 200:
        print(f"Error {r.status_code} for {origin}->{dest}: {r.text}")
        return {}
    return r.json()

def pick_cheapest(quotes: Dict) -> (Optional[Dict], Optional[float]):
    best, best_price = None, float('inf')
    for q in quotes.values():
        amt = q.get("minPrice", {}).get("amount")
        try:
            p = float(amt)
            if p > 10000: p /= 1000.0
            if p < best_price:
                best_price, best = p, q
        except:
            continue
    return best, best_price if best is not None else (None, None)

def normalize_list(vals: List[float]) -> List[float]:
    if not vals:
        return []
    mn, mx = min(vals), max(vals)
    if mn == mx:
        return [1.0] * len(vals)
    return [(v - mn) / (mx - mn) for v in vals]

# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    # 1) Load inputs
    destinations = json.load(open(INPUT_JSON, 'r', encoding='utf-8'))
    user         = json.load(open(USER_JSON,    'r', encoding='utf-8'))
    dep = datetime.fromisoformat(user["dateRange"]["startDate"]).date()
    ret = datetime.fromisoformat(user["dateRange"]["endDate"]).date()
    travelers = user["travelers"]

    # 2) Build exact-name → IATA map
    city_to_iata = load_airport_mapping(AIRPORTS_CSV)
    print(city_to_iata["Barcelona"])

    # 3) Derive each traveler's origin IATA (exact match)
    for t in travelers:
        sp = t.get("startingPoint", "")
        iata = city_to_iata.get(sp)
        if not iata:
            print(f"⚠️  No IATA for '{sp}', defaulting to MAD")
            iata = "MAD"
        t["origin_iata"] = iata

    # 4) Fetch flight prices for each destination & each traveler
    enriched = []
    for dest in destinations:
        dest_iata = dest["iata"]
        traveler_prices = []
        warnings = []

        for t in travelers:
            org = t["origin_iata"]
            # first try specific dates
            data = get_indicative(org, dest_iata, dep, ret)
            quotes = extract_quotes(data)
            used_any = False

            if not quotes:
                # fallback anytime
                data = get_indicative(org, dest_iata)
                quotes = extract_quotes(data)
                used_any = True

            q, price = pick_cheapest(quotes)
            if not q:
                print(f"  ⚠️  No quote for traveler {t['travelerNumber']} on {org}->{dest_iata}")
                traveler_prices = []
                break

            if used_any:
                price *= 2
                warnings.append(f"Traveler {t['travelerNumber']} used anytime (x2)")

            traveler_prices.append(price)
            sleep(0.2)

        # require every traveler to have a price
        if len(traveler_prices) != len(travelers):
            continue

        # apply individual budgets
        ok = True
        for t, p in zip(travelers, traveler_prices):
            if p > float(t["budgetRange"]["max"]):
                ok = False
                break
        if not ok:
            continue

        # record
        dest["traveler_prices"] = [round(p,2) for p in traveler_prices]
        if warnings:
            dest["warnings"] = warnings
        avg_price = sum(traveler_prices) / len(traveler_prices)
        dest["price_eur"] = round(avg_price, 2)
        enriched.append(dest)

    # 5) Composite scoring: combine Prolog 'score' and price
    pre_scores  = [d["score"]     for d in enriched]
    price_vals  = [d["price_eur"] for d in enriched]
    norm_pre    = normalize_list(pre_scores)
    norm_price  = normalize_list(price_vals)

    for i, d in enumerate(enriched):
        # 50% Prolog score, 50% inverted price
        c = 0.5 * norm_pre[i] + 0.5 * (1 - norm_price[i])
        # small penalty if any traveler used 'anytime'
        if d.get("warnings"):
            c *= 0.9
        d["composite_score"] = round(c, 3)

    # 6) Final rank & save
    enriched.sort(key=lambda x: x["composite_score"], reverse=True)
    for idx, d in enumerate(enriched, 1):
        d["final_rank"] = idx

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results written to {OUTPUT_JSON} ({len(enriched)} destinations)")

if __name__ == "__main__":
    main()
