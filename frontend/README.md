# Radio Reads Frontend

React + TypeScript frontend with SSR using Vite and React Router.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **React Router v7** for routing with file-based routing
- **Tailwind CSS** for styling
- **Bun** for SSR server (replaces Express/Node.js)
- **Lucide React** for icons

## Development

### Prerequisites

- **Bun** latest version ([install Bun](https://bun.sh))
- Django API running on `http://localhost:8000`

### Setup

```bash
bun install
```

### Run Development Server (Client-side only)

```bash
bun run dev
```

This runs Vite dev server on `http://localhost:5173`

### Run SSR Development Server

```bash
bun run ssr:dev
```

This runs the Bun SSR server on `http://localhost:3000`

## Building

### Build for Production

```bash
bun run ssr:build
```

This creates:
- `build/client/` - Client-side bundle (React Router v7)
- `dist-ssr/` - SSR server bundle (Bun)

### Run Production SSR Server

```bash
bun run ssr:start
```

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client functions
│   ├── components/    # React components
│   │   ├── ui/        # UI primitives (Button, etc.)
│   │   └── ...        # Feature components
│   ├── pages/         # Page components
│   ├── lib/           # Utilities
│   ├── types.ts       # TypeScript types
│   ├── App.tsx        # Main app component
│   └── main.tsx       # Client entry point
├── server.tsx         # SSR server
├── index.html         # HTML template
└── vite.config.ts     # Vite configuration
```

## API Integration

The frontend connects to the Django REST API. Set the API URL via:

- Environment variable: `VITE_API_URL` (defaults to `/api`)
- SSR server: `API_URL` environment variable (defaults to `http://localhost:8000`)

## Docker

The frontend is containerized and can be run with:

```bash
docker-compose -f docker-compose.react.yml up
```

This will:
- Build the React app
- Run the Bun SSR server on port 3000
- Proxy API requests to Django backend
- Serve static assets

## Features

- ✅ Server-Side Rendering (SSR) with Bun
- ✅ React Router v7 file-based routing
- ✅ Client-side routing with React Router
- ✅ Dark mode support
- ✅ Responsive design
- ✅ TypeScript for type safety
- ✅ Tailwind CSS for styling
- ✅ Matches Figma design exactly

## Migration Notes

This project migrated from Express/Node.js to Bun for:
- **Faster runtime performance**
- **Native TypeScript support** (no ts-node needed)
- **Built-in HTTP server** (no Express needed)
- **Simplified architecture**

