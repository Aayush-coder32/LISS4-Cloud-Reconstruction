"use client";

import { useEffect, useRef } from "react";

type Bounds = { left: number; bottom: number; right: number; top: number };

export function MapboxCanvas({ bounds }: { bounds: Bounds | null }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let map: import("mapbox-gl").Map | undefined;

    async function boot() {
      if (!ref.current || !process.env.NEXT_PUBLIC_MAPBOX_TOKEN) {
        return;
      }
      const mapboxgl = await import("mapbox-gl");
      mapboxgl.default.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
      map = new mapboxgl.default.Map({
        container: ref.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: bounds ? [(bounds.left + bounds.right) / 2, (bounds.top + bounds.bottom) / 2] : [78.9629, 20.5937],
        zoom: 4
      });
      if (bounds) {
        map.fitBounds(
          [
            [bounds.left, bounds.bottom],
            [bounds.right, bounds.top]
          ],
          { padding: 40 }
        );
      }
    }

    boot();
    return () => {
      map?.remove();
    };
  }, [bounds]);

  return <div ref={ref} className="h-[340px] w-full overflow-hidden rounded-2xl" />;
}
