from tools.lint_branding import check, violations


def test_product_copy_has_no_retired_attribution():
    assert check() == []


def test_guard_distinguishes_owner_namespace_from_product_copy():
    assert not violations('guide.md', 'https://github.com/AI-GO-APP/local-token-buffet-bridge')
    retired = ' '.join(('AI', 'GO'))
    assert violations('guide.md', retired + ' integration')
    assert violations('console.html', retired.lower() + ' console')
    assert violations('guide.md', 'https://github.com/owner/aigo-llm-bridge/releases')
