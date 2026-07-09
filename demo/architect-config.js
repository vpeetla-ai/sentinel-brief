window.ARCHITECT_CONFIG = {
  tagline:
    "Overnight intelligence brief: multi-source ingest, delta detection, eval gate, and optional email — governed batch agent, not a chatbot.",
  metricsUrl: (window.SENTINEL_API || "https://sentinel-brief-api.onrender.com") + "/api/v1/ops/metrics",
  metricsPath: "/api/v1/ops/metrics",
  metricLabels: { runs: "Brief runs", entities: "Sources monitored", latency: "P95 latency" },
  layers: [
    { tier: "L1", name: "Brief UI", role: "Reports + architecture", components: ["Mermaid flow", "Delta table", "Eval status"] },
    { tier: "L2", name: "LangGraph", role: "Ingest → synthesize", components: ["Source adapters", "Delta detect", "Brief writer"] },
    { tier: "L3", name: "Governance", role: "Quality gate", components: ["Eval harness", "Email gateway", "API key on /runs"] },
    { tier: "L4", name: "Ops", role: "JSON report archive", components: ["Report history", "Golden eval CI", "/api/v1/ops/metrics"] },
  ],
  tradeoffs: [
    { decision: "Batch brief vs interactive chat", gain: "Predictable cost + audit trail", trade: "Not real-time Q&A UX" },
    { decision: "Eval gate before email", gain: "No low-quality overnight sends", trade: "May skip delivery on eval fail" },
    { decision: "File-based report archive", gain: "Simple deploy on Render free tier", trade: "No SQL analytics without export" },
    { decision: "Multi-source adapters", gain: "Extensible intel pipeline", trade: "Each source needs maintenance" },
  ],
  adrLinks: [
    { title: "Case study — Sentinel Brief", href: "https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/case-studies/sentinel-brief.md" },
  ],
  docsLinks: [
    { title: "Architecture", href: "https://github.com/vpeetla-ai/sentinel-brief/blob/main/docs/ARCHITECTURE.md" },
    { title: "SLO targets", href: "https://github.com/vpeetla-ai/sentinel-brief/blob/main/docs/SLO.md" },
  ],
};
