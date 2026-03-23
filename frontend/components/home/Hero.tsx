export default function Hero() {
  try {
    return (
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="rounded-3xl bg-gray-900 text-white overflow-hidden relative min-h-[380px] md:min-h-[460px] flex flex-col justify-end">
          {/* Background image */}
          <img
            src="/hero-vard.png"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover opacity-30"
          />
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/70 to-gray-900/20" />
          {/* Content */}
          <div className="relative z-10 p-10 md:p-16">
            <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">
              Professionella arbetskläder
            </p>
            <h1 className="text-3xl md:text-5xl font-semibold leading-tight max-w-xl">
              Arbetskläder för<br />professionella team
            </h1>
            <p className="mt-4 text-gray-300 text-base max-w-md">
              För vård, service och restaurang – kvalitet som håller
            </p>
            <div className="mt-8">
              <a
                href="/shop"
                className="inline-block rounded-full bg-white text-gray-900 px-8 py-3 text-sm font-semibold tracking-wide hover:bg-gray-100 transition"
              >
                Se alla produkter
              </a>
            </div>
          </div>
        </div>
      </section>
    )
  } catch {
    return null
  }
}
