"""utils

パッケージの認証ファイルパスや環境変数に関するユーティリティ関数を定義するモジュール
"""

from pathlib import Path


def resolve_auth_paths(base_dir: Path) -> tuple[Path, Path]:
    """指定されたベースディレクトリを基に、認証情報のパスを決定

    Args:
        base_dir (Path): client_secret*.jsonとtoken.jsonを含むディレクトリ。

    Returns:
        tuple[Path, Path]: (client_secrets_path, token_path)

    Raises:
        FileNotFoundError: client_secret*.json が存在しない場合
    """
    # ユーザーが渡したパスを絶対パスに変換し、ディレクトリを自動作成
    resolved_dir = base_dir.expanduser().resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)

    # client_secret*.json のみを受け入れる。client_secret.json も含まれる。
    secret_files = sorted(resolved_dir.glob("client_secret*.json"))
    token_path = resolved_dir / "token.json"

    if len(secret_files) == 0:
        raise FileNotFoundError(
            f"認証ファイルが見つかりません。'{resolved_dir}/client_secret*.json' を配置してください。"
        )
    if len(secret_files) > 1:
        raise FileNotFoundError(
            "認証ファイルが複数検出されました。"
            "1つのディレクトリに client_secret*.json は1つだけ置いてください。"
        )

    return secret_files[0], token_path
