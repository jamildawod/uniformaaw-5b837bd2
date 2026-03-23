interface CtaCardProps {
  title: string
  text: string
  href: string
  label?: string
}

export function CtaCard({ title, text, href, label = "Läs mer" }: CtaCardProps) {
  return (
    <a
      href={href}
      className="flex-1 rounded-2xl border border-gray-200 p-6 bg-white flex flex-col justify-between hover:shadow-md hover:-translate-y-1 transition-all duration-200 group"
    >
      <div>
        <h3 className="text-base font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-500 leading-relaxed">{text}</p>
      </div>
      <span className="mt-4 inline-block text-sm font-medium text-gray-900 group-hover:underline">
        {label} →
      </span>
    </a>
  )
}
