// GE4u English Ward — shared plan catalogue and entitlement helpers (game + admin).
// Prices below are only the defaults used by the admin page's "Tạo bộ gói mặc định" button;
// the live prices are the documents in Firestore `plans/{planId}`, editable in the admin page.

// Specialty bundles: which doctor departments (startDoctor ids) and professions (startProf ids) each unlocks.
export const BUNDLES = {
  noi:       { vi: "Nội khoa",                         en: "Internal medicine", depts: ["im", "card", "resp", "gi", "endo", "neuro"], profs: [] },
  ngoai:     { vi: "Ngoại & Cấp cứu",                   en: "Surgery & emergency", depts: ["er", "surg", "ortho"], profs: [] },
  sannhi:    { vi: "Sản – Nhi",                         en: "Obstetrics & paediatrics", depts: ["ob", "ped"], profs: ["mid"] },
  dieuduong: { vi: "Điều dưỡng – Hộ sinh",              en: "Nursing & midwifery", depts: [], profs: ["nurse", "mid"] },
  duoc:      { vi: "Dược",                              en: "Pharmacy", depts: [], profs: ["pharm"] },
  ck:        { vi: "Chuyên khoa lẻ (Mắt, TMH, RHM, Da liễu)", en: "Eye, ENT, dental & skin", depts: ["eye", "ent", "dent", "derm"], profs: [] },
  ytcc:      { vi: "YTCC – Dinh dưỡng – CTXH",          en: "Public health, nutrition & social work", depts: [], profs: ["epi", "diet", "sw"] },
};

// type: time (days of full access) · spec (days for one bundle) · lifetime · group (class code with seats + days)
export const DEFAULT_PLANS = [
  { id: "p7",    type: "time", name: "Premium 7 ngày",  days: 7,   priceVnd: 29000,  order: 1, badge: "Dùng thử" },
  { id: "p30",   type: "time", name: "Premium 1 tháng", days: 30,  priceVnd: 79000,  order: 2, badge: "Phổ biến" },
  { id: "p90",   type: "time", name: "Premium 3 tháng", days: 90,  priceVnd: 199000, order: 3, badge: "" },
  { id: "p365",  type: "time", name: "Premium 1 năm",   days: 365, priceVnd: 599000, order: 4, badge: "Tiết kiệm nhất" },
  ...Object.entries(BUNDLES).map(([b, x], i) => ({ id: "spec-" + b, type: "spec", bundle: b, name: "Chuyên ngành " + x.vi + " · 3 tháng", days: 90, priceVnd: 99000, order: 10 + i, badge: "" })),
  { id: "life",       type: "lifetime", name: "Trọn đời",                          priceVnd: 899000,  order: 30, badge: "" },
  { id: "life-combo", type: "lifetime", name: "Trọn đời + toàn bộ bộ học liệu PDF", priceVnd: 1299000, packs: true, order: 31, badge: "Combo" },
  { id: "g10", type: "group", name: "Lớp học 10 người · 6 tháng", seats: 10, days: 180, priceVnd: 690000,  order: 40, badge: "" },
  { id: "g30", type: "group", name: "Lớp học 30 người · 6 tháng", seats: 30, days: 180, priceVnd: 1590000, order: 41, badge: "Giảng viên" },
  { id: "g60", type: "group", name: "Lớp học 60 người · 1 năm",   seats: 60, days: 365, priceVnd: 2990000, order: 42, badge: "" },
].map((p) => ({ active: true, ...p }));

export const PLAN_TYPES = { time: "Theo thời gian", spec: "Theo chuyên ngành", lifetime: "Trọn đời & combo", group: "Nhóm / lớp học" };

const ms = (t) => (t && typeof t.toMillis === "function" ? t.toMillis() : t ? new Date(t).getTime() : 0);

// Full access: lifetime, an unexpired `until`, or a legacy premium flag with no dates at all.
export function fullAccess(ent, now = Date.now()) {
  if (!ent || ent.premium !== true) return false;
  if (ent.lifetime === true) return true;
  if (ent.until) return ms(ent.until) > now;
  return !ent.spec; // legacy: premium:true set by hand before plans existed
}
export function bundleUntil(ent, bundle) { return ent && ent.spec && ent.spec[bundle] ? ms(ent.spec[bundle]) : 0; }
export function canPlay(ent, kind, id, now = Date.now()) {
  if (fullAccess(ent, now)) return true;
  if (!ent || !ent.spec || kind === "patient") return false;
  return Object.entries(BUNDLES).some(([b, x]) => bundleUntil(ent, b) > now && (kind === "doctor" ? x.depts : x.profs).includes(id));
}
export function describeEnt(ent, now = Date.now()) {
  if (!ent || ent.premium !== true) return "Miễn phí";
  if (ent.lifetime === true) return "Trọn đời ⭐";
  const out = [];
  if (ent.until && ms(ent.until) > now) out.push("Premium đến " + new Date(ms(ent.until)).toLocaleDateString("vi-VN"));
  for (const [b, t] of Object.entries(ent.spec || {})) if (ms(t) > now) out.push((BUNDLES[b] ? BUNDLES[b].vi : b) + " đến " + new Date(ms(t)).toLocaleDateString("vi-VN"));
  if (!out.length && !ent.until && !ent.spec) return "Premium ⭐";
  return out.join(" · ") || "Hết hạn";
}
export const vnd = (n) => Number(n || 0).toLocaleString("vi-VN") + "đ";
export function perDay(p) { return p.days ? Math.round(p.priceVnd / p.days) : 0; }

// VietQR quick link (free image API of vietqr.io): bank BIN + account number + exact amount + transfer note.
export function vietqrUrl(pay, amount, note) {
  return "https://img.vietqr.io/image/" + encodeURIComponent(pay.bankBin) + "-" + encodeURIComponent(pay.accountNo) +
    "-compact2.png?amount=" + encodeURIComponent(amount) + "&addInfo=" + encodeURIComponent(note) +
    "&accountName=" + encodeURIComponent(pay.accountName || "");
}
export const BANKS = [["970436", "Vietcombank"], ["970415", "VietinBank"], ["970418", "BIDV"], ["970405", "Agribank"], ["970407", "Techcombank"],
  ["970422", "MB Bank"], ["970416", "ACB"], ["970432", "VPBank"], ["970423", "TPBank"], ["970403", "Sacombank"], ["970441", "VIB"],
  ["970437", "HDBank"], ["970443", "SHB"], ["970448", "OCB"], ["970426", "MSB"], ["970440", "SeABank"], ["970431", "Eximbank"],
  ["970449", "LPBank"], ["970428", "Nam A Bank"], ["970454", "BVBank (Bản Việt)"], ["963388", "Timo"], ["546034", "CAKE"]];

// Order / class codes: 8 characters without look-alikes (no 0/O, 1/I/L).
export function newCode(prefix = "GE4U") {
  const A = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; let s = "";
  const r = crypto.getRandomValues(new Uint32Array(6)); for (const x of r) s += A[x % A.length];
  return prefix + s;
}
