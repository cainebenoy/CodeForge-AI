import { Database, Globe, Shield } from 'lucide-react'
import type { ReactNode } from 'react'

export interface SummaryCardData {
  icon: ReactNode
  title: string
  description: string
}

const defaultCards: SummaryCardData[] = [
  {
    icon: <Database className="size-5" />,
    title: 'Database',
    description: 'PostgreSQL 15 schema initialized.',
  },
  {
    icon: <Globe className="size-5" />,
    title: 'Endpoints',
    description: 'RESTful API routes planning.',
  },
  {
    icon: <Shield className="size-5" />,
    title: 'Auth',
    description: 'JWT Implementation pending.',
  },
]

/**
 * ProgressSummaryCards — Grid of contextual progress cards below the reasoning accordion.
 * Shows infrastructure status at a glance.
 */
export function ProgressSummaryCards({
  cards = defaultCards,
}: {
  cards?: SummaryCardData[]
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-card border border-border p-4 rounded-lg flex items-start gap-4"
        >
          <div className="bg-muted p-2 rounded text-muted-foreground">
            {card.icon}
          </div>
          <div>
            <h4 className="text-foreground text-sm font-medium mb-1">
              {card.title}
            </h4>
            <p className="text-muted-foreground text-xs">{card.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
