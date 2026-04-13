# Test Plan

## 1. Objective

Define a practical validation strategy for NoDisBot.

## 2. Current State

- Little or no automated test coverage
- Most validation is manual
- High-value behavior exists in setup, search, add, delete, and credential handling

## 3. Test Levels

### Static Validation

- syntax compilation
- linting
- secret scanning
- Docker build validation

### Unit Tests

Target these pure or mostly pure areas first:

- tag parsing helpers
- title query parsing
- duplicate detection payload generation
- env validation behavior
- encryption/decryption helpers

### Integration Tests

Target these flows with mocked external services:

- setup conversation validation
- add URL flow
- title search flow
- tag search flow
- delete flow
- upload flow

### Manual Smoke Tests

- bot starts with valid env vars
- setup command works
- add command stores a record
- search returns expected results
- delete updates record state correctly

## 4. Priority Test Cases

### Environment and Startup

- startup fails when `TOKEN` is missing
- startup fails when `SECRET_KEY` is missing
- SQLite path is created when `DATA_DIR` is set

### Setup

- invalid Notion API key is rejected
- invalid Notion database ID is rejected
- valid setup stores encrypted credentials

### Add

- invalid URL is rejected
- duplicate URL is rejected
- valid URL with auto-title is added
- valid URL with manual title fallback is added

### Search

- title search returns sorted results
- tag search returns only matching entries
- empty search input returns a helpful error

### Delete

- delete by title shows candidate list
- invalid selection is rejected
- valid selection patches target record

### Upload

- missing attachment is rejected
- attachment with title is stored

## 5. Suggested Tooling

- `pytest`
- `ruff`
- `unittest.mock` or `pytest-mock`
- mocked Notion HTTP responses

## 6. CI Expectations

Minimum CI checks:

- dependency install
- lint fatal errors
- compileall
- run tests if present
- Docker build
- Trivy scan

## 7. Exit Criteria

Minimum acceptable confidence for production hardening:

- syntax validation passes
- Docker build passes
- startup validation tested
- critical helper functions have unit coverage
- core add/search/delete flows have mocked integration tests

