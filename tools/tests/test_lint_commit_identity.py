"""Identity metadata follows the existing author-email exception, not a content bypass."""
import importlib.util
import hashlib
from pathlib import Path

spec = importlib.util.spec_from_file_location("lint_terms", Path(__file__).resolve().parents[1] / "lint_terms.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)
patterns = lint.compile_terms(["blockedidentityqzx"])

def hits(body):
    return lint.scan_text("commit", lint.commit_message_text(body), patterns)

def test_final_coauthor_email_matches_author_email_policy():
    body = "Summary.\n\nCo-authored-by: Contributor <blockedidentityqzx@users.noreply.github.com>\n"
    assert not hits(body)
    assert lint.commit_message_text(body).count("\n") == body.count("\n")

def test_coauthor_display_name_is_still_scanned():
    assert hits("Summary.\n\nCo-authored-by: blockedidentityqzx <safe@example.com>\n")

def test_ordinary_body_email_is_still_scanned():
    assert hits("Contact blockedidentityqzx@example.com for details.\n")

def test_nonfinal_coauthor_text_is_not_exempt():
    assert hits("Co-authored-by: Contributor <blockedidentityqzx@example.com>\n\nActual body continues.\n")

def test_malformed_coauthor_is_not_exempt():
    assert hits("Summary.\n\nCo-authored-by: blockedidentityqzx@example.com\n")

def test_body_content_remains_scanned_with_valid_trailer():
    assert hits("Mention blockedidentityqzx.\n\nCo-authored-by: Contributor <safe@example.com>\n")


def test_existing_author_baseline_is_bound_to_exact_commit_and_identity(monkeypatch):
    identity = 'blockedidentityqzx'
    monkeypatch.setattr(lint,'PUBLISHED_AUTHOR_BASELINE',{'a'*40:hashlib.sha256(identity.encode()).hexdigest()})
    assert not lint.scan_text('author',lint.commit_author_text('a'*40,identity),patterns)
    assert lint.scan_text('author',lint.commit_author_text('b'*40,identity),patterns)
    assert lint.commit_author_text('a'*40,'different identity')=='different identity'
    assert lint.scan_text('body',identity,patterns)
