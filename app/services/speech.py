from functools import lru_cache
from pathlib import Path

import av
import numpy as np
from faster_whisper import WhisperModel

from app.config import BASE_DIR, settings

MODEL_DIR = BASE_DIR / "storage" / "models"     # inside the project, never committed
SAMPLE_RATE = 16000                             # Whisper expects 16 kHz mono audio


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8",
                        download_root=str(MODEL_DIR))


def _load_audio(path: Path) -> np.ndarray:
    """Decode any audio file (webm, m4a, mp3, wav) to 16 kHz mono floats."""
    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    chunks = []
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            chunks.extend(f.to_ndarray() for f in resampler.resample(frame))
        chunks.extend(f.to_ndarray() for f in resampler.resample(None))   # flush the last samples
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks, axis=1).flatten().astype(np.float32) / 32768.0


def transcribe(path: Path) -> str:
    segments, _ = _model().transcribe(_load_audio(path), language="en", vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments)