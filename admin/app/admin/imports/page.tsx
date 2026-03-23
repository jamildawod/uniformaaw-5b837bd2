import { Panel } from "@/components/ui/panel";
import { CsvImportPanel } from "@/components/admin/csv-import-panel";
import { fetchPimImports } from "@/lib/api/server";
import type { PimImportRun } from "@/lib/types/pim";

export default async function AdminImportsPage() {
  let imports: PimImportRun[] = [];

  try {
    imports = await fetchPimImports();
  } catch (error) {
    console.error("Failed to fetch imports:", error);
  }

  return (
    <div className="space-y-6">
      <Panel>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">
          PIM control
        </p>
        <h2 className="mt-1 text-2xl font-semibold text-ink">
          CSV import system
        </h2>
        <p className="mt-3 text-sm text-slate-500">
          Upload a supplier CSV, then trigger the import run. Logs refresh automatically
          so you can monitor status, timestamps, and any errors.
        </p>

        <div className="mt-6">
          <CsvImportPanel initialLogs={imports} />
        </div>
      </Panel>
    </div>
  );
}
