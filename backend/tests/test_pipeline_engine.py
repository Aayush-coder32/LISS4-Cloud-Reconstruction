import numpy as np

from gencloudnet_ml.pipeline import PipelineConfig, PipelineEngine


def test_pipeline_engine_produces_artifacts() -> None:
    primary = np.random.default_rng(7).random((4, 64, 64), dtype=np.float32)
    temporal = [np.random.default_rng(11).random((4, 64, 64), dtype=np.float32)]
    sar = np.random.default_rng(13).random((1, 64, 64), dtype=np.float32)

    engine = PipelineEngine(PipelineConfig(explainability=True, enhance=True))
    artifacts = engine.run(primary, temporal_images=temporal, sar_image=sar, reference_target=temporal[0])

    assert artifacts.cloud_mask.shape == (64, 64)
    assert artifacts.fused.shape[1:] == (64, 64)
    assert artifacts.reconstruction.shape[1:] == (64, 64)
    assert artifacts.confidence.shape == (64, 64)
    assert artifacts.explainability is not None
    assert "psnr" in artifacts.metrics
