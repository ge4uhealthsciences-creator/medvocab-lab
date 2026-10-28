import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

function allowedOrigins(): string[] {
  return (Deno.env.get("ALLOWED_ORIGINS") ?? "").split(",").map((v) => v.trim()).filter(Boolean);
}
function headers(origin: string | null) {
  const h: Record<string, string> = {
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Vary": "Origin",
    "Content-Type": "application/json",
  };
  if (origin && allowedOrigins().includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}
function json(body: unknown, status = 200, origin: string | null = null) {
  return new Response(JSON.stringify(body), { status, headers: headers(origin) });
}
Deno.serve(async (req) => {
  const origin = req.headers.get("Origin");
  if (origin && !allowedOrigins().includes(origin)) return json({ error: "origin_not_allowed" }, 403, null);
  if (req.method === "OPTIONS") return new Response("ok", { headers: headers(origin) });
  if (req.method !== "GET") return json({ error: "method_not_allowed" }, 405, origin);
  const url = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !anonKey || !serviceRoleKey) return json({ error: "service_not_configured", status: "unavailable" }, 503, origin);
  const authHeader = req.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) return json({ error: "unauthorized" }, 401, origin);
  const authClient = createClient(url, anonKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: userData, error: userError } = await authClient.auth.getUser(authHeader.slice(7));
  if (userError || !userData.user) return json({ error: "unauthorized" }, 401, origin);
  if (userData.user.app_metadata?.role !== "admin") return json({ error: "forbidden" }, 403, origin);
  const adminClient = createClient(url, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } });
  // Daily reports use the Vietnam calendar day, independent of the Edge Function runtime timezone.
  const localDate = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date());
  const start = new Date(`${localDate}T00:00:00+07:00`);
  const end = new Date(new Date(start).getTime() + 24 * 60 * 60 * 1000);
  const { data, error } = await adminClient.rpc("ge4u_admin_overview", {
    p_start: start.toISOString(), p_end: end.toISOString(),
  });
  if (error) {
    console.error("admin_overview_query_failed", { code: error.code });
    return json({ error: "analytics_unavailable", status: "unavailable" }, 503, origin);
  }
  const { error: auditError } = await adminClient.from("audit_events").insert({
    actor_id: userData.user.id, action: "admin.overview.read", target_type: "analytics",
    target_id: "daily-overview", outcome: "success",
    metadata: { range_start: start.toISOString(), range_end: end.toISOString() },
  });
  if (auditError) console.error("audit_write_failed", { code: auditError.code });
  return json({ data, status: "ok" }, 200, origin);
});
