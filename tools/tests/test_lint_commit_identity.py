"""Identity metadata follows the existing author-email exception, not a content bypass."""
import importlib.util
import subprocess
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


def test_mailmap_identity_email_only_is_exempt():
    text = "Contributor <blockedidentityqzx@example.com>\n"
    assert not lint.scan_text("mailmap", lint.mailmap_text(text), patterns)
    assert lint.mailmap_text(text).count("\n") == text.count("\n")
    for text in (
        "blockedidentityqzx <safe@example.com>\n",
        "Contributor <safe@example.com> # blockedidentityqzx\n",
        "# blockedidentityqzx@example.com\n",
        "Contact blockedidentityqzx@example.com\n",
        "Contributor <blockedidentityqzx@example.com> unexpected text\n",
    ):
        assert lint.scan_text("mailmap", lint.mailmap_text(text), patterns)


def test_mailmap_canonicalizes_history_without_changing_commits(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "blockedidentityqzx")
    git("config", "user.email", "person@example.com")
    git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "Synthetic history")
    sha = git("rev-parse", "HEAD")
    assert lint.scan_text("author", lint.commit_records(tmp_path)[0][1], patterns)
    (tmp_path / ".mailmap").write_text("Contributor <person@example.com>\n")
    assert lint.commit_records(tmp_path) == [(sha, "Contributor", "Synthetic history")]
    assert git("rev-parse", "HEAD") == sha
    assert git("log", "-1", "--format=%an") == "blockedidentityqzx"
    # A mapping for another identity cannot suppress this author's failure.
    (tmp_path / ".mailmap").write_text("Contributor <other@example.com>\n")
    assert lint.scan_text("author", lint.commit_records(tmp_path)[0][1], patterns)
    (tmp_path / ".mailmap").write_text("blockedidentityqzx <person@example.com>\n")
    assert lint.scan_text("author", lint.commit_records(tmp_path)[0][1], patterns)
