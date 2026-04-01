document.addEventListener("DOMContentLoaded", () => {
  const uploadArea = document.getElementById("uploadArea");
  const fileInput = document.getElementById("fileInput");
  const previewArea = document.getElementById("previewArea");
  const previewImage = document.getElementById("previewImage");
  const resetBtn = document.getElementById("resetBtn");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const loading = document.getElementById("loading");
  const resultArea = document.getElementById("resultArea");
  const resultContent = document.getElementById("resultContent");

  let selectedFile = null;
  const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];
  const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

  function validateFile(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      showError("対応していないファイル形式です（PNG, JPG, GIF, WebP のみ）");
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      showError("ファイルサイズが大きすぎます（16MB以下にしてください）");
      return false;
    }
    return true;
  }

  function showPreview(file) {
    if (!validateFile(file)) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImage.src = e.target.result;
      uploadArea.style.display = "none";
      previewArea.style.display = "block";
      analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function reset() {
    selectedFile = null;
    fileInput.value = "";
    previewImage.src = "";
    uploadArea.style.display = "block";
    previewArea.style.display = "none";
    analyzeBtn.disabled = true;
    resultArea.style.display = "none";
  }

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      showPreview(e.target.files[0]);
    }
  });

  // Drag and drop
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });

  uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
  });

  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      showPreview(e.dataTransfer.files[0]);
    }
  });

  resetBtn.addEventListener("click", reset);

  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    analyzeBtn.disabled = true;
    loading.style.display = "block";
    resultArea.style.display = "none";

    const formData = new FormData();
    formData.append("image", selectedFile);
    const providerSelect = document.getElementById("providerSelect");
    if (providerSelect) {
      formData.append("provider", providerSelect.value);
    }

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        resultContent.innerHTML = formatResult(data.result);
        resultArea.style.display = "block";
      } else {
        showError(data.error || "エラーが発生しました");
      }
    } catch {
      showError("通信エラーが発生しました。ネットワーク接続を確認してください。");
    } finally {
      loading.style.display = "none";
      analyzeBtn.disabled = false;
    }
  });

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showError(msg) {
    resultContent.innerHTML = `<div class="error-msg">${escapeHtml(msg)}</div>`;
    resultArea.style.display = "block";
  }

  function formatResult(text) {
    const escaped = escapeHtml(text);
    return escaped
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/\n/g, "<br>");
  }
});
