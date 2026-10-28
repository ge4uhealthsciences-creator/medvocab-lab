import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const headers = {
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Content-Type": "application/json",
};
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers });
}
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "GET") return json({ error: "method_not_allowed" }, 405);
  const url = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !anonKey || !serviceRoleKey) return json({ error: "service_not_configured", status: "unavailable" }, 503);
  const authHeader = req.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) return json({ error: "unauthorized" }, 401);
  const authClient = createClient(url, anonKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: userData, error: userError } = await authClient.auth.getUser(authHeader.slice(7));
  if (userError || !userData.user) return json({ error: "unauthorized" }, 401);
  if (userData.user.app_metadata?.role !== "admin") return json({ error: "forbidden" }, 403);
  const adminClient = createClient(url, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const now = new Date();
  const start = new Date(now); start.setUTCHours(0, 0, 0, 0);
  const end = new Date(start); end.setUTCDate(end.getUTCDate() + 1);
  const { data, error } = await adminClient.rpc("ge4u_admin_overview", {
    p_start: start.toISOString(), p_end: end.toISOString(),
  });
  if (error) {
    console.error("admin_overview_query_failed", { code: error.code });
    return json({ error: "analytics_unavailable", status: "unavailable" }, 503);
  }
  const { error: auditError } = await adminClient.from("audit_events").insert({
    actor_id: userData.user.id, action: "admin.overview.read", target_type: "analytics",
    target_id: "daily-overview", outcome: "success",
    metadata: { range_start: start.toISOString(), range_end: end.toISOString() },
  });
  if (auditError) console.error("audit_write_failed", { code: auditError.code });
  return json({ data, status: "ok" });
});
