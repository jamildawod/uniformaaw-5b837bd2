export function Footer() {
  return (
    <footer className="bg-gray-100 mt-20">
      <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-2 gap-10">

        {/* COMPANY */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Uniforma</h3>
          <p className="text-gray-600 text-sm leading-relaxed">
            Arbetskläder och profilplagg för professionella miljöer.
          </p>
          <div className="mt-6 space-y-2 text-sm text-gray-700">
            <p>E-post: info@uniforma.se</p>
            <p>Telefon: 070-000 00 00</p>
            <p>Adress: Sverige</p>
          </div>
        </div>

        {/* NAVIGATION */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Navigation</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li><a href="/" className="hover:underline">Startsida</a></li>
            <li><a href="/shop" className="hover:underline">Produkter</a></li>
            <li><a href="/om-oss" className="hover:underline">Om oss</a></li>
            <li><a href="/kontakt" className="hover:underline">Kontakt</a></li>
            <li><a href="/storleksguide" className="hover:underline">Storleksguide</a></li>
          </ul>
        </div>

      </div>

      <div className="border-t text-center text-xs text-gray-500 py-4">
        © {new Date().getFullYear()} Uniforma. Alla rättigheter förbehållna.
      </div>
    </footer>
  );
}
