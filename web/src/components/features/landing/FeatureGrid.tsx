import { Workflow, ShieldCheck, RefreshCw } from 'lucide-react'

/**
 * FeatureGrid — 3-column feature teaser (visible in light mode, shown in both for consistency).
 */
const features = [
  {
    icon: Workflow,
    title: 'Blueprint to Code',
    description:
      'Convert high-level diagrams directly into Terraform, Pulumi, or CloudFormation templates.',
  },
  {
    icon: ShieldCheck,
    title: 'Policy as Code',
    description:
      'Embed compliance rules directly into the generation process. SOC2 compliant by default.',
  },
  {
    icon: RefreshCw,
    title: 'Drift Detection',
    description:
      'Real-time synchronization between your architectural diagrams and deployed infrastructure.',
  },
]

export function FeatureGrid() {
  return (
    <section id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 w-full max-w-5xl mx-auto">
      {features.map(({ icon: Icon, title, description }) => (
        <div
          key={title}
          className="group p-6 border border-border rounded-sm
                     bg-muted/50 hover:bg-background hover:border-muted-foreground/30
                     hover:shadow-sm transition-all"
        >
          <div className="w-10 h-10 bg-background border border-border rounded-sm flex items-center justify-center mb-4 group-hover:border-foreground transition-colors">
            <Icon className="size-5 text-foreground" />
          </div>
          <h3 className="text-foreground font-bold text-lg mb-2">{title}</h3>
          <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
        </div>
      ))}
    </section>
  )
}
