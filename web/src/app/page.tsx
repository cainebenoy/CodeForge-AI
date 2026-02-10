import Link from 'next/link'
import { Code2, GraduationCap, ArrowRight, Users } from 'lucide-react'

import { Navbar } from '@/components/features/landing/Navbar'
import { HeroTerminal } from '@/components/features/landing/HeroTerminal'
import { HeroCodeBlock } from '@/components/features/landing/HeroCodeBlock'
import { TrustedBy } from '@/components/features/landing/TrustedBy'
import { FeatureGrid } from '@/components/features/landing/FeatureGrid'
import { Footer } from '@/components/features/landing/Footer'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-cf-primary selection:text-black relative">
      {/* Background grid – adapts per theme */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.05] bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] dark:[mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

      <Navbar />

      <main className="relative z-10 flex flex-col flex-grow">
        {/* ═══════════════════════════════════════════
            HERO SECTION
        ═══════════════════════════════════════════ */}
        <section className="flex flex-col items-center justify-center flex-grow py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
          {/* ── Dark-mode hero text ── */}
          <div className="hidden dark:flex flex-col items-center gap-6 mb-12 text-center max-w-4xl mx-auto">
            {/* Status pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-secondary backdrop-blur-sm">
              <span className="relative flex size-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-cf-primary opacity-75 animate-ping" />
                <span className="relative inline-flex size-2 rounded-full bg-cf-primary" />
              </span>
              <span className="text-xs font-mono font-medium text-muted-foreground tracking-wide uppercase">
                System v2.4 Live
              </span>
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-[-0.04em] leading-[1.1] text-foreground">
              Your AI <br className="sm:hidden" /> Engineering Team
            </h1>

            <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Architect complex systems and ship production-ready code with
              high-precision AI agents working in unison.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center gap-4 mt-6 w-full sm:w-auto">
              <Link
                href="/dashboard/builder"
                className="group w-full sm:w-auto h-12 px-8 rounded-lg bg-foreground text-background text-base font-bold hover:bg-foreground/90 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-white/10"
              >
                <Code2 className="size-5 transition-transform group-hover:-translate-y-0.5" />
                Start Building
              </Link>
              <Link
                href="/dashboard/student"
                className="group w-full sm:w-auto h-12 px-8 rounded-lg border border-border text-foreground text-base font-medium violet-glow-btn bg-secondary flex items-center justify-center gap-2"
              >
                <GraduationCap className="size-5 transition-transform group-hover:rotate-12" />
                Start Learning
              </Link>
            </div>
          </div>

          {/* ── Light-mode hero text ── */}
          <div className="flex dark:hidden flex-col lg:flex-row gap-12 lg:gap-16 items-center w-full">
            <div className="flex flex-col gap-8 flex-1 w-full lg:max-w-[50%]">
              <div className="flex flex-col gap-4 text-left">
                {/* Version tag */}
                <div className="inline-flex items-center gap-2 px-2 py-1 bg-muted border border-border rounded-sm w-fit">
                  <span className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-wider">
                    v2.4.0 Stable
                  </span>
                </div>

                <h1 className="text-5xl lg:text-6xl font-black leading-[1.1] tracking-[-0.033em] text-foreground">
                  Architect the Future.
                </h1>
                <h2 className="text-muted-foreground text-lg lg:text-xl font-normal leading-relaxed max-w-[540px]">
                  Generate production-ready codebases from architectural
                  blueprints. No hallucinations, just logic.
                </h2>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  href="/dashboard/builder"
                  className="flex min-w-[140px] items-center justify-center rounded-sm h-12 px-6 bg-foreground hover:bg-foreground/90 text-background text-base font-bold tracking-[0.015em] transition-all lab-shadow hover:translate-y-[1px] hover:shadow-none"
                >
                  Start Building
                  <ArrowRight className="ml-2 size-4" />
                </Link>
                <Link
                  href="#"
                  className="flex min-w-[140px] items-center justify-center rounded-sm h-12 px-6 bg-background border border-border hover:border-muted-foreground text-foreground text-base font-medium tracking-[0.015em] transition-colors"
                >
                  Read Documentation
                </Link>
              </div>

              {/* Social proof */}
              <div className="flex items-center gap-4 text-sm text-muted-foreground font-medium pt-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full border-2 border-background bg-muted flex items-center justify-center"
                    >
                      <Users className="size-3 text-muted-foreground" />
                    </div>
                  ))}
                </div>
                <p>Trusted by 10,000+ Architects</p>
              </div>
            </div>

            {/* Light-mode code block visual */}
            <HeroCodeBlock />
          </div>

          {/* Dark-mode terminal visual */}
          <HeroTerminal />

          {/* Trusted-by section (both modes) */}
          <TrustedBy />
        </section>

        {/* Feature grid (both modes) */}
        <section className="px-4 sm:px-6 lg:px-8 pb-20">
          <FeatureGrid />
        </section>
      </main>

      <Footer />
    </div>
  )
}
