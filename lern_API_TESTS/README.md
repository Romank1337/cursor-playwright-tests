# REST API autotests learning project

## Setup

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Create local env file:
   - copy `.env.example` to `.env`
3. Run tests:
   - `python -m pytest -q`

## Current structure

- `conftest.py` - shared fixtures and API session
- `tests/api/test_monitoring_value_sorted_list.py` - regression tests for monitoring values API
- `.env.example` - required environment variables template
