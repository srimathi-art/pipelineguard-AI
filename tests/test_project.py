from github_utils import parse_github_repo_url
from ml_utils import clean_log

def test_parse_repo_url():
    assert parse_github_repo_url("https://github.com/openai/openai-python") == (
        "openai",
        "openai-python",
    )

def test_clean_log():
    value = clean_log("2026-07-11 12:30:10 ERROR CPU reached 95 percent")
    assert "timestamp" in value
    assert "number" in value
