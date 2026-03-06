import json

from django.contrib import admin
from django.db import models as db_models
from django.utils.html import format_html, escape
from django.urls import reverse, path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.conf import settings as django_settings

from .models import Station, Brand, Episode, Book, Phrase, Topic


class BookInline(admin.TabularInline):
    """Inline display of books for an episode"""

    model = Book.episodes.through
    extra = 0
    readonly_fields = ("book_title", "book_author", "view_link")
    fields = ("book_title", "book_author", "view_link")
    verbose_name = "Book"
    verbose_name_plural = "Books"
    can_delete = False

    def book_title(self, obj):
        return obj.book.title

    book_title.short_description = "Title"

    def book_author(self, obj):
        return obj.book.author

    book_author.short_description = "Author"

    def view_link(self, obj):
        if obj.book_id:
            url = reverse("admin:stations_book_change", args=[obj.book_id])
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
        "stage_display",
    )
    list_filter = ("stage", "brand", "aired_at")
    search_fields = ("title", "url")
    readonly_fields = (
        "has_book",
        "slug",
        "pipeline_display",
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
                "fields": ("pipeline_display",),
            },
        ),
    )

    def book_count(self, obj):
        """Display count of books"""
        count = obj.books.count()
        return f"{count} book{'s' if count != 1 else ''}" if count > 0 else "-"

    book_count.short_description = "Books"

    def stage_display(self, obj):
        """Colour-coded stage badge for list view."""
        colours = {
            Episode.STAGE_SCRAPED: "#999",
            Episode.STAGE_EXTRACTION_QUEUED: "#0d6efd",
            Episode.STAGE_EXTRACTING: "#0d6efd",
            Episode.STAGE_EXTRACTION_NO_BOOKS: "#aaa",
            Episode.STAGE_EXTRACTION_FAILED: "#dc3545",
            Episode.STAGE_VERIFICATION_QUEUED: "#d4a017",
            Episode.STAGE_VERIFICATION_FAILED: "#dc3545",
            Episode.STAGE_REVIEW: "#dc3545",
            Episode.STAGE_COMPLETE: "#28a745",
        }
        colour = colours.get(obj.stage, "#666")
        bold = " font-weight: bold;" if obj.stage == Episode.STAGE_REVIEW else ""
        label = obj.get_stage_display()
        return format_html(
            '<span style="color: {};{}">{}</span>',
            colour, bold, label,
        )

    stage_display.short_description = "Stage"
    stage_display.admin_order_field = "stage"

    def _json_block(self, data):
        """Render a JSON dict as a formatted, readable block."""
        if not data:
            return "<em>No data</em>"
        formatted = escape(json.dumps(data, indent=2, ensure_ascii=False))
        return (
            '<pre style="white-space: pre-wrap; word-break: break-word; '
            'max-width: 800px; background: #f8f8f8; padding: 10px; '
            'border: 1px solid #ddd; border-radius: 4px; font-size: 12px; '
            'line-height: 1.5;">' + formatted + '</pre>'
        )

    def pipeline_display(self, obj):
        """Render the full pipeline UX: progress bar + collapsible stage sections."""
        if not obj.pk:
            return "-"

        # --- Stage-to-step mapping ---
        STEPS = [
            ("scraped", "Scraped"),
            ("extracted", "Extracted"),
            ("verified", "Verified"),
            ("complete", "Complete"),
        ]

        stage_to_step = {
            Episode.STAGE_SCRAPED: ("scraped", "current", ""),
            Episode.STAGE_EXTRACTION_QUEUED: ("extracted", "current", "Queued"),
            Episode.STAGE_EXTRACTING: ("extracted", "current", "Extracting\u2026"),
            Episode.STAGE_EXTRACTION_NO_BOOKS: ("extracted", "terminal", "No books"),
            Episode.STAGE_EXTRACTION_FAILED: ("extracted", "failed", "Failed"),
            Episode.STAGE_VERIFICATION_QUEUED: ("verified", "current", "Queued"),
            Episode.STAGE_VERIFICATION_FAILED: ("verified", "failed", "Failed"),
            Episode.STAGE_REVIEW: ("complete", "review", "Needs Review"),
            Episode.STAGE_COMPLETE: ("complete", "done", ""),
        }

        step_key, step_state, step_label = stage_to_step.get(
            obj.stage, ("scraped", "current", "")
        )
        step_order = [s[0] for s in STEPS]
        current_idx = step_order.index(step_key)

        # --- Progress bar ---
        bar_html = '<div class="pipeline-bar">'
        for i, (key, label) in enumerate(STEPS):
            if i < current_idx:
                cls = "pipeline-step done"
                icon = "\u2713"
            elif i == current_idx:
                if step_state == "done":
                    cls = "pipeline-step done"
                    icon = "\u2713"
                elif step_state == "failed":
                    cls = "pipeline-step failed"
                    icon = "\u2717"
                elif step_state == "review":
                    cls = "pipeline-step review"
                    icon = "!"
                elif step_state == "terminal":
                    cls = "pipeline-step terminal"
                    icon = "\u2014"
                else:
                    cls = "pipeline-step current"
                    icon = "\u25cf"
            else:
                cls = "pipeline-step pending"
                icon = ""

            badge = ""
            if i == current_idx and step_label:
                badge_cls = "failed" if step_state == "failed" else (
                    "review" if step_state == "review" else "info"
                )
                badge = f'<span class="pipeline-badge {badge_cls}">{escape(step_label)}</span>'

            if i > 0 and i <= current_idx:
                connector = '<div class="pipeline-connector" style="background: #28a745;"></div>'
            elif i > 0:
                connector = '<div class="pipeline-connector"></div>'
            else:
                connector = ""
            bar_html += f'{connector}<div class="{cls}">'
            bar_html += f'<div class="pipeline-circle">{icon}</div>'
            bar_html += f'<div class="pipeline-label">{label}{badge}</div>'
            bar_html += '</div>'
        bar_html += '</div>'

        # --- Collapsible sections ---
        sections_html = ""

        # 1. Scraped section
        scraped_open = "open" if current_idx == 0 else ""
        sections_html += f'<details class="pipeline-section" {scraped_open}>'
        sections_html += '<summary>Scraped Data</summary>'
        sections_html += f'<div class="pipeline-section-body">{self._json_block(obj.scraped_data)}</div>'
        sections_html += '</details>'

        # 2. Extracted section
        extracted_open = "open" if step_key == "extracted" else ""
        reprocess_url = reverse("admin:stations_episode_reprocess", args=[obj.pk])
        reprocess_btn = (
            f'<div style="margin-top: 10px;">'
            f'<a href="{reprocess_url}" class="button" '
            f'style="background-color: #417690; color: white; padding: 8px 14px; '
            f'text-decoration: none; border-radius: 4px;">Reprocess with AI</a>'
            f'<p style="margin-top: 6px; color: #666; font-size: 12px;">'
            f'Re-run book extraction on this episode. Replaces any existing books.</p>'
            f'</div>'
        )
        confidence_html = ""
        if obj.ai_confidence is not None:
            pct = int(obj.ai_confidence * 100)
            colour = "#28a745" if pct >= 90 else ("#d4a017" if pct >= 70 else "#dc3545")
            confidence_html = (
                f'<p><strong>AI Confidence:</strong> '
                f'<span style="color: {colour}; font-weight: bold;">{pct}%</span></p>'
            )
        processed_html = ""
        if obj.processed_at:
            processed_html = f'<p><strong>Processed at:</strong> {escape(str(obj.processed_at))}</p>'
        error_html = ""
        if obj.last_error:
            error_html = (
                f'<p style="color: #dc3545;"><strong>Error:</strong> {escape(obj.last_error)}</p>'
            )

        sections_html += f'<details class="pipeline-section" {extracted_open}>'
        sections_html += '<summary>Extraction</summary>'
        sections_html += '<div class="pipeline-section-body">'
        sections_html += confidence_html + processed_html + error_html
        sections_html += self._json_block(obj.extraction_result)
        sections_html += reprocess_btn
        sections_html += '</div></details>'

        # 3. Verified section
        verified_open = "open" if step_key == "verified" else ""
        books = obj.books.all()
        if books.exists():
            book_summary = '<table style="width: 100%; border-collapse: collapse; margin-top: 6px;">'
            book_summary += '<tr style="border-bottom: 1px solid #ddd;"><th style="text-align:left; padding: 4px;">Title</th><th style="text-align:left; padding: 4px;">Author</th><th style="text-align:left; padding: 4px;">Status</th></tr>'
            for book in books:
                status_colours = {
                    "verified": "#28a745",
                    "not_found": "#dc3545",
                    "pending": "#d4a017",
                }
                sc = status_colours.get(book.verification_status, "#666")
                book_url = reverse("admin:stations_book_change", args=[book.pk])
                book_summary += (
                    f'<tr style="border-bottom: 1px solid #eee;">'
                    f'<td style="padding: 4px;"><a href="{book_url}">{escape(book.title)}</a></td>'
                    f'<td style="padding: 4px;">{escape(book.author)}</td>'
                    f'<td style="padding: 4px;"><span style="color: {sc};">{escape(book.verification_status)}</span></td>'
                    f'</tr>'
                )
            book_summary += '</table>'
        else:
            book_summary = '<p style="color: #666;"><em>No books extracted</em></p>'

        sections_html += f'<details class="pipeline-section" {verified_open}>'
        sections_html += '<summary>Verification</summary>'
        sections_html += f'<div class="pipeline-section-body">{book_summary}</div>'
        sections_html += '</details>'

        # 4. Complete / Review section
        complete_open = "open" if step_key == "complete" else ""
        complete_body = f'<p><strong>Current stage:</strong> {escape(obj.get_stage_display())}</p>'
        if obj.stage == Episode.STAGE_REVIEW:
            mark_url = reverse("admin:stations_episode_mark_complete", args=[obj.pk])
            complete_body += (
                f'<form method="post" action="{mark_url}" style="margin-top: 10px;">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="CSRF_PLACEHOLDER">'
                f'<button type="submit" class="button" '
                f'style="background-color: #28a745; color: white; padding: 8px 14px; '
                f'border: none; border-radius: 4px; cursor: pointer;">'
                f'Mark as Complete</button>'
                f'<p style="margin-top: 6px; color: #666; font-size: 12px;">'
                f'Confirm this episode\'s books are correct and mark it as reviewed.</p>'
                f'</form>'
            )

        sections_html += f'<details class="pipeline-section" {complete_open}>'
        sections_html += '<summary>Complete</summary>'
        sections_html += f'<div class="pipeline-section-body">{complete_body}</div>'
        sections_html += '</details>'

        return mark_safe(bar_html + sections_html)

    pipeline_display.short_description = "Pipeline"

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
            path(
                "<int:episode_id>/mark-complete/",
                self.admin_site.admin_view(self.mark_episode_complete),
                name="stations_episode_mark_complete",
            ),
        ]
        return custom_urls + urls

    def episode_status_json(self, request, episode_id):
        """Return episode status as JSON for polling."""
        from django.http import JsonResponse

        episode = Episode.objects.get(pk=episode_id)
        return JsonResponse({"status": episode.stage})

    def reprocess_episode(self, request, episode_id):
        """Reprocess a single episode: set QUEUED and enqueue AI extraction."""
        from .tasks import ai_extract_books_task

        episode = Episode.objects.get(pk=episode_id)

        if episode.stage in (Episode.STAGE_EXTRACTION_QUEUED, Episode.STAGE_EXTRACTING):
            messages.warning(request, "Already processing — please wait.")
            return redirect(
                reverse("admin:stations_episode_change", args=[episode_id])
                + "?awaiting_reprocess=1"
            )

        from django.utils import timezone as tz
        episode.stage = Episode.STAGE_SCRAPED
        episode.last_error = None
        episode.status_changed_at = tz.now()
        episode.save(update_fields=["stage", "last_error", "status_changed_at"])
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
            episode.stage = Episode.STAGE_SCRAPED
            episode.last_error = None
            episode.status_changed_at = tz.now()
            episode.save(update_fields=["stage", "last_error", "status_changed_at"])
            ai_extract_books_task.delay(episode.id)
        count = queryset.count()
        msg = f"Queued extraction for {count} episode(s)."
        flower_url = getattr(django_settings, "FLOWER_URL", "") or ""
        if flower_url:
            msg = format_html('{} <a href="{}" target="_blank">Open Flower</a>', msg, flower_url)
        self.message_user(request, msg)

    def mark_episode_complete(self, request, episode_id):
        """Mark an episode as complete from the episode detail page."""
        if request.method != "POST":
            return redirect(reverse("admin:stations_episode_change", args=[episode_id]))
        episode = Episode.objects.get(pk=episode_id)
        episode.stage = Episode.STAGE_COMPLETE
        episode.save(update_fields=["stage"])
        messages.success(request, f"'{episode.title[:50]}' marked as complete.")
        return redirect(reverse("admin:stations_episode_change", args=[episode_id]))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_reprocess_button"] = True
        extra_context["awaiting_reprocess"] = "awaiting_reprocess" in request.GET
        extra_context["status_url"] = reverse(
            "admin:stations_episode_status", args=[object_id]
        )
        episode = Episode.objects.get(pk=object_id)
        if episode.stage == Episode.STAGE_REVIEW:
            extra_context["show_mark_complete"] = True
            extra_context["mark_complete_url"] = reverse(
                "admin:stations_episode_mark_complete", args=[object_id]
            )
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "topic_list", "episode_brand", "gb_status", "cover_preview_small", "cover_error_short")
    list_filter = ("topics", "episodes__brand", "verification_status")
    filter_horizontal = ("topics",)
    search_fields = ("title", "author", "description")
    readonly_fields = ("slug", "cover_preview_large", "refetch_cover_button", "verify_book_button", "verification_status", "verification_checked_at", "cover_fetch_error", "episode_list")
    fieldsets = (
        ("Book Information", {"fields": ("title", "author", "topics", "slug", "description", "verification_status", "verification_checked_at", "verify_book_button")}),
        (
            "Cover Image",
            {
                "fields": ("cover_preview_large", "cover_image", "cover_fetch_error", "refetch_cover_button"),
            },
        ),
        ("Links", {"fields": ("purchase_link",)}),
        ("Episodes", {"fields": ("episode_list",)}),
    )

    def topic_list(self, obj):
        return ", ".join(t.name for t in obj.topics.all()) or "-"

    topic_list.short_description = "Topics"

    def episode_brand(self, obj):
        episode = obj.episodes.select_related("brand").first()
        if episode and episode.brand:
            return episode.brand.name
        return "-"

    episode_brand.short_description = "Show"

    def episode_list(self, obj):
        if not obj.pk:
            return "-"
        episodes = obj.episodes.select_related("brand").order_by("-aired_at")[:20]
        if not episodes:
            return format_html("<em>No episodes</em>")
        links = []
        for ep in episodes:
            url = reverse("admin:stations_episode_change", args=[ep.pk])
            brand = ep.brand.name if ep.brand else "?"
            date = ep.aired_at.strftime("%-d %b %Y") if ep.aired_at else ""
            links.append(format_html(
                '<a href="{}">{}</a> <span style="color:#666">({}{})</span>',
                url, ep.title[:80], brand, f", {date}" if date else "",
            ))
        html = "<br>".join(links)
        total = obj.episodes.count()
        if total > 20:
            html += format_html("<br><em>… and {} more</em>", total - 20)
        return mark_safe(html)

    episode_list.short_description = "Episodes"

    def gb_status(self, obj):
        if obj.verification_status == Book.VERIFICATION_VERIFIED:
            return format_html('<span style="color: #28a745;">Verified</span>')
        if obj.verification_status == Book.VERIFICATION_NOT_FOUND:
            return format_html('<span style="color: #dc3545;">Not found</span>')
        return format_html('<span style="color: #d4a017;">Pending</span>')

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

    def verify_book_button(self, obj):
        if not obj.pk or obj.verification_status != Book.VERIFICATION_PENDING:
            return "-"
        url = reverse("admin:stations_book_verify", args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="padding: 6px 12px;">Verify now</a>'
            '<p style="margin-top: 6px; color: #666; font-size: 12px;">'
            'Look up on Google Books and verify this book.</p>', url)

    verify_book_button.short_description = "Verify"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:book_id>/refetch-cover/",
                self.admin_site.admin_view(self.refetch_cover),
                name="stations_book_refetch_cover",
            ),
            path(
                "<int:book_id>/verify/",
                self.admin_site.admin_view(self.verify_book),
                name="stations_book_verify",
            ),
        ]
        return custom_urls + urls

    def refetch_cover(self, request, book_id):
        """Refetch cover for a single book via Google Books."""
        from .utils import verify_book_exists, GoogleBooksRateLimited
        from .ai_utils import download_and_save_cover

        book = Book.objects.get(pk=book_id)
        try:
            book_info = verify_book_exists(book.title, book.author)
        except GoogleBooksRateLimited:
            messages.error(request, "Google Books rate limit hit. Try again in a few minutes.")
            return redirect(reverse("admin:stations_book_change", args=[book_id]))

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

    def verify_book(self, request, book_id):
        """Verify a single book via Google Books."""
        from .utils import verify_book_exists, generate_bookshop_affiliate_url, GoogleBooksRateLimited
        from .ai_utils import download_and_save_cover
        from django.utils import timezone as tz

        book = Book.objects.get(pk=book_id)
        try:
            book_info = verify_book_exists(book.title, book.author)
        except GoogleBooksRateLimited:
            messages.error(request, "Google Books rate limit hit. Try again in a few minutes.")
            return redirect(reverse("admin:stations_book_change", args=[book_id]))

        book.verification_checked_at = tz.now()

        if book_info.get("exists"):
            book.verification_status = Book.VERIFICATION_VERIFIED
            # Download cover if available and not already present
            cover_url = book_info.get("cover_url") or ""
            if cover_url and not book.cover_image:
                download_and_save_cover(book, cover_url, allow_fallback=True)
            # Set purchase link if not already present
            if not book.purchase_link:
                book.purchase_link = generate_bookshop_affiliate_url(book.title, book.author)
            book.save(update_fields=["verification_status", "verification_checked_at", "purchase_link"])
            messages.success(request, f"'{book.title}' verified on Google Books.")
        else:
            book.verification_status = Book.VERIFICATION_NOT_FOUND
            book.save(update_fields=["verification_status", "verification_checked_at"])
            messages.warning(request, f"'{book.title}' not found on Google Books.")

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
        book_count = Book.objects.filter(episodes__brand=obj).distinct().count()
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


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "book_count")

    def book_count(self, obj):
        return obj.book_set.count()

    book_count.short_description = "Books"

    def changelist_view(self, request, extra_context=None):
        from collections import Counter

        counts = Counter()
        for val in (
            Book.objects.exclude(unmatched_topics="")
            .values_list("unmatched_topics", flat=True)
        ):
            for slug in val.split(","):
                slug = slug.strip()
                if slug:
                    counts[slug] += 1

        extra_context = extra_context or {}
        # Sort by count descending
        extra_context["unmatched_topics"] = sorted(
            counts.items(), key=lambda x: -x[1]
        )
        return super().changelist_view(request, extra_context)


# Register remaining models with default admin
admin.site.register([Station, Phrase])


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
    stuck.update(stage=Episode.STAGE_SCRAPED, last_error=None, status_changed_at=tz.now())
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


def system_health_run_verification(request):
    """Trigger verification task."""
    if request.method != "POST" or not request.user.is_staff:
        return redirect("admin:stations_system_health")

    from .tasks import verify_pending_books
    verify_pending_books.delay()
    messages.success(request, "Verification task queued.")
    return redirect("admin:stations_system_health")


def review_queue_view(request):
    """Standalone page showing episodes that need human review."""
    if not request.user.is_staff:
        from django.contrib.admin.sites import site as default_admin_site
        return redirect(default_admin_site.login_url)

    episodes = (
        Episode.objects.filter(stage=Episode.STAGE_REVIEW)
        .select_related("brand")
        .prefetch_related("books")
        .order_by("-aired_at")
    )

    rows = []
    for ep in episodes:
        reasons = []
        if ep.ai_confidence is not None and ep.ai_confidence < 0.9:
            reasons.append(f"Low confidence ({int(ep.ai_confidence * 100)}%)")
        not_found_books = ep.books.filter(verification_status=Book.VERIFICATION_NOT_FOUND)
        if not_found_books.exists():
            reasons.append("Book not found on Google Books")

        books_info = []
        for book in ep.books.all():
            books_info.append({
                "title": book.title,
                "author": book.author,
                "status": book.verification_status,
                "admin_url": reverse("admin:stations_book_change", args=[book.pk]),
            })

        rows.append({
            "brand": ep.brand.name if ep.brand else "?",
            "title": ep.title,
            "aired_at": ep.aired_at,
            "admin_url": reverse("admin:stations_episode_change", args=[ep.pk]),
            "episode_url": ep.url or "",
            "mark_reviewed_url": reverse("admin:stations_episode_mark_reviewed", args=[ep.pk]),
            "books": books_info,
            "reasons": reasons,
        })

    context = {
        **admin.site.each_context(request),
        "title": "Review Queue",
        "rows": rows,
    }
    return render(request, "admin/stations/review_queue.html", context)


def mark_episode_reviewed(request, episode_id):
    """Mark an episode as reviewed from the review queue."""
    if request.method != "POST" or not request.user.is_staff:
        return redirect("admin:stations_review_queue")
    episode = Episode.objects.get(pk=episode_id)
    episode.stage = Episode.STAGE_COMPLETE
    episode.save(update_fields=["stage"])
    messages.success(request, f"'{episode.title[:50]}' marked as complete.")
    return redirect("admin:stations_review_queue")


def extraction_evaluation_view(request):
    """Model evaluation dashboard: show books with input to AI, reasoning, and verify link."""
    from django.contrib.admin.sites import site as default_admin_site

    if not request.user.is_staff:
        return redirect(default_admin_site.login_url)

    books = (
        Book.objects.prefetch_related("episodes", "episodes__brand")
        .annotate(latest_aired=db_models.Max("episodes__aired_at"))
        .order_by("-latest_aired", "-id")[:200]
    )

    rows = []
    for book in books:
        episode = book.episodes.first()
        if not episode:
            continue
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
            "system-health/run-verification/",
            admin.site.admin_view(system_health_run_verification),
            name="stations_health_run_verification",
        ),
        path(
            "review-queue/",
            admin.site.admin_view(review_queue_view),
            name="stations_review_queue",
        ),
        path(
            "review-queue/<int:episode_id>/mark-reviewed/",
            admin.site.admin_view(mark_episode_reviewed),
            name="stations_episode_mark_reviewed",
        ),
        path(
            "stations/extraction-evaluation/",
            admin.site.admin_view(extraction_evaluation_view),
            name="stations_extraction_evaluation",
        ),
    ]
    return custom + urls


admin.site.get_urls = _admin_get_urls_with_extraction
