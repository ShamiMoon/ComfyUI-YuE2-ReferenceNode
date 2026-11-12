# ComfyUI YuE2 Reference Node

An independent ComfyUI custom node for reference-conditioned YuE2 generation.

Install by placing this directory under `ComfyUI/custom_nodes/`. The node follows
ComfyUI's native `AUDIO` object (`waveform` plus `sample_rate`) and submits a JSON
request to a local YuE2 worker. The worker is intentionally separate because the
YuE2/SheetSage2 dependency set should not be imported into ComfyUI's process.

The worker endpoint must accept:

```json
{
  "lyrics": "...",
  "style_prompt": "...",
  "reference_strength": 0.75,
  "melody_strength": 1.0,
  "style_strength": 1.0,
  "reference_audio_wav_base64": "..."
}
```

and return `{ "audio_wav_base64": "..." }`. The strength fields are explicit
conditioning controls; the worker must map them to its actual melody/audio adapter or
LoRA implementation rather than treating them as prompt text.
