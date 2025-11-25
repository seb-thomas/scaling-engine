from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from .models import Station, Brand, Episode, Book, Phrase, RawEpisodeData


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


class RawEpisodeDataInline(admin.StackedInline):
    """Inline display of raw episode data"""
    model = RawEpisodeData
    extra = 0
    fields = ("processed", "processed_at", "created_at", "scraped_data_preview")
    readonly_fields = ("processed", "processed_at", "created_at", "scraped_data_preview")
    can_delete = False

    def scraped_data_preview(self, obj):
        """Show a preview of the scraped data"""
        if not obj.scraped_data:
            return "-"

        import json
        data = obj.scraped_data
        preview = f"<strong>Title:</strong> {data.get('title', 'N/A')}<br>"
        preview += f"<strong>Date:</strong> {data.get('date_text', 'N/A')}<br>"
        preview += f"<strong>Description:</strong> {data.get('description', 'N/A')}<br>"
        preview += f"<strong>URL:</strong> <a href=\"{data.get('url')}\" target=\"_blank\">{data.get('url')}</a>"
        return format_html(preview)

    scraped_data_preview.short_description = "Scraped Data"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "aired_at", "has_book", "book_count", "raw_data_status")
    list_filter = ("has_book", "brand", "aired_at")
    search_fields = ("title", "url")
    readonly_fields = ("has_book", "slug", "book_links_readonly", "raw_data_link_readonly")
    date_hierarchy = "aired_at"
    inlines = [BookInline, RawEpisodeDataInline]

    fieldsets = (
        ("Episode Information", {
            "fields": ("brand", "title", "slug", "url", "aired_at", "has_book")
        }),
        ("Related Data", {
            "fields": ("book_links_readonly", "raw_data_link_readonly")
        }),
    )

    def book_count(self, obj):
        """Display count of books"""
        count = obj.book_set.count()
        return f"{count} book{'s' if count != 1 else ''}" if count > 0 else "-"

    book_count.short_description = "Books"

    def raw_data_status(self, obj):
        """Display raw data processing status"""
        if hasattr(obj, "raw_data") and obj.raw_data:
            status = "✅" if obj.raw_data.processed else "⏳"
            return format_html(status)
        return "-"

    raw_data_status.short_description = "Status"

    def book_links_readonly(self, obj):
        """Display links to related books (readonly)"""
        books = obj.book_set.all()
        if not books:
            return format_html('<em>No books detected</em>')

        links = []
        for book in books:
            url = reverse("admin:stations_book_change", args=[book.pk])
            links.append(f'<a href="{url}" target="_blank">{book.title}</a>')

        return format_html("<br>".join(links))

    book_links_readonly.short_description = "Books"

    def raw_data_link_readonly(self, obj):
        """Display link to raw episode data (readonly)"""
        if hasattr(obj, "raw_data") and obj.raw_data:
            url = reverse("admin:stations_rawepisodedata_change", args=[obj.raw_data.pk])
            status = "Processed" if obj.raw_data.processed else "Unprocessed"
            return format_html('<a href="{}" target="_blank">View Raw Data ({})</a>', url, status)
        return format_html('<em>No raw data</em>')

    raw_data_link_readonly.short_description = "Raw Data"

    def get_urls(self):
        """Add custom URL for reprocessing"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:episode_id>/reprocess/',
                self.admin_site.admin_view(self.reprocess_episode),
                name='stations_episode_reprocess',
            ),
        ]
        return custom_urls + urls

    def reprocess_episode(self, request, episode_id):
        """Reprocess a single episode (reset and trigger AI extraction)"""
        from .tasks import ai_extract_books_task

        episode = Episode.objects.get(pk=episode_id)

        # Reset processed flag if raw_data exists
        if hasattr(episode, "raw_data") and episode.raw_data:
            episode.raw_data.processed = False
            episode.raw_data.processed_at = None
            episode.raw_data.save(update_fields=["processed", "processed_at"])

        # Trigger AI extraction
        ai_extract_books_task.delay(episode_id)

        messages.success(request, f'Triggered AI extraction for "{episode.title}". Check results in a few seconds.')
        return redirect('admin:stations_episode_change', episode_id)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add reprocess button to change view"""
        extra_context = extra_context or {}
        extra_context['show_reprocess_button'] = True
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(RawEpisodeData)
class RawEpisodeDataAdmin(admin.ModelAdmin):
    list_display = ("episode_title", "processed", "processed_at", "created_at", "episode_link")
    list_filter = ("processed", "created_at", "processed_at")
    search_fields = ("episode__title",)
    readonly_fields = ("created_at", "processed_at")
    actions = ["reprocess_episodes"]

    def episode_title(self, obj):
        return obj.episode.title

    episode_title.short_description = "Episode"

    def episode_link(self, obj):
        """Display link to episode"""
        url = reverse("admin:stations_episode_change", args=[obj.episode.pk])
        return format_html('<a href="{}">View Episode</a>', url)

    episode_link.short_description = "Episode"

    @admin.action(description="Reprocess selected episodes (run AI extraction)")
    def reprocess_episodes(self, request, queryset):
        """Reprocess selected raw episode data (trigger AI extraction)"""
        from .tasks import ai_extract_books_task

        count = 0
        for raw_data in queryset:
            # Reset processed flag
            raw_data.processed = False
            raw_data.processed_at = None
            raw_data.save(update_fields=["processed", "processed_at"])

            # Trigger AI extraction
            ai_extract_books_task.delay(raw_data.episode.id)
            count += 1

        self.message_user(
            request, f"Triggered AI extraction for {count} episode(s). Check Celery logs for progress."
        )


# Register remaining models with default admin
admin.site.register([Station, Brand, Book, Phrase])
