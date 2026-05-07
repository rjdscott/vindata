import { QueryClientProvider } from "@tanstack/react-query";
import { Link, Route, BrowserRouter, Routes } from "react-router-dom";

import { queryClient } from "./lib/queryClient";
import { OverviewPage } from "./pages/OverviewPage";
import { VineyardPage } from "./pages/VineyardPage";

export function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <span aria-hidden className="text-emerald-700">●</span>
            VinData
            <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-normal text-slate-600">
              Stage 00 · Orange NSW
            </span>
          </Link>
          <span className="text-xs text-slate-500">
            Public-data PoC — advisory only
          </span>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/vineyards/:id" element={<VineyardPage />} />
          </Routes>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
