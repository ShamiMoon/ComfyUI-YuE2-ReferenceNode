# ComfyUI YuE2 Reference Node

This repository currently packages the native ComfyUI node layer from T8mars/Comfyui-YuE2-T8.
It connects to the T8 YuE2 service on `http://127.0.0.1:8189` by default.

Install this directory under `ComfyUI/custom_nodes/` and restart ComfyUI. Install and start the
T8 YuE2 runtime/service separately; the custom node layer alone does not contain model weights or
the service runtime.

Included nodes cover YuE2 model service, song generation, transcription, melody remake, reference
voice cover, RVC, style training, staged semantic/synthesis/decode, and artifact export.

Source: https://github.com/T8mars/Comfyui-YuE2-T8
