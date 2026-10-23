import pytest
from desktop_bridge.providers import model_snapshot as REAL_MODEL_SNAPSHOT
from desktop_bridge.providers import auth_generation as REAL_AUTH_GENERATION


@pytest.fixture(autouse=True)
def deterministic_public_catalog(monkeypatch):
    # Unit tests never use a paid provider or live Internet pricing.
    monkeypatch.setattr('desktop_bridge.pricing.fetch_catalog',lambda:{'data':[
        {'id':name,'pricing':{'prompt':'0.000001','completion':'0.000002'}} for name in (
            'anthropic/claude-haiku-4.5','openai/gpt-6-astra','openai/gpt-6.1-sol')]})


@pytest.fixture(autouse=True)
def no_real_cli_discovery(monkeypatch):
    monkeypatch.setattr('desktop_bridge.model_catalog.providers.model_snapshot',
        lambda p,s: {'ready': True, 'models': ['gpt-6-astra','gpt-6.1-sol'] if p=='codex' else None,
                     'source': 'cli_catalog' if p=='codex' else 'registration'})
    monkeypatch.setattr('desktop_bridge.model_catalog.providers.auth_generation', lambda p,s: 'test-account-'+p)
