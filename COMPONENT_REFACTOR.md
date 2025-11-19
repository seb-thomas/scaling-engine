# Component-Based Template Refactor

## Overview
Refactored Radio Reads to use **reusable Django components** inspired by your Figma Make design, combining Django template simplicity with component-based architecture. No build system required!

## 🎨 New Features from Figma Design

### 1. **Enhanced Visual Design**
- ✨ New wave icon logo (radio waves)
- 🎭 Manual dark mode toggle (Alpine.js powered)
- 📐 Cleaner header with centered logo
- 🎯 Sticky navigation with "Latest Books", "BBC", "NPR"
- 🖼️ Support for book cover images
- 📝 Rich book descriptions

### 2. **Component Architecture**

#### **Template Components** (`api/stations/templates/components/`)
- `book_card.html` - Reusable book card with featured variant
- `show_card.html` - Show/brand card with stats
- `pagination.html` - Smart pagination with page ranges

#### **Custom Template Tags** (`api/stations/templatetags/components.py`)
```django
{% load components %}
{% book_card book=book featured=True %}
{% show_card show=brand %}
{% pagination current_page=1 total_pages=10 url_name='stations:index' %}
```

#### **Base Layout** (`api/stations/templates/base.html`)
- Alpine.js integration (3KB)
- Dark mode with localStorage persistence
- Reusable header/footer
- Block-based content areas

### 3. **Interactive Features**
- 🌙 **Dark Mode Toggle** - Manual control with localStorage
- 🔍 **Search Button** - Ready for implementation
- 📱 **Responsive Design** - Mobile-first approach
- ⚡ **No Build Step** - Pure Django templates + Alpine.js

## 🗂️ File Structure

```
api/stations/
├── templates/
│   ├── base.html                    # NEW: Base layout with Alpine.js
│   ├── components/                  # NEW: Reusable components
│   │   ├── book_card.html          # Book display component
│   │   ├── show_card.html          # Show/brand display component
│   │   └── pagination.html         # Pagination component
│   └── stations/
│       ├── index.html              # UPDATED: Uses components
│       └── book_detail.html        # UPDATED: Uses base layout
├── templatetags/                    # NEW: Custom template tags
│   ├── __init__.py
│   └── components.py               # Component inclusion tags
└── static/stations/
    └── style.css                    # NEW: Component-based CSS
```

## 🎨 Design System

### Color Tokens
```css
--bg-primary: #ffffff / #0a0a0a
--bg-secondary: #fafafa / #1a1a1a
--text-primary: #121212 / #e5e5e5
--text-secondary: #6b6b6b / #a0a0a0
--border-color: #e5e5e5 / #2a2a2a
```

### Typography
- **Serif**: 'EB Garamond' (from Figma) / 'Libre Baskerville' (fallback)
- **Sans**: 'Inter' for body text
- Responsive font sizes with mobile breakpoints

## 📊 Database Changes

### New Book Model Fields
```python
class Book(models.Model):
    # ... existing fields ...
    description = models.TextField(blank=True, default="")      # NEW
    cover_image = models.URLField(blank=True, default="")       # NEW
```

### New Brand Model Features
```python
class Brand(models.Model):
    # ... existing fields ...
    description = models.TextField(blank=True, default="")      # NEW

    @property
    def book_count(self):                                       # NEW
        """Count of books for show cards"""
        return Book.objects.filter(episode__brand=self).count()
```

## 🚀 Next Steps

### To Apply Changes:

1. **Create migration:**
   ```bash
   docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations
   docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
   ```

2. **Restart containers (to pick up new templates):**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **View the site:**
   - Local: http://localhost:8080
   - Production: http://radioreads.fun

### Optional Enhancements:

1. **Add Book Descriptions**
   - Enhance AI extraction to pull book descriptions
   - Or manually add for featured books

2. **Add Book Cover Images**
   - Integrate Google Books API
   - Or use Open Library covers
   - Example: `https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg`

3. **Implement Search**
   - Add search form that triggers Alpine.js event
   - Create search view with filtering

4. **Add Show Pages**
   - Create `brand_detail.html` view
   - List all books from a specific show
   - Use `show_card` component on homepage

5. **Add Station Pages**
   - Create `station_detail.html` view
   - Show all brands from BBC/NPR
   - List books by station

## 💡 Nice Content from Figma

Your Figma design included these great examples that we've now enabled:

### Rich Book Data
- **Titles**: "Tomorrow, and Tomorrow, and Tomorrow"
- **Authors**: "Gabrielle Zevin"
- **Descriptions**: "A novel about two friends who build video games together, exploring creativity, identity, and the profound connections between art and life."
- **Cover Images**: Unsplash placeholder examples
- **Episode Context**: "The Art of Game Design in Literature"
- **Dates**: "November 15, 2024"

### Show/Brand Data
- **Front Row**: "BBC Radio 4's daily arts and culture programme" (1,247 books)
- **Fresh Air**: "Interviews with today's most compelling personalities" (2,134 books)
- **Bookclub**: "Monthly books discussion programme" (456 books)

### Visual Hierarchy
- Featured first book with image + full description
- Standard books with title, author, meta
- Show cards with book counts
- Clean pagination with page numbers

## 🎯 Benefits

### For Users:
- ✅ **Better UX** - Dark mode, rich content, images
- ✅ **More Context** - Descriptions, show info, book counts
- ✅ **Modern Design** - Clean, NY Times-inspired aesthetic

### For Developers:
- ✅ **Reusable Components** - DRY principle
- ✅ **No Build Step** - Simple deployment
- ✅ **Easy to Extend** - Add components as needed
- ✅ **Type Safety** - Python-based (no TypeScript needed)
- ✅ **Server-Side** - SEO friendly, fast initial load

## 📚 Usage Examples

### Using Components in Templates

```django
{% extends "base.html" %}
{% load components %}

{% block content %}
<div class="container">
    {# Render a featured book #}
    {% book_card book=featured_book featured=True %}

    {# Render standard books #}
    {% for book in books %}
        {% book_card book=book %}
    {% endfor %}

    {# Render show cards in grid #}
    <div class="grid grid--4">
        {% for brand in brands %}
            {% show_card show=brand %}
        {% endfor %}
    </div>

    {# Render pagination #}
    {% pagination current_page=page_obj.number total_pages=page_obj.paginator.num_pages %}
</div>
{% endblock %}
```

### Creating New Components

1. Create template in `templates/components/my_component.html`
2. Add template tag in `templatetags/components.py`:
   ```python
   @register.inclusion_tag('components/my_component.html')
   def my_component(param1, param2=None):
       return {'param1': param1, 'param2': param2}
   ```
3. Use in templates: `{% my_component param1=value %}`

## 🎉 Summary

You now have:
- ✅ **Component-based templates** (like React, but Django!)
- ✅ **Dark mode** (Alpine.js powered)
- ✅ **Rich content support** (descriptions, images)
- ✅ **Modern design** (Figma-inspired)
- ✅ **Simple deployment** (no build step!)
- ✅ **Reusable patterns** (DRY code)

**Best of both worlds**: React's component philosophy + Django's simplicity! 🚀
