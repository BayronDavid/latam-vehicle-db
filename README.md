# LatAm Vehicle Database (Open Data)

A comprehensive, open-source database of vehicle makes, models, and production years specifically curated for the Latin American market.

> **Current Status:** Colombia base (Full History 1970-2027) from the Fasecolda Guide,
> enriched with the modern Chinese marques (BYD, Chery, Haval, Omoda, Jaecoo, Changan,
> GAC, Wuling, Zeekr, …) from DBpedia.
> **Roadmap:** Mexico, Argentina, Brazil; motorcycle enrichment.

## Why this repo?
Most vehicle APIs (NHTSA, etc.) are US-centric and missing popular Latin American models (e.g., Renault Kwid, Chevrolet Joy, Toyota Hilux Diesel, Mazda 2 Sedan).

This repository provides a lightweight, static JSON database perfect for:
* Ride-sharing apps
* Insurance quoters
* Classifieds / Marketplaces
* Mechanic shops

### Cars & SUVs (`vehicles_cars.json`)
```json
{
  "CHEVROLET": [
    { "model": "SAIL", "years": [2013, 2027] },
    { "model": "SPARK", "years": [2004, 2027] },
    { "model": "TRACKER", "years": [2013, 2027] }
  ],
  "RENAULT": [
    { "model": "DUSTER", "years": [2012, 2027] },
    { "model": "LOGAN", "years": [2006, 2027] }
  ]
}
```
### Motorcycles (vehicles_motos.json)
```json
{
  "YAMAHA": [
    { "model": "NMAX", "years": [2016, 2027] },
    { "model": "DT 125", "years": [1980, 2010] }
  ]
}
```

## Data sources

| Layer | Source | Covers | Notes |
| --- | --- | --- | --- |
| Base | **Fasecolda** guide (Colombia) | Mainstream brands, full 1970–present history | Authoritative for Colombia; curated. |
| Enrichment | **DBpedia** (`scripts/enrich_from_dbpedia.py`) | Modern **Chinese** marques + sub-brands (Haval, Omoda, Jaecoo, Wey, Ora, Tank, Deepal, Voyah, Zeekr…) with production years | The fast-moving gap; tracked well on DBpedia. |

**Why DBpedia and not the obvious alternatives** (tested 2026-06):
- **NHTSA vPIC** — US-centric and useless for LATAM: `Chery` → 0 models, `Renault` → only 1980s US cars (LeCar, Fuego), `BYD` → only buses/trucks.
- **Wikidata Query Service** — was rate-limited (1 req/min) during an active outage; DBpedia mirrors the same Wikipedia infobox data without the throttle.

### Regenerating the enrichment
```bash
python scripts/enrich_from_dbpedia.py   # additive: only appends new brands/models
```
The script filters each candidate to `a dbo:Automobile` (drops motorcycles/concepts) and
routes every model to its true sub-brand by name prefix. It **never** modifies or removes
existing entries, so the Fasecolda base stays intact. Motorcycles are not yet enriched
(the Fasecolda moto base is already broad); that's on the roadmap.

> Consumers (e.g. miqpo's `sync_vehicles`) read these files via jsDelivr and upsert them;
> nothing here is ever deleted downstream, so re-running enrichment only grows the catalog.
