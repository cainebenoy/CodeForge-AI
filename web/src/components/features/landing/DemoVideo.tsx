'use client'

import { useState } from 'react'
import { Play, Pause, Volume2, VolumeX, Maximize2, Loader2 } from 'lucide-react'

interface DemoVideoProps {
  /** Video source URL */
  src?: string
  /** Poster/thumbnail image */
  poster?: string
  /** Video title */
  title?: string
  /** Video description */
  description?: string
  /** Additional className */
  className?: string
}

/**
 * DemoVideo — Product demo video section for the landing page.
 * 
 * Features:
 * - Responsive video player with custom controls
 * - Fallback placeholder when no video is available
 * - Play/pause overlay
 * - Dark/light theme adaptive styling
 */
export function DemoVideo({
  src,
  poster = '/demo-poster.png',
  title = 'See CodeForge in Action',
  description = 'Watch how AI agents transform your ideas into production-ready code in minutes.',
  className = '',
}: DemoVideoProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [hasVideo, setHasVideo] = useState(!!src)

  const handlePlayClick = () => {
    const video = document.getElementById('demo-video') as HTMLVideoElement
    if (video) {
      if (isPlaying) {
        video.pause()
      } else {
        setIsLoading(true)
        video.play()
          .then(() => setIsLoading(false))
          .catch(() => setIsLoading(false))
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleMuteClick = () => {
    const video = document.getElementById('demo-video') as HTMLVideoElement
    if (video) {
      video.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleFullscreen = () => {
    const video = document.getElementById('demo-video') as HTMLVideoElement
    if (video) {
      if (video.requestFullscreen) {
        video.requestFullscreen()
      }
    }
  }

  return (
    <section className={`py-20 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            {title}
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            {description}
          </p>
        </div>

        {/* Video container */}
        <div className="relative rounded-2xl overflow-hidden border border-border bg-muted/20 shadow-2xl aspect-video group">
          {hasVideo && src ? (
            <>
              {/* Video element */}
              <video
                id="demo-video"
                className="w-full h-full object-cover"
                poster={poster}
                muted={isMuted}
                playsInline
                onEnded={() => setIsPlaying(false)}
                onLoadStart={() => setIsLoading(true)}
                onCanPlay={() => setIsLoading(false)}
              >
                <source src={src} type="video/mp4" />
                Your browser does not support the video tag.
              </video>

              {/* Play/pause overlay */}
              {!isPlaying && (
                <button
                  onClick={handlePlayClick}
                  className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
                  aria-label="Play video"
                >
                  <div className="size-20 rounded-full bg-white/90 flex items-center justify-center shadow-lg hover:scale-105 transition-transform">
                    {isLoading ? (
                      <Loader2 className="size-8 text-cf-primary animate-spin" />
                    ) : (
                      <Play className="size-8 text-cf-primary ml-1" />
                    )}
                  </div>
                </button>
              )}

              {/* Controls bar */}
              <div
                className={`absolute bottom-0 left-0 right-0 px-4 py-3 bg-gradient-to-t from-black/80 to-transparent flex items-center gap-4 transition-opacity ${
                  isPlaying ? 'opacity-0 group-hover:opacity-100' : 'opacity-100'
                }`}
              >
                <button
                  onClick={handlePlayClick}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? (
                    <Pause className="size-5 text-white" />
                  ) : (
                    <Play className="size-5 text-white" />
                  )}
                </button>

                <div className="flex-1" />

                <button
                  onClick={handleMuteClick}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted ? (
                    <VolumeX className="size-5 text-white" />
                  ) : (
                    <Volume2 className="size-5 text-white" />
                  )}
                </button>

                <button
                  onClick={handleFullscreen}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label="Fullscreen"
                >
                  <Maximize2 className="size-5 text-white" />
                </button>
              </div>
            </>
          ) : (
            /* Placeholder when no video is available */
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-muted to-muted/50">
              {/* Animated placeholder */}
              <div className="relative mb-6">
                {/* Glowing ring */}
                <div className="absolute inset-0 rounded-full bg-cf-primary/20 animate-ping" />
                <div className="relative size-24 rounded-full bg-gradient-to-br from-cf-primary to-cf-primary/60 flex items-center justify-center shadow-lg">
                  <Play className="size-10 text-white ml-1" />
                </div>
              </div>

              <h3 className="text-xl font-semibold text-foreground mb-2">
                Demo Coming Soon
              </h3>
              <p className="text-sm text-muted-foreground max-w-sm text-center">
                We&apos;re putting the finishing touches on our product demo. 
                Check back soon to see CodeForge in action!
              </p>

              {/* Decorative elements */}
              <div className="absolute inset-0 pointer-events-none overflow-hidden">
                {/* Grid pattern */}
                <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
                
                {/* Floating code snippets - decorative */}
                <div className="absolute top-10 left-10 px-3 py-2 bg-background/50 backdrop-blur-sm rounded-lg border border-border text-xs font-mono text-muted-foreground opacity-30">
                  const app = codeforge.create()
                </div>
                <div className="absolute bottom-16 right-10 px-3 py-2 bg-background/50 backdrop-blur-sm rounded-lg border border-border text-xs font-mono text-muted-foreground opacity-30">
                  await agent.generate(spec)
                </div>
                <div className="absolute top-20 right-20 px-3 py-2 bg-background/50 backdrop-blur-sm rounded-lg border border-border text-xs font-mono text-muted-foreground opacity-20">
                  export to GitHub ✓
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Caption */}
        <p className="text-center text-sm text-muted-foreground mt-4">
          Watch the 2-minute overview of CodeForge AI
        </p>
      </div>
    </section>
  )
}
