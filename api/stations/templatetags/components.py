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


@register.inclusion_tag('components/breadcrumbs.html')
def breadcrumbs(items):
    """
    Renders breadcrumb navigation component

    Args:
        items: List of dicts with 'label' and optional 'href' keys
    """
    return {
        'items': items
    }


@register.inclusion_tag('components/pagination.html')
def pagination(current_page, total_pages, url_name='stations:index', show_id=None):
    """
    Renders pagination component

    Args:
        current_page: Current page number
        total_pages: Total number of pages
        url_name: URL name for pagination links
        show_id: Optional show ID for show_detail URL
    """
    # Generate page range with ellipsis (max 7 pages shown)
    pages = []
    if total_pages <= 7:
        pages = list(range(1, total_pages + 1))
    else:
        if current_page <= 4:
            pages = list(range(1, 6)) + [-1, total_pages]
        elif current_page >= total_pages - 3:
            pages = [1, -1] + list(range(total_pages - 4, total_pages + 1))
        else:
            pages = [1, -1, current_page - 1, current_page, current_page + 1, -1, total_pages]

    return {
        'current_page': current_page,
        'total_pages': total_pages,
        'pages': pages,
        'has_previous': current_page > 1,
        'has_next': current_page < total_pages,
        'previous_page': current_page - 1 if current_page > 1 else None,
        'next_page': current_page + 1 if current_page < total_pages else None,
        'url_name': url_name,
        'show_id': show_id
    }
