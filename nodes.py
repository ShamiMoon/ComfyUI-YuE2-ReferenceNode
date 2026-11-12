import base64
import io
import json
import os
import urllib.error
import urllib.request
import wave

import torch


def _audio_to_wav_bytes(audio):
    if not isinstance(audio, dict) or "waveform" not in audio or "sample_rate" not in audio:
        raise ValueError("reference_audio must be a ComfyUI AUDIO object")
    waveform = audio["waveform"].detach().float().cpu().clamp(-1, 1)
    if waveform.ndim != 3 or waveform.shape[0] < 1:
        raise ValueError("reference_audio waveform must have shape [B, C, T]")
    samples = waveform[0]
    channels, length = samples.shape
    pcm = (samples.transpose(0, 1).numpy() * 32767).astype("<i2").tobytes()
    out = io.BytesIO()
    with wave.open(out, "wb") as handle:
        handle.setnchannels(int(channels))
        handle.setsampwidth(2)
        handle.setframerate(int(audio["sample_rate"]))
        handle.writeframes(pcm)
    return out.getvalue()


def _decode_wav(payload):
    with wave.open(io.BytesIO(payload), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    data = torch.frombuffer(bytearray(frames), dtype=torch.int16).float() / 32768.0
    waveform = data.reshape(-1, channels).transpose(0, 1).unsqueeze(0).contiguous()
    return {"waveform": waveform, "sample_rate": sample_rate}


class YuE2ReferenceSong:
    """Submit a reference-conditioned YuE2 request to a local worker."""

    CATEGORY = "audio/YuE2"
    FUNCTION = "generate"
    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "request_manifest")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_audio": ("AUDIO",),
                "lyrics": ("STRING", {"multiline": True}),
                "style_prompt": ("STRING", {"multiline": True}),
                "reference_strength": ("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.0, "step": 0.01}),
                "melody_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "style_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "worker_url": ("STRING", {"default": "http://127.0.0.1:8188/v1/yue2/generate"}),
                "timeout_seconds": ("INT", {"default": 1800, "min": 1, "max": 86400}),
            },
        }

    def generate(
        self,
        reference_audio,
        lyrics,
        style_prompt,
        reference_strength,
        melody_strength,
        style_strength,
        worker_url,
        timeout_seconds,
    ):
        if not lyrics.strip():
            raise ValueError("lyrics must not be empty")
        wav = _audio_to_wav_bytes(reference_audio)
        request_data = {
            "lyrics": lyrics,
            "style_prompt": style_prompt,
            "reference_strength": float(reference_strength),
            "melody_strength": float(melody_strength),
            "style_strength": float(style_strength),
            "reference_audio_wav_base64": base64.b64encode(wav).decode("ascii"),
        }
        body = json.dumps(request_data).encode("utf-8")
        request = urllib.request.Request(
            worker_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=int(timeout_seconds)) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"YuE2 worker request failed: {exc}") from exc
        if "audio_wav_base64" not in response_data:
            raise RuntimeError("YuE2 worker response must contain audio_wav_base64")
        output_audio = _decode_wav(base64.b64decode(response_data["audio_wav_base64"]))
        manifest = json.dumps(
            {"worker_url": worker_url, **{k: v for k, v in request_data.items() if k != "reference_audio_wav_base64"}},
            ensure_ascii=False,
            indent=2,
        )
        return (output_audio, manifest)


NODE_CLASS_MAPPINGS = {"YuE2ReferenceSong": YuE2ReferenceSong}
NODE_DISPLAY_NAME_MAPPINGS = {"YuE2ReferenceSong": "YuE2 Reference Song"}
