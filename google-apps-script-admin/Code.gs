/**
 * GE4u PRIVATE ADMIN WEB APP — deploy as a separate Apps Script project.
 * Deployment settings: Execute as "User accessing the web app"; access "Only myself".
 * Never add this file to the public order-intake Apps Script project.
 *
 * Script property required: GE4U_ORDERS_SHEET_ID = private Google Sheet ID.
 * Sheet tabs: Orders, Products, Income, Expenses, AutomationLog.
 * Configure deliveryLink privately in Products; never put private links in public JSON.
 */
const TZ = "Asia/Ho_Chi_Minh";
const TABS = {
  Orders: ["orderId","createdAt","productId","productName","amountVnd","customerName","contact","status","paymentVerifiedAt","paymentVerifiedBy","transactionReference","deliveryStatus","fulfilledAt","deliveryError","adminNote"],
  Products: ["productId","productName","priceVnd","active","version","deliveryLink","deliveryEmailSubject","deliveryEmailBody"],
  Income: ["date","orderId","amountVnd","channel","transactionReference","verified","note"],
  Expenses: ["date","category","vendor","description","amountVnd","recurring","reference"],
  AutomationLog: ["timestamp","event","entityId","status","details"]
};

function doGet() {
  return HtmlService.createHtmlOutputFromFile("Admin")
    .setTitle("GE4u Admin")
    .addMetaTag("viewport", "width=device-width, initial-scale=1");
}

function setupPrivateSheets() {
  const ss = getDb_();
  Object.keys(TABS).forEach(function(name) {
    let sh = ss.getSheetByName(name);
    if (!sh) sh = ss.insertSheet(name);
    if (sh.getLastRow() === 0) sh.getRange(1, 1, 1, TABS[name].length).setValues([TABS[name]]);
    sh.setFrozenRows(1);
  });
  return "Đã kiểm tra/tạo các tab riêng tư. Hãy cấu hình sản phẩm và link giao học liệu trong tab Products.";
}

function getDashboardData() {
  const ss = getDb_();
  const orders = readRows_(ss, "Orders");
  const products = readRows_(ss, "Products");
  const income = readRows_(ss, "Income");
  const expenses = readRows_(ss, "Expenses");
  const paid = orders.filter(o => o.status === "PAID_VERIFIED" || o.status === "FULFILLED");
  const pending = orders.filter(o => ["REQUESTED","CONFIRMED","PAYMENT_PENDING","PAYMENT_REVIEW"].indexOf(o.status) >= 0);
  const fulfilled = orders.filter(o => o.status === "FULFILLED");
  const receipts = income.filter(i => String(i.verified).toLowerCase() === "true" || String(i.verified).toLowerCase() === "yes")
    .reduce((s, i) => s + num_(i.amountVnd), 0);
  const costs = expenses.reduce((s, e) => s + num_(e.amountVnd), 0);
  return {
    summary: {orders: orders.length, pending: pending.length, paid: paid.length, fulfilled: fulfilled.length, verifiedReceiptsVnd: receipts, expensesVnd: costs, netCashFlowVnd: receipts - costs},
    orders: orders.slice(-250).reverse(),
    products: products,
    expenses: expenses.slice(-100).reverse()
  };
}

/** Record manual bank verification, then deliver configured material by email.
 * Customer contact must be an email address; do not send until a delivery link is configured.
 */
function verifyPaymentAndDeliver(orderId, transactionReference) {
  orderId = String(orderId || "").trim();
  transactionReference = String(transactionReference || "").trim().slice(0, 200);
  if (!orderId || !transactionReference) throw new Error("Cần mã đơn và mã tham chiếu giao dịch ngân hàng.");
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = getDb_();
    const sh = ss.getSheetByName("Orders");
    if (!sh) throw new Error("Chưa có tab Orders. Chạy setupPrivateSheets() trước.");
    const data = sh.getDataRange().getValues();
    const headers = data[0].map(String);
    const ix = indexMap_(headers);
    let rowNo = -1, order = null;
    for (let i = 1; i < data.length; i++) {
      if (String(data[i][ix.orderId]) === orderId) { rowNo = i + 1; order = objectFrom_(headers, data[i]); break; }
    }
    if (!order) throw new Error("Không tìm thấy mã đơn.");
    if (order.status === "FULFILLED") throw new Error("Đơn này đã giao học liệu. Không gửi lại tự động.");
    if (order.status === "PAID_VERIFIED" && order.deliveryStatus === "SENDING") throw new Error("Đơn đang xử lý giao học liệu.");
    if (order.status === "CANCELLED" || order.status === "REFUNDED") throw new Error("Không thể giao đơn đã hủy/hoàn tiền.");

    const product = readRows_(ss, "Products").find(p => String(p.productId) === String(order.productId));
    if (!product || !String(product.deliveryLink || "").trim()) {
      throw new Error("Chưa cấu hình deliveryLink trong tab Products. Chưa ghi nhận đã giao.");
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(order.contact || "").trim())) {
      throw new Error("Thông tin liên hệ không phải email. Cần bổ sung email giao học liệu trước khi xác nhận/gửi.");
    }

    const now = new Date();
    setCell_(sh, rowNo, ix.status + 1, "PAID_VERIFIED");
    setCell_(sh, rowNo, ix.paymentVerifiedAt + 1, now);
    setCell_(sh, rowNo, ix.paymentVerifiedBy + 1, Session.getActiveUser().getEmail() || "authorized-admin");
    setCell_(sh, rowNo, ix.transactionReference + 1, transactionReference);
    setCell_(sh, rowNo, ix.deliveryStatus + 1, "SENDING");
    setCell_(sh, rowNo, ix.deliveryError + 1, "");
    log_(ss, "PAYMENT_VERIFIED", orderId, "OK", "Admin nhập tham chiếu giao dịch: " + transactionReference);

    const subject = String(product.deliveryEmailSubject || ("GE4u — Học liệu " + (product.productName || order.productName)));
    const body = String(product.deliveryEmailBody || "Cảm ơn bạn đã mua học liệu GE4u. Link truy cập học liệu của bạn:\n\n" + product.deliveryLink + "\n\nVui lòng không chia sẻ link nếu học liệu có giới hạn sử dụng.");
    MailApp.sendEmail({to: String(order.contact).trim(), subject: subject, body: body, name: "GE4u"});
    setCell_(sh, rowNo, ix.status + 1, "FULFILLED");
    setCell_(sh, rowNo, ix.deliveryStatus + 1, "SENT");
    setCell_(sh, rowNo, ix.fulfilledAt + 1, new Date());
    setCell_(sh, rowNo, ix.deliveryError + 1, "");
    if (ss.getSheetByName("Income")) {
      const inc = ss.getSheetByName("Income");
      inc.appendRow([now, orderId, num_(order.amountVnd || product.priceVnd), "Bank transfer", transactionReference, true, "Auto-recorded after manual verification"]);
    }
    log_(ss, "DELIVERY_SENT", orderId, "OK", "Email sent to customer.");
    return {ok:true, message:"Đã xác nhận thanh toán và gửi email học liệu.", orderId:orderId};
  } catch (err) {
    try { log_(getDb_(), "PAYMENT_OR_DELIVERY_ERROR", orderId, "ERROR", String(err.message || err)); } catch (_) {}
    throw err;
  } finally {
    lock.releaseLock();
  }
}

function updateOrderStatus(orderId, status, note) {
  const allowed = ["CONFIRMED","PAYMENT_PENDING","PAYMENT_REVIEW","CANCELLED"];
  if (allowed.indexOf(status) < 0) throw new Error("Trạng thái không hợp lệ.");
  const ss = getDb_(), sh = ss.getSheetByName("Orders");
  const data = sh.getDataRange().getValues(), headers = data[0].map(String), ix = indexMap_(headers);
  for (let i=1; i<data.length; i++) {
    if (String(data[i][ix.orderId]) === String(orderId)) {
      if (["PAID_VERIFIED","FULFILLED","REFUNDED"].indexOf(String(data[i][ix.status])) >= 0) throw new Error("Đơn đã thanh toán/giao/hoàn tiền; không thể đổi trạng thái bằng thao tác này.");
      setCell_(sh, i+1, ix.status+1, status);
      setCell_(sh, i+1, ix.adminNote+1, String(note || "").slice(0,1000));
      log_(ss, "ORDER_STATUS", orderId, status, String(note || ""));
      return {ok:true};
    }
  }
  throw new Error("Không tìm thấy mã đơn.");
}

function addExpense(entry) {
  entry = entry || {};
  const amount = num_(entry.amountVnd);
  if (!(amount > 0) || !entry.date || !entry.category) throw new Error("Cần ngày, danh mục và số tiền chi hợp lệ.");
  getDb_().getSheetByName("Expenses").appendRow([entry.date, String(entry.category).slice(0,100), String(entry.vendor||"").slice(0,150), String(entry.description||"").slice(0,500), amount, Boolean(entry.recurring), String(entry.reference||"").slice(0,200)]);
  log_(getDb_(), "EXPENSE_ADDED", "", "OK", entry.category + ": " + amount);
  return {ok:true};
}

function getDb_() {
  const id = PropertiesService.getScriptProperties().getProperty("GE4U_ORDERS_SHEET_ID");
  if (!id) throw new Error("Thiếu Script Property GE4U_ORDERS_SHEET_ID. Hãy đặt ID của Google Sheet riêng tư.");
  return SpreadsheetApp.openById(id);
}
function readRows_(ss, name) {
  const sh = ss.getSheetByName(name);
  if (!sh || sh.getLastRow() < 2) return [];
  const values = sh.getDataRange().getValues(), headers = values.shift().map(String);
  return values.filter(r => r.some(v => v !== "")).map(r => objectFrom_(headers, r));
}
function objectFrom_(headers, row) {
  const o = {};
  headers.forEach((h,i) => o[h] = row[i] instanceof Date ? Utilities.formatDate(row[i], TZ, "yyyy-MM-dd HH:mm:ss") : row[i]);
  return o;
}
function indexMap_(headers) { const o={}; headers.forEach((h,i)=>o[h]=i); return o; }
function setCell_(sh, row, col, value) { const h = sh.getRange(1,col).getValue(); const headers = sh.getRange(1,1,1,sh.getLastColumn()).getValues()[0].map(String); if (headers.indexOf(String(h)) < 0) throw new Error("Cột không hợp lệ."); sh.getRange(row,col).setValue(value); }
function num_(v) { const n = Number(String(v == null ? 0 : v).replace(/[^0-9.-]/g,"")); return isFinite(n) ? n : 0; }
function log_(ss, event, entityId, status, details) {
  const sh = ss.getSheetByName("AutomationLog");
  if (sh) sh.appendRow([new Date(), event, entityId, status, String(details || "").slice(0,1000)]);
}
