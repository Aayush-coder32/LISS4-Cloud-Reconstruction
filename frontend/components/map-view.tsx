"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const LeafletMap = dynamic(() => import("@/components/leaflet-map").then((module) => module.LeafletMap), {
  ssr: false
});
const MapboxCanvas = dynamic(() => import("@/components/mapbox-canvas").then((module) => module.MapboxCanvas), {
  ssr: false
});

type Bounds = { left: number; bottom: number; right: number; top: number };

export function MapView({
  title,
  bounds,
  overlayUrl
}: {
  title: string;
  bounds: Bounds | null;
  overlayUrl?: string | null;
}) {
  const [mode, setMode] = useState<"leaflet" | "mapbox">("leaflet");

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">GIS</p>
          <h3 className="mt-2 text-lg font-semibold">{title}</h3>
        </div>
        <div className="flex gap-2">
          <Button variant={mode === "leaflet" ? "secondary" : "ghost"} onClick={() => setMode("leaflet")}>
            Leaflet
          </Button>
          <Button variant={mode === "mapbox" ? "secondary" : "ghost"} onClick={() => setMode("mapbox")}>
            Mapbox
          </Button>
        </div>
      </div>
      {mode === "leaflet" ? <LeafletMap bounds={bounds} overlayUrl={overlayUrl} /> : <MapboxCanvas bounds={bounds} />}
    </Card>
  );
}
