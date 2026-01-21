# Lexicon-AI

AI-powered legal research platform built with Next.js 14, TypeScript, and cutting-edge AI technologies.

## 🚀 Overview

Lexicon-AI is a professional legal research platform that leverages advanced AI agents (DeepSeek, Gemini, Tavily) to provide comprehensive legal document search, analysis, and insights. The platform aggregates case law, statutes, regulations, and legal articles from multiple sources, providing intelligent reasoning and context-aware results.

## 🛠 Tech Stack

### Core Framework
- **Next.js 14** - App Router, Server Components, Server Actions
- **TypeScript** - Strict type checking with comprehensive type definitions
- **React 18** - Modern React with hooks and server components

### Styling & UI
- **TailwindCSS** - Utility-first CSS framework
- **shadcn/ui** - Re-usable component library built on Radix UI
- **Lucide Icons** - Beautiful, consistent icons

### Backend & Database
- **Supabase** - Authentication, PostgreSQL database, real-time subscriptions
- **Upstash Redis** - Fast caching and session management

### AI & Search
- **DeepSeek** - Legal research analysis and reasoning
- **Google Gemini** - Document understanding and entity extraction
- **Tavily** - Web-based legal research and discovery
- **Vercel AI SDK** - Unified AI integration layer

### Code Quality
- **ESLint** - Code linting with Next.js best practices
- **Prettier** - Code formatting with Tailwind plugin
- **TypeScript** - Static type checking

## 📁 Project Structure

```
lexicon/
├── app/                          # Next.js app directory
│   ├── page.tsx                 # Landing page
│   ├── layout.tsx               # Root layout
│   ├── globals.css              # Global styles
│   ├── dashboard/               # Dashboard pages
│   ├── auth/                    # Authentication pages
│   │   ├── login/
│   │   └── register/
│   └── api/                     # API routes
│       ├── search/
│       └── auth/
├── components/                   # React components
│   ├── ui/                      # shadcn/ui components
│   ├── layout/                  # Layout components (Header, Footer, Sidebar)
│   ├── auth/                    # Auth forms
│   └── dashboard/               # Dashboard components
├── lib/                         # Utilities and libraries
│   ├── agents/                  # AI agent integrations
│   │   ├── deepseek-agent.ts
│   │   ├── gemini-agent.ts
│   │   └── tavily-agent.ts
│   ├── database/                # Database clients
│   │   ├── supabase.ts
│   │   └── redis.ts
│   ├── self-healing/            # Self-healing engine
│   ├── types/                   # TypeScript type definitions
│   └── utils/                   # Utility functions
├── tests/                       # Test files
│   ├── unit/
│   └── e2e/
├── scripts/                     # Setup and deployment scripts
└── public/                      # Static assets
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Supabase account (for database and auth)
- Upstash Redis account (for caching)
- API keys for DeepSeek, Gemini, and Tavily

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/aayushmaan123/lexicon.git
   cd lexicon
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```
   
   Or use the setup script:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your actual credentials:
   - Supabase URL and anon key
   - Redis URL and token
   - AI API keys (DeepSeek, Gemini, Tavily)

4. **Run the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript compiler check

## 🎨 Component Library

This project uses shadcn/ui components. Currently implemented components:

- Button
- Input
- Card
- Label
- Textarea

To add more components, use:
```bash
npx shadcn-ui@latest add [component-name]
```

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Redis (Upstash)
REDIS_URL=your_redis_url
REDIS_TOKEN=your_redis_token

# AI APIs
DEEPSEEK_API_KEY=your_deepseek_key
GOOGLE_GEMINI_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## 🏗 Architecture

### Type-Safe Development

All data structures are strongly typed using TypeScript interfaces:

- **User types** (`lib/types/user.ts`) - User, authentication, and role types
- **Document types** (`lib/types/document.ts`) - Legal document structures and metadata
- **Search types** (`lib/types/search.ts`) - Search queries, filters, and results

### AI Agent Architecture

The platform uses a multi-agent approach:

1. **DeepSeek Agent** - Legal research analysis and reasoning
2. **Gemini Agent** - Document understanding and entity extraction
3. **Tavily Agent** - Web-based legal research

Each agent is designed as a separate module for easy testing and replacement.

### Self-Healing System

The self-healing engine monitors system health and automatically recovers from errors, ensuring high availability and reliability.

## 🎯 Current Status

**Phase 1: Scaffold Complete** ✅

This is the initial scaffold with:
- ✅ Complete project structure
- ✅ All configuration files
- ✅ TypeScript type definitions
- ✅ Page placeholders (landing, dashboard, auth)
- ✅ API route stubs
- ✅ Component library setup
- ✅ AI agent placeholders
- ✅ Zero TypeScript errors
- ✅ Runs locally with `npm run dev`

**Phase 2: Feature Implementation** (Coming Soon)

- Supabase authentication implementation
- AI agent integration
- Search functionality
- Document management
- User dashboard features

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Aayushmaan

## 🙏 Acknowledgments

- Next.js team for the amazing framework
- shadcn for the beautiful component library
- Vercel for AI SDK
- All open-source contributors