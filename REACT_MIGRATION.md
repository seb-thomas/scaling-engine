# React Migration Guide

This document describes the migration from Django templates to React + TypeScript with SSR.

## Architecture

### Frontend (React)
- **Location**: `frontend/`
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router
- **SSR**: Express server with React Router SSR
- **Styling**: Tailwind CSS

### Backend (Django)
- **API**: Django REST Framework
- **Endpoints**: `/api/stations/`, `/api/brands/`, `/api/books/`
- **Templates**: Still available for backward compatibility

## Key Changes

### 1. API Endpoints

New REST API endpoints:
- `GET /api/stations/` - List all stations
- `GET /api/stations/?station_id=<id>` - Get station by ID
- `GET /api/brands/` - List all shows/brands
- `GET /api/brands/?station_id=<id>` - Get shows by station
- `GET /api/brands/<id>/` - Get show details
- `GET /api/books/` - List all books (paginated)
- `GET /api/books/?episode__brand=<id>` - Get books by show
- `GET /api/books/<id>/` - Get book details

### 2. Component Structure

All components match the Figma design:
- `Layout` - Header, navigation, footer
- `HomePage` - Latest books + All shows
- `StationPage` - Station detail with shows
- `ShowPage` - Show detail with books
- `BookDetailPage` - Book detail page
- `BookCard` - Book card component (featured & regular)
- `ShowCard` - Show card with wave pattern
- `Pagination` - Pagination component
- `Breadcrumbs` - Navigation breadcrumbs

### 3. Routing

React Router routes:
- `/` - HomePage
- `/station/:stationId` - StationPage
- `/show/:showId` - ShowPage
- `/book/:bookId` - BookDetailPage

### 4. SSR Setup

The SSR server:
- Renders React components server-side
- Proxies API requests to Django
- Serves static assets
- Handles all routes for SEO

## Running Locally

### Development (Client-side only)

```bash
cd frontend
bun install
bun run dev
```

Visit `http://localhost:5173`

### Development (SSR)

```bash
cd frontend
bun install
bun run ssr:dev
```

Visit `http://localhost:3000`

Make sure Django API is running on `http://localhost:8000`

### Production Build

```bash
cd frontend
bun run ssr:build
bun run ssr:start
```

## Docker Deployment

Use `docker-compose.react.yml`:

```bash
docker-compose -f docker-compose.react.yml up --build
```

This will:
1. Build Django API
2. Build React frontend
3. Run SSR server
4. Configure Nginx to route:
   - `/api/*` → Django
   - `/*` → React SSR

## Environment Variables

### Frontend
- `VITE_API_URL` - API base URL (default: `/api`)
- `API_URL` - API URL for SSR server (default: `http://localhost:8000`)
- `PORT` - SSR server port (default: `3000`)

### Django
- `CORS_ALLOWED_ORIGINS` - Add `http://frontend:3000` for Docker

## Migration Status

✅ All components converted from Figma
✅ SSR server configured
✅ API endpoints created
✅ Docker setup ready
✅ TypeScript types defined
✅ Tailwind CSS configured

## Next Steps

1. Test locally with `bun run ssr:dev`
2. Update Nginx config to use `nginx.conf.react`
3. Deploy with `docker-compose.react.yml`
4. Remove Django templates once confirmed working

