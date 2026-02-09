import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="container flex flex-col items-center gap-12 px-4 py-16">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-[5rem]">
          CodeForge <span className="text-agent-code">AI</span>
        </h1>
        <p className="text-center text-2xl text-muted-foreground">
          Your AI Engineering Team
        </p>
        <div className="flex gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg bg-primary px-10 py-3 font-semibold text-primary-foreground transition hover:bg-primary/90"
          >
            Get Started
          </Link>
          <Link
            href="/docs"
            className="rounded-lg border border-border bg-background px-10 py-3 font-semibold transition hover:bg-muted"
          >
            Learn More
          </Link>
        </div>
      </div>
    </main>
  )
}
