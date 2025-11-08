# 🎨 CrewUp Frontend

Modern React SPA with TypeScript, Vite, TailwindCSS, and Leaflet maps.

## ✨ Features

- **Interactive Map**: See all events on a map with Leaflet
- **Real-time Chat**: WebSocket-based group messaging
- **Party Mode**: Safety alert system with one-tap help button
- **Responsive Design**: Works on mobile and desktop
- **Dark Mode**: Full dark mode support
- **Type-Safe**: 100% TypeScript

## 🛠️ Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Lightning-fast build tool
- **TailwindCSS** - Utility-first CSS
- **React Router** - Client-side routing
- **Zustand** - State management
- **React Leaflet** - Interactive maps
- **Lucide React** - Beautiful icons
- **Axios** - HTTP client

## 🚀 Development

### Install dependencies

```bash
cd frontend
npm install
```

### Run dev server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for production

```bash
npm run build
```

### Preview production build

```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # Reusable UI components
│   │   ├── Layout.tsx    # App layout wrapper
│   │   └── Navbar.tsx    # Navigation bar
│   ├── pages/
│   │   ├── HomePage.tsx          # Map + Events list
│   │   ├── EventDetailPage.tsx   # Event details + Groups
│   │   ├── EventsPage.tsx        # My groups list
│   │   ├── GroupChatPage.tsx     # Real-time chat
│   │   ├── ProfilePage.tsx       # User profile
│   │   ├── LoginPage.tsx         # Login form
│   │   └── RegisterPage.tsx      # Registration form
│   ├── stores/
│   │   ├── authStore.ts   # Authentication state
│   │   └── appStore.ts    # Global app state
│   ├── types/
│   │   └── index.ts       # TypeScript types
│   ├── App.tsx            # Main app component
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

## 🎨 Design System

### Colors

- **Primary**: Blue (`#0ea5e9`)
- **Danger**: Red (`#ef4444`) - Used for safety alerts
- **Gray**: Neutral colors for text and backgrounds

### Components

- **Button**: Primary, Secondary, Danger, Ghost variants
- **Card**: Container with shadow and hover effects
- **Input**: Text input with label and error states
- **Modal**: Overlay dialog

## 🗺️ Pages

### Home Page (`/`)
- Interactive map showing all nearby events
- List of events with details
- Click marker or card to see event details

### Event Detail (`/events/:id`)
- Full event information
- List of groups for this event
- Create new group or join existing

### Events (`/events`)
- List of groups you've joined
- Quick access to group chats

### Group Chat (`/groups/:id`)
- Real-time messaging (WebSocket)
- Member list
- **Party Mode**: Emergency help button

### Profile (`/profile`)
- User information
- Reputation score
- Review history

### Login/Register
- Authentication forms
- Input validation

## 🔒 Party Mode

When enabled (click button in navbar):
- Shows **HELP** button in group chat
- One-tap emergency alert
- Notifies all group members
- Logs incident with timestamp

## 🌐 API Integration

The frontend expects these API endpoints:

```
GET  /api/event/events          - List events
GET  /api/event/events/:id      - Event details
POST /api/event/events          - Create event

GET  /api/group/groups          - List groups
GET  /api/group/groups/:id      - Group details
POST /api/group/groups          - Create group
POST /api/group/groups/:id/join - Join group

GET  /api/group/messages/:groupId - Get messages
POST /api/group/messages        - Send message

POST /api/safety/alerts         - Create safety alert

POST /api/user/auth/login       - Login
POST /api/user/auth/register    - Register
GET  /api/user/profile          - Get profile
```

## 🐳 Docker

### Build

```bash
docker build -t crewup-frontend .
```

### Run

```bash
docker run -p 3000:80 crewup-frontend
```

The frontend is served by Nginx in production.

## 🔧 Environment Variables

Create `.env` file (optional):

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📝 TODO

- [ ] Connect to real backend APIs
- [ ] Implement WebSocket connection
- [ ] Add loading states
- [ ] Add error boundaries
- [ ] Add toast notifications
- [ ] Add image uploads
- [ ] Add event filters
- [ ] Add search functionality
- [ ] Add pagination

## 🎯 Next Steps

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`
3. Connect backend APIs in `stores/`
4. Test all pages and flows
5. Build and deploy!

---

**Built with ❤️ for M7011E**
