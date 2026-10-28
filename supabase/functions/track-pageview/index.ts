import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

function allowedOrigins(): string[] {
  return (Deno.env.get("ALLOWED_ORIGINS") ?? "").split(",").map((v) => v.trim()).filter(Boolean);
}
function headers(origin: string | null) {
  const h: Record<string, string> = {
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
    "Content-Type": "application/json",
  };
  if (origin && allowedOrigins().includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}
function json(body: unknown, status = 200, origin: string | null = null) {
  return new Response(JSON.stringify(body), { status, headers: headers(origin) });
}
function isUuid(value: unknown): value is string {
  return typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
Deno.serve(async (req) => {
  const origin = req.headers.get("Origin");
  if (!origin || !allowedOrigins().includes(origin)) return json({ error: "origin_not_allowed" }, 403, null);
  if (req.method === "OPTIONS") return new Response("ok", { headers: headers(origin) });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405, origin);
  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "invalid_json" }, 400, origin); }
  const { visitor_id, session_id, path, referrer_host } = body;
  if (!isUuid(visitor_id) || !isUuid(session_id)) return json({ error: "invalid_visitor_or_session_id" }, 400, origin);
  if (typeof path !== "string" || !path.startsWith("/") || path.length > 300 || path.startsWith("//") || path.includes("\\\\") || /[\\r\\n]/.test(path)) {
    return json({ error: "invalid_path" }, 400, origin);
  }
  if (referrer_host !== undefined && referrer_host !== null &&
      (typeof referrer_host !== "string" || referrer_host.length > 253 || /[^a-zA-Z0-9.:-]/.test(referrer_host))) {
    return json({ error: "invalid_referrer_host" }, 400, origin);
  }
  const url = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceRoleKey) return json({ error: "service_not_configured" }, 503, origin);
  const client = createClient(url, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { error } = await client.from("page_events").insert({
    visitor_id, session_id, path: path.split("?")[0].split("#")[0],
    referrer_host: referrer_host ?? null, event_type: "page_view",
  });
  if (error) {
    console.error("pageview_insert_failed", { code: error.code });
    return json({ error: "event_unavailable" }, 503, origin);
  }
  return json({ accepted: true }, 202, origin);
});
