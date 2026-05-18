# 📰 Briefly Admin Portal

A lightweight React + TypeScript admin portal for managing RSS feeds and content sources with a modern, UX-friendly interface.

## ✨ Features

- **📊 Dashboard**: Overview with statistics and recent activity
- **📑 Feeds Management**: Create, edit, delete, and manage RSS feeds
- **📚 Sources Management**: Organize and manage content sources
- **🎨 Modern UI**: Clean, intuitive interface with smooth animations
- **⚡ Fast**: Built with Vite for rapid development
- **🔄 Real-time Updates**: React Query for efficient server state management
- **📱 Responsive**: Works on desktop and tablet devices
- **🛡️ Type-Safe**: Full TypeScript coverage

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will open automatically at `http://localhost:5173`

### Build for Production

```bash
npm run build
npm run preview
```

## 📋 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build optimized production bundle |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint checks |
| `npm run type-check` | Run TypeScript compiler |

## 🏗️ Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Layout.tsx     # Main layout wrapper
│   ├── Sidebar.tsx    # Navigation sidebar
│   ├── Header.tsx     # Page header
│   ├── FeedForm.tsx   # Feed CRUD form
│   └── SourceForm.tsx # Source CRUD form
├── pages/            # Page components
│   ├── Dashboard.tsx # Overview page
│   ├── Feeds.tsx     # Feeds management page
│   └── Sources.tsx   # Sources management page
├── api/              # API integration
│   └── client.ts     # Axios client & endpoints
├── hooks/            # Custom React hooks
│   └── useApi.ts     # API query hooks
├── stores/           # State management
│   └── admin.ts      # Zustand store
├── types/            # TypeScript types
│   └── index.ts      # Type definitions
└── styles/           # Global styles
    └── index.css
```

## 🔌 API Integration

### Environment Variables

Create a `.env.local` file in the project root:

```env
VITE_API_URL=http://localhost:3000/api
```

### API Endpoints

The admin portal connects to these endpoints:

- **Feeds**
  - `GET /feeds` - List feeds
  - `POST /feeds` - Create feed
  - `GET /feeds/:id` - Get feed details
  - `PUT /feeds/:id` - Update feed
  - `DELETE /feeds/:id` - Delete feed
  - `PATCH /feeds/:id/status` - Toggle feed status

- **Sources**
  - `GET /sources` - List sources
  - `POST /sources` - Create source
  - `GET /sources/:id` - Get source details
  - `PUT /sources/:id` - Update source
  - `DELETE /sources/:id` - Delete source
  - `PATCH /sources/:id/status` - Toggle source status

## 🎨 Design System

- **Color Palette**: Purple gradient (#667eea → #764ba2)
- **Typography**: System fonts for consistent rendering
- **Spacing**: 8px grid system
- **Transitions**: 0.2-0.3s smooth animations
- **Responsive**: Mobile-first approach

## 📦 Dependencies

### Core
- `react` - UI library
- `react-dom` - React DOM rendering
- `react-router-dom` - Client-side routing
- `typescript` - Type safety

### Data Management
- `@tanstack/react-query` - Server state management
- `zustand` - Client state management
- `axios` - HTTP client

### Utilities
- `date-fns` - Date formatting
- `vite` - Build tool

### Development
- `@vitejs/plugin-react` - React support for Vite
- `@typescript-eslint/*` - TypeScript linting
- `eslint` - Code quality

## 🚀 Deployment

### Build
```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Deploy to Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Deploy to Other Platforms
The `dist/` folder is a static site and can be deployed to any static hosting:
- Netlify
- GitHub Pages  
- AWS S3 + CloudFront
- Firebase Hosting

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## 📝 License

This project is part of the Briefly platform.

## 🆘 Support

For issues or questions, please reach out to the development team.

---

**Happy coding!** 🎉
