from __future__ import annotations


DASHBOARD_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Crypto Relative Strength Scanner</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #687385;
      --line: #d9dee7;
      --green: #008f70;
      --red: #c2413b;
      --accent: #2457a6;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    .wrap {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 72px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 760;
    }
    .meta {
      color: var(--muted);
      font-size: 14px;
      text-align: right;
    }
    main {
      padding: 24px 0 40px;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .label {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .value {
      font-size: 28px;
      font-weight: 760;
      line-height: 1.1;
    }
    .toolbar {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      margin: 18px 0 10px;
    }
    .tabs {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--panel);
    }
    button {
      border: 0;
      border-right: 1px solid var(--line);
      background: transparent;
      min-width: 80px;
      height: 36px;
      padding: 0 12px;
      font: inherit;
      cursor: pointer;
    }
    button:last-child { border-right: 0; }
    button.active {
      background: var(--accent);
      color: #fff;
    }
    input {
      width: min(320px, 45vw);
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 12px;
      font: inherit;
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    th, td {
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      text-align: right;
      font-size: 14px;
      white-space: nowrap;
    }
    th:first-child, td:first-child,
    th:nth-child(2), td:nth-child(2) {
      text-align: left;
    }
    th {
      color: var(--muted);
      font-weight: 650;
      background: #fbfcfd;
    }
    tr:last-child td { border-bottom: 0; }
    .pos { color: var(--green); font-weight: 700; }
    .neg { color: var(--red); font-weight: 700; }
    .empty {
      padding: 40px;
      text-align: center;
      color: var(--muted);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    @media (max-width: 760px) {
      .topbar { align-items: flex-start; flex-direction: column; padding: 16px 0; }
      .meta { text-align: left; }
      .summary { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      input { width: 100%; }
      .table-scroll { overflow-x: auto; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <h1>AI Crypto Relative Strength Scanner</h1>
      <div class="meta" id="scan-time">Latest scan: -</div>
    </div>
  </header>
  <main class="wrap">
    <section class="summary">
      <div class="metric">
        <div class="label">BTC Return</div>
        <div class="value" id="btc-return">-</div>
      </div>
      <div class="metric">
        <div class="label">Alt Season Index</div>
        <div class="value" id="alt-score">-</div>
      </div>
      <div class="metric">
        <div class="label">Strongest Coin</div>
        <div class="value" id="leader">-</div>
      </div>
    </section>
    <section>
      <div class="toolbar">
        <div class="tabs">
          <button id="top10" class="active">TOP10</button>
          <button id="top20">TOP20</button>
        </div>
        <input id="search" placeholder="Search symbol" autocomplete="off">
      </div>
      <div id="content"></div>
    </section>
  </main>
  <script>
    const state = { rows: [], limit: 10, query: "" };
    const fmt = (value, suffix = "") => Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}${suffix}` : "-";
    const cls = value => Number(value) >= 0 ? "pos" : "neg";
    function render() {
      const rows = state.rows
        .slice(0, state.limit)
        .filter(row => row.symbol.toLowerCase().includes(state.query.toLowerCase()));
      document.getElementById("content").innerHTML = rows.length ? `
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Rank</th><th>Symbol</th><th>AI</th><th>Relative</th><th>Coin</th><th>Volume</th><th>Trend</th><th>T10</th><th>T20</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map(row => `
                <tr>
                  <td>${row.rank}</td>
                  <td>${row.symbol.replace("USDT", "")}</td>
                  <td>${fmt(row.aiScore)}</td>
                  <td class="${cls(row.relativeScore)}">${fmt(row.relativeScore, "%")}</td>
                  <td class="${cls(row.coinReturn)}">${fmt(row.coinReturn, "%")}</td>
                  <td>${fmt(row.volumeScore)}</td>
                  <td>${fmt(row.trendScore)}</td>
                  <td>${row.top10Streak}</td>
                  <td>${row.top20Streak}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>` : `<div class="empty">No scan data yet. Run <code>python -m app.main scan</code>.</div>`;
    }
    async function fetchFirst(paths) {
      for (const path of paths) {
        try {
          const response = await fetch(path, { cache: "no-store" });
          if (response.ok) return await response.json();
        } catch (error) {}
      }
      return {};
    }
    async function load() {
      const [latest, alt] = await Promise.all([
        fetchFirst(["/api/dashboard", "dashboard.json", "data/dashboard/dashboard.json"]),
        fetchFirst(["/api/altscore", "../ranking/altscore.json", "data/ranking/altscore.json"])
      ]);
      state.rows = latest.ranking ?? [];
      document.getElementById("scan-time").textContent = `Latest scan: ${latest.scanTime ?? "-"}`;
      document.getElementById("btc-return").textContent = latest.scanTime ? fmt(latest.btcReturn, "%") : "-";
      document.getElementById("alt-score").textContent = fmt(alt.altSeasonIndex);
      document.getElementById("leader").textContent = first ? first.symbol.replace("USDT", "") : "-";
      render();
    }
    document.getElementById("top10").addEventListener("click", () => {
      state.limit = 10;
      document.getElementById("top10").classList.add("active");
      document.getElementById("top20").classList.remove("active");
      render();
    });
    document.getElementById("top20").addEventListener("click", () => {
      state.limit = 20;
      document.getElementById("top20").classList.add("active");
      document.getElementById("top10").classList.remove("active");
      render();
    });
    document.getElementById("search").addEventListener("input", event => {
      state.query = event.target.value;
      render();
    });
    load();
  </script>
</body>
</html>
"""
