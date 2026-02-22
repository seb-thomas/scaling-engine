import json

from django.contrib import admin
from django.utils.html import format_html, escape
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
    fields = ("title", "author", "description", "view_link")
    readonly_fields = ("title", "author", "description", "view_link")
    can_delete = False

    def view_link(self, obj):
        if obj.pk:
            url = reverse("admin:stations_book_change", args=[obj.pk])
            return format_html('<a href="{}">View</a>', url)
        return "-"

    view_link.short_description = "Edit"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "brand",
        "aired_at",
        "book_count",
        "needs_review_display",
        "status_display",
    )
    list_filter = ("brand", "aired_at", "status")
    search_fields = ("title", "url")
    readonly_fields = (
        "has_book",
        "slug",
        "status",
        "ai_confidence",
        "processed_at",
        "last_error",
        "scraped_data_formatted",
        "extraction_result_formatted",
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
                    "ai_confidence",
                    "processed_at",
                    "last_error",
                    "scraped_data_formatted",
                    "extraction_result_formatted",
                ),
            },
        ),
    )

    def book_count(self, obj):
        """Display count of books"""
        count = obj.book_set.count()
        return f"{count} book{'s' if count != 1 else ''}" if count > 0 else "-"

    book_count.short_description = "Books"

    def needs_review_display(self, obj):
        if obj.ai_confidence is None:
            return "-"
        if obj.needs_review:
            # Build reason hint
            reasons = []
            if obj.ai_confidence < 0.9:
                reasons.append(f"confidence {int(obj.ai_confidence * 100)}%")
            if obj.book_set.filter(google_books_verified=False).exists():
                reasons.append("unverified book")
            hint = ", ".join(reasons)
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;" title="{}">Review</span>',
                hint,
            )
        return format_html('<span style="color: #28a745;">OK</span>')

    needs_review_display.short_description = "Review"

    def status_display(self, obj):
        """Status chip for list view"""
        return obj.get_status_display()

    status_display.short_description = "Status"

    def _json_block(self, data):
        """Render a JSON dict as a formatted, readable block."""
        if not data:
            return format_html("<em>-</em>")
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="white-space: pre-wrap; word-break: break-word; '
            'max-width: 800px; background: #f8f8f8; padding: 10px; '
            'border: 1px solid #ddd; border-radius: 4px; font-size: 12px; '
            'line-height: 1.5;">{}</pre>',
            formatted,
        )

    def scraped_data_formatted(self, obj):
        return self._json_block(obj.scraped_data)

    scraped_data_formatted.short_description = "Scraped data"

    def extraction_result_formatted(self, obj):
        return self._json_block(obj.extraction_result)

    extraction_result_formatted.short_description = "Extraction result"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:episode_id>/reprocess/",
                self.admin_site.admin_view(self.reprocess_episode),
                name="stations_episode_reprocess",
            ),
            path(
                "<int:episode_id>/status/",
                self.admin_site.admin_view(self.episode_status_json),
                name="stations_episode_status",
            ),
        ]
        return custom_urls + urls

    def episode_status_json(self, request, episode_id):
        """Return episode status as JSON for polling."""
        from django.http import JsonResponse

        episode = Episode.objects.get(pk=episode_id)
        return JsonResponse({"status": episode.status})

    def reprocess_episode(self, request, episode_id):
        """Reprocess a single episode: set QUEUED and enqueue AI extraction."""
        from .tasks import ai_extract_books_task

        episode = Episode.objects.get(pk=episode_id)

        if episode.status in (Episode.STATUS_QUEUED, Episode.STATUS_PROCESSING):
            messages.warning(request, "Already processing — please wait.")
            return redirect(
                reverse("admin:stations_episode_change", args=[episode_id])
                + "?awaiting_reprocess=1"
            )

        episode.status = Episode.STATUS_QUEUED
        episode.last_error = None
        episode.save(update_fields=["status", "last_error"])
        ai_extract_books_task.delay(episode_id)

        messages.info(
            request,
            "Reprocessing started. This page will refresh automatically when done.",
        )
        return redirect(
            reverse("admin:stations_episode_change", args=[episode_id])
            + "?awaiting_reprocess=1"
        )

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
        extra_context["awaiting_reprocess"] = "awaiting_reprocess" in request.GET
        extra_context["status_url"] = reverse(
            "admin:stations_episode_status", args=[object_id]
        )
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "episode_brand", "gb_status", "cover_preview_small", "cover_error_short")
    list_filter = ("episode__brand", "google_books_verified")
    search_fields = ("title", "author", "description")
    readonly_fields = ("slug", "cover_preview_large", "refetch_cover_button", "google_books_verified", "cover_fetch_error")
    fieldsets = (
        ("Book Information", {"fields": ("title", "author", "slug", "description", "google_books_verified")}),
        (
            "Cover Image",
            {
                "fields": ("cover_preview_large", "cover_image", "cover_fetch_error", "refetch_cover_button"),
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

    def gb_status(self, obj):
        if obj.google_books_verified:
            return format_html('<span style="color: #28a745;">Verified</span>')
        return format_html('<span style="color: #999;">-</span>')

    gb_status.short_description = "Google Books"

    def cover_error_short(self, obj):
        if obj.cover_fetch_error:
            truncated = obj.cover_fetch_error[:60]
            if len(obj.cover_fetch_error) > 60:
                truncated += "..."
            return format_html('<span style="color: #dc3545;" title="{}">{}</span>', obj.cover_fetch_error, truncated)
        return "-"

    cover_error_short.short_description = "Cover Error"

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

    def refetch_cover_button(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("admin:stations_book_refetch_cover", args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="padding: 6px 12px;">Refetch cover</a>'
            '<p style="margin-top: 6px; color: #666; font-size: 12px;">'
            'Look up on Google Books and download cover image.</p>',
            url,
        )

    refetch_cover_button.short_description = "Refetch"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:book_id>/refetch-cover/",
                self.admin_site.admin_view(self.refetch_cover),
                name="stations_book_refetch_cover",
            ),
        ]
        return custom_urls + urls

    def refetch_cover(self, request, book_id):
        """Refetch cover for a single book via Google Books."""
        from .utils import verify_book_exists
        from .ai_utils import download_and_save_cover

        book = Book.objects.get(pk=book_id)
        book_info = verify_book_exists(book.title, book.author)
        cover_url = book_info.get("cover_url") or ""

        if cover_url:
            success = download_and_save_cover(book, cover_url, allow_fallback=True)
            if success:
                messages.success(request, f"Cover downloaded for '{book.title}'.")
            else:
                messages.error(request, f"Download failed: {book.cover_fetch_error}")
        else:
            book.cover_fetch_error = "No cover available on Google Books"
            book.save(update_fields=["cover_fetch_error"])
            messages.warning(request, "No cover available on Google Books.")

        return redirect(reverse("admin:stations_book_change", args=[book_id]))

    actions = ["refetch_covers"]

    @admin.action(description="Refetch covers from Google Books")
    def refetch_covers(self, request, queryset):
        """Refetch cover images from Google Books for selected books."""
        from .utils import verify_book_exists
        from .ai_utils import download_and_save_cover

        downloaded = 0
        failed = 0

        for book in queryset:
            if book.cover_image:
                continue  # Skip if already has cover

            book_info = verify_book_exists(book.title, book.author)
            cover_url = book_info.get("cover_url") or ""

            if not cover_url:
                book.cover_fetch_error = "No cover available on Google Books"
                book.save(update_fields=["cover_fetch_error"])
                failed += 1
                continue

            if download_and_save_cover(book, cover_url, allow_fallback=True):
                downloaded += 1
            else:
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
