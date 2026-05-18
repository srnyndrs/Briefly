# Briefly Admin Portal - Copilot Instructions

## Project Overview
Lightweight React + TypeScript admin portal for managing feeds and sources with Vite as the build tool. This is a modern, UX-friendly interface for the Briefly content aggregation system.

## Architecture

### Tech Stack
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool & dev server
- **React Router v6**: Client-side routing
- **TanStack Query (React Query)**: Server state management & caching
- **Zustand**: Client state management
- **Axios**: HTTP client

### Directory Structure
```
src/
  ├── components/       # Reusable UI components
  │   ├── Layout/      # Main layout wrapper
  │   ├── Sidebar/     # Navigation sidebar
  │   ├── Header/      # Page header
  │   ├── FeedForm/    # Feed creation/edit form
  │   └── SourceForm/  # Source creation/edit form
  ├── pages/           # Page components
  │   ├── Dashboard/   # Overview & statistics
  │   ├── Feeds/       # Feeds management
  │   └── Sources/     # Sources management
  ├── hooks/           # Custom React hooks
  │   └── useApi/      # API query/mutation hooks
  ├── api/
  │   └── client.ts    # Axios configuration & API endpoints
  ├── stores/
  │   └── admin.ts     # Zustand state management
  ├── types/
  │   └── index.ts     # TypeScript type definitions
  └── styles/
      └── index.css    # Global styles
```

## API Integration

### Environment Variables
- `VITE_API_URL`: Backend API base URL (defaults to http://localhost:3000/api)

### API Endpoints Used
- `GET/POST /feeds` - List & create feeds
- `GET/PUT/DELETE /feeds/{id}` - Feed CRUD
- `PATCH /feeds/{id}/status` - Toggle feed status
- `GET/POST /sources` - List & create sources  
- `GET/PUT/DELETE /sources/{id}` - Source CRUD
- `PATCH /sources/{id}/status` - Toggle source status

## Development Commands

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler

## Key Features

✅ **Dashboard**: Overview with statistics and recent activity
✅ **Feeds Management**: CRUD operations, status management, URL preview
✅ **Sources Management**: Organize feeds by source
✅ **Responsive Design**: Works on desktop and tablet
✅ **Error Handling**: Graceful error states and user feedback
✅ **State Management**: React Query for server state, Zustand for UI state
✅ **Type Safety**: Full TypeScript coverage

## Styling Approach

- **CSS-in-JS**: Inline styles for component-scoped styling
- **Design System**: Purple gradient theme (#667eea, #764ba2)
- **Responsive Grid**: Auto-responsive layouts
- **Smooth Transitions**: 0.2-0.3s easing for interactive elements

## Next Steps

1. Connect backend API (update VITE_API_URL)
2. Implement authentication/authorization
3. Add pagination for feed/source lists
4. Enhance error handling with toast notifications
5. Add search/filter functionality
6. Implement feed refresh scheduling
7. Add bulk operations (select multiple, batch delete)
