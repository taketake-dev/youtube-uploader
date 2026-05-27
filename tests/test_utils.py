from pathlib import Path

import pytest

from youtube_uploader.utils import resolve_auth_paths


def test_resolve_auth_paths_finds_client_secret_json(tmp_path: Path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    secret_file = auth_dir / "client_secret.json"
    secret_file.write_text("{}", encoding="utf-8")

    client_secrets_path, token_path = resolve_auth_paths(auth_dir)

    assert client_secrets_path == secret_file
    assert token_path == auth_dir / "token.json"


def test_resolve_auth_paths_finds_client_secret_glob(tmp_path: Path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    secret_file = auth_dir / "client_secret_12345.json"
    secret_file.write_text("{}", encoding="utf-8")

    client_secrets_path, token_path = resolve_auth_paths(auth_dir)

    assert client_secrets_path == secret_file
    assert token_path == auth_dir / "token.json"


def test_resolve_auth_paths_multiple_client_secret_files_error(tmp_path: Path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / "client_secret.json").write_text("{}", encoding="utf-8")
    (auth_dir / "client_secret_other.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="複数検出されました"):
        resolve_auth_paths(auth_dir)


def test_resolve_auth_paths_no_matching_secret_file_error(tmp_path: Path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()

    with pytest.raises(FileNotFoundError, match=r"client_secret\*\.json"):
        resolve_auth_paths(auth_dir)
