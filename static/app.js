const form = document.querySelector("#note-form");
const modelSelect = document.querySelector("#model");
const languageSelect = document.querySelector("#language");
const statusText = document.querySelector("#status-text");
const submitBtn = document.querySelector("#submit-btn");
const resultSection = document.querySelector("#result");
const notePathEl = document.querySelector("#note-path");
const copyPathEl = document.querySelector("#copy-path");
const downloadLink = document.querySelector("#download-link");
const notePreview = document.querySelector("#note-preview");
const copyMarkdownBtn = document.querySelector("#copy-markdown");

async function loadOptions() {
  try {
    const res = await fetch("/api/options");
    if (!res.ok) throw new Error("Failed to load options");
    const data = await res.json();
    modelSelect.innerHTML = "";
    data.models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      if (model === data.defaultModel) option.selected = true;
      modelSelect.appendChild(option);
    });
    languageSelect.innerHTML = "";
    data.languages.forEach((lang) => {
      const option = document.createElement("option");
      option.value = lang.key;
      option.textContent = lang.label;
      if (lang.key === data.defaultLanguage) option.selected = true;
      languageSelect.appendChild(option);
    });
    statusText.textContent = `Output folder: ${data.paths.output}`;
  } catch (error) {
    console.error(error);
    statusText.textContent = "Kunne ikkje laste alternativ. Prøv å laste sida på nytt.";
  }
}

loadOptions();

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  if (!formData.get("file")) {
    statusText.textContent = "Vel ei fil før du startar.";
    return;
  }
  toggleLoading(true);
  statusText.textContent = "Sender fil og ventar på svar frå modellen ...";
  resultSection.hidden = true;
  notePreview.textContent = "";
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Feil under generering.");
    }
    const payload = await response.json();
    statusText.textContent = "Ferdig! Sjå resultatet under.";
    notePathEl.textContent = payload.notePath;
    downloadLink.href = payload.downloadUrl;
    downloadLink.setAttribute("download", payload.noteName);
    notePreview.textContent = payload.noteText;
    if (payload.copiedPath) {
      copyPathEl.hidden = false;
      copyPathEl.textContent = `Presentasjonen vart kopiert til: ${payload.copiedPath}`;
    } else {
      copyPathEl.hidden = true;
      copyPathEl.textContent = "";
    }
    resultSection.hidden = false;
    copyMarkdownBtn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(payload.noteText);
        copyMarkdownBtn.textContent = "Kopiert!";
        setTimeout(() => (copyMarkdownBtn.textContent = "Copy Markdown"), 1500);
      } catch (err) {
        console.error(err);
        copyMarkdownBtn.textContent = "Feil ved kopiering";
      }
    };
  } catch (error) {
    console.error(error);
    statusText.textContent = error.message;
  } finally {
    toggleLoading(false);
  }
});

function toggleLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Working..." : "Generate note";
}
