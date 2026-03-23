interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  trend?: { value: string; positive?: boolean };
}

export function StatCard({ label, value, sub, trend }: StatCardProps) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">{label}</p>
      <p className="mt-3 text-4xl font-semibold tabular-nums text-ink">{value}</p>
      {sub ? <p className="mt-2 text-sm text-slate-500">{sub}</p> : null}
      {trend ? (
        <p className={`mt-2 text-xs font-medium ${trend.positive ? "text-green-600" : "text-red-600"}`}>
          {trend.value}
        </p>
      ) : null}
    </div>
  );
}

interface InfoCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export function InfoCard({ title, description, children, action }: InfoCardProps) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-ink">{title}</p>
          {description ? <p className="mt-1 text-xs text-slate-500">{description}</p> : null}
        </div>
        {action ?? null}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
