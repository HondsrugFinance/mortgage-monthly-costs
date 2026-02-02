"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health endpoints."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_version_info(self, client):
        """Test version endpoint returns version info."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "available_fiscal_years" in data


class TestCalculateEndpoint:
    """Tests for calculate endpoint."""

    def test_calculate_success(self, client):
        """Test successful calculation."""
        response = client.post(
            "/calculate/monthly-costs",
            json={
                "fiscal_year": 2026,
                "woz_value": 400000,
                "loan_parts": [
                    {
                        "id": "main",
                        "principal": 300000,
                        "interest_rate": 4.5,
                        "term_years": 30,
                        "loan_type": "annuity",
                        "box": 1,
                    }
                ],
                "partners": [{"id": "owner", "taxable_income": 60000, "age": 35}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "net_monthly_cost" in data
        assert "tax_breakdown" in data
        assert "loan_parts" in data
        assert data["fiscal_year"] == 2026
        assert len(data["loan_parts"]) == 1

    def test_calculate_with_two_partners(self, client):
        """Test calculation with two partners."""
        response = client.post(
            "/calculate/monthly-costs",
            json={
                "fiscal_year": 2026,
                "woz_value": 450000,
                "loan_parts": [
                    {
                        "id": "hypotheek",
                        "principal": 350000,
                        "interest_rate": 4.2,
                        "term_years": 30,
                        "loan_type": "annuity",
                        "box": 1,
                    }
                ],
                "partners": [
                    {"id": "partner1", "taxable_income": 90000, "age": 38},
                    {"id": "partner2", "taxable_income": 45000, "age": 36},
                ],
                "partner_distribution": {"method": "optimize"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["partner_results"] is not None
        assert len(data["partner_results"]) == 2

    def test_calculate_mixed_box1_box3(self, client):
        """Test calculation with mixed box 1 and box 3 loans."""
        response = client.post(
            "/calculate/monthly-costs",
            json={
                "fiscal_year": 2026,
                "woz_value": 500000,
                "loan_parts": [
                    {
                        "id": "box1_loan",
                        "principal": 250000,
                        "interest_rate": 4.0,
                        "term_years": 30,
                        "loan_type": "annuity",
                        "box": 1,
                    },
                    {
                        "id": "box3_loan",
                        "principal": 100000,
                        "interest_rate": 4.5,
                        "term_years": 30,
                        "loan_type": "interest_only",
                        "box": 3,
                    },
                ],
                "partners": [{"id": "owner", "taxable_income": 80000, "age": 40}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Box 3 interest should not be deductible
        assert float(data["total_interest_box3_monthly"]) > 0
        assert float(data["total_interest_box1_monthly"]) > 0

    def test_calculate_validation_error(self, client):
        """Test validation error for invalid input."""
        response = client.post(
            "/calculate/monthly-costs",
            json={
                "fiscal_year": 2026,
                "woz_value": -100,  # Invalid: negative
                "loan_parts": [],  # Invalid: empty
                "partners": [],  # Invalid: empty
            },
        )

        assert response.status_code == 422

    def test_calculate_unknown_year(self, client):
        """Test 404 for unknown fiscal year."""
        response = client.post(
            "/calculate/monthly-costs",
            json={
                "fiscal_year": 2040,  # Within valid range but no rules file
                "woz_value": 400000,
                "loan_parts": [
                    {
                        "id": "main",
                        "principal": 300000,
                        "interest_rate": 4.5,
                        "term_years": 30,
                        "loan_type": "annuity",
                        "box": 1,
                    }
                ],
                "partners": [{"id": "owner", "taxable_income": 60000, "age": 35}],
            },
        )

        assert response.status_code == 404


class TestRulesEndpoints:
    """Tests for rules endpoints."""

    def test_list_available_years(self, client):
        """Test listing available years."""
        response = client.get("/rules")
        assert response.status_code == 200
        data = response.json()
        assert "available_years" in data
        assert 2026 in data["available_years"]

    def test_get_rules_2026(self, client):
        """Test getting rules for 2026."""
        response = client.get("/rules/2026")
        assert response.status_code == 200
        data = response.json()
        assert data["fiscal_year"] == 2026
        assert "tax_brackets_box1" in data
        assert "ewf_table" in data
        assert "hillen" in data

    def test_get_rules_unknown_year(self, client):
        """Test 404 for unknown year."""
        response = client.get("/rules/2099")
        assert response.status_code == 404

    def test_validate_rules_success(self, client):
        """Test successful rules validation."""
        rules = {
            "fiscal_year": 2027,
            "tax_brackets_box1": [
                {"lower": 0, "upper": 40000, "rate": 0.37},
                {"lower": 40000, "upper": None, "rate": 0.50},
            ],
            "max_mortgage_interest_deduction_rate": 0.37,
            "ewf_table": [
                {"lower": 0, "upper": 75000, "percentage": 0},
                {"lower": 75001, "upper": None, "percentage": 0.0035},
            ],
            "hillen": {"enabled": True, "reduction_percentage": 0.70},
        }

        response = client.post("/rules/2027/validate", json=rules)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_rules_year_mismatch(self, client):
        """Test validation fails when URL year doesn't match rules."""
        rules = {
            "fiscal_year": 2027,  # Doesn't match URL
            "tax_brackets_box1": [{"lower": 0, "upper": None, "rate": 0.37}],
            "max_mortgage_interest_deduction_rate": 0.37,
            "ewf_table": [{"lower": 0, "upper": None, "percentage": 0}],
            "hillen": {"enabled": True, "reduction_percentage": 0.70},
        }

        response = client.post("/rules/2028/validate", json=rules)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("URL year" in e for e in data["errors"])
