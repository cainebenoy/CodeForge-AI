import {
  Triangle,
  Globe,
  Leaf,
  Umbrella,
  Layers,
} from 'lucide-react'

/**
 * TrustedBy — "Powering engineering at" logos strip.
 * Renders styled text+icon logos; dark mode shows SVG shapes, light mode shows named logos.
 */
export function TrustedBy() {
  return (
    <div className="mt-24 pt-10 border-t border-border w-full max-w-5xl mx-auto">
      <p className="text-center text-xs sm:text-sm font-semibold text-muted-foreground mb-8 uppercase tracking-[0.2em] font-mono">
        <span className="hidden dark:inline">Powering engineering at</span>
        <span className="inline dark:hidden">Powering Architecture Teams At</span>
      </p>

      {/* Dark-mode: abstract SVG logos */}
      <div className="hidden dark:flex flex-wrap justify-center items-center gap-x-12 gap-y-8 opacity-30 hover:opacity-50 transition-opacity duration-500 grayscale hover:grayscale-0">
        <svg className="h-6 w-auto text-white" fill="currentColor" height="24" viewBox="0 0 100 30" xmlns="http://www.w3.org/2000/svg">
          <path d="M10,25 L20,5 L30,25 M15,15 H25 M40,5 H60 M50,5 V25 M70,5 H90 L75,25" stroke="currentColor" strokeWidth="3" />
        </svg>
        <svg className="h-6 w-auto text-white" fill="currentColor" height="24" viewBox="0 0 100 30" xmlns="http://www.w3.org/2000/svg">
          <circle cx="15" cy="15" r="10" />
          <rect height="14" rx="2" width="50" x="35" y="8" />
        </svg>
        <svg className="h-6 w-auto text-white" fill="currentColor" height="24" viewBox="0 0 100 30" xmlns="http://www.w3.org/2000/svg">
          <path d="M10,15 Q25,5 40,15 T70,15 T100,15" fill="none" stroke="currentColor" strokeWidth="3" />
          <circle cx="10" cy="15" r="3" />
          <circle cx="100" cy="15" r="3" />
        </svg>
        <svg className="h-5 w-auto text-white" fill="currentColor" height="20" viewBox="0 0 100 30" xmlns="http://www.w3.org/2000/svg">
          <rect height="20" transform="rotate(45 15 15)" width="20" x="5" y="5" />
          <rect height="10" width="50" x="40" y="10" />
        </svg>
      </div>

      {/* Light-mode: named text logos */}
      <div className="flex dark:hidden flex-wrap items-center justify-center gap-x-12 gap-y-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
        {[
          { icon: Triangle, name: 'ACME' },
          { icon: Globe, name: 'GLOBEX' },
          { icon: Leaf, name: 'SOYLENT' },
          { icon: Umbrella, name: 'UMBRELLA' },
          { icon: Layers, name: 'INITECH' },
        ].map(({ icon: Icon, name }) => (
          <div
            key={name}
            className="flex items-center gap-2 text-foreground font-bold text-xl font-sans"
          >
            <Icon className="size-5" />
            {name}
          </div>
        ))}
      </div>
    </div>
  )
}
