from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.conf import settings as django_settings

from .models import Station, Brand, Episode, Book, Phrase


class BookInline(admin.TabularInline):
    """Inline display of books for an episode"""

    model = Book
    extra = 0
    fields = ("title", "author", "description")
    readonly_fields = ("title", "author", "description")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "brand",
        "aired_at",
        "has_book",
        "book_count",
        "status_display",
    )
    list_filter = ("has_book", "brand", "aired_at", "status")
    search_fields = ("title", "url")
    readonly_fields = (
        "has_book",
        "slug",
        "status",
        "processed_at",
        "last_error",
        "scraped_data_preview",
        "extraction_result_preview",
        "book_links_readonly",
    )
    date_hierarchy = "aired_at"
    inlines = [BookInline]
    actions = ["reprocess_episodes_action"]

    fieldsets = (
        (
            "Episode Information",
            {"fields": ("brand", "title", "slug", "url", "aired_at", "has_book")},
        ),
        (
            "Pipeline",
            {
                "fields": (
                    "status",
                    "processed_at",
                    "last_error",
                    "scraped_data_preview",
                    "extraction_result_preview",
                ),
            },
        ),
        ("Related Data", {"fields": ("book_links_readonly",)}),
    )

    def book_count(self, obj):
        """Display count of books"""
        count = obj.book_set.count()
        return f"{count} book{'s' if count != 1 else ''}" if count > 0 else "-"

    book_count.short_description = "Books"

    def status_display(self, obj):
        """Status chip for list view"""
        return obj.get_status_display()

    status_display.short_description = "Status"

    def scraped_data_preview(self, obj):
        """Preview of scraped description from episode.scraped_data"""
        if not obj.scraped_data:
            return "-"
        desc = (obj.scraped_data.get("description") or "")[:200]
        return desc + ("..." if len(obj.scraped_data.get("description") or "") > 200 else "")

    scraped_data_preview.short_description = "Scraped description"

    def extraction_result_preview(self, obj):
        """Preview of extraction reasoning"""
        if not obj.extraction_result:
            return "-"
        return (obj.extraction_result.get("reasoning") or "")[:500]

    extraction_result_preview.short_description = "Extraction reasoning"

    def book_links_readonly(self, obj):
        """Display links to related books (readonly)"""
        books = obj.book_set.all()
        if not books:
            return format_html("<em>No books detected</em>")
        links = []
        for book in books:
            url = reverse("admin:stations_book_change", args=[book.pk])
            links.append(f'<a href="{url}" target="_blank">{book.title}</a>')
        return format_html("<br>".join(links))

    book_links_readonly.short_description = "Books"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:episode_id>/reprocess/",
                self.admin_site.admin_view(self.reprocess_episode),
                name="stations_episode_reprocess",
            ),
        ]
        return custom_urls + urls

    def reprocess_episode(self, request, episode_id):
        """Reprocess a single episode: set QUEUED and enqueue AI extraction."""
        from .tasks import ai_extract_books_task

        episode = Episode.objects.get(pk=episode_id)
        episode.status = Episode.STATUS_QUEUED
        episode.last_error = None
        episode.save(update_fields=["status", "last_error"])
        ai_extract_books_task.delay(episode_id)

        msg = "Queued extraction for 1 episode."
        flower_url = getattr(django_settings, "FLOWER_URL", "") or ""
        if flower_url:
            msg = format_html('{} <a href="{}" target="_blank">Open Flower</a>', msg, flower_url)
        messages.success(request, msg)
        return redirect("admin:stations_episode_change", episode_id)

    @admin.action(description="Reprocess (AI) selected episodes")
    def reprocess_episodes_action(self, request, queryset):
        from .tasks import ai_extract_books_task

        for episode in queryset:
            episode.status = Episode.STATUS_QUEUED
            episode.last_error = None
            episode.save(update_fields=["status", "last_error"])
            ai_extract_books_task.delay(episode.id)
        count = queryset.count()
        msg = f"Queued extraction for {count} episode(s)."
        flower_url = getattr(django_settings, "FLOWER_URL", "") or ""
        if flower_url:
            msg = format_html('{} <a href="{}" target="_blank">Open Flower</a>', msg, flower_url)
        self.message_user(request, msg)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_reprocess_button"] = True
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "episode_brand", "cover_preview_small")
    list_filter = ("episode__brand",)
    search_fields = ("title", "author", "description")
    readonly_fields = ("slug", "cover_preview_large")
    fieldsets = (
        ("Book Information", {"fields": ("title", "author", "slug", "description")}),
        (
            "Cover Image",
            {
                "fields": ("cover_preview_large", "cover_image"),
            },
        ),
        ("Links", {"fields": ("purchase_link",)}),
        ("Episode", {"fields": ("episode",)}),
    )

    def episode_brand(self, obj):
        if obj.episode and obj.episode.brand:
            return obj.episode.brand.name
        return "-"

    episode_brand.short_description = "Show"

    def cover_preview_small(self, obj):
        """Small thumbnail for list view"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 40px;" />',
                obj.cover_image.url,
            )
        return "-"

    cover_preview_small.short_description = "Cover"

    def cover_preview_large(self, obj):
        """Large preview for detail view"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 150px; border: 1px solid #ddd; padding: 4px;" />',
                obj.cover_image.url,
            )
        return format_html("<em>No cover image</em>")

    cover_preview_large.short_description = "Current Cover"

    actions = ["fetch_and_download_covers"]

    @admin.action(description="Fetch and download covers from Open Library")
    def fetch_and_download_covers(self, request, queryset):
        """Fetch cover images from Open Library and store locally"""
        import tempfile
        import urllib.request
        import os
        from django.core.files import File
        from .utils import fetch_book_cover

        downloaded = 0
        failed = 0

        for book in queryset:
            if book.cover_image:
                continue  # Skip if already has cover

            # First fetch the URL from Open Library
            cover_url = fetch_book_cover(book.title, book.author)
            if not cover_url:
                failed += 1
                continue

            # Then download and save locally
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ) as tmp_file:
                    req = urllib.request.Request(
                        cover_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; RadioReads/1.0)"
                        },
                    )
                    with urllib.request.urlopen(req, timeout=30) as response:
                        tmp_file.write(response.read())
                        tmp_path = tmp_file.name

                filename = f"{book.slug}.jpg"
                with open(tmp_path, "rb") as f:
                    book.cover_image.save(filename, File(f), save=True)

                os.unlink(tmp_path)
                downloaded += 1

            except Exception as e:
                failed += 1

        self.message_user(
            request, f"Downloaded {downloaded} cover(s). {failed} failed or skipped."
        )


# Register remaining models with default admin
admin.site.register([Station, Brand, Phrase])


def extraction_evaluation_view(request):
    """Model evaluation dashboard: show books with input to AI, reasoning, and verify link."""
    from django.contrib.admin.sites import site as default_admin_site

    if not request.user.is_staff:
        return redirect(default_admin_site.login_url)

    books = (
        Book.objects.select_related("episode", "episode__brand")
        .order_by("-episode__aired_at", "-episode__id")[:200]
    )

    rows = []
    for book in books:
        episode = book.episode
        if episode.scraped_data:
            input_text = (
                (episode.scraped_data.get("title") or "")
                + ". "
                + (episode.scraped_data.get("description") or "")
            )
            input_text = (input_text.strip() or episode.title or "")[:500]
        else:
            input_text = (episode.title or "")[:500]

        reasoning = ""
        if episode.extraction_result:
            reasoning = (episode.extraction_result.get("reasoning") or "")[:500]

        verify_url = episode.url or "#"
        rows.append(
            {
                "book": book,
                "episode_title": episode.title,
                "input_to_ai": input_text,
                "reasoning": reasoning,
                "verify_url": verify_url,
            }
        )

    context = {
        "title": "Extraction Evaluation",
        "rows": rows,
    }
    return render(request, "admin/stations/extraction_evaluation.html", context)


# Add extraction evaluation URL to admin
_original_admin_get_urls = admin.site.get_urls


def _admin_get_urls_with_extraction():
    urls = _original_admin_get_urls()
    custom = [
        path(
            "stations/extraction-evaluation/",
            admin.site.admin_view(extraction_evaluation_view),
            name="stations_extraction_evaluation",
        ),
    ]
    return custom + urls


admin.site.get_urls = _admin_get_urls_with_extraction
