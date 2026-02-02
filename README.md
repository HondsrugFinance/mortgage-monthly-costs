# Nederlandse Hypotheek Maandlasten Calculator

Een onafhankelijke FastAPI microservice voor het berekenen van bruto- en netto-maandlasten van Nederlandse hypotheken.

## Features

- **Bruto maandlasten** per leningdeel (annuïtair, lineair, aflossingsvrij)
- **Netto maandlasten** op basis van NL fiscale regels:
  - Eigenwoningforfait (EWF) op basis van WOZ-waarde
  - Renteaftrekbeperking (max aftrekpercentage per jaar)
  - Wet Hillen (met afbouwregeling)
  - Partner verdeling (fixed percent, fixed amount, optimize)
- **Config-driven fiscale regels** per jaar (JSON)
- Box 1 vs Box 3 onderscheid (alleen box 1 rente is aftrekbaar)

## Snel starten

### Lokaal draaien

```bash
# Clone de repository
cd "Netto maandlasten berekenen"

# Maak een virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Installeer dependencies
pip install -e ".[dev]"

# Start de server
uvicorn app.main:app --reload
```

De API is nu beschikbaar op http://localhost:8000

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Tests draaien

```bash
pytest
```

## API Endpoints

| Method | Endpoint | Beschrijving |
|--------|----------|--------------|
| POST | `/calculate/monthly-costs` | Hoofdberekening |
| GET | `/rules` | Lijst beschikbare jaren |
| GET | `/rules/{year}` | Ophalen fiscale regels |
| POST | `/rules/upload` | Upload nieuwe regels |
| POST | `/rules/{year}/validate` | Valideer regels |
| GET | `/health` | Health check |
| GET | `/version` | Versie info |

## Voorbeeld Request

```bash
curl -X POST http://localhost:8000/calculate/monthly-costs \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year": 2026,
    "woz_value": 400000,
    "loan_parts": [{
      "id": "main",
      "principal": 300000,
      "interest_rate": 4.5,
      "term_years": 30,
      "loan_type": "annuity",
      "box": 1
    }],
    "partners": [{
      "id": "owner",
      "taxable_income": 60000,
      "age": 35
    }]
  }'
```

## Voorbeeld Response

```json
{
  "fiscal_year": 2026,
  "month_number": 1,
  "woz_value": 400000,
  "loan_parts": [{
    "loan_part_id": "main",
    "loan_type": "annuity",
    "box": 1,
    "principal": 300000,
    "remaining_principal": 299604.94,
    "interest_payment": 1125.00,
    "principal_payment": 395.06,
    "gross_payment": 1520.06
  }],
  "total_gross_monthly": 1520.06,
  "total_interest_monthly": 1125.00,
  "total_interest_box1_monthly": 1125.00,
  "total_interest_box3_monthly": 0,
  "tax_breakdown": {
    "ewf_annual": 1400.00,
    "ewf_monthly": 116.67,
    "total_interest_box1_annual": 13500.00,
    "total_interest_box1_monthly": 1125.00,
    "marginal_rate": 0.3756,
    "effective_deduction_rate": 0.3756,
    "interest_deduction_annual": 5070.60,
    "interest_deduction_monthly": 422.55,
    "hillen_applicable": false,
    "hillen_deduction_annual": 0,
    "hillen_benefit_monthly": 0,
    "net_ewf_addition_annual": 1400.00,
    "ewf_tax_monthly": 43.84,
    "total_tax_benefit_monthly": 422.55,
    "total_tax_cost_monthly": 43.84,
    "net_tax_effect_monthly": 378.71
  },
  "net_monthly_cost": 1141.35,
  "disclaimer": "Indicatief - geen aangifteadvies..."
}
```

## Twee Partners met Verdeling

```bash
curl -X POST http://localhost:8000/calculate/monthly-costs \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year": 2026,
    "woz_value": 450000,
    "loan_parts": [{
      "id": "hypotheek",
      "principal": 350000,
      "interest_rate": 4.2,
      "term_years": 30,
      "loan_type": "annuity",
      "box": 1
    }],
    "partners": [
      {"id": "partner1", "taxable_income": 90000, "age": 38},
      {"id": "partner2", "taxable_income": 45000, "age": 36}
    ],
    "partner_distribution": {
      "method": "optimize"
    }
  }'
```

### Verdeling Methodes

- `fixed_percent`: Verdeel renteaftrek op percentage (parameter: 0-100)
- `fixed_amount`: Verdeel op vast bedrag (parameter: bedrag voor partner 1)
- `optimize`: Wijs alles toe aan partner met hoogste effectieve tarief

## Jaarlijkse Fiscale Update

1. **Kopieer bestaand bestand**
   ```bash
   cp app/rules/2026.json app/rules/2027.json
   ```

2. **Update waarden** in `2027.json`:
   - `fiscal_year`
   - `tax_brackets_box1` (schijfgrenzen en tarieven)
   - `max_mortgage_interest_deduction_rate`
   - `ewf_table` (grenzen en percentages)
   - `hillen.reduction_percentage`

3. **Valideer de regels**
   ```bash
   curl -X POST http://localhost:8000/rules/2027/validate \
     -H "Content-Type: application/json" \
     -d @app/rules/2027.json
   ```

4. **Run tests**
   ```bash
   pytest
   ```

5. **Deploy** (geen code wijzigingen nodig)

## Fiscale Regels Structuur

```json
{
  "fiscal_year": 2026,
  "tax_brackets_box1": [
    {"lower": 0, "upper": 38883, "rate": 0.3575},
    {"lower": 38883, "upper": 78426, "rate": 0.3756},
    {"lower": 78426, "upper": null, "rate": 0.495}
  ],
  "max_mortgage_interest_deduction_rate": 0.3756,
  "ewf_table": [
    {"lower": 0, "upper": 75000, "percentage": 0},
    {"lower": 75001, "upper": 1350000, "percentage": 0.0035},
    {"lower": 1350001, "upper": null,
     "fixed_amount": 4725, "excess_percentage": 0.0235, "threshold": 1350000}
  ],
  "hillen": {"enabled": true, "reduction_percentage": 0.71867}
}
```

## Deploy naar Render

1. Push naar GitHub
2. Maak een nieuw Web Service aan op Render
3. Verbind met je GitHub repository
4. Render detecteert automatisch `render.yaml`
5. Deploy

Of gebruik de Blueprint:
```bash
render blueprint launch
```

## Docker

```bash
# Build
docker build -t mortgage-calculator .

# Run
docker run -p 8000:8000 mortgage-calculator
```

## Projectstructuur

```
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   └── schemas/         # Pydantic models
│   ├── domain/              # Business logic
│   │   ├── calculator.py    # Main orchestrator
│   │   ├── loan_calc.py     # Loan calculations
│   │   ├── ewf.py           # Eigenwoningforfait
│   │   ├── hillen.py        # Wet Hillen
│   │   ├── tax_calc.py      # Tax brackets
│   │   └── partner.py       # Partner distribution
│   ├── rules/               # Fiscal rules (JSON)
│   └── exceptions/          # Error handling
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # API tests
├── pyproject.toml
├── Dockerfile
└── render.yaml
```

## Formules

### Annuïteit
```
r = jaarrente / 12
n = looptijd_jaren * 12
annuiteit = P × (r × (1+r)^n) / ((1+r)^n - 1)
```

### Netto maandlasten
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

## Disclaimer

Deze calculator is indicatief en geen aangifteadvies. Wijzigingen in wetgeving, inkomen of rente kunnen de uitkomst beïnvloeden. Raadpleeg een financieel adviseur voor persoonlijk advies.

## Licentie

MIT
