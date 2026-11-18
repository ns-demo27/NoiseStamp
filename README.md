# NoiseStamp audio demonstration

A static research demo for **NoiseStamp: Training-Free Multi-Bit Watermarking for Streaming Text-to-Speech via Noise-Space Embedding**.

## Contents

- A one-second reference / NoiseStamp preview from F5-TTS.
- Selected English and Chinese NoiseStamp examples across F5-TTS, IndexTTS2, CosyVoice3, and VoxCPM2.
- One English listening comparison per method on IndexTTS2, including six baselines and NoiseStamp.
- A small table of aggregate results reported in the manuscript.

The collection contains 14 curated listening pairs with full and one-second versions, plus one independent preview pair: 58 WAV files in total. Recordings are copied without resampling, normalization, trimming, or other modification. The original-language spoken text is available beneath each pair; the interface is English.

Examples are illustrative, not a matched-sentence ranking or a substitute for aggregate evaluation. Reference and watermarked recordings may be separate synthesis draws. This page does not run a watermark decoder or simulate acceptance results.

## Local preview

Serve this directory over HTTP, for example:

```bash
python -m http.server 8765
```

Open `http://localhost:8765/`. No package installation, build framework, analytics, external fonts, or third-party runtime scripts are required.

## Audio preparation

The export script accepts the directory containing the supplied audio index and recordings:

```bash
python -I scripts/prepare_audio.py --source /path/to/source-audio
```

Selection is fixed by model, method, language, and source example order, not by computed audio-quality scores. Two Chinese examples use the second supplied variant to avoid a spoken-text claim about a public detector being mistaken for a claim about NoiseStamp's shared-seed decoder. No source CSV or local filesystem path is published in the generated manifest.

Check the complete public collection:

```bash
python -I scripts/check_site.py
```

## GitHub Pages

Publish the `main` branch from the repository root. All asset URLs are relative, so the site works at a project URL such as `https://ns-demo27.github.io/NoiseStamp/`.

The existing repository license is retained.
