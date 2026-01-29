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
const browseButtons = document.querySelectorAll(".browse-btn");

const modal = document.querySelector("#browser-modal");
const modalTitle = document.querySelector("#browser-title");
const modalRoot = document.querySelector("#browser-root");
const browserCurrent = document.querySelector("#browser-current");
const browserEntries = document.querySelector("#browser-entries");
const browserSelectBtn = document.querySelector("#browser-select");
const browserCloseBtn = document.querySelector("#browser-close");
const browserUpBtn = document.querySelector("#browser-up");
const configBtn = document.querySelector("#config-btn");
const configModal = document.querySelector("#config-modal");
const configCloseBtn = document.querySelector("#config-close");
const configForm = document.querySelector("#config-form");
const configMessage = document.querySelector("#config-message");
const configApiKeyInput = document.querySelector("#config-api-key");
const configInputPathInput = document.querySelector("#config-input-path");
const configOutputPathInput = document.querySelector("#config-output-path");
const configCopyPathInput = document.querySelector("#config-copy-path");

const optionsState = { paths: {}, config: null };
const browserState = {
  root: null,
  selectType: "dir",
  currentPath: "",
  parentPath: "",
  targetInput: null,
};
let isLoading = false;
let configModalForced = false;

loadOptions();

/**
 * Load available options and configuration from the backend.
 */
async function loadOptions() {
  try {
    const res = await fetch("/api/options");
    if (!res.ok) throw new Error("Failed to load options");
    const data = await res.json();
    optionsState.paths = data.paths || {};
    optionsState.config = data.config || null;
    populateModelOptions(data);
    handleConfigState();
  } catch (error) {
    console.error(error);
    statusText.textContent = "Kunne ikkje laste alternativ. Prøv å laste sida på nytt.";
  }
}

/**
 * Populate model and language selection dropdowns.
 * @param {Object} data - The options data from the API.
 */
function populateModelOptions(data) {
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
}

/**
 * Update UI based on the current configuration state.
 */
function handleConfigState() {
  const needsSetup = optionsState.config?.needsSetup;
  if (needsSetup) {
    statusText.textContent = "Fullfør konfigureringa før du genererer notat.";
    if (!configModalForced) {
      openConfigModal(true);
    }
  } else {
    statusText.textContent = `Notatmappe: ${optionsState.paths.outputRoot || "ukjent"}`;
    if (!configModalForced) {
      closeConfigModal();
    }
  }
  updateSubmitState();
}

/**
 * Enable or disable the submit button based on configuration status.
 */
function updateSubmitState() {
  const needsSetup = optionsState.config?.needsSetup;
  if (form) {
    form.classList.toggle("blocked", !!needsSetup);
  }
  submitBtn.disabled = isLoading || !!needsSetup;
}

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

/**
 * Open the file browser modal.
 * @param {string} root - The root directory type ('input', 'output', 'copy').
 * @param {string} selectType - 'dir' or 'file'.
 * @param {HTMLElement} targetInput - The input element to update with the selected path.
 */
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



/**
 * Close the file browser modal and reset state.
 */
function closeBrowser() {
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
  browserEntries.innerHTML = "";
  browserState.root = null;
  browserState.targetInput = null;
}

/**
 * Load directory contents into the browser modal.
 * @param {string} root - The root directory type.
 * @param {string} path - The relative path to load.
 */
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

/**
 * Render file and directory entries in the browser list.
 * @param {Array} entries - List of file/directory objects.
 */
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
  if (optionsState.config?.needsSetup) {
    statusText.textContent = "Fullfør konfigureringa før du genererer notat.";
    return;
  }
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
    notePreview.textContent = payload.noteText;
    if (payload.copiedPath) {
      copyPathEl.hidden = false;
      copyPathEl.textContent = `Presentasjonen vart kopiert til: ${payload.copiedPath}`;
    } else {
      copyPathEl.hidden = true;
      copyPathEl.textContent = "";
    }
    resultSection.hidden = false;

    downloadLink.href = payload.downloadUrl;
    downloadLink.setAttribute("download", payload.noteName);

    copyMarkdownBtn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(payload.noteText);
        copyMarkdownBtn.textContent = "Kopiert!";
        setTimeout(() => (copyMarkdownBtn.textContent = "Copy"), 1500);
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

/**
 * Toggle the loading state of the form.
 * @param {boolean} state - True if loading, false otherwise.
 */
function toggleLoading(state) {
  isLoading = state;
  submitBtn.textContent = state ? "Arbeider…" : "Generer notat";
  updateSubmitState();
}

configBtn?.addEventListener("click", () => openConfigModal(false));
configCloseBtn?.addEventListener("click", () => closeConfigModal());
configForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  configMessage.textContent = "Lagrer konfigurasjon …";
  const payload = {
    apiKey: configApiKeyInput.value.trim() || null,
    inputPath: configInputPathInput.value.trim(),
    outputPath: configOutputPathInput.value.trim(),
    copyPath: configCopyPathInput.value.trim(),
  };
  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || "Feil ved lagring.");
    }
    configMessage.textContent = "Konfig lagra.";
    configModalForced = false;
    configCloseBtn.hidden = false;
    await loadOptions();
    setTimeout(() => {
      closeConfigModal();
    }, 600);
  } catch (error) {
    console.error(error);
    configMessage.textContent = error.message;
  }
});

/**
 * Open the configuration modal.
 * @param {boolean} force - If true, prevents closing the modal until config is valid.
 */
async function openConfigModal(force = false) {
  configModalForced = force;
  configCloseBtn.hidden = !!force;
  configModal.classList.remove("hidden");
  configModal.setAttribute("aria-hidden", "false");
  configMessage.textContent = force
    ? "Ingen konfigurasjon funnen. Fyll ut felta for å starte."
    : "Oppdater konfigurasjonen og lagre.";
  fillConfigForm(optionsState.config);
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Klarte ikkje å laste konfigurasjon.");
    const data = await res.json();
    optionsState.config = data;
    fillConfigForm(data);
  } catch (error) {
    console.error(error);
    configMessage.textContent = error.message;
  }
}

/**
 * Fill the configuration form with current values.
 * @param {Object} configData - The configuration data.
 */
function fillConfigForm(configData) {
  if (!configData) {
    configApiKeyInput.placeholder = "OpenAI API key";
    return;
  }
  const values = configData.values || {};
  configApiKeyInput.value = "";
  configApiKeyInput.placeholder = configData.keyPreview
    ? `Stored key: ${configData.keyPreview}`
    : "OpenAI API key";
  configInputPathInput.value = values.inputPath || "";
  configOutputPathInput.value = values.outputPath || "";
  configCopyPathInput.value = values.copyPath || "";
}

/**
 * Close the configuration modal.
 */
function closeConfigModal() {
  if (configModalForced) return;
  configModal.classList.add("hidden");
  configModal.setAttribute("aria-hidden", "true");
  configMessage.textContent = "";
}
