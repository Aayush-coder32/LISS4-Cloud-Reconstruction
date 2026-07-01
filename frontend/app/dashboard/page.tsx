"use client";

import { useQuery } from "@tanstack/react-query";
import { Gauge, Layers3, Timer, TriangleAlert } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { MapView } from "@/components/map-view";
import { PipelineConsole } from "@/components/pipeline-console";
import { ResultCard } from "@/components/result-card";
import { UploadPanel } from "@/components/upload-panel";
import { Card } from "@/components/ui/card";
import { fetchAssets, fetchHistory, fetchMetrics, toPublicFileUrl } from "@/lib/api";

const stats = [
  { key: "cloud_percentage_mean", label: "Mean cloud cover", icon: Layers3, suffix: "%" },
  { key: "average_processing_seconds", label: "Avg processing", icon: Timer, suffix: "s" },
  { key: "completed_jobs", label: "Completed jobs", icon: Gauge, suffix: "" },
  { key: "failed_jobs", label: "Failed jobs", icon: TriangleAlert, suffix: "" }
] as const;

export default function DashboardPage() {
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: fetchMetrics });
  const { data: history } = useQuery({ queryKey: ["history"], queryFn: fetchHistory });
  const { data: assets = [] } = useQuery({ queryKey: ["assets"], queryFn: fetchAssets });

  const latestAsset = assets[0];
  const latestJob = history?.jobs[0];

  return (
    <AppShell>
      <div className="space-y-6">
        <section className="rounded-xl2 border border-white/10 bg-black/15 p-6 text-cloud shadow-panel">
          <p className="font-mono text-xs uppercase tracking-[0.35em] text-mint/80">Operations</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-bold leading-tight text-white">
            Multi-temporal cloud removal, fusion, reconstruction, and geospatial validation in one workstation.
          </h1>
          <p className="mt-4 max-w-2xl text-cloud/75">
            Upload LISS-IV, Sentinel, Landsat, or custom GeoTIFF scenes, then launch cloud masking, temporal fusion,
            and reconstruction jobs with explainability and confidence outputs.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {stats.map(({ key, label, icon: Icon, suffix }) => (
            <Card key={key}>
              <div className="flex items-center justify-between">
                <span className="text-sm text-cloud/65">{label}</span>
                <Icon size={18} className="text-mint" />
              </div>
              <p className="mt-4 text-3xl font-bold text-white">
                {metrics ? Number(metrics[key]).toFixed(key.includes("jobs") ? 0 : 2) : "--"}
                {suffix}
              </p>
            </Card>
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <UploadPanel />
          <PipelineConsole />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <MapView
            title="Latest uploaded scene"
            bounds={latestAsset?.bounds_json ?? null}
            overlayUrl={toPublicFileUrl(latestAsset?.preview_path ?? null)}
          />
          <Card>
            <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">Preview</p>
            <h3 className="mt-2 text-lg font-semibold">Current asset context</h3>
            {latestAsset ? (
              <div className="mt-5 space-y-3 text-sm text-cloud/80">
                <div className="flex justify-between"><span>Filename</span><span>{latestAsset.filename}</span></div>
                <div className="flex justify-between"><span>Resolution</span><span>{latestAsset.width} x {latestAsset.height}</span></div>
                <div className="flex justify-between"><span>Bands</span><span>{latestAsset.band_count}</span></div>
                <div className="flex justify-between"><span>CRS</span><span>{latestAsset.crs ?? "None"}</span></div>
                <div className="flex justify-between"><span>Cloud estimate</span><span>{latestAsset.cloud_coverage?.toFixed(2) ?? "--"}%</span></div>
              </div>
            ) : (
              <p className="mt-5 text-sm text-cloud/65">Upload a scene to populate the geospatial panel.</p>
            )}
          </Card>
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">Results</p>
              <h2 className="mt-2 text-2xl font-semibold">Recent processing jobs</h2>
            </div>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            {history?.jobs.length ? history.jobs.slice(0, 4).map((job) => <ResultCard key={job.id} job={job} />) : <Card>No jobs yet.</Card>}
          </div>
          {latestJob?.result_path ? (
            <div className="mt-6">
              <MapView
                title="Latest reconstruction overlay"
                bounds={latestAsset?.bounds_json ?? null}
                overlayUrl={toPublicFileUrl(latestJob.result_path)}
              />
            </div>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
