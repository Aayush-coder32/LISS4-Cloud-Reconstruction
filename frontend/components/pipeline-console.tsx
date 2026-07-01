"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createCloudMask, fetchAssets, runFusion, runPrediction, runSuperResolution } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";

export function PipelineConsole() {
  const queryClient = useQueryClient();
  const { data: assets = [] } = useQuery({ queryKey: ["assets"], queryFn: fetchAssets });
  const [primaryId, setPrimaryId] = useState("");
  const [temporalIds, setTemporalIds] = useState<string[]>([]);
  const [sarId, setSarId] = useState("");
  const [generatorModel, setGeneratorModel] = useState("classical");
  const [srModel, setSrModel] = useState("none");

  const temporalOptions = useMemo(() => assets.filter((asset) => asset.id !== primaryId), [assets, primaryId]);

  const predictMutation = useMutation({
    mutationFn: () =>
      runPrediction({
        image_id: primaryId,
        temporal_image_ids: temporalIds,
        sar_image_id: sarId || undefined,
        generator_model: generatorModel,
        super_resolution_model: srModel,
        enhance: true,
        use_deep_cloud_model: false,
        explainability: true
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
    }
  });

  const maskMutation = useMutation({
    mutationFn: () => createCloudMask(primaryId, "heuristic"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["history"] })
  });

  const fusionMutation = useMutation({
    mutationFn: () => runFusion({ image_id: primaryId, temporal_image_ids: temporalIds, sar_image_id: sarId || undefined }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["history"] })
  });

  const srMutation = useMutation({
    mutationFn: () => runSuperResolution(primaryId, srModel === "none" ? "realesrgan" : srModel),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["history"] })
  });

  return (
    <Card>
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-mint/80">Pipeline</p>
      <h2 className="mt-2 text-xl font-semibold">Launch reconstruction jobs</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <Select value={primaryId} onChange={(event) => setPrimaryId(event.target.value)}>
          <option value="">Select primary image</option>
          {assets.map((asset) => (
            <option key={asset.id} value={asset.id}>
              {asset.filename}
            </option>
          ))}
        </Select>
        <Select value={sarId} onChange={(event) => setSarId(event.target.value)}>
          <option value="">Optional SAR image</option>
          {temporalOptions.map((asset) => (
            <option key={asset.id} value={asset.id}>
              {asset.filename}
            </option>
          ))}
        </Select>
        <Select
          multiple
          className="min-h-36"
          value={temporalIds}
          onChange={(event) =>
            setTemporalIds(Array.from(event.target.selectedOptions).map((option) => option.value))
          }
        >
          {temporalOptions.map((asset) => (
            <option key={asset.id} value={asset.id}>
              {asset.filename}
            </option>
          ))}
        </Select>
        <div className="grid gap-4">
          <Select value={generatorModel} onChange={(event) => setGeneratorModel(event.target.value)}>
            <option value="classical">Classical baseline</option>
            <option value="pix2pixhd">Pix2PixHD</option>
            <option value="cyclegan">CycleGAN</option>
            <option value="latent_diffusion">Latent Diffusion</option>
            <option value="stable_diffusion">Stable Diffusion</option>
          </Select>
          <Select value={srModel} onChange={(event) => setSrModel(event.target.value)}>
            <option value="none">No super-resolution</option>
            <option value="realesrgan">Real-ESRGAN</option>
            <option value="swinir">SwinIR</option>
          </Select>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-3">
        <Button onClick={() => maskMutation.mutate()} disabled={!primaryId || maskMutation.isPending}>
          Cloud Mask
        </Button>
        <Button onClick={() => fusionMutation.mutate()} disabled={!primaryId || fusionMutation.isPending} variant="secondary">
          Fusion
        </Button>
        <Button onClick={() => predictMutation.mutate()} disabled={!primaryId || predictMutation.isPending}>
          Reconstruct
        </Button>
        <Button onClick={() => srMutation.mutate()} disabled={!primaryId || srMutation.isPending} variant="ghost">
          Super Resolution
        </Button>
      </div>
      {[predictMutation, maskMutation, fusionMutation, srMutation].map((mutation, index) =>
        mutation.error ? (
          <p key={index} className="mt-3 text-sm text-red-300">
            {mutation.error.message}
          </p>
        ) : null
      )}
    </Card>
  );
}
