import "maplibre-gl/dist/maplibre-gl.css";

import { useEffect, useRef } from "react";
import maplibregl, { type Map as MapLibre } from "maplibre-gl";

import type { VineyardSummary } from "../types";

interface Props {
  vineyards: VineyardSummary[];
  onSelect: (id: number) => void;
}

/**
 * MapLibre map of the pilot vineyards. OSM raster tiles — no API key needed.
 *
 * The map is centred on the centroid of the supplied vineyards so the view
 * adapts when more pilot sites are added without code changes.
 */
export function VineyardMap({ vineyards, onSelect }: Props): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibre | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const lats = vineyards.map((v) => v.centroid.lat);
    const lons = vineyards.map((v) => v.centroid.lon);
    const centerLat = lats.length > 0 ? avg(lats) : -33.32;
    const centerLon = lons.length > 0 ? avg(lons) : 148.96;

    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [centerLon, centerLat],
      zoom: 11,
    });

    const map = mapRef.current;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    for (const v of vineyards) {
      const el = document.createElement("button");
      el.className =
        "h-3 w-3 rounded-full border-2 border-white bg-emerald-600 shadow ring-2 ring-emerald-700/30 hover:scale-125 transition";
      el.title = v.name;
      el.addEventListener("click", () => onSelect(v.id));

      new maplibregl.Marker({ element: el })
        .setLngLat([v.centroid.lon, v.centroid.lat])
        .setPopup(
          new maplibregl.Popup({ offset: 12 }).setHTML(
            `<div class="text-sm"><div class="font-semibold">${escapeHtml(v.name)}</div><div class="text-slate-500">${escapeHtml(v.region)}</div></div>`,
          ),
        )
        .addTo(map);
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [vineyards, onSelect]);

  return <div ref={containerRef} className="h-full w-full" />;
}

function avg(xs: number[]): number {
  return xs.reduce((s, n) => s + n, 0) / xs.length;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>'"]/g, (c) => {
    switch (c) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case "'":
        return "&#39;";
      case '"':
        return "&quot;";
      default:
        return c;
    }
  });
}
