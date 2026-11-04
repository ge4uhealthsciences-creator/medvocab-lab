// GE4u English Ward — account gate, free-play limit, Premium unlock and GE4u vocabulary.
// Loaded as a module after the game script. Accounts use Firebase Authentication;
// entitlements and premium vocabulary live in Firestore (see firebase/firestore.rules).
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, createUserWithEmailAndPassword,
  signInWithEmailAndPassword, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, getDocs, collection, serverTimestamp, query, where, writeBatch, increment, Timestamp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { firebaseConfig, firebaseReady } from "./ge4u-firebase-config.js";
import { BUNDLES, PLAN_TYPES, fullAccess, canPlay, describeEnt, vnd, perDay, vietqrUrl, newCode } from "./ge4u-plans.js";

const FREE_CASES_PER_DAY = 3;   // signed-in free players
const GUEST_CASES_PER_DAY = 1;  // only while Firebase is not configured yet
const PRODUCTS_URL = "ge4u-products.html";
// No-account trial: TRIAL_SECONDS in each mode, counted per device AND per network (a hash of the IP address,
// never the address itself), so clearing the browser does not reset it. After that an account is required.
const TRIAL_SECONDS = 180;
const TRIAL_DAYS = 30;  // the network record expires after this (Firestore TTL on expireAt)
const TRIAL_MODES = { P: "Bệnh nhân / Cấp cứu", R: "Đóng vai nhân viên y tế", Q: "Ôn tập & quiz", T: "Tham quan bệnh viện" };
const $ = (id) => document.getElementById(id);
const today = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());

let auth = null, db = null, user = null, premium = false, guest = false, ent = null, trial = false;
if (firebaseReady) { const app = initializeApp(firebaseConfig); auth = getAuth(app); db = getFirestore(app); }

// ---------- UI ----------
const css = document.createElement("style");
css.textContent = `
#g4gate{position:fixed;inset:0;z-index:60;background:rgba(16,40,58,.97);color:#fff;display:flex;align-items:center;justify-content:center;padding:16px;overflow:auto}
#g4gate .card{width:min(400px,100%);background:#fff;color:#10283a;border-radius:18px;padding:18px;display:flex;flex-direction:column;gap:10px}
#g4gate h2{margin:0;font-size:22px}#g4gate p{margin:0;color:#4b6475;font-size:14px}
#g4gate input{width:100%;padding:11px;border:1px solid #cfdce3;border-radius:10px;font:inherit}
#g4gate button{border:0;border-radius:12px;padding:12px;font:inherit;font-weight:700;cursor:pointer}
#g4gate .pri{background:#087e83;color:#fff}#g4gate .sec{background:#eaf1f4;color:#10283a}
#g4gate .msg{min-height:18px;font-size:13px;color:#8f1d2c}
#g4bar{position:static;background:rgba(255,255,255,.95);color:#10283a;border-radius:10px;padding:6px 10px;font-size:12.5px;display:none;gap:8px;align-items:center;flex-wrap:wrap;justify-content:center;width:min(560px,94vw);margin:0 auto}
#g4bar button{border:0;background:#10283a;color:#fff;border-radius:8px;padding:4px 8px;font:inherit;font-size:12px;cursor:pointer}
#g4wall{position:fixed;inset:0;z-index:61;background:rgba(16,40,58,.95);display:none;align-items:center;justify-content:center;padding:16px}
#g4wall .card{width:min(400px,100%);background:#fff;color:#10283a;border-radius:18px;padding:18px;display:flex;flex-direction:column;gap:10px;text-align:center}
#g4wall a,#g4wall button{display:block;border:0;border-radius:12px;padding:12px;font:inherit;font-weight:700;text-decoration:none;cursor:pointer}
#g4wall a{background:#f5a30a;color:#10283a}#g4wall button{background:#eaf1f4;color:#10283a}
#g4voc{position:fixed;inset:0;z-index:59;background:rgba(16,40,58,.97);color:#fff;display:none;flex-direction:column;padding:16px;overflow:auto}
#g4voc .row{display:flex;justify-content:space-between;align-items:center;gap:8px;max-width:640px;width:100%;margin:0 auto 10px}
#g4voc select{flex:1;padding:8px;border-radius:10px;font:inherit}
#g4voc .w{max-width:640px;width:100%;margin:0 auto 6px;background:#fff;color:#10283a;border-radius:12px;padding:8px 12px;cursor:pointer}
#g4voc .w b{display:block}#g4voc .w span{font-size:13px;color:#4b6475}
#g4shop{position:fixed;inset:0;z-index:62;background:rgba(16,40,58,.97);display:none;justify-content:center;overflow:auto;padding:16px}
#g4shop .in{width:min(760px,100%);color:#fff;display:flex;flex-direction:column;gap:12px}
#g4shop h2{margin:0;font-size:22px}#g4shop .sub{color:#c7dbe5;font-size:14px;margin:0}
#g4shop .tabs{display:flex;gap:6px;flex-wrap:wrap}#g4shop .tabs button{border:0;border-radius:99px;padding:8px 12px;font:inherit;font-size:14px;background:#24465d;color:#fff;cursor:pointer}
#g4shop .tabs button[aria-pressed=true]{background:#f5a30a;color:#10283a;font-weight:700}
#g4shop .plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:10px}
#g4shop .plan{background:#fff;color:#10283a;border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:6px;position:relative}
#g4shop .plan .b{position:absolute;top:-8px;right:10px;background:#f5a30a;color:#10283a;border-radius:99px;padding:2px 9px;font-size:12px;font-weight:700}
#g4shop .plan .p{font-size:22px;font-weight:800}#g4shop .plan small{color:#4b6475}
#g4shop .plan button,#g4shop .box button{border:0;border-radius:12px;padding:10px;font:inherit;font-weight:700;cursor:pointer;background:#087e83;color:#fff}
#g4shop .box{background:#fff;color:#10283a;border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:8px}
#g4shop .box input{padding:10px;border:1px solid #cfdce3;border-radius:10px;font:inherit}
#g4shop .qr{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}#g4shop .qr img{width:220px;max-width:100%;border-radius:12px;border:1px solid #d5e4ea}
#g4shop .kv{font-size:14px;line-height:1.7}#g4shop .kv b{font-family:ui-monospace,monospace;font-size:15px}
#g4shop .close{align-self:flex-end;border:0;border-radius:10px;padding:8px 12px;font:inherit;cursor:pointer}
#g4shop [hidden]{display:none!important}
#g4shop .ord{font-size:13.5px;border-top:1px solid #e3ecf0;padding-top:6px}
`;
document.head.append(css);

const gate = document.createElement("div");
gate.id = "g4gate";
gate.innerHTML = `<div class="card">
  <h2>🏥 GE4u English Ward</h2>
  <p>Create a free account to play. Free: ${FREE_CASES_PER_DAY} games a day and unlimited hospital tours. Premium: unlimited games plus the GE4u learning-pack vocabulary.</p><p style="font-size:12.5px">Tạo tài khoản miễn phí để chơi.</p>
  <button class="pri" id="g4google">Continue with Google</button>
  <p style="text-align:center">or use email</p>
  <input id="g4email" type="email" autocomplete="email" placeholder="Email">
  <input id="g4pass" type="password" autocomplete="current-password" placeholder="Password (at least 6 characters)">
  <button class="sec" id="g4in">Sign in</button>
  <button class="sec" id="g4up">Create account</button>
  <button class="sec" id="g4guest" hidden>Play as guest (${GUEST_CASES_PER_DAY} game a day)</button>
  <button class="sec" id="g4trial" style="background:#fff4dc">▶ Try without an account · 3 minutes in each mode<small style="display:block;font-weight:400;font-size:12px">Chơi thử không cần tài khoản: 3 phút mỗi chế độ</small></button>
  <p id="g4trialNote" style="font-size:11.5px">Chơi thử được giới hạn theo thiết bị và theo mạng: GE4u lưu một mã băm (không lưu địa chỉ IP gốc) trong ${TRIAL_DAYS} ngày để chặn chơi thử lặp lại. Hết thời gian chơi thử cần tạo tài khoản miễn phí.</p>
  <div class="msg" id="g4msg"></div>
</div>`;
document.body.append(gate);

const bar = document.createElement("div");
bar.id = "g4bar";
bar.innerHTML = `<span id="g4who"></span><button id="g4shopBtn" style="background:#f5a30a;color:#10283a;font-weight:700">⭐ Nâng cấp</button><button id="g4vocBtn">📚 GE4u words</button><button id="g4out">Sign out</button>`;
(document.getElementById("menuTop") || document.body).append(bar);  // inside the menu, so it never covers the joystick or buttons

const wall = document.createElement("div");
wall.id = "g4wall";
wall.innerHTML = `<div class="card"><h2>That's all your free games for today</h2>
  <p id="g4wallTxt"></p>
  <a href="#" id="g4wallShop">⭐ Xem các gói Premium (từ 29.000đ)</a>
  <p style="font-size:13px;color:#4b6475">Chuyển khoản bằng mã QR; GE4u kích hoạt ngay khi nhận được tiền.</p>
  <button id="g4wallClose">Back to the hospital tour</button></div>`;
document.body.append(wall);

const voc = document.createElement("div");
voc.id = "g4voc";
voc.innerHTML = `<div class="row"><b>📚 GE4u vocabulary</b><button id="g4vocClose" style="border:0;border-radius:10px;padding:8px 12px;font:inherit">Close</button></div>
  <div class="row"><select id="g4vocSel" aria-label="Word set"></select></div><div id="g4vocList"></div>`;
document.body.append(voc);

const shop = document.createElement("div");
shop.id = "g4shop";
shop.innerHTML = `<div class="in"><button class="close" id="g4shopClose">✕ Đóng</button>
  <h2>⭐ GE4u English Ward Premium</h2>
  <p class="sub" id="g4shopNow"></p>
  <div class="tabs" id="g4tabs"></div>
  <div class="plans" id="g4plans"></div>
  <div class="box" id="g4pay" hidden></div>
  <div class="box"><b>🎓 Có mã lớp học từ giảng viên?</b><div style="display:flex;gap:8px"><input id="g4code" placeholder="VD: LOPAB12CD34" style="flex:1"><button id="g4redeem">Kích hoạt</button></div><small id="g4codeMsg"></small></div>
  <div class="box"><b>🧾 Đơn của tôi</b><div id="g4orders"><small>Chưa có đơn nào.</small></div></div>
</div>`;
document.body.append(shop);

const msg = (t) => { $("g4msg").textContent = t; };
const vi = (e) => {
  const c = (e && e.code) || "";
  if (c.includes("invalid-credential") || c.includes("wrong-password") || c.includes("user-not-found")) return "Wrong email or password.";
  if (c.includes("email-already-in-use")) return "This email already has an account. Tap Sign in.";
  if (c.includes("weak-password")) return "Your password needs at least 6 characters.";
  if (c.includes("popup")) return "The Google sign-in window was closed or blocked. Try again or use email.";
  return "Could not sign in. Check your connection and try again.";
};

if (!firebaseReady) {
  msg("Accounts are being set up. You can play as a guest for now.");
  ["g4google", "g4in", "g4up"].forEach((id) => { $(id).disabled = true; $(id).style.opacity = .5; });
  $("g4guest").hidden = false;
}
$("g4guest").onclick = () => { guest = true; gate.style.display = "none"; showBar(); loadVocab(); };
$("g4google").onclick = async () => { try { await signInWithPopup(auth, new GoogleAuthProvider()); } catch (e) { msg(vi(e)); } };
$("g4in").onclick = async () => { try { await signInWithEmailAndPassword(auth, $("g4email").value.trim(), $("g4pass").value); } catch (e) { msg(vi(e)); } };
$("g4up").onclick = async () => { try { await createUserWithEmailAndPassword(auth, $("g4email").value.trim(), $("g4pass").value); } catch (e) { msg(vi(e)); } };
$("g4out").onclick = async () => {
  if (trial && !user) { tSaveNet(); trial = false; tCur = null; msg(""); tRefreshGate(); gate.style.display = "flex"; bar.style.display = "none"; return; }
  if (auth && user) await signOut(auth); location.reload();
};
$("g4wallClose").onclick = () => { wall.style.display = "none"; };
$("g4wallShop").onclick = (e) => { e.preventDefault(); wall.style.display = "none"; openShop(); };
$("g4shopBtn").onclick = () => openShop();
$("g4shopClose").onclick = () => { shop.style.display = "none"; };
window.GE4U_SHOP = () => openShop();
// Upgrade entry in the main menu too (the bottom bar sits under the menu overlay)
try {
  const mb = document.createElement("button"); mb.className = "big"; mb.id = "mShop"; mb.style.cssText = "background:#f5a30a;color:#10283a";
  mb.innerHTML = "⭐ Premium &amp; mã lớp học<small>Gói 7 ngày · tháng · năm · chuyên ngành · trọn đời · lớp học</small>";
  mb.onclick = () => openShop();
  const anchor = document.getElementById("mQ") || document.getElementById("mV");
  if (anchor) anchor.before(mb);
} catch (e) {}
$("g4vocBtn").onclick = () => { voc.style.display = "flex"; renderVoc(); };
$("g4vocClose").onclick = () => { voc.style.display = "none"; };

function showBar() {
  bar.style.display = "flex";
  $("g4who").textContent = trial ? trialLabel() : guest ? "Guest" : ((user.email || "Signed in") + " · " + describeEnt(ent));
  $("g4out").textContent = trial ? "Create account" : "Sign out";
  $("g4shopBtn").hidden = trial;
}

// ---------- no-account trial ----------
const TKEY = "ge4u-trial-v1";
let tUsed = { P: 0, R: 0, Q: 0, T: 0 }, tCur = null, tNet = null, tDirty = false;
try { Object.assign(tUsed, JSON.parse(localStorage.getItem(TKEY) || "{}")); } catch (e) {}
const tLeft = (m) => Math.max(0, TRIAL_SECONDS - (tUsed[m] || 0));
const tAnyLeft = () => Object.keys(TRIAL_MODES).some((m) => tLeft(m) > 0);
const mmss = (s) => Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
function trialLabel() {
  return "Chơi thử · " + (tCur ? TRIAL_MODES[tCur] + " còn " + mmss(tLeft(tCur)) : Object.keys(TRIAL_MODES).filter((m) => tLeft(m) > 0).length + "/4 chế độ còn thời gian");
}
function tSaveLocal() { try { localStorage.setItem(TKEY, JSON.stringify(tUsed)); } catch (e) {} }
async function tNetworkId() {
  try {
    const r = await fetch("https://api.ipify.org?format=json", { cache: "no-store" });
    const ip = (await r.json()).ip;
    if (!ip) return null;
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("ge4u-trial|" + ip));
    return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
  } catch (e) { return null; }
}
async function tLoadNet() {
  tNet = await tNetworkId();
  if (!tNet || !db) return;
  try {
    const d = await getDoc(doc(db, "trials", tNet));
    if (d.exists()) for (const m of Object.keys(TRIAL_MODES)) tUsed[m] = Math.max(tUsed[m] || 0, Number(d.data()[m]) || 0);
    tSaveLocal();
  } catch (e) {}
}
async function tSaveNet() {
  if (!tNet || !db || !tDirty) return;
  tDirty = false;
  const data = { updatedAt: serverTimestamp(), expireAt: Timestamp.fromMillis(Date.now() + TRIAL_DAYS * 864e5) };
  for (const m of Object.keys(TRIAL_MODES)) data[m] = Math.min(TRIAL_SECONDS, Math.round(tUsed[m] || 0));
  try { await setDoc(doc(db, "trials", tNet), data); } catch (e) {}
}
function tRefreshGate() {
  const left = tAnyLeft();
  $("g4trial").hidden = !left || !!user;
  $("g4trialNote").hidden = !!user;
}
function tLock(m) {
  // tCur stays: if the player goes "Back to the game" in this mode, the next tick locks again.
  try { document.getElementById("menuBtn").click(); } catch (e) {}
  tSaveNet();
  tRefreshGate();
  msg(`Hết 3 phút chơi thử "${TRIAL_MODES[m]}". Tạo tài khoản miễn phí để chơi tiếp` + (tAnyLeft() ? " — hoặc chơi thử chế độ khác." : "."));
  $("g4trial").firstChild.textContent = tAnyLeft() ? "▶ Try another mode" : "";
  gate.style.display = "flex";
  bar.style.display = "none";
}
// Called before a mode starts; true when the trial still has time in that mode.
function tAllow(m) {
  if (tLeft(m) > 0) { tCur = m; showBar(); return true; }
  tLock(m);
  return false;
}
$("g4trial").onclick = async () => {
  $("g4trial").disabled = true;
  await tLoadNet();
  $("g4trial").disabled = false;
  tRefreshGate();
  if (!tAnyLeft()) { msg("Bạn đã dùng hết thời gian chơi thử trên thiết bị hoặc mạng này. Tạo tài khoản miễn phí để chơi tiếp."); return; }
  trial = true; msg(""); gate.style.display = "none"; showBar(); loadVocab();
  try { document.getElementById("menu").style.display = "flex"; } catch (e) {}
};
setInterval(() => {
  if (!trial || user || !tCur || gate.style.display === "flex" || document.visibilityState !== "visible") return;
  const menu = document.getElementById("menu");
  if (menu && menu.style.display !== "none" && getComputedStyle(menu).display !== "none") return;
  if (tLeft(tCur) <= 0) { tLock(tCur); return; }
  tUsed[tCur] = (tUsed[tCur] || 0) + 1; tDirty = true; tSaveLocal();
  $("g4who").textContent = trialLabel();
  if (tLeft(tCur) <= 0) tLock(tCur);
}, 1000);
setInterval(tSaveNet, 15000);
addEventListener("pagehide", () => { tSaveNet(); });
// The tour and review are not cases, so they are gated here.
try {
  const mT = document.getElementById("mT"), tourClick = mT && mT.onclick;
  if (tourClick) mT.onclick = (e) => { if (trial && !tAllow("T")) return; return tourClick.call(mT, e); };
} catch (e) {}
if (typeof window.startReview === "function") {
  const rv = window.startReview;
  window.startReview = function (...a) { if (trial && !tAllow("Q")) return; return rv.apply(this, a); };
}
tRefreshGate();

if (auth) onAuthStateChanged(auth, async (u) => {
  user = u;
  if (!u) { if (!trial) { gate.style.display = "flex"; bar.style.display = "none"; } tRefreshGate(); return; }
  trial = false; tCur = null;
  gate.style.display = "none";
  try { await setDoc(doc(db, "users", u.uid), { email: u.email || "", lastSeen: serverTimestamp() }, { merge: true }); } catch (e) {}
  await loadEnt();
  showBar();
  loadVocab();
});

async function loadEnt() {
  try { const d = await getDoc(doc(db, "entitlements", user.uid)); ent = d.exists() ? d.data() : null; } catch (e) { ent = null; }
  premium = fullAccess(ent); window.GE4U_ENT = ent;
}

// ---------- shop: plans, VietQR payment, class codes, my orders ----------
let PLANS = [], PAY = null, tab = "time";
async function openShop() {
  if (!user) { gate.style.display = "flex"; return; }
  shop.style.display = "flex";
  $("g4shopNow").textContent = "Tài khoản: " + (user.email || "") + " · Hiện tại: " + describeEnt(ent);
  if (!PLANS.length) {
    try { (await getDocs(collection(db, "plans"))).forEach((d) => { const p = { id: d.id, ...d.data() }; if (p.active) PLANS.push(p); }); } catch (e) {}
    PLANS.sort((a, b) => (a.order || 0) - (b.order || 0));
    try { const c = await getDoc(doc(db, "config", "payment")); PAY = c.exists() ? c.data() : null; } catch (e) {}
  }
  renderTabs(); renderPlans(); renderOrders();
}
function renderTabs() {
  const t = $("g4tabs"); t.replaceChildren();
  Object.entries(PLAN_TYPES).forEach(([k, v]) => { if (!PLANS.some((p) => p.type === k)) return;
    const b = document.createElement("button"); b.textContent = v; b.setAttribute("aria-pressed", String(k === tab)); b.onclick = () => { tab = k; renderTabs(); renderPlans(); }; t.append(b); });
}
function planDesc(p) {
  if (p.type === "time") return "Mở toàn bộ ca bệnh, mọi vai, ôn tập không giới hạn · " + p.days + " ngày · ~" + vnd(perDay(p)) + "/ngày";
  if (p.type === "spec") { const b = BUNDLES[p.bundle] || {}; return "Không giới hạn các ca " + (b.vi || p.bundle) + " · " + p.days + " ngày"; }
  if (p.type === "lifetime") return "Mở toàn bộ game vĩnh viễn, gồm mọi ca bệnh mới" + (p.packs ? " + toàn bộ bộ học liệu PDF GE4u" : "");
  if (p.type === "group") return p.seats + " tài khoản học viên · " + p.days + " ngày · ~" + vnd(Math.round(p.priceVnd / p.seats)) + "/người. Nhận 1 mã lớp để học viên tự kích hoạt.";
  return "";
}
function renderPlans() {
  const box = $("g4plans"); box.replaceChildren();
  const list = PLANS.filter((p) => p.type === tab);
  if (!list.length) { box.textContent = "Các gói đang được cập nhật."; return; }
  list.forEach((p) => {
    const c = document.createElement("div"); c.className = "plan";
    if (p.badge) { const b = document.createElement("span"); b.className = "b"; b.textContent = p.badge; c.append(b); }
    const h = document.createElement("b"); h.textContent = p.name;
    const pr = document.createElement("div"); pr.className = "p"; pr.textContent = vnd(p.priceVnd);
    const d = document.createElement("small"); d.textContent = planDesc(p);
    const bt = document.createElement("button"); bt.textContent = "Chọn gói này"; bt.onclick = () => buy(p);
    c.append(h, pr, d, bt); box.append(c);
  });
}
async function buy(p) {
  const pay = $("g4pay"); pay.hidden = false; pay.replaceChildren();
  if (!PAY || !PAY.accountNo) { pay.textContent = "GE4u đang cập nhật thông tin nhận thanh toán. Vui lòng quay lại sau."; return; }
  const code = newCode("GE4U");
  try {
    await setDoc(doc(db, "orders", code), { code, uid: user.uid, email: user.email || "", planId: p.id, planName: p.name, amount: p.priceVnd, status: "pending", createdAt: serverTimestamp() });
  } catch (e) { pay.textContent = "Không tạo được đơn (" + (e.code || e.message) + "). Thử lại sau ít phút."; return; }
  const wrap = document.createElement("div"); wrap.className = "qr";
  const img = document.createElement("img"); img.alt = "Mã VietQR"; img.src = vietqrUrl(PAY, p.priceVnd, code);
  const kv = document.createElement("div"); kv.className = "kv";
  const bank = (PAY.bankName || "") ;
  [["Gói", p.name], ["Số tiền", vnd(p.priceVnd)], ["Ngân hàng", bank], ["Số tài khoản", PAY.accountNo], ["Chủ tài khoản", PAY.accountName || ""], ["Nội dung CK", code]].forEach(([k, v]) => {
    const r = document.createElement("div"); r.append(k + ": "); const b = document.createElement("b"); b.textContent = v; r.append(b); kv.append(r); });
  const note = document.createElement("small"); note.textContent = "Quét mã bằng app ngân hàng (đã điền sẵn số tiền và nội dung). Giữ đúng nội dung " + code + " để GE4u đối chiếu. Premium được kích hoạt khi GE4u nhận được tiền, thường trong ngày.";
  kv.append(note); wrap.append(img, kv);
  const done = document.createElement("button"); done.textContent = "✅ Tôi đã chuyển khoản";
  done.onclick = async () => { try { await setDoc(doc(db, "orders", code), { status: "claimed", claimedAt: serverTimestamp() }, { merge: true }); done.disabled = true; done.textContent = "Đã báo GE4u — đang chờ xác nhận"; renderOrders(); } catch (e) { done.textContent = "Lỗi, thử lại"; } };
  pay.append(wrap, done); pay.scrollIntoView({ behavior: "smooth" }); renderOrders();
}
const ST = { pending: "Chờ chuyển khoản", claimed: "Đã báo chuyển khoản – chờ xác nhận", paid: "✅ Đã kích hoạt", cancelled: "Đã huỷ" };
async function renderOrders() {
  const box = $("g4orders"); if (!user) return;
  let rows = [];
  try { (await getDocs(query(collection(db, "orders"), where("uid", "==", user.uid)))).forEach((d) => rows.push(d.data())); } catch (e) { return; }
  if (!rows.length) return;
  rows.sort((a, b) => ((b.createdAt && b.createdAt.toMillis()) || 0) - ((a.createdAt && a.createdAt.toMillis()) || 0));
  box.replaceChildren(...rows.slice(0, 8).map((o) => { const d = document.createElement("div"); d.className = "ord";
    d.textContent = o.code + " · " + o.planName + " · " + vnd(o.amount) + " · " + (ST[o.status] || o.status) + (o.classCode ? " · Mã lớp: " + o.classCode : ""); return d; }));
  if (rows.some((o) => o.status === "paid")) { await loadEnt(); showBar(); $("g4shopNow").textContent = "Tài khoản: " + (user.email || "") + " · Hiện tại: " + describeEnt(ent); }
}
$("g4redeem").onclick = async () => {
  const code = $("g4code").value.trim().toUpperCase(), m = $("g4codeMsg"); m.textContent = "";
  if (!code) return;
  try {
    const c = await getDoc(doc(db, "classCodes", code));
    if (!c.exists() || !c.data().active) { m.textContent = "Mã không đúng hoặc đã hết hiệu lực."; return; }
    const cd = c.data();
    if (cd.used >= cd.seats) { m.textContent = "Mã lớp đã dùng hết số chỗ."; return; }
    if (fullAccess(ent)) { m.textContent = "Tài khoản đã có Premium đến " + describeEnt(ent) + "."; return; }
    const b = writeBatch(db);
    b.set(doc(db, "classCodes", code, "members", user.uid), { email: user.email || "", at: serverTimestamp() });
    b.update(doc(db, "classCodes", code), { used: increment(1) });
    b.set(doc(db, "entitlements", user.uid), { premium: true, via: "code", code, until: cd.until, updatedAt: serverTimestamp() });
    await b.commit();
    await loadEnt(); showBar(); m.textContent = "🎉 Đã kích hoạt: " + describeEnt(ent);
  } catch (e) { m.textContent = "Không kích hoạt được (" + (e.code || "lỗi") + "). Mỗi tài khoản chỉ dùng mã một lần."; }
};

// ---------- progress saving ----------
window.GE4U_SAVE = (k, v) => {
  if (!db || !user) return;
  setDoc(doc(db, "users", user.uid, "game", "progress"), { [String(k).slice(0, 60)]: v, updatedAt: serverTimestamp() }, { merge: true }).catch(() => {});
};

// ---------- free-play limit ----------
const usageKey = () => "ge4u-h3d-usage-" + (user ? user.uid : "guest");
function usedToday() {
  try { const u = JSON.parse(localStorage.getItem(usageKey()) || "{}"); return u.date === today() ? u.n : 0; } catch (e) { return 0; }
}
function countCase() {
  const n = usedToday() + 1;
  try { localStorage.setItem(usageKey(), JSON.stringify({ date: today(), n })); } catch (e) {}
  if (db && user) setDoc(doc(db, "users", user.uid), { usage: { date: today(), n } }, { merge: true }).catch(() => {});
}
function allowCase(kind, id) {
  if (trial && !user) return tAllow(kind === "patient" ? "P" : "R");
  if (canPlay(ent, kind, id)) return true;
  if (!guest && !user) { gate.style.display = "flex"; return false; }
  const limit = guest ? GUEST_CASES_PER_DAY : FREE_CASES_PER_DAY;
  if (usedToday() >= limit) {
    $("g4wallTxt").textContent = `Gói miễn phí có ${limit} lượt chơi mỗi ngày. Bạn vẫn có thể đi tham quan bệnh viện và dùng chế độ Ôn tập, hoặc mở Premium để chơi không giới hạn.`;
    wall.style.display = "flex";
    return false;
  }
  countCase();
  return true;
}
const KIND = { startPatient: "patient", startDoctor: "doctor", startProf: "prof" };
for (const name of ["startPatient", "startDoctor", "startProf"]) {
  const orig = window[name];
  if (typeof orig !== "function") continue;
  window[name] = function (...args) {
    if (!allowCase(KIND[name], args[0])) {
      try { const m = document.getElementById("menu"); if (m) m.style.display = "flex"; } catch (e) {}
      return;
    }
    return orig.apply(this, args);
  };
}

// ---------- GE4u vocabulary ----------
const PACKS = [];  // {id, title, premium, terms:[{term, ipa, meaning, definition, example}]}
async function loadVocab() {
  PACKS.length = 0;
  try {
    const parts = await (await fetch("data/word-parts.json")).json();
    PACKS.push({ id: "word-parts", title: "Word parts (free)", premium: false,
      terms: parts.parts.map((p) => ({ term: p.example, ipa: "", meaning: p.example_vi, definition: p.part + " = " + p.vi, example: "" })) });
  } catch (e) {}
  try {
    const bank = await (await fetch("data/social-video-bank.json")).json();
    for (const [cid, rows] of Object.entries(bank.channels)) {
      PACKS.push({ id: "free-" + cid, title: "Starter · " + cid + " (free)", premium: false,
        terms: rows.map((r) => ({ term: r[0], ipa: r[1], meaning: r[2], definition: r[3], example: r[4] })) });
    }
  } catch (e) {}
  if (premium && db) {
    try {
      const snap = await getDocs(collection(db, "packs"));
      snap.forEach((d) => {
        const p = d.data(); const terms = [];
        (p.groups || []).forEach((g) => (g.terms || []).forEach((t) => terms.push(Array.isArray(t)
          ? { term: t[0], ipa: t[1], meaning: t[2], definition: t[3], example: t[4] } : t)));
        PACKS.push({ id: d.id, title: "⭐ " + (p.vi || d.id), premium: true, terms });
      });
    } catch (e) {}
  }
  enrichCases();
}

// Add GE4u terms that appear in a case's own dialogue to that case's word chips (max 3 per case).
function enrichCases() {
  const all = [];
  PACKS.forEach((p) => p.terms.forEach((t) => { if (t.term && t.term.length > 3) all.push(t); }));
  const lists = [];
  try { if (Array.isArray(window.CASES)) lists.push(window.CASES); } catch (e) {}
  try { if (Array.isArray(window.RCASES)) lists.push(window.RCASES); } catch (e) {}
  for (const list of lists) for (const cs of list) {
    if (!cs || typeof cs !== "object") continue;
    cs.v = Array.isArray(cs.v) ? cs.v : [];
    const have = new Set(cs.v.map((w) => String(w[0]).toLowerCase()));
    const text = JSON.stringify(cs).toLowerCase();
    let added = 0;
    for (const t of all) {
      if (added >= 3) break;
      const k = t.term.toLowerCase();
      if (have.has(k)) continue;
      if (new RegExp("\\b" + k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(text)) {
        cs.v.push([t.term, t.meaning]); have.add(k); added++;
      }
    }
  }
}

function renderVoc() {
  const sel = $("g4vocSel");
  if (!sel.options.length || sel.options.length !== PACKS.length) {
    sel.innerHTML = "";
    PACKS.forEach((p, i) => sel.append(new Option(p.title + " · " + p.terms.length, String(i))));
    if (!premium) sel.append(new Option("🔒 Topic packs (Anatomy, Physiology, Internal Medicine…) — Premium", "locked"));
    sel.onchange = renderVoc;
  }
  const list = $("g4vocList"); list.innerHTML = "";
  if (sel.value === "locked") {
    const a = document.createElement("a"); a.href = PRODUCTS_URL; a.target = "_blank"; a.rel = "noopener";
    a.textContent = "Unlock Premium to study ~100 terms per topic →"; a.style.cssText = "color:#f5a30a;display:block;text-align:center;margin-top:12px";
    list.append(a); return;
  }
  const p = PACKS[Number(sel.value) || 0]; if (!p) return;
  p.terms.forEach((t) => {
    const w = document.createElement("div"); w.className = "w";
    const b = document.createElement("b"); b.textContent = "🔊 " + t.term + (t.ipa ? "  " + t.ipa : "");
    const s = document.createElement("span"); s.textContent = t.meaning + (t.definition ? " — " + t.definition : "");
    w.append(b, s); w.onclick = () => { try { window.say ? window.say(t.term) : speechSynthesis.speak(new SpeechSynthesisUtterance(t.term)); } catch (e) {} };
    list.append(w);
  });
}
