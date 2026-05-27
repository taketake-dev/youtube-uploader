from __future__ import annotations

import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .exceptions import AuthError, UploadError
from .models import YoutubeConfig
from .youtube import YoutubeUploader

logger = logging.getLogger(__name__)


def _normalize_tags(tags: str | Iterable[str] | None) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def _normalize_publish_at(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(
        "publish_at must be datetime, ISO 8601 string, or None."
    )


def _read_file_data(file_path: Path) -> tuple[bytes, str]:
    path = file_path.expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    mimetype, _ = mimetypes.guess_type(path.as_posix())
    if not mimetype:
        raise ValueError(f"MIMEタイプを推定できませんでした: {path}")

    return path.read_bytes(), mimetype


def upload_video_from_file(
    auth_dir: str | Path,
    video_file: str | Path,
    title: str,
    description: str = "",
    tags: str | Iterable[str] | None = None,
    category_id: str = "24",
    privacy_status: str = "private",
    selfDeclaredMadeForKids: bool = False,
    publish_at: datetime | str | None = None,
    thumbnail_file: str | Path | None = None,
    show_progress: bool = False,
    chunksize: int = -1,
) -> dict:
    """動画ファイルをパス指定で読み込み、YouTube にアップロードする。

    Args:
        auth_dir: 認証情報ディレクトリパス。
        video_file: アップロードする動画ファイルのパス。
        title: 動画のタイトル。
        description: 動画の説明文。
        tags: カンマ区切り文字列またはタグリスト。
        category_id: YouTube のカテゴリ ID。
        privacy_status: 動画の公開設定。
        selfDeclaredMadeForKids: 子供向けコンテンツかどうか。
        publish_at: 予約投稿日時。datetime か ISO 8601 文字列。
        thumbnail_file: サムネイル画像ファイルのパス。
        show_progress: 進捗表示を有効にするか。
        chunksize: アップロードのチャンクサイズ。

    Returns:
        YouTube API のレスポンス辞書。

    Raises:
        FileNotFoundError: 指定ファイルが存在しない場合。
        ValueError: MIMEタイプを推定できない場合など。
        AuthError: 認証に失敗した場合。
        UploadError: アップロードに失敗した場合。
    """
    auth_path = Path(auth_dir).expanduser().resolve()
    video_path = Path(video_file)
    video_bytes, video_mimetype = _read_file_data(video_path)

    thumbnail_bytes = None
    thumbnail_mimetype = None
    if thumbnail_file is not None:
        thumb_path = Path(thumbnail_file)
        thumbnail_bytes, thumbnail_mimetype = _read_file_data(thumb_path)

    uploader = YoutubeUploader(auth_path)
    uploader.connect()

    config = YoutubeConfig(
        video_bytes=video_bytes,
        video_mimetype=video_mimetype,
        title=title,
        description=description,
        tags=_normalize_tags(tags),
        category_id=category_id,
        privacy_status=privacy_status,
        selfDeclaredMadeForKids=selfDeclaredMadeForKids,
        publish_at=_normalize_publish_at(publish_at),
        thumbnail_bytes=thumbnail_bytes,
        thumbnail_mimetype=thumbnail_mimetype,
    )

    progress_callback = None
    if show_progress:
        def _print_progress(progress: float) -> None:
            print(f"🔄 アップロード進捗: {progress:.2%} 完了", end="\r", flush=True)

        progress_callback = _print_progress

    response = uploader.upload_video(
        config,
        progress_callback=progress_callback,
        chunksize=chunksize,
    )

    if show_progress:
        print()

    return response
