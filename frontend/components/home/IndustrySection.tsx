const industries = [
  {
    title: "Vård & Omsorg",
    href: "/shop?category=vard-omsorg",
    image: "/hero-vard.png",
  },
  {
    title: "Kök & Restaurang",
    href: "/shop?category=kok",
    image: "/hero-kok.png",
  },
  {
    title: "Städ & Service",
    href: "/shop?category=stad-service",
    image: "/hero-stad.png",
  },
  {
    title: "Skönhet & Wellness",
    href: "/shop?category=skonhet",
    image: "/hero-skonhet.png",
  },
]

export function IndustrySection() {
  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-20">
      <h2 className="text-xl font-semibold text-gray-900 mb-8">Branscher &amp; arbetsområden</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
        {industries.map(({ title, href, image }) => (
          <a
            key={title}
            href={href}
            className="group relative rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 aspect-[3/4]"
          >
            {/* Background image */}
            <img
              src={image}
              alt={title}
              className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
            {/* Dark overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-gray-900/80 via-gray-900/20 to-transparent" />
            {/* Title */}
            <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
              <p className="text-white font-semibold text-sm md:text-base leading-snug">{title}</p>
              <p className="text-gray-300 text-xs mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                Utforska →
              </p>
            </div>
          </a>
        ))}
      </div>
    </section>
  )
}
