"""Export the supplied audio index into a static, reproducible demo collection."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import wave
from collections import defaultdict

MODELS = ["F5-TTS", "IndexTTS2", "CosyVoice3", "VoxCPM2"]
METHODS = ["NoiseStamp", "AudioSeal-utt", "AudioSeal-str", "WavMark", "Perth", "VoiceMark", "TraceableSpeech"]
CATEGORIES = {"listening": "listening", "case study": "caseStudies", "verification": "preview"}


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build(source, destination):
    source = source.resolve()
    index = source / "音频索引.csv"
    with index.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    grouped = defaultdict(list)
    for row in rows:
        path = (source / row["文件"]).resolve()
        if not path.is_relative_to(source) or not path.is_file():
            raise ValueError(f"Invalid source audio: {row['文件']}")
        key = (row["类别"], row["语音模型"], row["水印方法"], row["语言"], str(Path(row["文件"]).parent))
        grouped[key].append(row)

    manifest = {"version": 1, "models": MODELS, "methods": METHODS, "listening": [], "preview": []}
    counters = defaultdict(int)
    exported = set()
    for key, entries in sorted(grouped.items()):
        category, model, method, language, _ = key
        group = CATEGORIES[category]
        counters[key[:4]] += 1
        number = counters[key[:4]]
        if group != "listening":
            continue
        selected_number = 2 if language == "zh" and model in {"CosyVoice3", "VoxCPM2"} else 1
        if group == "listening" and (number != selected_number or not (method == "NoiseStamp" or (model == "IndexTTS2" and language == "en"))):
            continue
        sample_id = "-".join([slug(group), slug(model), slug(method), language, f"{number:02d}"])
        transcripts = {entry["文本"] for entry in entries}
        if len(transcripts) != 1:
            raise ValueError(f"Inconsistent transcripts for {sample_id}")
        record = {"id": sample_id, "model": model, "method": method, "language": language,
                  "example": number, "transcript": transcripts.pop(),
                  "reference": {}, "watermarked": {}}
        for entry in entries:
            state = {"original": "reference", "watermarked": "watermarked"}[entry["水印状态"]]
            length = {"full": "full", "1s": "excerpt"}[entry["长度类型"]]
            if length in record[state]:
                raise ValueError(f"Duplicate audio in {sample_id}")
            original = source / entry["文件"]
            relative = Path("assets/audio") / slug(group) / slug(model) / slug(method) / language / f"{number:02d}" / f"{state}-{length}.wav"
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            with wave.open(str(target)) as audio:
                duration = audio.getnframes() / audio.getframerate()
                sample_rate = audio.getframerate()
                channels = audio.getnchannels()
                sample_width = audio.getsampwidth()
            if abs(duration - float(entry["时长（秒）"])) > 0.001:
                raise ValueError(f"Indexed duration mismatch: {sample_id}")
            if sample_rate != int(entry["采样率（Hz）"]) or channels != 1 or sample_width != 2:
                raise ValueError(f"Unexpected audio format: {sample_id}")
            if length == "excerpt" and abs(duration - 1) > 1 / sample_rate:
                raise ValueError(f"Excerpt is not one second: {sample_id}")
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != hashlib.sha256(original.read_bytes()).hexdigest():
                raise ValueError(f"Copy mismatch: {sample_id}")
            record[state][length] = {"src": relative.as_posix(), "duration": round(duration, 4),
                                      "sampleRate": sample_rate, "sha256": digest}
            exported.add(relative.as_posix())
        expected = {"excerpt"} if group == "preview" else {"full", "excerpt"}
        if any(set(record[state]) != expected for state in ("reference", "watermarked")):
            raise ValueError(f"Incomplete audio pair: {sample_id}")
        manifest[group].append(record)

    for group in ("listening", "preview"):
        manifest[group].sort(key=lambda sample: (MODELS.index(sample["model"]), METHODS.index(sample["method"]), sample["language"], sample["example"]))
    assert len(manifest["listening"]) == 14
    assert len(manifest["preview"]) == 0
    assert len(exported) == 56
    manifest["counts"] = {"listeningPairs": 14, "previewPairs": 0, "audioFiles": len(exported)}
    output = destination / "data/samples.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(exported)} byte-identical WAV files and {len(manifest['listening']) + len(manifest['preview'])} curated comparison pairs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    build(arguments.source, arguments.destination)
