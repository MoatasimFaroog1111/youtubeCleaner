"""Safety tests never contact YouTube."""
from unittest.mock import Mock
import pytest
import safety
import cleaner
import educator

def test_default_is_preview(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    assert safety.is_dry_run() is True
    monkeypatch.setenv("DRY_RUN", "false")
    assert safety.is_dry_run() is False
    monkeypatch.setenv("DRY_RUN", "maybe")
    assert safety.is_dry_run() is True

@pytest.mark.parametrize("flag,approval", [("true", "I_APPROVE"), ("false", ""), ("false", "yes")])
def test_denied_without_both_flags(monkeypatch, flag, approval):
    monkeypatch.setenv("DRY_RUN", flag)
    monkeypatch.setenv("YOUTUBE_WRITE_APPROVAL", approval)
    with pytest.raises(PermissionError):
        safety.require_write_approval(False)

def test_allowed_only_with_both_flags(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("YOUTUBE_WRITE_APPROVAL", "I_APPROVE")
    safety.require_write_approval(False)

@pytest.mark.parametrize("fn,args", [
    (cleaner.delete_playlist_item, ("item", "title")),
    (cleaner.remove_like_from_video, ("video", "title")),
    (cleaner.unsubscribe_inappropriate_channel, ("channel", "title")),
])
def test_preview_does_not_write(monkeypatch, fn, args):
    monkeypatch.delenv("DRY_RUN", raising=False)
    youtube = Mock()
    assert fn(youtube, *args) is True
    assert youtube.mock_calls == []

@pytest.mark.parametrize("fn,args", [
    (cleaner.delete_playlist_item, ("item", "title")),
    (cleaner.remove_like_from_video, ("video", "title")),
    (cleaner.unsubscribe_inappropriate_channel, ("channel", "title")),
])
def test_direct_live_mutation_denied(monkeypatch, fn, args):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.delenv("YOUTUBE_WRITE_APPROVAL", raising=False)
    youtube = Mock()
    with pytest.raises(PermissionError):
        fn(youtube, *args, dry_run=False)
    assert youtube.mock_calls == []

def test_educator_preview_never_writes(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    youtube = Mock()
    assert educator.add_to_child_playlist(youtube, "video") is False
    assert youtube.mock_calls == []

def test_educator_live_denied(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.delenv("YOUTUBE_WRITE_APPROVAL", raising=False)
    youtube = Mock()
    with pytest.raises(PermissionError):
        educator.add_to_child_playlist(youtube, "video", dry_run=False)
    assert youtube.mock_calls == []
