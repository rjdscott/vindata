import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api, queryKeys } from "../api/client";
import { AdvisoryBanner } from "../components/AdvisoryBanner";
import { VineyardMap } from "../components/VineyardMap";

export function OverviewPage(): JSX.Element {
  const navigate = useNavigate();
  const vineyardsQ = useQuery({
    queryKey: queryKeys.vineyards,
    queryFn: api.listVineyards,
  });

  return (
    <div className="grid h-[calc(100vh-3.5rem)] grid-cols-1 gap-4 p-4 lg:grid-cols-[1fr_320px]">
      <section className="min-h-[60vh] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {vineyardsQ.isLoading && (
          <div className="flex h-full items-center justify-center text-slate-500">
            Loading map…
          </div>
        )}
        {vineyardsQ.isError && (
          <div className="p-4 text-red-600">
            Failed to load vineyards: {(vineyardsQ.error as Error).message}
          </div>
        )}
        {vineyardsQ.data && (
          <VineyardMap
            vineyards={vineyardsQ.data}
            onSelect={(id) => navigate(`/vineyards/${id}`)}
          />
        )}
      </section>

      <aside className="space-y-4">
        <AdvisoryBanner />
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Pilot vineyards
        </h2>
        <ul className="space-y-2">
          {vineyardsQ.data?.map((v) => (
            <li key={v.id}>
              <button
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm shadow-sm hover:border-emerald-400 hover:bg-emerald-50"
                onClick={() => navigate(`/vineyards/${v.id}`)}
              >
                <div className="font-medium">{v.name}</div>
                <div className="text-xs text-slate-500">
                  {v.region} · {v.centroid.lat.toFixed(3)}, {v.centroid.lon.toFixed(3)}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
