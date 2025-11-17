const form = document.querySelector("#note-form");
const fileInput = document.querySelector("#file");
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
const sourceRadios = document.querySelectorAll('input[name="source_mode"]');
const sourceSections = document.querySelectorAll(".source-mode");
const existingPathInput = document.querySelector("#existing-path");
const outputDirInput = document.querySelector("#output-dir");
const copyDirInput = document.querySelector("#copy-dir");
const hints = {
  input: document.querySelector("#input-root-hint"),
  output: document.querySelector("#output-root-hint"),
  copy: document.querySelector("#copy-root-hint"),
};
const browseButtons = document.querySelectorAll(".browse-btn");
const modal = document.querySelector("#browser-modal");
const modalTitle = document.querySelector("#browser-title");
const modalRoot = document.querySelector("#browser-root");
const browserCurrent = document.querySelector("#browser-current");
const browserEntries = document.querySelector("#browser-entries");
const browserSelectBtn = document.querySelector("#browser-select");
const browserCloseBtn = document.querySelector("#browser-close");
const browserUpBtn = document.querySelector("#browser-up");

const optionsState = { paths: {} };
const browserState = {
  root: null,
  selectType: "dir",
  currentPath: "",
  parentPath: "",
  targetInput: null,
};

async function loadOptions() {
  try {
    const res = await fetch("/api/options");
    if (!res.ok) throw new Error("Failed to load options");
    const data = await res.json();
    optionsState.paths = data.paths;
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
    updateHints();
    statusText.textContent = `Output folder: ${data.paths.outputRoot}`;
  } catch (error) {
    console.error(error);
    statusText.textContent = "Kunne ikkje laste alternativ. Prøv å laste sida på nytt.";
  }
}

function updateHints() {
  hints.input.textContent = optionsState.paths.inputRoot
    ? `Input root: ${optionsState.paths.inputRoot}`
    : "";
  hints.output.textContent = optionsState.paths.outputRoot
    ? `Output root: ${optionsState.paths.outputRoot}`
    : "";
  hints.copy.textContent = optionsState.paths.copyRoot ? `Copy root: ${optionsState.paths.copyRoot}` : "";
}

loadOptions();

sourceRadios.forEach((radio) => {
  radio.addEventListener("change", () => {
    const selected = document.querySelector('input[name="source_mode"]:checked')?.value;
    sourceSections.forEach((section) => {
      section.classList.toggle("hidden", section.dataset.mode !== selected);
    });
  });
});

sourceSections.forEach((section) => {
  const selected = document.querySelector('input[name="source_mode"]:checked')?.value;
  section.classList.toggle("hidden", section.dataset.mode !== selected);
});

browseButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const root = button.dataset.root;
    const selectType = button.dataset.select;
    const targetInputId =
      root === "input" && selectType === "file"
        ? "#existing-path"
        : root === "output"
        ? "#output-dir"
        : "#copy-dir";
    const targetInput = document.querySelector(targetInputId);
    openBrowser(root, selectType, targetInput);
  });
});

browserCloseBtn.addEventListener("click", closeBrowser);
browserUpBtn.addEventListener("click", () => {
  if (!browserState.root) return;
  loadDirectory(browserState.root, browserState.parentPath || "");
});
browserSelectBtn.addEventListener("click", () => {
  if (!browserState.targetInput) return;
  browserState.targetInput.value = browserState.currentPath || "";
  closeBrowser();
});

browserEntries.addEventListener("click", (event) => {
  const btn = event.target.closest("button[data-path]");
  if (!btn) return;
  const entryPath = btn.dataset.path;
  const entryType = btn.dataset.type;
  if (entryType === "dir") {
    loadDirectory(browserState.root, entryPath);
  } else if (entryType === "file" && browserState.selectType === "file") {
    if (browserState.targetInput) {
      browserState.targetInput.value = entryPath;
    }
    closeBrowser();
  }
});

async function openBrowser(root, selectType, targetInput) {
  browserState.root = root;
  browserState.selectType = selectType;
  browserState.targetInput = targetInput;
  browserSelectBtn.hidden = selectType !== "dir";
  modalTitle.textContent =
    root === "input"
      ? "Browse input files"
      : root === "output"
      ? "Browse output folders"
      : "Browse copy folders";
  modalRoot.textContent = optionsState.paths[`${root}Root`] || "";
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
  await loadDirectory(root, targetInput.value.trim());
}

function closeBrowser() {
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
  browserEntries.innerHTML = "";
  browserState.root = null;
  browserState.targetInput = null;
}

async function loadDirectory(root, path) {
  if (!root) return;
  const params = new URLSearchParams({ root, path: path || "" });
  try {
    const res = await fetch(`/api/browse?${params.toString()}`);
    if (!res.ok) throw new Error("Klarte ikkje å lese mappe.");
    const data = await res.json();
    browserState.currentPath = data.currentPath || "";
    browserState.parentPath = data.parentPath || "";
    renderEntries(data.entries);
    browserCurrent.textContent = data.currentPath ? `/${data.currentPath}` : "/";
    browserUpBtn.disabled = !browserState.parentPath;
  } catch (error) {
    console.error(error);
    statusText.textContent = error.message;
  }
}

function renderEntries(entries) {
  browserEntries.innerHTML = "";
  if (!entries.length) {
    const empty = document.createElement("li");
    empty.textContent = "Tom mappe";
    browserEntries.appendChild(empty);
    return;
  }
  entries.forEach((entry) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.dataset.path = entry.path;
    button.dataset.type = entry.type;
    button.textContent = entry.type === "dir" ? `📁 ${entry.name}` : `📄 ${entry.name}`;
    li.appendChild(button);
    browserEntries.appendChild(li);
  });
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const selectedMode = document.querySelector('input[name="source_mode"]:checked')?.value || "upload";
  if (selectedMode === "upload") {
    if (!fileInput?.files?.length) {
      statusText.textContent = "Vel ei fil før du startar.";
      return;
    }
    formData.set("existing_path", "");
  } else {
    const existingPath = existingPathInput.value.trim();
    if (!existingPath) {
      statusText.textContent = "Vel ei fil frå inndatamappa.";
      return;
    }
    formData.delete("file");
    formData.set("existing_path", existingPath);
  }
  formData.set("output_dir", outputDirInput.value.trim());
  formData.set("copy_dir", copyDirInput.value.trim());

  toggleLoading(true);
  statusText.textContent = "Behandlar fila …";
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
    statusText.textContent = `Ferdig! Notatet ligg i ${payload.outputDir}.`;
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
