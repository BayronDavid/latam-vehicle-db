# LatAm Vehicle Database (Open Data)

A comprehensive, open-source database of vehicle makes, models, and production years specifically curated for the Latin American market.

> **Current Status:** Colombia (Full History 1970-2027) based on Fasecolda Guide.
> **Roadmap:** Mexico, Argentina, Brazil.

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
