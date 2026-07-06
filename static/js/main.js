// ── Drag-and-drop upload zone ────────────────────────────
const uploadZone = document.getElementById("upload-zone");
const fileInput  = document.getElementById("file-input");

if (uploadZone && fileInput) {
  uploadZone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) showFileName(fileInput.files[0].name);
  });

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("drag-over");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("drag-over");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length) {
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      fileInput.files = dt.files;
      showFileName(files[0].name);
    }
  });
}

function showFileName(name) {
  const label = document.getElementById("file-label");
  if (label) {
    label.textContent = `✓  ${name}`;
    label.style.color = "#4CC9F0";
  }
}

// ── Loading overlay on form submit ───────────────────────
const uploadForm    = document.getElementById("upload-form");
const loadingOverlay = document.getElementById("loading-overlay");

if (uploadForm && loadingOverlay) {
  uploadForm.addEventListener("submit", (e) => {
    if (fileInput && !fileInput.files.length) {
      e.preventDefault();
      alert("Please choose a CSV or Excel file first.");
      return;
    }
    loadingOverlay.classList.add("active");
  });
}

// ── Plotly chart renderer ─────────────────────────────────
function renderCharts(chartsData) {
  chartsData.forEach((chart, idx) => {
    const containerId = `chart-${idx}`;
    const el = document.getElementById(containerId);
    if (!el) return;

    const data   = chart.chart_json.data;
    const layout = Object.assign({}, chart.chart_json.layout, {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor:  "rgba(0,0,0,0)",
      font: { family: "Inter, sans-serif", size: 12, color: "#8b949e" },
      margin: { l: 45, r: 20, t: 40, b: 50 },
      autosize: true,
    });

    Plotly.newPlot(containerId, data, layout, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["toImage", "sendDataToCloud"],
    });
  });
}

// ── Smooth scroll to charts section ──────────────────────
const toCharts = document.getElementById("scroll-to-charts");
if (toCharts) {
  toCharts.addEventListener("click", () => {
    document.getElementById("charts-section")?.scrollIntoView({ behavior: "smooth" });
  });
}

// ── Custom Chart Builder ──────────────────────────────────
(function () {
  const generateBtn   = document.getElementById("generate-custom-chart-btn");
  if (!generateBtn) return; // not on dashboard page

  const xSelect       = document.getElementById("x-axis-select");
  const ySelect       = document.getElementById("y-axis-select");
  const typeSelect    = document.getElementById("chart-type-select");
  const errorBox      = document.getElementById("builder-error");
  const spinner       = document.getElementById("builder-spinner");
  const outputPanel   = document.getElementById("custom-chart-output");
  const outputTitle   = document.getElementById("custom-chart-title");
  const outputBadge   = document.getElementById("custom-chart-badge");
  const outputDesc    = document.getElementById("custom-chart-description");
  const plotContainer = document.getElementById("custom-chart-plot");

  // Badge colour map (mirrors CSS)
  const badgeClasses = {
    line:    "badge-line",
    bar:     "badge-bar",
    scatter: "badge-scatter",
    pie:     "badge-pie",
  };
  const badgeLabels = {
    line:    "LINE",
    bar:     "BAR",
    scatter: "SCATTER",
    pie:     "PIE",
  };

  function showError(msg) {
    errorBox.textContent = msg;
    // Force re-animation on repeated errors
    errorBox.style.animation = "none";
    errorBox.offsetHeight; // reflow
    errorBox.style.animation = "";
    errorBox.style.display = "flex";
  }

  function hideError() {
    errorBox.style.display = "none";
    errorBox.textContent   = "";
  }

  function setLoading(on) {
    generateBtn.disabled    = on;
    generateBtn.textContent = on ? "⏳ Generating…" : "✨ Generate Chart";
    spinner.style.display   = on ? "block" : "none";
  }

  function renderCustomChart(chartData) {
    const type   = chartData.chart_type;
    const title  = chartData.title;

    // Update header
    outputTitle.textContent = title;
    outputBadge.className   = `chart-type-badge ${badgeClasses[type] || ""}`;
    outputBadge.textContent = badgeLabels[type] || type.toUpperCase();
    outputDesc.textContent  = chartData.description || "";

    // Show panel with animation
    outputPanel.style.display = "block";
    outputPanel.classList.remove("visible");
    void outputPanel.offsetWidth; // reflow to restart animation
    outputPanel.classList.add("visible");

    // Plotly render
    const data   = chartData.chart_json.data;
    const layout = Object.assign({}, chartData.chart_json.layout, {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor:  "rgba(0,0,0,0)",
      font: { family: "Inter, sans-serif", size: 12, color: "#8b949e" },
      margin: { l: 45, r: 20, t: 40, b: 50 },
      autosize: true,
    });

    Plotly.react("custom-chart-plot", data, layout, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["toImage", "sendDataToCloud"],
    });

    // Smooth scroll to the output
    setTimeout(() => {
      outputPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 150);
  }

  generateBtn.addEventListener("click", async () => {
    const xCol     = xSelect.value.trim();
    const yCol     = ySelect.value.trim();
    const chartType = typeSelect.value;

    // ── Client-side validation ──────────────────────────
    if (!xCol || !yCol) {
      showError("Please select both an X-axis and a Y-axis column.");
      return;
    }
    if (xCol === yCol) {
      showError("Please make sure the two selected columns are different.");
      return;
    }
    hideError();

    // ── Fetch chart from server ─────────────────────────
    setLoading(true);
    outputPanel.style.display = "none";

    try {
      const response = await fetch("/generate_custom_chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x_col: xCol, y_col: yCol, chart_type: chartType }),
      });

      const json = await response.json();

      if (!response.ok || json.error) {
        showError(json.error || "An unexpected error occurred. Please try again.");
        return;
      }

      renderCustomChart(json.chart);

    } catch (err) {
      showError("Network error — could not reach the server. Please try again.");
      console.error("Custom chart fetch error:", err);
    } finally {
      setLoading(false);
    }
  });
})();

