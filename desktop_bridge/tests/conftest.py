import pytest


@pytest.fixture(autouse=True)
def deterministic_public_catalog(monkeypatch):
    # Unit tests never use a paid provider or live Internet pricing.
    monkeypatch.setattr('desktop_bridge.pricing.fetch_catalog',lambda:{'data':[
        {'id':name,'pricing':{'prompt':'0.000001','completion':'0.000002'}} for name in (
            'anthropic/claude-haiku-4.5','openai/gpt-6-astra','openai/gpt-6.1-sol')]})
