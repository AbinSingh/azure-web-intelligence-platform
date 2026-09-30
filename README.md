# Property Underwriting Web Intelligence Agent

Production-oriented reference implementation for autonomous property-risk research using **FastAPI + LangGraph + Tavily + Firecrawl + Azure OpenAI GPT-4o**.

## What it does

1. Accepts a property address/profile and underwriting questions.
2. Generates targeted web research queries.
3. Searches the web with Tavily.
4. Deduplicates and ranks candidate sources.
5. Scrapes selected pages with Firecrawl.
6. Converts source content into explicit evidence objects.
7. Uses Azure OpenAI GPT-4o to synthesize a structured underwriting research report.
8. Returns findings, severity, confidence, evidence IDs, information gaps, and follow-up questions.

The design intentionally separates **discovery**, **retrieval**, **evidence**, and **reasoning** so the report can be audited.

## Architecture

```text
FastAPI
  |
  v
LangGraph StateGraph
  |
  +--> Query Planner
  |
  +--> Tavily Search -----------+
  |                             |
  +--> Firecrawl Scrape <-------+
  |
  +--> Evidence Builder
  |
  +--> Azure OpenAI GPT-4o
  |
  v
Structured Underwriting Report
```

## Setup

```bash
cp .env.example .env
# populate Azure OpenAI, Tavily and Firecrawl credentials
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## Example request

```bash
curl -X POST http://localhost:8000/v1/underwriting/research \
  -H 'Content-Type: application/json' \
  -d '{
    "property": {
      "address": "10 Example Road, Bengaluru, Karnataka, India",
      "property_type": "commercial",
      "occupancy": "warehouse"
    }
  }'
```

## Azure configuration

The implementation uses the OpenAI Python SDK against Azure's OpenAI-compatible `/openai/v1/` endpoint. Set `AZURE_OPENAI_DEPLOYMENT` to the deployment name of your GPT-4o model.

For production, prefer Microsoft Entra ID/keyless authentication rather than storing long-lived API keys where your Azure environment supports it.

## Enterprise hardening roadmap

- Persist LangGraph checkpoints in PostgreSQL/Redis rather than in-memory state.
- Add OpenTelemetry/LangSmith tracing and correlation IDs.
- Add source allow/deny lists and domain trust policies.
- Add robots/terms/compliance controls and rate limits.
- Add geospatial hazard APIs and authoritative government datasets alongside open-web search.
- Add document storage and immutable evidence snapshots.
- Add human-in-the-loop review before an underwriting decision is made.
- Add policy/rules engine for underwriting appetite; keep deterministic rules separate from LLM reasoning.
- Add PII/secret redaction before sending data to third-party services.
- Add evaluation datasets for factuality, citation coverage, source quality, and extraction accuracy.
- Add tenant isolation, RBAC, audit logs, quotas, and encrypted storage.

## Important underwriting boundary

This service is a **research and decision-support component**, not an autonomous underwriting decision-maker. Public web evidence can be incomplete, stale, contradictory, or incorrectly attributed. Final underwriting decisions should remain subject to your organization's rules, authoritative hazard data, inspections, policy wording, and human review.
