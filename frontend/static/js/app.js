/**
 * app.js — Upload handling, drag-and-drop, API call orchestration.
 *
 * - initUpload(): sets up drag-and-drop and file input listeners
 * - handleFile(file): validates and uploads file to /api/score
 * - showError(msg): displays error banner
 * - showLoading(show): toggles loading state in upload zone
 */

(function () {
  "use strict";

  const uploadZone = document.getElementById("upload-zone");
  const fileInput = document.getElementById("file-input");
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const uploadIcon = document.getElementById("upload-icon");
  const uploadLoading = document.getElementById("upload-loading");
  const loadingStatus = document.getElementById("loading-status");
  const resultsSection = document.getElementById("results-section");
  const heroSection = document.getElementById("hero");
  const rescanBtn = document.getElementById("rescan-btn");

  const ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
  ];
  const ALLOWED_EXTS = ["pdf", "docx", "doc"];
  const MAX_SIZE = 5 * 1024 * 1024;

  // --- LOADING MESSAGES ---
  const LOADING_STEPS = [
    "Extracting text from document…",
    "Simulating ATS parser…",
    "Checking layout structure…",
    "Detecting fonts and encoding…",
    "Computing ATS score…",
    "Almost there…",
  ];

  let loadingInterval = null;

  function cycleLoadingMessages() {
    let i = 0;
    loadingStatus.textContent = LOADING_STEPS[0];
    loadingInterval = setInterval(() => {
      i = (i + 1) % LOADING_STEPS.length;
      loadingStatus.textContent = LOADING_STEPS[i];
    }, 1200);
  }

  function stopLoadingMessages() {
    if (loadingInterval) {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
  }

  // --- SHOW/HIDE ---
  function showLoading(show) {
    if (show) {
      uploadIcon.classList.add("hidden");
      uploadIcon.classList.remove("flex");
      uploadLoading.classList.remove("hidden");
      uploadLoading.classList.add("flex");
      uploadZone.classList.add("drop-active");
      cycleLoadingMessages();
    } else {
      uploadIcon.classList.remove("hidden");
      uploadIcon.classList.add("flex");
      uploadLoading.classList.add("hidden");
      uploadLoading.classList.remove("flex");
      uploadZone.classList.remove("drop-active");
      stopLoadingMessages();
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove("hidden");
    setTimeout(() => errorBanner.classList.add("hidden"), 6000);
  }

  function hideError() {
    errorBanner.classList.add("hidden");
  }

  function showResults() {
    heroSection.classList.add("hidden");
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showUpload() {
    heroSection.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    fileInput.value = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // --- FILE VALIDATION ---
  function validateFile(file) {
    if (!file) return "No file selected.";

    const ext = file.name.toLowerCase().split(".").pop();
    const typeOk =
      ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTS.includes(ext);
    if (!typeOk) {
      return "Only PDF and DOCX files are supported.";
    }
    if (file.size > MAX_SIZE) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 5 MB.`;
    }
    if (file.size === 0) {
      return "File appears to be empty.";
    }
    return null;
  }

  // --- MAIN UPLOAD HANDLER ---
  async function handleFile(file) {
    hideError();
    const validationError = validateFile(file);
    if (validationError) {
      showError(validationError);
      return;
    }

    showLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/score", {
        method: "POST",
        body: formData,
      });

      stopLoadingMessages();

      if (!response.ok) {
        let errMsg = `Server error (${response.status})`;
        try {
          const errData = await response.json();
          errMsg = errData.detail || errMsg;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const data = await response.json();

      showLoading(false);

      // Store globally for tab switching
      window.__atsResult = data;
      window.__atsFileName = file.name;
      window.__atsFileSize = file.size;

      // Render results
      renderResults(data, file.name, file.size);
      showResults();
    } catch (err) {
      showLoading(false);
      showError(err.message || "Something went wrong. Please try again.");
    }
  }

  // --- DRAG AND DROP ---
  uploadZone.addEventListener("dragenter", (e) => {
    e.preventDefault();
    uploadZone.classList.add("border-sky-400", "bg-sky-50");
  });

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
  });

  uploadZone.addEventListener("dragleave", (e) => {
    if (!uploadZone.contains(e.relatedTarget)) {
      uploadZone.classList.remove("border-sky-400", "bg-sky-50");
    }
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("border-sky-400", "bg-sky-50");
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  });

  // --- FILE INPUT CHANGE ---
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  });

  // --- RESCAN BUTTON ---
  rescanBtn.addEventListener("click", () => {
    showUpload();
  });

  // --- KEYBOARD ACCESS ---
  uploadZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  // --- TAB SWITCHING ---
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;

    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active", "bg-white", "shadow-sm", "text-gray-900");
      b.classList.add("text-gray-500");
    });
    btn.classList.add("active", "bg-white", "shadow-sm", "text-gray-900");
    btn.classList.remove("text-gray-500");

    const tabId = btn.dataset.tab;
    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.classList.remove("active");
    });
    const panel = document.getElementById("tab-" + tabId);
    if (panel) panel.classList.add("active");
  });

  // Expose handleFile globally for any future use
  window.handleFile = handleFile;
})();
