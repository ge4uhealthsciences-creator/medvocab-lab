// GE4u Hospital 3D — account gate, free-play limit, Premium unlock and GE4u vocabulary.
// Loaded as a module after the game script. Accounts use Firebase Authentication;
// entitlements and premium vocabulary live in Firestore (see firebase/firestore.rules).
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, createUserWithEmailAndPassword,
  signInWithEmailAndPassword, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, getDocs, collection, serverTimestamp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { firebaseConfig, firebaseReady } from "./ge4u-firebase-config.js";

const FREE_CASES_PER_DAY = 3;   // signed-in free players
const GUEST_CASES_PER_DAY = 1;  // only while Firebase is not configured yet
const PRODUCTS_URL = "ge4u-products.html";
const $ = (id) => document.getElementById(id);
const today = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());

let auth = null, db = null, user = null, premium = false, guest = false;
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
#g4bar{position:fixed;left:8px;bottom:8px;z-index:8;background:rgba(255,255,255,.95);color:#10283a;border-radius:10px;padding:6px 10px;font-size:12.5px;display:none;gap:8px;align-items:center}
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
`;
document.head.append(css);

const gate = document.createElement("div");
gate.id = "g4gate";
gate.innerHTML = `<div class="card">
  <h2>🏥 English Ward 3D</h2>
  <p>Create a free account to play. Free: ${FREE_CASES_PER_DAY} games a day and unlimited hospital tours. Premium: unlimited games plus the GE4u learning-pack vocabulary.</p><p style="font-size:12.5px">Tạo tài khoản miễn phí để chơi.</p>
  <button class="pri" id="g4google">Continue with Google</button>
  <p style="text-align:center">or use email</p>
  <input id="g4email" type="email" autocomplete="email" placeholder="Email">
  <input id="g4pass" type="password" autocomplete="current-password" placeholder="Password (at least 6 characters)">
  <button class="sec" id="g4in">Sign in</button>
  <button class="sec" id="g4up">Create account</button>
  <button class="sec" id="g4guest" hidden>Play as guest (${GUEST_CASES_PER_DAY} game a day)</button>
  <div class="msg" id="g4msg"></div>
</div>`;
document.body.append(gate);

const bar = document.createElement("div");
bar.id = "g4bar";
bar.innerHTML = `<span id="g4who"></span><button id="g4vocBtn">📚 GE4u words</button><button id="g4out">Sign out</button>`;
document.body.append(bar);

const wall = document.createElement("div");
wall.id = "g4wall";
wall.innerHTML = `<div class="card"><h2>That's all your free games for today</h2>
  <p id="g4wallTxt"></p>
  <a href="${PRODUCTS_URL}" target="_blank" rel="noopener">Unlock Premium (buy a GE4u learning pack)</a>
  <p style="font-size:13px;color:#4b6475">After GE4u confirms your bank transfer, your account becomes Premium. Sign in again to use it.</p>
  <button id="g4wallClose">Back to the hospital tour</button></div>`;
document.body.append(wall);

const voc = document.createElement("div");
voc.id = "g4voc";
voc.innerHTML = `<div class="row"><b>📚 GE4u vocabulary</b><button id="g4vocClose" style="border:0;border-radius:10px;padding:8px 12px;font:inherit">Close</button></div>
  <div class="row"><select id="g4vocSel" aria-label="Word set"></select></div><div id="g4vocList"></div>`;
document.body.append(voc);

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
$("g4out").onclick = async () => { if (auth && user) await signOut(auth); location.reload(); };
$("g4wallClose").onclick = () => { wall.style.display = "none"; };
$("g4vocBtn").onclick = () => { voc.style.display = "flex"; renderVoc(); };
$("g4vocClose").onclick = () => { voc.style.display = "none"; };

function showBar() {
  bar.style.display = "flex";
  $("g4who").textContent = guest ? "Guest" : ((user.email || "Signed in") + (premium ? " · Premium ⭐" : " · Free"));
}

if (auth) onAuthStateChanged(auth, async (u) => {
  user = u;
  if (!u) { gate.style.display = "flex"; bar.style.display = "none"; return; }
  gate.style.display = "none";
  try { await setDoc(doc(db, "users", u.uid), { email: u.email || "", lastSeen: serverTimestamp() }, { merge: true }); } catch (e) {}
  try { const ent = await getDoc(doc(db, "entitlements", u.uid)); premium = ent.exists() && ent.data().premium === true; } catch (e) { premium = false; }
  showBar();
  loadVocab();
});

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
function allowCase() {
  if (premium) return true;
  if (!guest && !user) { gate.style.display = "flex"; return false; }
  const limit = guest ? GUEST_CASES_PER_DAY : FREE_CASES_PER_DAY;
  if (usedToday() >= limit) {
    $("g4wallTxt").textContent = `The free plan includes ${limit} game(s) a day. You can still explore the hospital, or unlock Premium for unlimited play.`;
    wall.style.display = "flex";
    return false;
  }
  countCase();
  return true;
}
for (const name of ["startPatient", "startDoctor", "startProf"]) {
  const orig = window[name];
  if (typeof orig !== "function") continue;
  window[name] = function (...args) {
    if (!allowCase()) {
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
