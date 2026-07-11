import os
import subprocess
import tempfile

import soundfile as sf
import torch
import torchaudio
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

MODEL_NAME = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_feature_extractor = None
_model = None


def _load_model():
    global _feature_extractor, _model
    if _model is None:
        _feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
        _model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
        _model.to(DEVICE)
        _model.eval()
        print("AI voice detector loaded.")
        print("Running on:", DEVICE)
        print("Labels:", _model.config.id2label)


def get_sample_rate():
    sample_rate = getattr(_feature_extractor, "sampling_rate", None)
    return int(sample_rate or 16000)


def convert_to_wav(input_path, target_sample_rate):
    if not input_path:
        raise ValueError("Audio path is missing.")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Audio file not found: {input_path}")

    temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_path = temp.name
    temp.close()

    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", str(target_sample_rate),
        "-c:a", "pcm_s16le",
        wav_path,
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        if os.path.exists(wav_path):
            os.remove(wav_path)
        details = completed.stderr.strip()
        raise RuntimeError(
            "FFmpeg conversion failed: "
            + (details[-700:] if details else "unknown error")
        )

    if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
        raise RuntimeError("FFmpeg produced an empty WAV file.")

    return wav_path


def detect_ai_voice(audio_path):
    wav_path = None

    try:
        _load_model()

        target_sr = get_sample_rate()
        wav_path = convert_to_wav(audio_path, target_sr)

        audio_data, sample_rate = sf.read(
            wav_path,
            dtype="float32",
            always_2d=False,
        )

        if audio_data is None or audio_data.size == 0:
            raise ValueError("The converted recording has no readable audio.")

        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        waveform = torch.from_numpy(audio_data).unsqueeze(0)
        duration = waveform.shape[1] / sample_rate

        if duration < 2:
            return {
                "is_likely_ai": None,
                "error": "Recording too short. Record at least 2 seconds.",
            }

        if duration > 20:
            waveform = waveform[:, : 20 * sample_rate]
            duration = 20

        if sample_rate != target_sr:
            waveform = torchaudio.functional.resample(
                waveform,
                sample_rate,
                target_sr,
            )

        audio_array = waveform.squeeze(0).cpu().numpy()

        inputs = _feature_extractor(
            audio_array,
            sampling_rate=target_sr,
            return_tensors="pt",
        )

        inputs = {key: value.to(DEVICE) for key, value in inputs.items()}

        with torch.no_grad():
            logits = _model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)[0].cpu()

        labels = _model.config.id2label
        scores = {
            str(labels[i]): round(float(probabilities[i]), 4)
            for i in range(len(probabilities))
        }

        fake_keywords = ("fake", "spoof", "synthetic", "ai", "deepfake")
        matches = [
            probability
            for label, probability in scores.items()
            if any(keyword in label.lower() for keyword in fake_keywords)
        ]

        if not matches:
            return {
                "is_likely_ai": None,
                "error": "The model labels could not be interpreted.",
                "raw_scores": scores,
            }

        ai_probability = max(matches)

        if ai_probability >= 0.85:
            verdict = "Very Likely AI"
        elif ai_probability >= 0.65:
            verdict = "Likely AI"
        elif ai_probability >= 0.40:
            verdict = "Uncertain"
        else:
            verdict = "Likely Human"

        return {
            "verdict": verdict,
            "is_likely_ai": ai_probability > 0.5,
            "ai_confidence": round(ai_probability * 100, 2),
            "duration": round(duration, 2),
            "sample_rate": target_sr,
            "raw_scores": scores,
        }

    except Exception as error:
        return {
            "is_likely_ai": None,
            "error": f"{type(error).__name__}: {error}",
        }

    finally:
        if wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except OSError:
                pass


if __name__ == "__main__":
    print("AI Voice Detector Ready")