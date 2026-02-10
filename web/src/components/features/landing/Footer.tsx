import Link from 'next/link'
import { Compass } from 'lucide-react'

export function Footer() {
  return (
    <footer className="flex flex-col gap-6 px-5 py-10 text-center border-t border-border bg-background">
      <div className="max-w-[1200px] mx-auto w-full flex flex-col md:flex-row justify-between items-center gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-foreground">
          <Compass className="size-5" />
          <span className="text-sm font-bold">CodeForge AI</span>
        </Link>

        {/* Links */}
        <div className="flex flex-wrap items-center justify-center gap-8">
          <Link
            href="#"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Privacy Policy
          </Link>
          <Link
            href="#"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Terms of Service
          </Link>
          <Link
            href="#"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Documentation
          </Link>
          <Link
            href="https://github.com"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </Link>
        </div>

        <p className="text-muted-foreground text-sm">© 2024 CodeForge AI.</p>
      </div>
    </footer>
  )
}
