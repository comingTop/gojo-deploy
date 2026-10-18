"""Generate the Gojo PT-BR voice lines ONCE with Chatterbox Multilingual.

Chatterbox is MIT-licensed (commercial use OK), so the audio is yours forever
with no subscription — exactly what the client was promised. You supply a short
REFERENCE clip that defines an ORIGINAL Gojo-style voice. Do NOT use the real
Brazilian dub actor's voice (voice/personality rights — design spec risk R4);
use an original/generic performance.

Usage:
    python voice/generate.py --reference path/to/gojo_reference.wav

Produces one wav per reaction id (names match config/reactions.json voice_clip)
into voice/output/. API verified against resemble-ai/chatterbox (Chatterbox
MultilingualTTS, language_id="pt").
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Gojo PT-BR voice lines (Chatterbox)")
    ap.add_argument("--reference", required=True,
                    help="reference voice clip (.wav) — an ORIGINAL voice, never the dub actor")
    ap.add_argument("--lines", default=str(HERE / "lines.pt-br.json"))
    ap.add_argument("--out", default=str(HERE / "output"))
    ap.add_argument("--language", default="pt")
    args = ap.parse_args()

    lines: dict[str, str] = json.loads(Path(args.lines).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    device = _device()
    print(f"[voice] loading Chatterbox Multilingual on {device} (first run downloads the model)…")
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")

    for reaction_id, text in lines.items():
        print(f"[voice] {reaction_id}: {text!r}")
        wav = model.generate(text, language_id=args.language, audio_prompt_path=args.reference)
        path = out / f"{reaction_id}.wav"
        ta.save(str(path), wav, model.sr)
        print(f"[voice] wrote {path}")

    print(f"[voice] done → {out} (these files are yours, commercial use OK, no subscription)")


if __name__ == "__main__":
    main()
