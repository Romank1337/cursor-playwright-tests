# UI autotests learning project

Tech stack:
- Python
- Pytest
- Playwright

## 1) Install dependencies

```bash
pip install -r requirements.txt
playwright install
```

## 2) Run tests

```bash
python -m pytest
```

## Current structure

```
lern_UI_TESTS/
  conftest.py
  pytest.ini
  requirements.txt
  pages/
    login_page.py
  tests/
    ui/
      auth/
        test_login_page.py
```

## Step-by-step plan

1. Smoke test: login page opens and key controls are visible.
2. Negative tests: empty form, invalid credentials.
3. Positive login test with valid user.
4. Session checks: redirect, sign out, protected page access.
5. Stabilization: test data, retries strategy, report integration.
