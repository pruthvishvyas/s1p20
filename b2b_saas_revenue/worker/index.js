import { getAssetFromKV } from "@cloudflare/kv-asset-handler";
import manifestJSON from "__STATIC_CONTENT_MANIFEST";

const assetManifest = JSON.parse(manifestJSON);

const CORS = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id"
};

const TOOLS = [
  { name: "get_kpis", description: "Get all current KPI values for B2B SaaS Revenue and Retention", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "get_insights", description: "Get business insights ranked by severity (HIGH/MEDIUM/LOW)",
    inputSchema: { type: "object", properties: { severity: { type: "string", enum: ["HIGH", "MEDIUM", "LOW", "ALL"], default: "ALL" } }, required: [] } },
  { name: "get_anomalies", description: "Get detected anomalies and unusual business patterns", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "get_recommendations", description: "Get prioritized action recommendations for the business", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "get_forecast", description: "Get the latest forecast data and predictions", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "get_summary", description: "Get pipeline run summary and data freshness info", inputSchema: { type: "object", properties: {}, required: [] } }
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const method = request.method;
    if (method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    if (method === "POST" && url.pathname === "/api") return handleForecast(request, env);
    if (url.pathname === "/mcp" || url.pathname.startsWith("/mcp/")) return handleMCP(request, env, url);
    return serveAsset(request, env, ctx);
  }
};

// ---- static assets with SPA fallback
async function serveAsset(request, env, ctx) {
  try {
    return await getAssetFromKV(
      { request, waitUntil: ctx.waitUntil.bind(ctx) },
      {
        ASSET_NAMESPACE: env.__STATIC_CONTENT,
        ASSET_MANIFEST: assetManifest,
        mapRequestToAsset: (req) => {
          const u = new URL(req.url);
          if (!u.pathname.includes(".")) {
            u.pathname = "/index.html";
            return new Request(u.toString(), req);
          }
          return req;
        }
      }
    );
  } catch (e) {
    try {
      const fallback = new Request(new URL("/index.html", request.url).toString(), request);
      const res = await getAssetFromKV(
        { request: fallback, waitUntil: ctx.waitUntil.bind(ctx) },
        { ASSET_NAMESPACE: env.__STATIC_CONTENT, ASSET_MANIFEST: assetManifest }
      );
      return new Response(res.body, { status: 200, headers: res.headers });
    } catch (e2) {
      return new Response("Not found", { status: 404 });
    }
  }
}

// ---- forecaster lookup
async function handleForecast(request, env) {
  try {
    const body = await request.json().catch(() => ({}));
    const raw = env.FORECAST_LOOKUP ?? null;
    if (!raw) return json({ error: "Forecast data not configured. Run: wrangler secret put FORECAST_LOOKUP" }, 503);
    const lookup = JSON.parse(raw);
    const keys = Object.keys(lookup).map(Number).filter((n) => !isNaN(n)).sort((a, b) => a - b);
    if (keys.length === 0) return json({ error: "Forecast lookup table is empty." }, 503);
    const inputVal = Number(body.input);
    if (body.input === null || body.input === undefined || body.input === "" || isNaN(inputVal)) {
      return json({ error: "Invalid input value. Must be a number." }, 400);
    }
    const nearest = keys.reduce((a, b) => (Math.abs(b - inputVal) < Math.abs(a - inputVal) ? b : a));
    const result = lookup[nearest];
    const isObj = result !== null && typeof result === "object";
    return json({
      prediction: isObj ? (result.value ?? null) : (result ?? null),
      confidence: isObj ? (result.confidence ?? null) : null,
      range_low: isObj ? (result.range_low ?? null) : null,
      range_high: isObj ? (result.range_high ?? null) : null,
      input_received: inputVal,
      nearest_key: nearest
    }, 200);
  } catch (e) {
    return json({ error: "Forecast error: " + e.message }, 500);
  }
}

// ---- read-only MCP tools (simple REST style + JSON-RPC 2.0 for Claude connectors)
async function runTool(tool, params, baseUrl) {
  const fetchJSON = async (path) => {
    const r = await fetch(baseUrl + path);
    if (!r.ok) return null;
    return r.json().catch(() => null);
  };
  switch (tool) {
    case "get_kpis": {
      const d = await fetchJSON("/data/understand/kpis.json");
      return d ? { result: d } : { error: "KPI data not available. Run pipeline first.", status: 503 };
    }
    case "get_insights": {
      const d = await fetchJSON("/data/decide/insights.json");
      if (!d) return { error: "Insights not available. Run pipeline first.", status: 503 };
      const sev = String((params && params.severity) || "ALL").toUpperCase();
      return { result: sev === "ALL" || !Array.isArray(d) ? d : d.filter((i) => i.severity === sev), filter: sev };
    }
    case "get_anomalies": {
      const d = await fetchJSON("/data/understand/anomalies.json");
      return d ? { result: d } : { error: "Anomaly data not available. Run pipeline first.", status: 503 };
    }
    case "get_recommendations": {
      const d = await fetchJSON("/data/decide/recommendations.json");
      return d ? { result: d } : { error: "Recommendations not available. Run pipeline first.", status: 503 };
    }
    case "get_forecast": {
      const d = await fetchJSON("/data/monitor/forecast.json");
      return d ? { result: d } : { error: "Forecast data not available. Run pipeline first.", status: 503 };
    }
    case "get_summary": {
      const log = await fetchJSON("/data/meta/run_log.json");
      const summary = await fetchJSON("/data/meta/summary.json");
      return { result: { run_log: log, summary: summary } };
    }
    default:
      return { error: 'Unknown tool: "' + tool + '". Call GET /mcp for available tools.', status: 400 };
  }
}

async function handleMCP(request, env, url) {
  const method = request.method;
  if (method === "GET") {
    return json({ name: "B2B SaaS Revenue and Retention Analytics MCP", description: "Read-only business analytics tools for B2B SaaS Revenue and Retention", version: "1.0.0", tools: TOOLS }, 200);
  }
  if (method === "POST") {
    try {
      const body = await request.json().catch(() => ({}));
      // JSON-RPC 2.0 (standard MCP clients)
      if (body && body.jsonrpc === "2.0") {
        const id = body.id ?? null;
        const rpc = (result) => json({ jsonrpc: "2.0", id, result }, 200);
        const rpcErr = (code, message) => json({ jsonrpc: "2.0", id, error: { code, message } }, 200);
        switch (body.method) {
          case "initialize":
            return rpc({ protocolVersion: "2025-03-26", capabilities: { tools: {} }, serverInfo: { name: "b2b_saas_revenue-mcp", version: "1.0.0" } });
          case "notifications/initialized":
            return new Response(null, { status: 202, headers: CORS });
          case "ping":
            return rpc({});
          case "tools/list":
            return rpc({ tools: TOOLS });
          case "tools/call": {
            const out = await runTool(body.params && body.params.name, (body.params && body.params.arguments) || {}, url.origin);
            if (out.error) return rpc({ content: [{ type: "text", text: out.error }], isError: true });
            return rpc({ content: [{ type: "text", text: JSON.stringify(out.result) }] });
          }
          default:
            return rpcErr(-32601, "Method not found: " + body.method);
        }
      }
      // simple REST style: { "tool": "get_kpis", "params": {} }
      const tool = body.tool ?? body.name ?? "";
      const out = await runTool(tool, body.params ?? body.arguments ?? {}, url.origin);
      if (out.error) return json({ error: out.error }, out.status || 500);
      return json({ tool, result: out.result, ...(out.filter ? { filter: out.filter } : {}) }, 200);
    } catch (e) {
      return json({ error: "MCP error: " + e.message }, 500);
    }
  }
  return json({ error: "MCP: use GET /mcp for manifest, POST /mcp to call tools." }, 405);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), { status, headers: CORS });
}
