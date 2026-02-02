# CLAUDE.md - Project Context

## Project Overzicht

Nederlandse Hypotheek Maandlasten Calculator - een onafhankelijke FastAPI microservice voor het berekenen van bruto- en netto-maandlasten van Nederlandse hypotheken.

## Technische Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **Pydantic v2** - Data validatie
- **Uvicorn** - ASGI server
- **Pytest** - Testing

## Architectuur

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic Settings
├── api/
│   ├── routes/          # API endpoints (calculate, rules, health)
│   ├── schemas/         # Pydantic input/output models
│   └── dependencies.py  # FastAPI dependencies
├── domain/              # Pure Python business logic
│   ├── calculator.py    # Main orchestrator
│   ├── loan_calc.py     # Annuity/Linear/InterestOnly calculators
│   ├── ewf.py           # Eigenwoningforfait berekening
│   ├── hillen.py        # Wet Hillen berekening
│   ├── tax_calc.py      # Belastingschijven, marginaal tarief
│   └── partner.py       # Partner verdeling (fixed_percent/amount/optimize)
├── rules/               # Fiscale configuraties per jaar (JSON)
│   ├── loader.py        # JSON loader met caching
│   ├── validator.py     # Rules validatie
│   ├── 2025.json
│   └── 2026.json
└── exceptions/          # Custom exceptions + handlers
```

## Belangrijke Commando's

```bash
# Installeren
pip install -e ".[dev]"

# Server starten
uvicorn app.main:app --reload

# Tests draaien
pytest

# Alleen unit tests
pytest tests/unit/

# Met coverage
pytest --cov=app
```

## API Endpoints

| Method | Endpoint | Functie |
|--------|----------|---------|
| POST | `/calculate/monthly-costs` | Hoofdberekening |
| GET | `/rules` | Lijst beschikbare jaren |
| GET | `/rules/{year}` | Ophalen fiscale regels |
| POST | `/rules/upload` | Upload nieuwe regels |
| POST | `/rules/{year}/validate` | Valideer regels |
| GET | `/health` | Health check |
| GET | `/version` | Versie info |

## Kernconcepten

### Leningtypen
- **annuity** - Vaste maandlast (annuïteit)
- **linear** - Vaste aflossing, dalende rente
- **interest_only** - Alleen rente, geen aflossing

### Fiscale Box
- **Box 1** - Eigen woning, rente is aftrekbaar
- **Box 3** - Belegging, rente telt mee in bruto maar geen aftrek

### Partner Verdeling
- `fixed_percent` - Verdeel renteaftrek op percentage (0-100)
- `fixed_amount` - Verdeel op vast bedrag
- `optimize` - Wijs toe aan partner met hoogste effectieve tarief

## Fiscale Regels (Config-Driven)

Regels worden geladen uit `app/rules/{year}.json`. Structuur:

```json
{
  "fiscal_year": 2026,
  "tax_brackets_box1": [...],
  "max_mortgage_interest_deduction_rate": 0.3756,
  "ewf_table": [...],
  "hillen": {"enabled": true, "reduction_percentage": 0.71867}
}
```

### Jaarlijkse Update
1. Kopieer `app/rules/2026.json` naar `app/rules/2027.json`
2. Update tarieven
3. Valideer via `/rules/2027/validate`
4. Run tests
5. Deploy (geen code changes)

## Formules

### Netto Maandlasten
```
netto = bruto
        - (rente_box1 × effectief_tarief) / 12    # renteaftrek
        + (ewf - hillen_aftrek) × tarief / 12      # EWF bijtelling
```

### Wet Hillen
```
als rente_box1 < ewf:
    hillen_aftrek = (ewf - rente_box1) × hillen_percentage
```

## Code Conventies

- **Decimal** voor alle monetaire berekeningen (geen float)
- **Frozen Pydantic models** voor immutability
- **Pure functions** in domain layer (geen side effects)
- **Type hints** overal
- Afronding: `ROUND_HALF_UP` naar 2 decimalen

## Testing

- Unit tests in `tests/unit/` - test individuele modules
- Integration tests in `tests/integration/` - test API endpoints
- Fixtures in `tests/conftest.py`

## Deployment

- **Render**: `render.yaml` blueprint
- **Docker**: `Dockerfile` met multi-stage build
- Health check: `/health`

## Belangrijke Bestanden

| Bestand | Functie |
|---------|---------|
| `app/domain/calculator.py` | Orchestrator - combineert alle berekeningen |
| `app/domain/loan_calc.py` | Leningtype calculators |
| `app/api/schemas/input.py` | Request validatie |
| `app/rules/2026.json` | Fiscale configuratie |
