"use client"

import { useEffect, useState } from "react"
import { fetchSuperDeals, type SuperDeal } from "@/lib/api"
import { SuperDealCard } from "@/components/SuperDealCard"

export function SuperDealsSection() {
  const [deals, setDeals] = useState<SuperDeal[]>([])

  useEffect(() => {
    let active = true

    async function loadDeals() {
      try {
        const data = await fetchSuperDeals()

        if (active) {
          setDeals(data.filter((deal) => deal.active === true))
        }
      } catch {
        if (active) setDeals([])
      }
    }

    loadDeals()

    return () => {
      active = false
    }
  }, [])

  return (
    <section className="mx-auto max-w-7xl px-6 py-16">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-400">
            Kampanjer
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-stone-950">
            Super Deals
          </h2>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
        {deals.map((deal) => (
          <SuperDealCard key={deal.id} deal={deal} />
        ))}
      </div>
    </section>
  )
}
