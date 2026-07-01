"use client";

import { ExternalLink } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Job } from "@/lib/types";
import { toPublicFileUrl } from "@/lib/api";

export function ResultCard({ job }: { job: Job }) {
  const links = [
    { label: "Result", href: toPublicFileUrl(job.result_path) },
    { label: "Fusion", href: toPublicFileUrl(job.fused_path) },
    { label: "Mask", href: toPublicFileUrl(job.mask_path) },
    { label: "Confidence", href: toPublicFileUrl(job.confidence_path) },
    { label: "Explainability", href: toPublicFileUrl(job.explainability_path) }
  ].filter((item) => item.href);

  return (
    <Card className="h-full">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">{job.task_type}</p>
          <h3 className="mt-2 text-lg font-semibold text-white">{job.status}</h3>
          <p className="mt-1 text-sm text-cloud/65">{new Date(job.created_at).toLocaleString()}</p>
        </div>
        <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cloud/70">
          {job.generator_model}
        </span>
      </div>
      <div className="mt-5 grid gap-2 text-sm text-cloud/80">
        {Object.entries(job.metrics_json).slice(0, 6).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between border-b border-white/5 pb-2">
            <span>{key}</span>
            <span>{Number(value).toFixed(3)}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs uppercase tracking-[0.2em] text-cloud/80 hover:bg-white/5"
          >
            {link.label}
            <ExternalLink size={12} />
          </a>
        ))}
      </div>
      {job.error_message ? <p className="mt-4 text-sm text-red-300">{job.error_message}</p> : null}
    </Card>
  );
}
