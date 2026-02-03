# CLAUDE.md - Project Context

## Project Overzicht

Nederlandse Hypotheek Maandlasten Calculator - een onafhankelijke FastAPI microservice voor het berekenen van bruto- en netto-maandlasten van Nederlandse hypotheken.

## Live API

- **Production URL**: https://mortgage-monthly-costs.onrender.com
- **Swagger Docs**: https://mortgage-monthly-costs.onrender.com/docs
- **Health Check**: https://mortgage-monthly-costs.onrender.com/health
- **GitHub**: https://github.com/HondsrugFinance/mortgage-monthly-costs

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

- **Render**: https://mortgage-monthly-costs.onrender.com
  - Build command: `pip install -e .`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Auto-deploy via GitHub main branch
- **Docker**: `Dockerfile` beschikbaar
- Health check: `/health`

### Deploy Updates
1. Commit & push naar GitHub main branch
2. Render detecteert automatisch en herdeployt

## Belangrijke Bestanden

| Bestand | Functie |
|---------|---------|
| `app/domain/calculator.py` | Orchestrator - combineert alle berekeningen |
| `app/domain/loan_calc.py` | Leningtype calculators |
| `app/api/schemas/input.py` | Request validatie |
| `app/rules/2026.json` | Fiscale configuratie |

## Lovable Integratie - Complete Prompt

### TypeScript Interfaces

```typescript
interface LoanPart {
  id: string;
  principal: number;
  interest_rate: number;
  term_years: number;
  loan_type: "annuity" | "linear" | "interest_only";
  box: 1 | 3;
}

interface Partner {
  id: string;
  taxable_income: number;
  age: number;
}

interface MonthlyCostsRequest {
  fiscal_year: number;
  woz_value: number;
  loan_parts: LoanPart[];
  partners: Partner[];
  partner_distribution?: {
    method: "optimize" | "fixed_percent" | "fixed_amount";
    parameter?: number;
  };
}
```

### Data Mapping Functies

```typescript
// WOZ-waarde uit Stap 4
function getWozValue(formData): number {
  return formData.stap4.wozWaarde;
}

// Partners opbouwen uit Stap 4
function buildPartners(formData): Partner[] {
  const partners: Partner[] = [];

  // Partner 1 inkomen berekenen
  const inkomen1 = formData.stap4.hoofdinkomen1
                 + formData.stap4.lijfrente1
                 + formData.stap4.partneralimentatie1
                 - formData.stap4.maandlastAlimentatie1;

  partners.push({
    id: "partner1",
    taxable_income: inkomen1 * 12,  // Naar jaarbasis
    age: formData.stap4.leeftijd1
  });

  // Partner 2 indien aanwezig
  if (formData.stap4.heeftPartner) {
    const inkomen2 = formData.stap4.hoofdinkomen2
                   + formData.stap4.lijfrente2
                   + formData.stap4.partneralimentatie2
                   - formData.stap4.maandlastAlimentatie2;
    partners.push({
      id: "partner2",
      taxable_income: inkomen2 * 12,
      age: formData.stap4.leeftijd2
    });
  }

  return partners;
}

// Leningdelen opbouwen uit Stap 5
function buildLoanParts(formData): LoanPart[] {
  return formData.stap5.leningdelen.map((deel, index) => ({
    id: `leningdeel_${index + 1}`,
    principal: deel.hoofdsom,
    interest_rate: deel.rentepercentage,
    term_years: deel.looptijdJaren,
    loan_type: mapAflosvorm(deel.aflosvorm),
    box: deel.box || 1  // Default box 1
  }));
}

// Aflosvorm mapping
function mapAflosvorm(aflosvorm: string): "annuity" | "linear" | "interest_only" {
  const mapping = {
    "Annuïtair": "annuity",
    "Lineair": "linear",
    "Aflossingsvrij": "interest_only"
  };
  return mapping[aflosvorm] || "annuity";
}
```

### Complete API Call (Stap 5 → 6)

```typescript
async function calculateMonthlyCosts(formData) {
  const response = await fetch(
    'https://mortgage-monthly-costs.onrender.com/calculate/monthly-costs',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fiscal_year: 2026,
        woz_value: getWozValue(formData),
        loan_parts: buildLoanParts(formData),
        partners: buildPartners(formData),
        partner_distribution: {
          method: "optimize"  // Automatisch optimale verdeling
        }
      })
    }
  );

  return await response.json();
}
```

### Response Mapping naar Stap 6

```typescript
// API Response gebruiken in resultaten scherm
function displayResults(apiResponse) {
  return {
    // Bruto maandlasten
    brutoMaandlasten: apiResponse.total_gross_monthly,

    // Netto maandlasten
    nettoMaandlasten: apiResponse.net_monthly_cost,

    // Netto belastingvoordeel per maand (renteaftrek − EWF bijtelling)
    nettoRenteaftrek: apiResponse.tax_breakdown.net_tax_effect_monthly,

    // Bruto renteaftrek (alleen het rentevoordeel, exclusief EWF)
    brutoRenteaftrek: apiResponse.tax_breakdown.interest_deduction_monthly,

    // EWF bijtelling
    ewfBijtellingPerMaand: apiResponse.tax_breakdown.ewf_tax_monthly,

    // Hillen voordeel (indien van toepassing)
    hillenVoordeel: apiResponse.tax_breakdown.hillen_benefit_monthly,

    // Per leningdeel breakdown
    leningdelenBreakdown: apiResponse.loan_parts.map(lp => ({
      id: lp.loan_part_id,
      rentePerMaand: lp.interest_payment,
      aflossing: lp.principal_payment,
      brutoBetaling: lp.gross_payment
    }))
  };
}
```

### Veldmapping Overzicht

**Input (Lovable → API)**

| Lovable Veld | API Veld |
|--------------|----------|
| stap4.wozWaarde | woz_value |
| stap4.hoofdinkomen1 + lijfrente1 + partneralimentatie1 - maandlastAlimentatie1 | partners[0].taxable_income (×12) |
| stap4.leeftijd1 | partners[0].age |
| stap5.leningdelen[].hoofdsom | loan_parts[].principal |
| stap5.leningdelen[].rentepercentage | loan_parts[].interest_rate |
| stap5.leningdelen[].looptijdJaren | loan_parts[].term_years |
| stap5.leningdelen[].aflosvorm | loan_parts[].loan_type (mapped) |
| stap5.leningdelen[].box | loan_parts[].box |

**Output (API → Lovable)**

| API Response | Lovable Veld |
|--------------|--------------|
| total_gross_monthly | Bruto maandlasten |
| net_monthly_cost | Netto maandlasten |
| tax_breakdown.net_tax_effect_monthly | Netto belastingvoordeel (renteaftrek − EWF) |
| tax_breakdown.interest_deduction_monthly | Bruto renteaftrek (alleen rentevoordeel) |
| tax_breakdown.ewf_tax_monthly | EWF bijtelling |
| tax_breakdown.hillen_benefit_monthly | Hillen voordeel |

### Belangrijke Notities

1. **Partner distribution**: Gebruik `method: "optimize"` om automatisch de renteaftrek toe te wijzen aan de partner met het hoogste effectieve tarief

2. **Inkomen berekening**: Het jaarsalaris voor de API is:
   `(hoofdinkomen + lijfrente + partneralimentatie - maandlastAlimentatie) × 12`

3. **Box 1 vs Box 3**:
   - Box 1 leningdelen: rente is aftrekbaar
   - Box 3 leningdelen: rente telt mee in bruto, maar GEEN aftrek

4. **Fiscaal jaar**: Gebruik altijd `fiscal_year: 2026` (of het actuele jaar)
