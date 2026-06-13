import os

from rdn.handoff import sync


def test_find_git_repos_skips_filtered_dirs(tmp_path):
    repo_a = tmp_path / "repo-a"
    repo_a.mkdir()
    (repo_a / ".git").mkdir()

    skipped = tmp_path / "node_modules" / "repo-b"
    skipped.mkdir(parents=True)
    (skipped / ".git").mkdir()

    repos = sync.find_git_repos(str(tmp_path))
    assert str(repo_a) in repos
    assert str(skipped) not in repos


def test_install_hooks_appends_to_existing_hook(tmp_path):
    repo = tmp_path / "repo"
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)
    hook_path = hooks / "post-commit"
    original = "#!/bin/sh\necho 'custom hook'\n"
    hook_path.write_text(original, encoding="utf-8")

    installed = sync.install_hooks(str(repo))
    content = hook_path.read_text(encoding="utf-8")

    assert str(hook_path) in installed
    assert "custom hook" in content
    assert sync.HOOK_MARKER in content


def test_run_once_aggregates_scan_results(monkeypatch):
    class DummyRDN:
        pass

    monkeypatch.setattr(sync, "ReasonRDN", lambda node_url=None: DummyRDN())
    monkeypatch.setattr(
        sync,
        "scan_repos",
        lambda root, install_repo_hooks: {
            "repos": ["a", "b"],
            "states": [{"repo_path": "a", "repo_name": "a"}, {"repo_path": "b", "repo_name": "b", "error": "boom"}],
            "hooks_installed": 2,
            "errors": [{"repo": "b", "error": "boom"}],
        },
    )
    monkeypatch.setattr(sync, "deposit_state", lambda rdn, state: {"status": "remembered"})

    result = sync.run_once(repo=None, root=os.getcwd(), node_url=None, install_repo_hooks=True)

    assert result["repos_scanned"] == 2
    assert result["deposits_attempted"] == 2
    assert result["deposits_succeeded"] == 1
    assert result["hooks_installed"] == 2
    assert len(result["errors"]) >= 1
