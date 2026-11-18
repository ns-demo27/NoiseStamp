"use strict";

(() => {
  const state = { language: "en", length: "full", baselineLength: "full" };
  let data;
  const byId = (id) => document.getElementById(id);
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const durationText = (seconds) => `${seconds.toFixed(seconds === 1 ? 0 : 2)} s`;

  function audioCell(asset, label, context, compact = false) {
    const cell = make("div", compact ? "preview-audio" : "audio-cell");
    const heading = make("div", compact ? "player-label" : "audio-type", label);
    if (compact) heading.append(make("span", "player-meta", `${durationText(asset.duration)} / ${asset.sampleRate / 1000} kHz`));
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.preload = compact ? "metadata" : "none";
    audio.src = asset.src;
    audio.setAttribute("aria-label", `${context}, ${label}, ${durationText(asset.duration)}`);
    const fallback = make("a", "", "Download this recording");
    fallback.href = asset.src;
    audio.append(fallback);
    const error = make("p", "audio-error", "This recording could not be loaded. Reload the page or use the direct audio link.");
    error.hidden = true;
    const download = make("a", "", "Open audio file");
    download.href = asset.src;
    error.append(document.createTextNode(" "), download);
    audio.addEventListener("error", () => { error.hidden = false; });
    cell.append(heading, audio);
    if (!compact) cell.append(make("p", "audio-caption", `${durationText(asset.duration)} / ${asset.sampleRate / 1000} kHz / mono`));
    cell.append(error);
    return cell;
  }

  function comparisonRow(sample, length, byModel) {
    const isOurs = sample.method === "NoiseStamp";
    const row = make("article", `comparison-row${byModel ? " host-row" : isOurs ? " is-ours" : ""}`);
    row.dataset.sample = sample.id;
    const name = make("div", "method-name");
    const title = make("h3", "", byModel ? sample.model : sample.method);
    if (!byModel && isOurs) title.append(make("span", "ours-label", "Ours"));
    const description = byModel ? "NoiseStamp / 32-bit payload" : sample.method === "Perth" ? "Presence-only watermark" : isOurs ? "32-bit payload" : "16-bit payload";
    name.append(title, make("p", "", description));
    const context = `${sample.model}, ${sample.method}, ${sample.language === "en" ? "English" : "Chinese"}, ${length === "full" ? "full recording" : "one-second excerpt"}`;
    const transcript = make("details", "transcript");
    transcript.append(make("summary", "", "Spoken text"));
    const text = make("p", "", sample.transcript);
    text.lang = sample.language === "zh" ? "zh-Hans" : "en";
    transcript.append(text);
    row.append(name,
      audioCell(sample.reference[length], "Unwatermarked reference", context),
      audioCell(sample.watermarked[length], isOurs ? "NoiseStamp output" : "Watermarked output", context),
      transcript);
    return row;
  }

  function renderModels() {
    const target = byId("comparison-list");
    const fragment = document.createDocumentFragment();
    data.models.forEach((model) => {
      const sample = data.listening.find((item) => item.model === model && item.method === "NoiseStamp" && item.language === state.language);
      if (!sample) throw new Error(`Missing curated sample for ${model}`);
      fragment.append(comparisonRow(sample, state.length, true));
    });
    target.replaceChildren(fragment);
    target.setAttribute("aria-busy", "false");
    byId("selection-summary").textContent = `${state.language === "en" ? "English" : "Chinese"} speech across four TTS models. ${state.length === "full" ? "Full recordings." : "One-second excerpts."}`;
  }

  function renderBaselines() {
    const target = byId("baseline-list");
    const fragment = document.createDocumentFragment();
    data.methods.forEach((method) => {
      const sample = data.listening.find((item) => item.model === "IndexTTS2" && item.language === "en" && item.method === method);
      if (!sample) throw new Error(`Missing baseline example for ${method}`);
      fragment.append(comparisonRow(sample, state.baselineLength, false));
    });
    target.replaceChildren(fragment);
    target.setAttribute("aria-busy", "false");
  }

  function renderPreview() {
    const sample = data.preview[0];
    byId("preview-reference").replaceChildren(audioCell(sample.reference.excerpt, "Unwatermarked reference", "F5-TTS preview", true));
    byId("preview-watermarked").replaceChildren(audioCell(sample.watermarked.excerpt, "NoiseStamp output", "F5-TTS preview", true));
    byId("preview-transcript").textContent = sample.transcript;
  }

  function stopAudio() {
    document.querySelectorAll("audio").forEach((audio) => audio.pause());
  }

  document.addEventListener("play", (event) => {
    if (!(event.target instanceof HTMLAudioElement)) return;
    document.querySelectorAll("audio").forEach((audio) => {
      if (audio !== event.target && !audio.paused) audio.pause();
    });
  }, true);

  byId("language").addEventListener("change", (event) => {
    state.language = event.target.value;
    stopAudio();
    if (data) renderModels();
  });
  byId("filters").addEventListener("change", (event) => {
    if (event.target.name !== "length") return;
    state.length = event.target.value;
    stopAudio();
    if (data) renderModels();
  });
  document.querySelectorAll('input[name="baseline-length"]').forEach((input) => {
    input.addEventListener("change", (event) => {
      state.baselineLength = event.target.value;
      stopAudio();
      if (data) renderBaselines();
    });
  });
  byId("reload-button").addEventListener("click", () => window.location.reload());

  async function initialize() {
    try {
      const response = await fetch("data/samples.json");
      if (!response.ok) throw new Error(`Audio index returned ${response.status}`);
      data = await response.json();
      renderPreview();
      renderModels();
      renderBaselines();
    } catch (error) {
      console.error("NoiseStamp audio index:", error);
      byId("load-error").hidden = false;
      byId("comparison-list").replaceChildren();
      byId("comparison-list").setAttribute("aria-busy", "false");
      byId("baseline-list").replaceChildren(make("p", "loading-text", "Audio examples are temporarily unavailable."));
      byId("baseline-list").setAttribute("aria-busy", "false");
      byId("selection-summary").textContent = "Audio examples are temporarily unavailable.";
    }
  }
  initialize();
})();
