"use client";

import "leaflet/dist/leaflet.css";

import { useEffect, useMemo, useRef } from "react";

type Bounds = { left: number; bottom: number; right: number; top: number };

type LeafletModule = typeof import("leaflet");

const DEFAULT_BOUNDS: [[number, number], [number, number]] = [
  [20.5937, 68.1097],
  [28.7041, 88.3639]
];

export function LeafletMap({
  bounds,
  overlayUrl,
  geoJson
}: {
  bounds: Bounds | null;
  overlayUrl?: string | null;
  geoJson?: any;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const overlayRef = useRef<import("leaflet").ImageOverlay | null>(null);
  const geoJsonRef = useRef<import("leaflet").GeoJSON | null>(null);
  const tileLayerRef = useRef<import("leaflet").TileLayer | null>(null);

  const boundsKey = useMemo(() => {
    if (!bounds) {
      return "default";
    }
    return `${bounds.left}:${bounds.bottom}:${bounds.right}:${bounds.top}`;
  }, [bounds]);

  const geoJsonKey = useMemo(() => (geoJson ? JSON.stringify(geoJson) : "none"), [geoJson]);

  useEffect(() => {
    let cancelled = false;

    async function initializeMap() {
      const L: LeafletModule = await import("leaflet");
      const container = containerRef.current;

      if (cancelled || !container) {
        return;
      }

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      // Leaflet tracks initialized DOM nodes with a private id, which can survive
      // fast refresh and trigger "Map container is already initialized".
      if ("_leaflet_id" in container) {
        delete (container as HTMLDivElement & { _leaflet_id?: number })._leaflet_id;
      }

      const map = L.map(container, {
        zoomControl: true,
        preferCanvas: true
      });
      mapRef.current = map;

      const activeBounds: [[number, number], [number, number]] = bounds
        ? [
            [bounds.bottom, bounds.left],
            [bounds.top, bounds.right]
          ]
        : DEFAULT_BOUNDS;

      tileLayerRef.current = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
      }).addTo(map);

      map.fitBounds(activeBounds, { padding: [20, 20] });

      if (bounds && overlayUrl) {
        overlayRef.current = L.imageOverlay(overlayUrl, activeBounds, { opacity: 0.8 }).addTo(map);
      } else {
        overlayRef.current = null;
      }

      if (geoJson) {
        geoJsonRef.current = L.geoJSON(geoJson).addTo(map);
      } else {
        geoJsonRef.current = null;
      }
    }

    void initializeMap();

    return () => {
      cancelled = true;
      overlayRef.current = null;
      geoJsonRef.current = null;
      tileLayerRef.current = null;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      if (containerRef.current && "_leaflet_id" in containerRef.current) {
        delete (containerRef.current as HTMLDivElement & { _leaflet_id?: number })._leaflet_id;
      }
    };
  }, [bounds, boundsKey, geoJson, geoJsonKey, overlayUrl]);

  return <div ref={containerRef} className="h-[340px] w-full overflow-hidden rounded-2xl" />;
}
