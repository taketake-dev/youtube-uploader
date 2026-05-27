"""YouTube Uploader CLI entry point.

このモジュールは、ユーザーがシェルスクリプトや他のプロジェクトからOAuthの初期化および動画の
アップロードを行えるように、ライブラリの周囲に小さなコマンドラインラッパーを提供します。"""

import argparse
import logging
import mimetypes
from datetime import datetime
from pathlib import Path

from . import AuthError, UploadError, YoutubeConfig, YoutubeUploader

logger = logging.getLogger(__name__)


def _parse_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _parse_publish_at(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "publish_at must be ISO 8601 format, e.g. 2026-10-20T02:30:00+09:00"
        ) from exc


def _get_file_data(file_path: Path) -> tuple[bytes, str]:
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    mimetype, _ = mimetypes.guess_type(file_path.as_posix())
    if not mimetype:
        raise ValueError(f"MIMEタイプを推定できませんでした: {file_path}")

    return file_path.read_bytes(), mimetype


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="YouTube 動画のアップロードを実行する CLI。"
    )
    parser.add_argument(
        "--auth-dir",
        "-a",
        type=Path,
        default=Path.cwd(),
        help="client_secret.json と token.json を置いたディレクトリ。デフォルトはカレントディレクトリ。",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_parser = subparsers.add_parser(
        "auth-init",
        help="初回認証と token.json の作成を行います。",
    )

    upload_parser = subparsers.add_parser(
        "upload",
        help="YouTube に動画をアップロードします。",
    )
    upload_parser.add_argument(
        "--video-file",
        "-v",
        type=Path,
        required=True,
        help="アップロードする動画ファイルのパス。",
    )
    upload_parser.add_argument(
        "--title",
        "-t",
        type=str,
        required=True,
        help="動画のタイトル。",
    )
    upload_parser.add_argument(
        "--description",
        "-d",
        type=str,
        default="",
        help="動画の説明文。",
    )
    upload_parser.add_argument(
        "--tags",
        type=_parse_tags,
        default=[],
        help="カンマ区切りのタグ一覧。例: Python,自動化,テスト",
    )
    upload_parser.add_argument(
        "--category-id",
        type=str,
        default="24",
        help="YouTube のカテゴリ ID。デフォルトは 24(エンターテイメント)。",
    )
    upload_parser.add_argument(
        "--privacy-status",
        type=str,
        choices=["public", "private", "unlisted"],
        default="private",
        help="動画の公開設定。",
    )
    upload_parser.add_argument(
        "--made-for-kids",
        action="store_true",
        help="動画を子供向けコンテンツとしてマークします。",
    )
    upload_parser.add_argument(
        "--publish-at",
        type=_parse_publish_at,
        help="予約投稿日時。ISO 8601 形式で指定。",
    )
    upload_parser.add_argument(
        "--thumbnail-file",
        type=Path,
        help="サムネイル画像ファイルのパス。",
    )
    upload_parser.add_argument(
        "--show-progress",
        action="store_true",
        help="アップロード進捗を表示します。",
    )
    upload_parser.add_argument(
        "--chunksize",
        type=int,
        default=-1,
        help="アップロードのチャンクサイズ（バイト）。デフォルトは -1 で一括アップロード。",
    )

    return parser


def _print_progress(progress: float) -> None:
    print(f"🔄 アップロード進捗: {progress:.2%} 完了", end="\r", flush=True)


def init_auth_setup() -> None:
    parser = argparse.ArgumentParser(
        description="初回認証と token.json の生成を行います。"
    )
    parser.add_argument(
        "--auth-dir",
        "-a",
        type=Path,
        default=Path.cwd(),
        help="client_secret.json と token.json を置いたディレクトリ。デフォルトはカレントディレクトリ。",
    )
    args = parser.parse_args()

    uploader = YoutubeUploader(args.auth_dir)
    try:
        uploader.connect()
        print(
            f"認証に成功しました。token.json は {args.auth_dir / 'token.json'} に保存されました。"
        )
    except AuthError as exc:
        logger.critical(f"認証に失敗しました: {exc}")
        raise SystemExit(1) from exc


def _run_upload(args: argparse.Namespace) -> None:
    uploader = YoutubeUploader(args.auth_dir)
    uploader.connect()

    video_bytes, video_mimetype = _get_file_data(args.video_file)
    thumbnail_bytes = None
    thumbnail_mimetype = None
    if args.thumbnail_file:
        thumbnail_bytes, thumbnail_mimetype = _get_file_data(args.thumbnail_file)

    config = YoutubeConfig(
        video_bytes=video_bytes,
        video_mimetype=video_mimetype,
        title=args.title,
        description=args.description,
        tags=args.tags,
        category_id=args.category_id,
        privacy_status=args.privacy_status,
        selfDeclaredMadeForKids=args.made_for_kids,
        publish_at=args.publish_at,
        thumbnail_bytes=thumbnail_bytes,
        thumbnail_mimetype=thumbnail_mimetype,
    )

    try:
        response = uploader.upload_video(
            config,
            progress_callback=_print_progress if args.show_progress else None,
            chunksize=args.chunksize,
        )
        print()
        print(f"動画アップロードが完了しました。動画 ID: {response.get('id')}")
    except (AuthError, UploadError, FileNotFoundError, ValueError) as exc:
        logger.critical(exc)
        raise SystemExit(1) from exc


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "auth-init":
        uploader = YoutubeUploader(args.auth_dir)
        try:
            uploader.connect()
            print(
                f"認証に成功しました。token.json は {args.auth_dir / 'token.json'} に保存されました。"
            )
        except AuthError as exc:
            logger.critical(f"認証に失敗しました: {exc}")
            raise SystemExit(1) from exc
    elif args.command == "upload":
        _run_upload(args)


if __name__ == "__main__":
    main()
