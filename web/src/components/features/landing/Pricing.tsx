import Link from 'next/link'
import { Check, Sparkles, Building2, Rocket } from 'lucide-react'

interface PricingTier {
  name: string
  price: string
  period: string
  description: string
  features: string[]
  cta: string
  ctaLink: string
  highlighted?: boolean
  icon: React.ElementType
}

const pricingTiers: PricingTier[] = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for learning and exploring CodeForge capabilities',
    icon: Sparkles,
    features: [
      'Access to Student Mode',
      'Up to 3 projects',
      'Basic AI agents',
      'Community support',
      'Core features access',
      '100 AI requests/month',
    ],
    cta: 'Start Free',
    ctaLink: '/dashboard',
  },
  {
    name: 'Pro',
    price: '$29',
    period: 'per month',
    description: 'For professional developers building production apps',
    icon: Rocket,
    highlighted: true,
    features: [
      'Everything in Free',
      'Unlimited projects',
      'Advanced AI agents',
      'Priority support',
      'GitHub integration',
      'Unlimited AI requests',
      'Export to multiple formats',
      'Custom templates',
      'Real-time collaboration',
    ],
    cta: 'Get Pro',
    ctaLink: '/dashboard',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'For teams that need advanced features and support',
    icon: Building2,
    features: [
      'Everything in Pro',
      'Dedicated account manager',
      'Custom AI agent training',
      'SSO & advanced security',
      'SLA guarantees',
      'On-premise deployment',
      'Team collaboration tools',
      'Custom integrations',
      'Volume discounts',
    ],
    cta: 'Contact Sales',
    ctaLink: '#waitlist',
  },
]

export function Pricing() {
  return (
    <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/20">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-background mb-4">
            <span className="text-xs font-mono font-medium text-muted-foreground tracking-wide uppercase">
              Pricing
            </span>
          </div>
          <h2 className="text-4xl sm:text-5xl font-extrabold text-foreground mb-4 tracking-tight">
            Choose Your Plan
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Start free and scale as you grow. All plans include access to our core AI agents.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {pricingTiers.map((tier) => {
            const Icon = tier.icon
            return (
              <div
                key={tier.name}
                className={`relative flex flex-col rounded-2xl border transition-all duration-300 ${
                  tier.highlighted
                    ? 'border-cf-primary bg-background shadow-2xl shadow-cf-primary/10 scale-105 md:scale-110 z-10'
                    : 'border-border bg-background hover:border-muted-foreground/30 hover:shadow-lg'
                }`}
              >
                {/* Popular badge */}
                {tier.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-cf-primary text-white text-xs font-bold rounded-full shadow-lg">
                    MOST POPULAR
                  </div>
                )}

                {/* Card content */}
                <div className="p-8 flex flex-col flex-grow">
                  {/* Icon and name */}
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`size-10 rounded-lg flex items-center justify-center ${
                        tier.highlighted
                          ? 'bg-cf-primary/10 text-cf-primary'
                          : 'bg-muted text-foreground'
                      }`}
                    >
                      <Icon className="size-5" />
                    </div>
                    <h3 className="text-2xl font-bold text-foreground">{tier.name}</h3>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-muted-foreground mb-6 min-h-[40px]">
                    {tier.description}
                  </p>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-5xl font-extrabold text-foreground">
                        {tier.price}
                      </span>
                      {tier.price !== 'Custom' && (
                        <span className="text-muted-foreground text-sm">/{tier.period}</span>
                      )}
                    </div>
                    {tier.price === 'Custom' && (
                      <span className="text-muted-foreground text-sm">{tier.period}</span>
                    )}
                  </div>

                  {/* CTA Button */}
                  <Link
                    href={tier.ctaLink}
                    className={`w-full h-12 rounded-lg text-base font-semibold flex items-center justify-center transition-all mb-8 ${
                      tier.highlighted
                        ? 'bg-cf-primary hover:bg-cf-primary/90 text-white shadow-lg shadow-cf-primary/20'
                        : 'bg-muted hover:bg-muted-foreground/10 text-foreground border border-border'
                    }`}
                  >
                    {tier.cta}
                  </Link>

                  {/* Features list */}
                  <div className="flex-grow">
                    <p className="text-xs uppercase tracking-wider font-semibold text-muted-foreground mb-4">
                      Features
                    </p>
                    <ul className="space-y-3">
                      {tier.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3">
                          <Check
                            className={`size-5 mt-0.5 flex-shrink-0 ${
                              tier.highlighted ? 'text-cf-primary' : 'text-muted-foreground'
                            }`}
                          />
                          <span className="text-sm text-foreground">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom note */}
        <div className="mt-12 text-center">
          <p className="text-sm text-muted-foreground">
            All plans include 14-day money-back guarantee. No credit card required for Free tier.
          </p>
        </div>
      </div>
    </section>
  )
}
