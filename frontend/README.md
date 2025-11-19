# Radio Reads Frontend

React + TypeScript frontend with SSR using Vite and React Router.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **React Router** for routing
- **Tailwind CSS** for styling
- **Express** for SSR server
- **Lucide React** for icons

## Development

### Prerequisites

- Node.js 20+
- Django API running on `http://localhost:8000`

### Setup

```bash
npm install
```

### Run Development Server (Client-side only)

```bash
npm run dev
```

This runs Vite dev server on `http://localhost:5173`

### Run SSR Development Server

```bash
npm run ssr:dev
```

This runs the Express SSR server on `http://localhost:3000`

## Building

### Build for Production

```bash
npm run build
npm run ssr:build
```

This creates:
- `dist/` - Client-side bundle
- `dist-ssr/` - SSR server bundle

### Run Production SSR Server

```bash
npm run ssr:start
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
- Run the SSR server on port 3000
- Proxy API requests to Django backend
- Serve static assets

## Features

- ✅ Server-Side Rendering (SSR)
- ✅ Client-side routing with React Router
- ✅ Dark mode support
- ✅ Responsive design
- ✅ TypeScript for type safety
- ✅ Tailwind CSS for styling
- ✅ Matches Figma design exactly

