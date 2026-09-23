"""Tests for cover thumbnails (stations/covers.py)."""
import io
import os
import time

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from PIL import Image

from stations.covers import generate_thumbnails, thumbnail_names, thumbnail_urls
from stations.models import Book
from stations.serializers import BookSerializer


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path


def jpeg(width=1000, height=1500) -> ContentFile:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (40, 120, 90)).save(buf, "JPEG", quality=90)
    return ContentFile(buf.getvalue(), name="cover.jpg")


@pytest.fixture
def book_with_cover(episode):
    book = Book.objects.create(title="Vigil", author="George Saunders")
    book.episodes.add(episode)
    # cover_image.save() is what the admin, extraction and download paths call
    book.cover_image.save("cover.jpg", jpeg(), save=True)
    return book


def test_thumbnail_names():
    assert thumbnail_names("covers/front-row/a-b.jpg") == {
        160: "thumbs/front-row/a-b-160.webp",
        240: "thumbs/front-row/a-b-240.webp",
        400: "thumbs/front-row/a-b-400.webp",
    }


@pytest.mark.django_db
def test_saving_a_cover_generates_webp_thumbnails(book_with_cover):
    for width, name in thumbnail_names(book_with_cover.cover_image.name).items():
        assert default_storage.exists(name)
        with default_storage.open(name) as f:
            img = Image.open(f)
            assert img.format == "WEBP"
            assert img.size == (width, width * 3 // 2)


@pytest.mark.django_db
def test_generation_is_idempotent_until_the_cover_changes(book_with_cover):
    assert generate_thumbnails(book_with_cover) == 0

    cover = default_storage.path(book_with_cover.cover_image.name)
    later = time.time() + 10
    os.utime(cover, (later, later))
    assert generate_thumbnails(book_with_cover) == 3


@pytest.mark.django_db
def test_small_covers_are_not_upscaled(episode):
    book = Book.objects.create(title="Tiny")
    book.episodes.add(episode)
    book.cover_image.save("cover.jpg", jpeg(120, 180), save=True)
    with default_storage.open(thumbnail_names(book.cover_image.name)[400]) as f:
        assert Image.open(f).size == (120, 180)


@pytest.mark.django_db
def test_corrupt_cover_is_logged_not_raised(episode):
    book = Book.objects.create(title="Broken")
    book.episodes.add(episode)
    book.cover_image.save("cover.jpg", ContentFile(b"not an image", name="c.jpg"), save=True)
    assert generate_thumbnails(book, force=True) == 0
    assert thumbnail_urls(book) == []


@pytest.mark.django_db
def test_api_lists_thumbnails_with_version(book_with_cover):
    data = BookSerializer(book_with_cover).data
    assert [t["width"] for t in data["cover_thumbnails"]] == [160, 240, 400]
    assert data["cover_thumbnails"][0]["url"].startswith("/media/thumbs/")
    assert "?v=" in data["cover_thumbnails"][0]["url"]


@pytest.mark.django_db
def test_api_has_no_thumbnails_without_cover(book):
    assert BookSerializer(book).data["cover_thumbnails"] == []


@pytest.mark.django_db
def test_backfill_command(book_with_cover, capsys):
    for name in thumbnail_names(book_with_cover.cover_image.name).values():
        default_storage.delete(name)
    call_command("generate_cover_thumbnails")
    assert "3 written for 1 covers" in capsys.readouterr().out
    assert len(thumbnail_urls(book_with_cover)) == 3
