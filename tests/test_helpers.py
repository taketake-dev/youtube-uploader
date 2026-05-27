from pathlib import Path
from datetime import datetime

import pytest

from youtube_uploader.helpers import upload_video_from_file


def test_upload_video_from_file_calls_uploader(tmp_path: Path, mocker):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / "client_secret_abc.json").write_text("{}", encoding="utf-8")

    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"dummy video content")

    thumbnail_path = tmp_path / "thumb.jpg"
    thumbnail_path.write_bytes(b"dummy image content")

    mock_uploader = mocker.MagicMock()
    mock_uploader.upload_video.return_value = {"id": "VIDEO_ID_123"}
    mocker.patch("youtube_uploader.helpers.YoutubeUploader", return_value=mock_uploader)

    response = upload_video_from_file(
        auth_dir=auth_dir,
        video_file=video_path,
        title="Test Title",
        description="Test Description",
        tags="tag1,tag2",
        category_id="24",
        privacy_status="private",
        selfDeclaredMadeForKids=True,
        publish_at="2026-10-20T02:30:00+09:00",
        thumbnail_file=thumbnail_path,
        show_progress=False,
        chunksize=-1,
    )

    assert response == {"id": "VIDEO_ID_123"}
    mock_uploader.connect.assert_called_once()
    upload_config = mock_uploader.upload_video.call_args.args[0]
    assert upload_config.title == "Test Title"
    assert upload_config.description == "Test Description"
    assert upload_config.tags == ["tag1", "tag2"]
    assert upload_config.category_id == "24"
    assert upload_config.privacy_status == "private"
    assert upload_config.selfDeclaredMadeForKids is True
    assert upload_config.publish_at == datetime.fromisoformat(
        "2026-10-20T02:30:00+09:00"
    )
    assert upload_config.thumbnail_bytes == b"dummy image content"
    assert upload_config.thumbnail_mimetype == "image/jpeg"


def test_upload_video_from_file_raises_if_video_missing(tmp_path: Path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / "client_secret_abc.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        upload_video_from_file(
            auth_dir=auth_dir,
            video_file=tmp_path / "missing.mp4",
            title="Missing",
        )
