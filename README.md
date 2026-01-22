# Lexicon AI Platform

AI-powered legal research and document intelligence platform integrating DeepSeek reasoning and Google-based RAG.

## 🏗️ Architecture

Lexicon is built as a modern TypeScript monorepo with three main packages:

```
lexicon/
├── backend/          # Express.js API server
├── frontend/         # Next.js web application
└── shared/           # Shared TypeScript types and interfaces
```

### Technology Stack

- **Language**: TypeScript (100%)
- **Backend**: Node.js + Express
- **Frontend**: Next.js 14 + React 18
- **Package Management**: npm workspaces
- **Code Quality**: ESLint + Prettier

## 📦 Project Structure

### Backend (`/backend`)

```
backend/
├── src/
│   ├── agents/           # AI agent implementations
│   │   ├── base.agent.ts
│   │   ├── deepseek.agent.ts
│   │   ├── google-rag.agent.ts
│   │   └── agent.factory.ts
│   ├── config/           # Configuration management
│   ├── middleware/       # Express middleware
│   ├── routes/           # API routes
│   │   ├── ai.routes.ts
│   │   ├── auth.routes.ts
│   │   ├── document.routes.ts
│   │   └── health.routes.ts
│   ├── services/         # Business logic layer
│   │   ├── ai.service.ts
│   │   ├── auth.service.ts
│   │   └── document.service.ts
│   ├── utils/            # Utilities
│   ├── app.ts            # Express app setup
│   └── index.ts          # Server entry point
└── package.json
```

### Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── app/              # Next.js app directory
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/       # React components (Phase 2)
│   ├── lib/              # Utilities (Phase 2)
│   └── styles/           # Stylesheets (Phase 2)
└── package.json
```

### Shared (`/shared`)

```
shared/
└── src/
    ├── interfaces/       # TypeScript interfaces
    │   ├── agent.interface.ts
    │   ├── auth.interface.ts
    │   └── document.interface.ts
    ├── types/            # Type definitions
    │   ├── api.types.ts
    │   └── config.types.ts
    └── index.ts          # Package exports
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm 9+

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd lexicon

# Install dependencies for all workspaces
npm install

# Build shared package
npm run build --workspace=shared
```

### Development

```bash
# Run backend only (port 3000)
npm run backend

# Run frontend only (port 3001)
npm run frontend

# Note: Run both commands in separate terminal windows
```

### Building

```bash
# Build all packages
npm run build

# Build specific workspace
npm run build --workspace=backend
npm run build --workspace=frontend
npm run build --workspace=shared
```

### Linting

```bash
# Lint all packages
npm run lint

# Lint specific workspace
npm run lint --workspace=backend
```

## 🔌 API Endpoints

### Health & Status

- `GET /api/health` - Health check
- `GET /api/health/status` - Detailed status

### AI Agents (Stub Implementation)

- `POST /api/ai/deepseek` - Query DeepSeek AI agent
- `POST /api/ai/search` - Query Google RAG agent

### Authentication (Phase 2)

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout

### Documents (Phase 2)

- `POST /api/documents/upload` - Upload document
- `GET /api/documents/search` - Search documents
- `GET /api/documents/:id` - Get document
- `DELETE /api/documents/:id` - Delete document

## 🤖 AI Agent System

The platform uses a clean, modular agent architecture:

### Agent Interface

All agents implement the `AIAgent` interface:

```typescript
interface AIAgent {
  readonly agentType: AgentType;
  initialize(config: AgentConfig): Promise<void>;
  execute(query: AgentQuery): Promise<AgentResponse>;
  isReady(): boolean;
}
```

### Available Agents

1. **DeepSeek Agent** (`AgentType.DEEPSEEK`)
   - Handles reasoning and advanced AI tasks
   - Stub implementation in Phase 1

2. **Google RAG Agent** (`AgentType.GOOGLE_RAG`)
   - Handles document retrieval and search
   - Stub implementation in Phase 1

3. **Orchestrator** (Phase 2)
   - Self-healing orchestration layer
   - Multi-agent coordination

## 🔐 Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `NODE_ENV` - Environment (development/production/test)
- `PORT` - Server port (default: 3000)
- API keys (Phase 2)
- Database URLs (Phase 2)
- Storage configuration (Phase 2)

## 📝 Phase 1 Status

✅ **Completed:**
- TypeScript monorepo structure
- Backend API scaffold with Express
- Frontend scaffold with Next.js
- Type-safe AI agent interfaces
- Modular service architecture
- Authentication placeholders
- Document management placeholders
- Clean folder structure
- Linting and formatting setup
- Environment configuration

## 🎯 Phase 2 Roadmap

**AI Integration:**
- [ ] Implement DeepSeek API integration
- [ ] Build Google RAG pipeline
- [ ] Add vector database (Pinecone, Weaviate, or Qdrant)
- [ ] Implement document embedding
- [ ] Add semantic search

**Document Processing:**
- [ ] PDF/DOCX parsing
- [ ] Text extraction
- [ ] Metadata extraction
- [ ] Document storage (S3/GCS)
- [ ] Document chunking for RAG

**Authentication:**
- [ ] JWT token generation
- [ ] Password hashing (bcrypt)
- [ ] Session management
- [ ] OAuth providers
- [ ] User database

**Frontend:**
- [ ] Search interface
- [ ] Document upload UI
- [ ] Results display
- [ ] Authentication UI
- [ ] Dashboard

**Orchestration:**
- [ ] Multi-agent coordination
- [ ] Self-healing logic
- [ ] Query routing
- [ ] Response synthesis
- [ ] Caching layer

## 🧪 Testing

Testing infrastructure will be added in Phase 2:
- Unit tests (Jest)
- Integration tests
- E2E tests (Playwright)

## 📄 License

MIT

## 👥 Contributing

This is a Phase 1 scaffold. Contributions for Phase 2 implementation are welcome.

---

**Note:** This is a Phase 1 scaffold. Most functionality returns stub responses or "not implemented" errors. Real implementation begins in Phase 2.