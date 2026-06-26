#!/usr/bin/env python3
"""Enrich vehicles_cars.json with Chinese marques from DBpedia (additive).

Run:  python scripts/enrich_from_dbpedia.py

Design notes / why DBpedia:
- The base catalog is Fasecolda-derived and already authoritative for mainstream
  brands in Colombia. Pulling those from DBpedia only adds global noise and
  sub-brand bleed, so we deliberately enrich ONLY the fast-moving Chinese marques
  — the real coverage gap for LATAM.
- DBpedia (not Wikidata): the Wikidata Query Service was rate-limited during an
  outage. NHTSA vPIC is US-centric and useless here (Chery -> 0 models,
  Renault -> only 1980s US cars), so it was rejected after testing.
- Each model is filtered to `a dbo:Automobile` (drops motorcycles/concepts) and
  routed to its true sub-brand by name prefix (e.g. "Great Wall Haval H6" ->
  HAVAL / "H6", "Chery Omoda 5" -> OMODA / "5").

This script is ADDITIVE: existing entries are never modified or removed; only new
brands/models are appended. Re-running is safe (idempotent on the data).
"""
import urllib.request, urllib.parse, json, re, sys, time, datetime, os

sys.stdout.reconfigure(encoding="utf-8")
UA = "miqpo-vehicle-db/1.0 (https://github.com/BayronDavid/latam-vehicle-db)"
ENDPOINT = "https://dbpedia.org/sparql"
CUR = datetime.date.today().year
OPEN_MAX = CUR + 1
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS = os.path.join(HERE, "vehicles_cars.json")

# parent DBpedia resource(s) -> ordered prefix rules (most specific first).
PARENTS = [
    (["BYD_Auto"], [("BYD", "BYD")]),
    (["Chery"], [("Chery Omoda", "OMODA"), ("Omoda", "OMODA"),
                 ("Chery Jaecoo", "JAECOO"), ("Jaecoo", "JAECOO"),
                 ("Chery Exeed", "EXEED"), ("Exeed", "EXEED"),
                 ("Chery iCar", "ICAR"), ("iCar", "ICAR"), ("Chery", "CHERY")]),
    (["JAC_Group", "JAC_Motors"], [("JAC", "JAC")]),
    (["Changan_Automobile", "Changan"], [("Changan Deepal", "DEEPAL"), ("Deepal", "DEEPAL"),
                                          ("Changan Avatr", "AVATR"), ("Avatr", "AVATR"),
                                          ("Changan", "CHANGAN"), ("Chana", "CHANGAN")]),
    (["Great_Wall_Motor"], [("Great Wall Haval", "HAVAL"), ("Haval", "HAVAL"),
                            ("Great Wall Wey", "WEY"), ("Wey", "WEY"),
                            ("Great Wall Ora", "ORA"), ("Ora", "ORA"),
                            ("Great Wall Tank", "TANK"), ("Tank", "TANK"),
                            ("Great Wall", "GREAT WALL"), ("GWM", "GREAT WALL")]),
    (["Geely_Auto", "Geely"], [("Geely", "GEELY")]),
    (["Dongfeng_Motor_Corporation", "Dongfeng_Motor"], [("Dongfeng Voyah", "VOYAH"), ("Voyah", "VOYAH"),
                                                         ("Dongfeng", "DONGFENG"), ("DFSK", "DFSK")]),
    (["Foton_Motor"], [("Foton", "FOTON")]),
    (["Jetour"], [("Jetour", "JETOUR")]),
    (["BAIC_Group", "BAIC_Motor"], [("BAIC", "BAIC")]),
    (["GAC_Group", "GAC_Motor"], [("GAC Aion", "AION"), ("Aion", "AION"),
                                  ("Trumpchi", "GAC"), ("GAC", "GAC")]),
    (["SAIC-GM-Wuling", "Wuling_Motors"], [("Wuling", "WULING")]),
    (["MG_Motor", "MG_Cars"], [("MG", "MG")]),
    (["Zeekr"], [("Zeekr", "ZEEKR")]),
]

YEAR_RE = re.compile(r"(19[5-9]\d|20[0-4]\d)")


def sparql(q):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "application/sparql-results+json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    return json.loads(urllib.request.urlopen(req, timeout=90).read())["results"]["bindings"]


def fetch(resources):
    values = " ".join("dbr:" + r for r in resources)
    q = f"""SELECT DISTINCT ?n ?prod ?ps ?pe WHERE {{
      VALUES ?mfr {{ {values} }}
      ?m (dbo:manufacturer|dbp:manufacturer) ?mfr ; a dbo:Automobile ; rdfs:label ?n .
      FILTER(lang(?n)="en")
      OPTIONAL {{ ?m dbp:production ?prod }} OPTIONAL {{ ?m dbo:productionStartYear ?ps }}
      OPTIONAL {{ ?m dbo:productionEndYear ?pe }} }}"""
    return sparql(q)


def route(name, rules):
    n = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
    for prefix, brand in rules:
        if n.lower().startswith(prefix.lower()):
            return brand, re.sub(r"\s+", " ", n[len(prefix):].strip(" -–")).upper()
    return rules[-1][1], re.sub(r"\s+", " ", n).upper()


def parse_years(hints):
    years, open_ended = [], False
    for h in hints:
        s = str(h)
        if re.search(r"present|current|presente", s, re.I):
            open_ended = True
        years += [int(y) for y in YEAR_RE.findall(s)]
    if not years:
        return None
    lo = min(years)
    hi = OPEN_MAX if open_ended else max(years)
    if not open_ended and len(set(years)) == 1 and years[0] >= CUR - 4:
        hi = OPEN_MAX
    return [lo, min(max(hi, lo), OPEN_MAX)]


def junk(model):
    if not model or len(model) > 30:
        return True
    low = model.lower()
    return any(w in low for w in ("list of", "concept", "platform", "lineup",
              "architecture", "segment", "modular")) or not re.search(r"[A-Z0-9]", model)


def main():
    catalog = json.load(open(CARS, encoding="utf-8"))
    index = {b: {m["model"].strip().upper() for m in ms} for b, ms in catalog.items()}
    pending = {}  # brand -> list of new {model, years}
    added = 0
    for resources, rules in PARENTS:
        try:
            rows = fetch(resources)
        except Exception as e:
            print(f"  ! {resources[0]}: {e}"); time.sleep(2); continue
        agg = {}
        for b in rows:
            nm = b.get("n", {}).get("value")
            if not nm:
                continue
            brand, model = route(nm, rules)
            if junk(model):
                continue
            hints = agg.setdefault((brand, model), [])
            for k in ("prod", "ps", "pe"):
                if k in b:
                    hints.append(b[k]["value"])
        for (brand, model), hints in sorted(agg.items()):
            if model in index.get(brand, set()):
                continue
            pending.setdefault(brand, []).append({"model": model, "years": parse_years(hints) or [2005, OPEN_MAX]})
            index.setdefault(brand, set()).add(model)
            added += 1
        print(f"  {resources[0]:26} rows {len(rows):3}")
        time.sleep(1)

    # additive write: keep original order, append new models per brand, new brands last
    out = {}
    for brand, models in catalog.items():
        extra = sorted(pending.get(brand, []), key=lambda m: m["model"])
        out[brand] = models + extra
    for brand in sorted(b for b in pending if b not in catalog):
        out[brand] = sorted(pending[brand], key=lambda m: m["model"])
    with open(CARS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"\nAppended {added} new models. brands {len(catalog)}->{len(out)}, "
          f"models {sum(len(v) for v in catalog.values())}->{sum(len(v) for v in out.values())}")


if __name__ == "__main__":
    main()
