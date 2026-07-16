/**
 * Sentinel Brief glass-box center — honest LangGraph phase replay.
 *
 * Prefer API `phases` / report `phases` (real TraceRecorder node spans with
 * duration_ms). Fall back to outcome-inferred status with no invented ms.
 */
(function () {
  const CANONICAL = [
    { id: "fetch_sources", label: "Fetch", detail: "9 allowlisted sources" },
    { id: "diff_items", label: "Diff", detail: "Overnight deltas" },
    { id: "write_brief", label: "Summarize", detail: "Exec brief" },
    { id: "run_eval", label: "Eval", detail: "Quality gate" },
    { id: "gateway_and_email", label: "Gateway", detail: "AegisAI + email" },
    { id: "archive_report", label: "Archive", detail: "JSON report" },
  ];

  const els = {
    pipeline: () => document.getElementById("gbPipeline"),
    gate: () => document.getElementById("gbGate"),
    log: () => document.getElementById("gbEventLog"),
    ops: () => document.getElementById("gbOpsStrip"),
    badge: () => document.getElementById("gbSourceBadge"),
  };

  let timer = null;
  let activeId = null;
  let done = new Set();

  function setBadge(source) {
    const b = els.badge();
    if (!b) return;
    b.className = "gb-source-badge";
    if (source === "live") {
      b.classList.add("live");
      b.textContent = "live spans";
    } else if (source === "outcome") {
      b.classList.add("fallback");
      b.textContent = "outcome map";
    } else {
      b.textContent = "awaiting run";
    }
  }

  function setGate(text) {
    const g = els.gate();
    if (g) g.textContent = text;
  }

  function clearLog() {
    const log = els.log();
    if (log) log.innerHTML = "";
  }

  function appendLog(line) {
    const log = els.log();
    if (!log) return;
    if (log.querySelector(".muted")) log.innerHTML = "";
    const row = document.createElement("div");
    row.className = "ev-live";
    row.textContent = line;
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
  }

  function setOps(meta) {
    const ops = els.ops();
    if (!ops) return;
    ops.innerHTML =
      "<span><strong>nodes</strong> " +
      (meta.nodes ?? "—") +
      "</span><span><strong>latency</strong> " +
      (meta.latency ?? "n/a") +
      "</span><span><strong>eval</strong> " +
      (meta.eval ?? "—") +
      "</span><span><strong>status</strong> " +
      (meta.status ?? "idle") +
      "</span>";
  }

  function normalizeName(name) {
    return String(name || "")
      .replace(/^node\./, "")
      .replace(/^sentinel\./, "");
  }

  function renderNodes(highlight) {
    const root = els.pipeline();
    if (!root) return;
    const lat = (highlight && highlight.latency) || {};
    root.innerHTML = CANONICAL.map((p, i) => {
      const cls =
        activeId === p.id ? " gb-active" : done.has(p.id) ? " gb-done" : "";
      const ms = lat[p.id] != null ? Number(lat[p.id]).toFixed(0) + "ms" : "—";
      return (
        (i > 0 ? '<span class="gb-agent-arrow" aria-hidden="true">→</span>' : "") +
        '<div class="gb-agent-node' +
        cls +
        '" data-phase-id="' +
        p.id +
        '">' +
        '<span class="gb-agent-idx">' +
        String(i + 1).padStart(2, "0") +
        "</span>" +
        "<div><strong>" +
        p.label +
        "</strong><small>" +
        p.detail +
        "</small></div><em>" +
        ms +
        "</em></div>"
      );
    }).join("");
  }

  function highlight(id) {
    activeId = id;
    document.querySelectorAll(".gb-agent-node").forEach((n) => {
      const pid = n.getAttribute("data-phase-id");
      n.classList.toggle("gb-active", pid === activeId);
      n.classList.toggle("gb-done", done.has(pid) && pid !== activeId);
    });
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function phasesFromApi(phases) {
    const latency = {};
    const order = [];
    (phases || []).forEach((p) => {
      const name = normalizeName(p.name);
      const match = CANONICAL.find((c) => c.id === name || name.endsWith(c.id));
      const id = match ? match.id : name;
      if (!order.includes(id)) order.push(id);
      if (p.duration_ms != null) latency[id] = p.duration_ms;
    });
    return { order: order.length ? order : CANONICAL.map((c) => c.id), latency, source: "live" };
  }

  /** Infer completed nodes from report outcome — no invented ms. */
  function phasesFromOutcome(report) {
    const status = report.status || "";
    const order = ["fetch_sources", "diff_items"];
    if (report.brief_markdown || ["summarized", "evaluated", "emailed", "blocked_by_eval", "blocked_by_gateway", "archived"].includes(status)) {
      order.push("write_brief");
    }
    if (report.eval_result || ["evaluated", "emailed", "blocked_by_eval", "blocked_by_gateway"].includes(status)) {
      order.push("run_eval");
    }
    if (report.email_result || report.gateway || status === "emailed" || status === "blocked_by_gateway") {
      order.push("gateway_and_email");
    }
    if (report.run_id) order.push("archive_report");
    return { order, latency: {}, source: "outcome" };
  }

  function replay(plan, meta) {
    clearTimer();
    done = new Set();
    activeId = null;
    clearLog();
    renderNodes({ latency: plan.latency });
    setBadge(plan.source);
    const totalMs = Object.values(plan.latency).reduce((a, b) => a + Number(b || 0), 0);
    setOps({
      nodes: plan.order.length,
      latency: totalMs > 0 ? totalMs.toFixed(0) + " ms" : plan.source === "live" ? "spans" : "n/a",
      eval: meta.eval,
      status: meta.status,
    });

    let i = 0;
    let prev = null;
    const tick = () => {
      if (i >= plan.order.length) {
        if (prev) done.add(prev);
        activeId = null;
        highlight(null);
        setGate(
          meta.finalGate ||
            (plan.source === "live"
              ? "Brief pipeline complete — replayed real node spans."
              : "Outcome map complete — no duration_ms in this report archive.")
        );
        if (typeof window.SentinelRefreshMetrics === "function") window.SentinelRefreshMetrics();
        return;
      }
      const id = plan.order[i];
      if (prev) done.add(prev);
      highlight(id);
      prev = id;
      const metaNode = CANONICAL.find((c) => c.id === id);
      const label = metaNode ? metaNode.label : id;
      const ms = plan.latency[id] != null ? " " + Number(plan.latency[id]).toFixed(0) + "ms" : "";
      setGate(label + " — " + (metaNode ? metaNode.detail : "node") + ms);
      appendLog("▸ " + id + ms + (plan.source === "live" ? " · live" : " · outcome"));
      i += 1;
      timer = setTimeout(tick, 360);
    };
    tick();
  }

  window.GlassBox = {
    reset() {
      clearTimer();
      done = new Set();
      activeId = null;
      renderNodes({ latency: {} });
      clearLog();
      const log = els.log();
      if (log) {
        log.innerHTML =
          '<div class="muted" style="font-style:italic">No spans yet — run a brief to replay LangGraph nodes.</div>';
      }
      setBadge("idle");
      setGate(
        "Fetch → Diff → Summarize → Eval → Gateway email → Archive. Replay uses real TraceRecorder duration_ms when the API returns phases."
      );
      setOps({});
    },

    /** From POST /runs response (includes phases when API is updated). */
    onRunComplete(data) {
      const hasPhases = Array.isArray(data.phases) && data.phases.length > 0;
      const plan = hasPhases ? phasesFromApi(data.phases) : phasesFromOutcome(data);
      replay(plan, {
        eval: data.eval_passed ? "pass" : "fail",
        status: data.status || "done",
        finalGate: data.eval_passed
          ? "Eval passed — email path " + (data.email_status || "n/a") + "."
          : "Eval failed or blocked — check report detail.",
      });
    },

    /** From GET /reports/{id} — may include archived phases. */
    onReport(data) {
      const hasPhases = Array.isArray(data.phases) && data.phases.length > 0;
      const plan = hasPhases ? phasesFromApi(data.phases) : phasesFromOutcome(data);
      const evalPassed = data.eval_result ? !!data.eval_result.passed : null;
      replay(plan, {
        eval: evalPassed == null ? "—" : evalPassed ? "pass" : "fail",
        status: data.status || "—",
      });
    },

    setRunning() {
      clearTimer();
      done = new Set();
      activeId = null;
      renderNodes({ latency: {} });
      setBadge("live");
      setGate("Running brief — waiting for POST /runs (cold start may take ~30–90s)…");
      clearLog();
      appendLog("▸ wake API / POST /runs");
      setOps({ nodes: "…", latency: "running", eval: "—", status: "running" });
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => window.GlassBox.reset());
  } else {
    window.GlassBox.reset();
  }
})();
