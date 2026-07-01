"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { uploadAsset } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function UploadPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [captureDate, setCaptureDate] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => {
      if (!file) {
        throw new Error("Select a GeoTIFF or PNG first");
      }
      return uploadAsset(file, captureDate);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["history"] });
      setFile(null);
      setCaptureDate("");
    }
  });

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">Ingestion</p>
          <h2 className="mt-2 text-xl font-semibold">Upload multi-band imagery</h2>
        </div>
      </div>
      <div className="mt-5 space-y-4">
        <Input type="file" accept=".tif,.tiff,.png" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <Input type="datetime-local" value={captureDate} onChange={(event) => setCaptureDate(event.target.value)} />
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "Uploading..." : "Upload Scene"}
        </Button>
        {mutation.error ? <p className="text-sm text-red-300">{mutation.error.message}</p> : null}
      </div>
    </Card>
  );
}
