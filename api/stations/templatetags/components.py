"""
Reusable component template tags for Radio Reads
"""
from django import template

register = template.Library()


@register.inclusion_tag('components/book_card.html')
def book_card(book, featured=False):
    """
    Renders a book card component

    Args:
        book: Book instance
        featured: Boolean to render as featured/hero card (default: False)
    """
    return {
        'book': book,
        'featured': featured
    }


@register.inclusion_tag('components/show_card.html')
def show_card(show):
    """
    Renders a show card component

    Args:
        show: Brand instance (show)
    """
    return {
        'show': show
    }


@register.inclusion_tag('components/pagination.html')
def pagination(current_page, total_pages, url_name='stations:index'):
    """
    Renders pagination component

    Args:
        current_page: Current page number
        total_pages: Total number of pages
        url_name: URL name for pagination links
    """
    # Generate page range (show max 5 pages at a time)
    page_range = []
    if total_pages <= 5:
        page_range = range(1, total_pages + 1)
    else:
        if current_page <= 3:
            page_range = range(1, 6)
        elif current_page >= total_pages - 2:
            page_range = range(total_pages - 4, total_pages + 1)
        else:
            page_range = range(current_page - 2, current_page + 3)

    return {
        'current_page': current_page,
        'total_pages': total_pages,
        'page_range': page_range,
        'has_previous': current_page > 1,
        'has_next': current_page < total_pages,
        'previous_page': current_page - 1 if current_page > 1 else None,
        'next_page': current_page + 1 if current_page < total_pages else None,
        'url_name': url_name
    }
