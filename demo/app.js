/* Product panel — run brief, list reports, drive GlassBox from real API JSON. */
(function () {
  const API_BASE = (window.SENTINEL_API || "").replace(/\/$/, "");
  const el = document.getElementById("report-list");
  const hint = document.getElementById("api-hint");
  const detail = document.getElementById("report-detail");
  const runBtn = document.getElementById("run-now");
  const runStatus = document.getElementById("run-status");
  const progress = document.getElementById("run-progress");

  if (hint) hint.textContent = API_BASE ? "API: " + API_BASE : "API URL not configured.";

  function renderMarkdown(md) {
    const esc = (s) =>
      String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const lines = String(md || "").split("\n");
    const html = [];
    let inList = false;
    const closeList = () => {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
    };
    for (const raw of lines) {
      const line = raw.trimEnd();
      if (/^###\s+/.test(line)) {
        closeList();
        html.push("<h4>" + esc(line.replace(/^###\s+/, "")) + "</h4>");
      } else if (/^##\s+/.test(line)) {
        closeList();
        html.push("<h3>" + esc(line.replace(/^##\s+/, "")) + "</h3>");
      } else if (/^#\s+/.test(line)) {
        closeList();
        html.push("<h2>" + esc(line.replace(/^#\s+/, "")) + "</h2>");
      } else if (/^[-*]\s+/.test(line)) {
        if (!inList) {
          html.push("<ul>");
          inList = true;
        }
        html.push("<li>" + esc(line.replace(/^[-*]\s+/, "")) + "</li>");
      } else if (!line.trim()) {
        closeList();
      } else {
        closeList();
        html.push("<p>" + esc(line) + "</p>");
      }
    }
    closeList();
    return html.join("") || "<p class='muted'>Empty brief.</p>";
  }

  async function loadReports() {
    if (!API_BASE) {
      el.innerHTML = "<p>Set window.SENTINEL_API in config.js</p>";
      return;
    }
    try {
      const res = await fetch(API_BASE + "/reports?limit=10");
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      if (!data.reports?.length) {
        el.textContent = "No reports yet — click Run brief now (takes ~1 min).";
        return;
      }
      el.innerHTML =
        "<table class='compare-table'><tr><th>Run</th><th>When</th><th>Status</th><th>Deltas</th><th>Eval</th></tr>" +
        data.reports
          .map(
            (r) =>
              `<tr data-run="${r.run_id}" style="cursor:pointer">` +
              `<td><code>${(r.run_id || "").slice(0, 8)}…</code></td>` +
              `<td>${(r.created_at || "").slice(0, 19).replace("T", " ")}</td>` +
              `<td>${r.status || "—"}</td>` +
              `<td>${r.delta_count ?? "—"}</td>` +
              `<td class="${r.eval_passed ? "status-ok" : ""}">${r.eval_passed ? "pass" : "fail"}</td></tr>`
          )
          .join("") +
        "</table>";
      el.querySelectorAll("tr[data-run]").forEach((row) => {
        row.addEventListener("click", () => showReport(row.dataset.run));
      });
    } catch (err) {
      el.textContent =
        "Could not reach API (" + err.message + "). Render may be waking up — retry in 30s.";
    }
  }

  async function showReport(runId) {
    try {
      const res = await fetch(API_BASE + "/reports/" + runId);
      const data = await res.json();
      detail.classList.remove("hidden");
      if (data.brief_markdown) {
        detail.innerHTML =
          "<p class='muted' style='margin:0 0 0.75rem'>Run <code>" +
          (runId || "").slice(0, 8) +
          "…</code></p>" +
          renderMarkdown(data.brief_markdown);
      } else {
        detail.innerHTML = "<pre class='trace'>" + JSON.stringify(data, null, 2) + "</pre>";
      }
      if (window.GlassBox) window.GlassBox.onReport(data);
    } catch {
      detail.classList.remove("hidden");
      detail.innerHTML = "<p class='alert alert-error'>Failed to load report.</p>";
    }
  }

  async function wakeApi(maxAttempts = 4) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const res = await fetch(API_BASE + "/health", { signal: AbortSignal.timeout(45000) });
        if (res.ok) return true;
      } catch {
        /* cold start */
      }
      await new Promise((r) => setTimeout(r, 8000));
    }
    return false;
  }

  runBtn.addEventListener("click", async () => {
    if (!API_BASE) return;
    runBtn.disabled = true;
    progress.textContent = "";
    runStatus.textContent = "Waking API…";
    if (window.GlassBox) window.GlassBox.setRunning();
    try {
      const awake = await wakeApi();
      if (!awake) throw new Error("API not reachable — Render may still be starting");
      runStatus.textContent = "Running… fetching 9 sources (~60–90s)";
      const apiKey = document.getElementById("api-key-input").value.trim();
      const headers = apiKey ? { "X-API-Key": apiKey } : {};
      const res = await fetch(API_BASE + "/runs", {
        method: "POST",
        headers,
        signal: AbortSignal.timeout(120000),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "HTTP " + res.status);
      runStatus.textContent =
        `Done — ${data.delta_count} deltas, eval ${data.eval_passed ? "pass" : "fail"}, email: ${data.email_status || "—"}`;
      progress.textContent = data.phases?.length
        ? `Replayed ${data.phases.length} live node span(s).`
        : "No phases in response yet — showing outcome map (deploy API for live spans).";
      if (window.GlassBox) window.GlassBox.onRunComplete(data);
      await loadReports();
      if (data.run_id) showReport(data.run_id);
    } catch (err) {
      const msg = err.name === "TimeoutError" ? "Timed out — retry in 30s" : err.message;
      runStatus.textContent = "Failed: " + msg;
      progress.innerHTML = `<p class="alert alert-error">${msg}</p>`;
      if (window.GlassBox) window.GlassBox.reset();
    } finally {
      runBtn.disabled = false;
    }
  });

  loadReports();
})();
