from __future__ import annotations

from app.utils.git_versioning import GitVersioner


def test_git_versioner_commits_before_rebase_and_retries_push(monkeypatch, tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    calls: list[list[str]] = []
    push_attempts = 0

    def fake_run(args, cwd, check=False, capture_output=False, text=False):
        nonlocal push_attempts
        calls.append(args)
        if args[:2] == ["git", "status"]:
            class Status:
                stdout = " M data/ranking/latest.json\n"

            return Status()
        if args[:2] == ["git", "push"] and not check:
            push_attempts += 1

            class Push:
                returncode = 1 if push_attempts == 1 else 0

            return Push()

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr("app.utils.git_versioning.subprocess.run", fake_run)

    pushed = GitVersioner(repo_dir=tmp_path).commit_and_push("test")

    assert pushed is True
    assert ["git", "fetch", "origin", "main"] in calls
    assert ["git", "rebase", "origin/main"] in calls
    assert calls.count(["git", "push", "origin", "main"]) == 2
    assert calls.index(["git", "commit", "-m", "test"]) < calls.index(["git", "rebase", "origin/main"])
