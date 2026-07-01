"use client";

import { MapContainer, TileLayer, ImageOverlay, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

type Bounds = { left: number; bottom: number; right: number; top: number };

export function LeafletMap({
  bounds,
  overlayUrl,
  geoJson
}: {
  bounds: Bounds | null;
  overlayUrl?: string | null;
  geoJson?: GeoJSON.GeoJsonObject | null;
}) {
  const mapBounds: [[number, number], [number, number]] = bounds
    ? [
        [bounds.bottom, bounds.left],
        [bounds.top, bounds.right]
      ]
    : [
        [20.5937, 78.9629],
        [28.7041, 77.1025]
      ];

  return (
    <MapContainer bounds={mapBounds} className="h-[340px] w-full overflow-hidden rounded-2xl">
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {bounds && overlayUrl ? <ImageOverlay bounds={mapBounds} url={overlayUrl} opacity={0.8} /> : null}
      {geoJson ? <GeoJSON data={geoJson} /> : null}
    </MapContainer>
  );
}
