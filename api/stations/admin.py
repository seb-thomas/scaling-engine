import json

from django import forms
from django.contrib import admin
from django.utils.html import format_html, escape
from django.urls import reverse, path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.conf import settings as django_settings

from .models import Station, Brand, Episode, Book, Phrase, Category


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


class EpisodeAdminForm(forms.ModelForm):
    class Meta:
        model = Episode
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "review_status" in self.fields:
            status = self.instance.review_status if self.instance else ""
            if status in (Episode.REVIEW_REQUIRED, Episode.REVIEW_REVIEWED):
                self.fields["review_status"].choices = [
                    (Episode.REVIEW_REQUIRED, "Required"),
                    (Episode.REVIEW_REVIEWED, "Reviewed"),
                ]
            else:
                # NOT_REQUIRED or blank — show current value, disabled
                label = dict(Episode.REVIEW_CHOICES).get(status, "Unprocessed")
                self.fields["review_status"].choices = [(status, label)]
                self.fields["review_status"].disabled = True


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    form = EpisodeAdminForm
    list_display = (
        "title",
        "brand",
        "aired_at",
        "book_count",
        "review_status_display",
        "status_display",
    )
    list_filter = ("review_status", "brand", "aired_at", "status")
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
            {"fields": ("brand", "title", "slug", "url", "aired_at", "has_book", "review_status")},
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

    def review_status_display(self, obj):
        if obj.review_status == Episode.REVIEW_REQUIRED:
            reasons = []
            if obj.ai_confidence is not None and obj.ai_confidence < 0.9:
                reasons.append(f"confidence {int(obj.ai_confidence * 100)}%")
            if obj.book_set.filter(google_books_verified=False).exists():
                reasons.append("unverified book")
            hint = ", ".join(reasons) or "flagged"
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;" title="{}">Review</span>',
                hint,
            )
        if obj.review_status == Episode.REVIEW_REVIEWED:
            return format_html('<span style="color: #0d6efd; font-weight: bold;">Reviewed</span>')
        if obj.review_status == Episode.REVIEW_NOT_REQUIRED:
            return format_html('<span style="color: #28a745;">OK</span>')
        return "-"

    review_status_display.short_description = "Review"
    review_status_display.admin_order_field = "review_status"

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

        from django.utils import timezone as tz
        episode.status = Episode.STATUS_QUEUED
        episode.last_error = None
        episode.status_changed_at = tz.now()
        episode.save(update_fields=["status", "last_error", "status_changed_at"])
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

        from django.utils import timezone as tz
        for episode in queryset:
            episode.status = Episode.STATUS_QUEUED
            episode.last_error = None
            episode.status_changed_at = tz.now()
            episode.save(update_fields=["status", "last_error", "status_changed_at"])
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
    list_display = ("title", "author", "category_list", "episode_brand", "gb_status", "cover_preview_small", "cover_error_short")
    list_filter = ("categories", "episode__brand", "google_books_verified")
    filter_horizontal = ("categories",)
    search_fields = ("title", "author", "description")
    readonly_fields = ("slug", "cover_preview_large", "refetch_cover_button", "google_books_verified", "cover_fetch_error")
    fieldsets = (
        ("Book Information", {"fields": ("title", "author", "categories", "slug", "description", "google_books_verified")}),
        (
            "Cover Image",
            {
                "fields": ("cover_preview_large", "cover_image", "cover_fetch_error", "refetch_cover_button"),
            },
        ),
        ("Links", {"fields": ("purchase_link",)}),
        ("Episode", {"fields": ("episode",)}),
    )

    def category_list(self, obj):
        return ", ".join(c.name for c in obj.categories.all()) or "-"

    category_list.short_description = "Categories"

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


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "station", "episode_stats", "backfill_link")
    readonly_fields = ("episode_stats_detail",)

    def episode_stats(self, obj):
        count = Episode.objects.filter(brand=obj).count()
        if count == 0:
            return "0 episodes"
        oldest = Episode.objects.filter(brand=obj).order_by("aired_at").first()
        newest = Episode.objects.filter(brand=obj).order_by("-aired_at").first()
        oldest_str = oldest.aired_at.strftime("%-d %b %Y") if oldest and oldest.aired_at else "?"
        newest_str = newest.aired_at.strftime("%-d %b %Y") if newest and newest.aired_at else "?"
        return f"{count} episodes ({oldest_str} – {newest_str})"

    episode_stats.short_description = "Episodes"

    def episode_stats_detail(self, obj):
        if not obj.pk:
            return "-"
        count = Episode.objects.filter(brand=obj).count()
        if count == 0:
            return format_html("<em>No episodes yet</em>")
        oldest = Episode.objects.filter(brand=obj).order_by("aired_at").first()
        newest = Episode.objects.filter(brand=obj).order_by("-aired_at").first()
        oldest_str = oldest.aired_at.strftime("%-d %b %Y") if oldest and oldest.aired_at else "?"
        newest_str = newest.aired_at.strftime("%-d %b %Y") if newest and newest.aired_at else "?"
        book_count = Book.objects.filter(episode__brand=obj).count()
        return format_html(
            "<strong>{}</strong> episodes ({} – {})<br>"
            "<strong>{}</strong> books extracted",
            count, oldest_str, newest_str, book_count,
        )

    episode_stats_detail.short_description = "Episode coverage"

    def backfill_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("admin:stations_brand_backfill", args=[obj.pk])
        return format_html('<a href="{}">Backfill</a>', url)

    backfill_link.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:brand_id>/backfill/",
                self.admin_site.admin_view(self.backfill_view),
                name="stations_brand_backfill",
            ),
        ]
        return custom_urls + urls

    def backfill_view(self, request, brand_id):
        brand = Brand.objects.get(pk=brand_id)

        # Episode stats for context
        episode_count = Episode.objects.filter(brand=brand).count()
        oldest = Episode.objects.filter(brand=brand).order_by("aired_at").first()
        newest = Episode.objects.filter(brand=brand).order_by("-aired_at").first()

        if request.method == "POST":
            max_episodes = int(request.POST.get("max_episodes", 100))
            since_date = request.POST.get("since_date", "2024-01-01")
            extract = request.POST.get("extract") == "on"

            from .tasks import backfill_brand_task

            backfill_brand_task.delay(
                brand_id=brand.id,
                max_episodes=max_episodes,
                since_date=since_date,
                extract=extract,
            )

            extract_msg = " + AI extraction" if extract else ""
            messages.success(
                request,
                f"Backfill queued for {brand.name}: up to {max_episodes} episodes "
                f"since {since_date}{extract_msg}",
            )
            return redirect(reverse("admin:stations_brand_change", args=[brand_id]))

        context = {
            **self.admin_site.each_context(request),
            "brand": brand,
            "episode_count": episode_count,
            "oldest_episode": oldest,
            "newest_episode": newest,
            "title": f"Backfill: {brand.name}",
            "opts": self.model._meta,
        }
        return render(request, "admin/stations/brand/backfill.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_backfill_button"] = True
        return super().change_view(request, object_id, form_url, extra_context)


# Register remaining models with default admin
admin.site.register([Station, Phrase, Category])


def system_health_view(request):
    """System health dashboard."""
    if not request.user.is_staff:
        from django.contrib.admin.sites import site as default_admin_site
        return redirect(default_admin_site.login_url)

    from .health import get_system_health
    health = get_system_health()
    context = {
        **admin.site.each_context(request),
        "title": "System Health",
        "health": health,
    }
    return render(request, "admin/stations/system_health.html", context)


def system_health_unstick(request):
    """Reset stuck episodes back to SCRAPED."""
    if request.method != "POST" or not request.user.is_staff:
        return redirect("admin:stations_system_health")

    from django.utils import timezone as tz
    stuck = Episode.stuck(threshold_minutes=60)
    count = stuck.count()
    stuck.update(status=Episode.STATUS_SCRAPED, last_error=None, status_changed_at=tz.now())
    messages.success(request, f"Reset {count} stuck episode(s) back to SCRAPED.")
    return redirect("admin:stations_system_health")


def system_health_run_extraction(request):
    """Trigger extraction task."""
    if request.method != "POST" or not request.user.is_staff:
        return redirect("admin:stations_system_health")

    from .tasks import extract_books_from_new_episodes
    extract_books_from_new_episodes.delay()
    messages.success(request, "Extraction task queued.")
    return redirect("admin:stations_system_health")


def system_health_run_scrape(request):
    """Trigger scrape task."""
    if request.method != "POST" or not request.user.is_staff:
        return redirect("admin:stations_system_health")

    from .tasks import scrape_all_brands
    scrape_all_brands.delay()
    messages.success(request, "Scrape task queued.")
    return redirect("admin:stations_system_health")


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
            "system-health/",
            admin.site.admin_view(system_health_view),
            name="stations_system_health",
        ),
        path(
            "system-health/unstick/",
            admin.site.admin_view(system_health_unstick),
            name="stations_health_unstick",
        ),
        path(
            "system-health/run-extraction/",
            admin.site.admin_view(system_health_run_extraction),
            name="stations_health_run_extraction",
        ),
        path(
            "system-health/run-scrape/",
            admin.site.admin_view(system_health_run_scrape),
            name="stations_health_run_scrape",
        ),
        path(
            "stations/extraction-evaluation/",
            admin.site.admin_view(extraction_evaluation_view),
            name="stations_extraction_evaluation",
        ),
    ]
    return custom + urls


admin.site.get_urls = _admin_get_urls_with_extraction
