# HCIE Frontend V3

Next.js 16 (App Router) frontend for the HCIE Adaptive Learning Platform with real-time cognitive governance.

## Tech Stack

- **Framework**: Next.js 16 with App Router (React 19)
- **Runtime**: Bun (Node.js alternative for faster builds)
- **State Management**: 
  - Zustand (UI state)
  - TanStack Query (server state)
- **Real-time**: Socket.io for Kafka-powered updates
- **Math Engine**: KaTeX (display) + MathLive (input)
- **Graph Visualization**: React Flow for DAG/Knowledge Components
- **Data Visualization**: Recharts
- **Localization**: custom lightweight `LanguageProvider` (`src/contexts/language_context.tsx`) reading `src/lib/i18n/dictionary.ts` for EN/ID. (Note: `next-intl` was never wired up and has been removed.)
- **Validation**: Zod (syncs with backend Schema Registry)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI based)

## Architecture

### Core Layers

1. **API Client** (`src/lib/api-client.ts`)
   - Axios-based HTTP client
   - JWT authentication with automatic token refresh
   - Type-safe API methods for all backend endpoints

2. **State Management**
   - `src/store/` - Zustand stores for UI state
   - `src/hooks/` - TanStack Query hooks for server state
   - Context providers for Auth and WebSocket

3. **Providers** (`src/components/providers/`)
   - `QueryClientProvider` - TanStack Query setup
   - `AuthProvider` - Authentication context
   - `WebSocketProvider` - Real-time updates

### Core Screens

1. **Landing Page** (`/`) - Public overview
2. **Login** (`/login`) - Authentication
3. **Dashboard** (`/dashboard`) - System overview with real-time updates
4. **Learning** (`/learning`) - Adaptive learning interface with real-time progress
5. **Admin** (`/admin`) - Experiment management and system monitoring

### Research & Analysis Pages

6. **Research** (`/research`) - Advanced analytics with concept performance, user insights, and learning curves
7. **System Status** (`/system-status`) - Real-time system health monitoring with WebSocket
8. **Experiments** (`/experiments`) - Experiment management (create, start, stop, delete)
9. **Replay** (`/replay`) - Trajectory replay for research validation
10. **Cold Start** (`/cold-start`) - Cold start analysis with scenario comparison

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Backend API running at `http://localhost:8011`

### Installation

```bash
# Install dependencies
npm install

# or with Bun
bun install
```

### Configuration

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Configure environment variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8011
NEXT_PUBLIC_WS_URL=ws://localhost:8011
NEXT_PUBLIC_APP_NAME=HCIE
NEXT_PUBLIC_APP_VERSION=3.0.0
```

### Development

```bash
# Run development server
npm run dev

# or with Bun
bun run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
# Build for production
npm run build

# or with Bun
bun run build
```

### Production

```bash
# Start production server
npm start

# or with Bun
bun start
```

## API Integration

The frontend integrates with the HCIE backend API at `/api` and `/v3` endpoints:

### Authentication
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `GET /auth/profile` - Get user profile
- `POST /auth/logout` - Logout

### Learning APIs
- `GET /api/learning/next-task` - Get next task
- `POST /api/learning/submit` - Submit task answer
- `GET /v3/experience/user/{user_id}/learning-state` - Get learning state
- `POST /v3/experience/user/{user_id}/recommendation` - Get recommendation

### Dashboard APIs
- `GET /v3/frontend/dashboard/overview` - System overview
- `GET /v3/frontend/dashboard/user/{user_id}` - User dashboard
- `GET /v3/frontend/dashboard/analytics` - System analytics

### Experiment APIs (Admin)
- `GET /experiments/` - List experiments
- `POST /experiments/` - Create experiment
- `POST /experiments/{id}/start` - Start experiment
- `POST /experiments/{id}/stop` - Stop experiment
- `DELETE /experiments/{id}` - Delete experiment

### Analytics APIs
- `GET /v3/analytics/concept-performance` - Concept performance metrics
- `GET /v3/analytics/user-insights/{user_id}` - User learning insights
- `GET /v3/analytics/learning-curves` - Learning curve data
- `GET /v3/analytics/system-stats` - System-wide statistics

### Replay APIs
- `POST /api/replay/trajectory` - Start trajectory replay
- `GET /api/replay/status/{replay_id}` - Get replay status

### Cold Start APIs
- `GET /v3/analytics/cold-start` - Cold start analysis results

## Real-time Updates

WebSocket connection for real-time projection updates:

```typescript
const { connected, connect, disconnect } = useWebSocket()

// Connect when user is authenticated
useEffect(() => {
  if (user) {
    connect(user.id)
  }
  return () => disconnect()
}, [user, connect, disconnect])
```

### Available WebSocket Hooks

- `useSystemStatus()` - Real-time system health, active users, processing rate
- `useLearningProgress()` - Real-time mastery updates and bandit scores
- `useUserInsights(userId)` - User learning analytics

## State Management

### UI State (Zustand)

```typescript
import { useAuthStore } from '@/store/useAuthStore'
import { useLearningStore } from '@/store/useLearningStore'

const { user, isAuthenticated } = useAuthStore()
const { currentTask, setCurrentTask } = useLearningStore()
```

### Server State (TanStack Query)

```typescript
import { useLearningState, useNextTask } from '@/hooks/useLearning'

const { data: learningState } = useLearningState(userId)
const { data: nextTask } = useNextTask(userId)
```

## Math Rendering

### Display (KaTeX)

```typescript
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'

<BlockMath math="E = mc^2" />
```

### Input (MathLive)

```typescript
import { Mathfield } from 'mathlive'

<Mathfield
  value={mathValue}
  onInput={(mathField) => setMathValue(mathField.value)}
/>
```

## DAG Visualization

```typescript
import ReactFlow from 'reactflow'

<ReactFlow
  nodes={dagNodes}
  edges={dagEdges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
/>
```

## Localization

Configure in `next-intl`:

```typescript
import { useTranslations } from 'next-intl'

const t = useTranslations('common')
<h1>{t('welcome')}</h1>
```

## Type Safety

All API responses are typed in `src/types/index.ts`:

```typescript
import { LearningState, Recommendation, Task } from '@/types'

const state: LearningState = await apiClient.getLearningState(userId)
```

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Vercel

```bash
vercel --prod
```

## License

This project is part of the HCIE research system.
