import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <span className="text-lg font-bold">L</span>
            </div>
            <span className="text-xl font-bold">Lexicon-AI</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/auth/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/auth/register">
              <Button>Get Started</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container flex flex-col items-center justify-center gap-4 py-24 text-center md:py-32">
        <div className="flex max-w-[980px] flex-col gap-4">
          <h1 className="text-4xl font-bold leading-tight tracking-tighter md:text-6xl lg:text-7xl">
            AI-Powered Legal Research
            <br className="hidden sm:inline" />
            <span className="text-primary"> Made Simple</span>
          </h1>
          <p className="max-w-[750px] text-lg text-muted-foreground sm:text-xl">
            Access comprehensive legal databases with the power of AI. Search
            case law, statutes, regulations, and legal articles with advanced
            reasoning and analysis.
          </p>
        </div>
        <div className="flex gap-4">
          <Link href="/auth/register">
            <Button size="lg" className="h-12 px-8">
              Start Researching
            </Button>
          </Link>
          <Link href="#features">
            <Button size="lg" variant="outline" className="h-12 px-8">
              Learn More
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container py-24">
        <div className="mx-auto flex max-w-[980px] flex-col gap-12">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Everything you need for comprehensive legal research
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Search</CardTitle>
                <CardDescription>
                  Advanced natural language processing understands your legal
                  queries
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Leverages DeepSeek, Gemini, and Tavily for comprehensive
                  multi-source analysis
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Multi-Source Aggregation</CardTitle>
                <CardDescription>
                  Access case law, statutes, regulations, and legal articles
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Comprehensive coverage across multiple jurisdictions and
                  legal domains
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Intelligent Reasoning</CardTitle>
                <CardDescription>
                  Get AI-generated insights and analysis for your research
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Understand context, relevance, and connections between legal
                  documents
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Fast & Reliable</CardTitle>
                <CardDescription>
                  Lightning-fast search with enterprise-grade reliability
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Powered by Redis caching and optimized database queries
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Secure & Compliant</CardTitle>
                <CardDescription>
                  Enterprise-grade security for sensitive legal research
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  SOC 2 compliant infrastructure with end-to-end encryption
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Self-Healing System</CardTitle>
                <CardDescription>
                  Automatic error recovery and system optimization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Built-in monitoring and self-healing capabilities ensure
                  24/7 uptime
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t py-6">
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">
            © 2024 Lexicon-AI. All rights reserved.
          </p>
          <nav className="flex gap-4 text-sm text-muted-foreground">
            <Link href="#" className="hover:underline">
              Terms
            </Link>
            <Link href="#" className="hover:underline">
              Privacy
            </Link>
            <Link href="#" className="hover:underline">
              Contact
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
