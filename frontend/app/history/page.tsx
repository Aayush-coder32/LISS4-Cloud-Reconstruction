"use client";

import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/app-shell";
import { ResultCard } from "@/components/result-card";
import { Card } from "@/components/ui/card";
import { fetchHistory } from "@/lib/api";

export default function HistoryPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["history"], queryFn: fetchHistory });

  return (
    <AppShell>
      <section className="space-y-6">
        <div className="rounded-xl2 border border-white/10 bg-black/15 p-6 shadow-panel">
          <p className="font-mono text-xs uppercase tracking-[0.35em] text-mint/80">Audit Trail</p>
          <h1 className="mt-3 text-4xl font-bold text-white">Inference and reconstruction history</h1>
          <p className="mt-4 max-w-2xl text-cloud/75">
            Review generated masks, fused products, reconstructions, and validation metrics for every processed scene.
          </p>
        </div>
        {isLoading ? <Card>Loading jobs...</Card> : null}
        {error instanceof Error ? <Card>{error.message}</Card> : null}
        <div className="grid gap-4 xl:grid-cols-2">
          {data?.jobs.map((job) => <ResultCard key={job.id} job={job} />)}
        </div>
      </section>
    </AppShell>
  );
}
