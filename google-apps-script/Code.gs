/**
 * GE4u order notification endpoint.
 * Deploy as a Google Apps Script Web App:
 * Execute as: Me
 * Who has access: Anyone
 * Then paste the deployed /exec URL into ge4u-dental-english.html.
 *
 * Sends an order notification and, when GE4U_ORDERS_SHEET_ID is configured in Script Properties,
 * appends the order to the private Orders tab. It never verifies bank transfers or confirms payment.
 */
const NOTIFICATION_EMAIL = "ge4u.health.sciences@gmail.com";
const PRODUCT_PRICE_VND = 99000;
const PRODUCTS = {
  dentistry: {name: "Dental English Learning Pack", vi: "Răng Hàm Mặt"},
  medical: {name: "Medical English Learning Pack", vi: "Y khoa"},
  pharmacy: {name: "Pharmacy English Learning Pack", vi: "Dược học"},
  nursing: {name: "Nursing English Learning Pack", vi: "Điều dưỡng"},
  midwifery: {name: "Midwifery English Learning Pack", vi: "Hộ sinh"},
  "social-work": {name: "Healthcare Social Work English Learning Pack", vi: "Công tác xã hội"},
  "pharmaceutical-chemistry": {name: "Pharmaceutical Chemistry English Learning Pack", vi: "Hóa dược"},
  "pharmaceutical-technology": {name: "Pharmaceutical Technology English Learning Pack", vi: "Công nghệ dược phẩm"},
  "traditional-medicine": {name: "Traditional Medicine English Learning Pack", vi: "Y học cổ truyền"},
  "public-health": {name: "Public Health English Learning Pack", vi: "Y tế công cộng"},
  psychology: {name: "Psychology English Learning Pack", vi: "Tâm lý học"},
  nutrition: {name: "Nutrition English Learning Pack", vi: "Dinh dưỡng"}
};

function doPost(e) {
  const p = (e && e.parameter) || {};
  const name = String(p.name || "").trim().slice(0, 100);
  const contact = String(p.contact || "").trim().slice(0, 200);
  const consent = String(p.consent || "") === "yes";
  const productId = String(p.product || "").trim();
  const product = PRODUCTS[productId];
  const website = String(p.website || "").trim();

  // Record even rejected requests when the shared sheet is configured.
  if (website) {
    auditOrderEvent_("ORDER_REJECTED", "", "Honeypot field was populated.");
    return output_("Yêu cầu không hợp lệ.");
  }
  if (!name || !contact || !consent || !product) {
    auditOrderEvent_("ORDER_REJECTED", "", "Missing name/contact/consent or invalid product. productId=" + productId);
    return output_("Chưa gửi được yêu cầu. Vui lòng kiểm tra tên, thông tin liên hệ, sản phẩm và ô đồng ý xử lý thông tin.");
  }
  const looksLikeEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact);
  const looksLikePhone = /^\+?[\d\s().-]{8,20}$/.test(contact);
  if (!looksLikeEmail && !looksLikePhone) {
    auditOrderEvent_("ORDER_REJECTED", "", "Invalid contact format.");
    return output_("Vui lòng kiểm tra thông tin liên hệ.");
  }

  const now = new Date();
  const orderId = "GE4U-" + Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "yyMMdd-HHmmss") + "-" + Utilities.getUuid().slice(0, 6).toUpperCase();
  const order = {
    orderId: orderId, createdAt: now, productId: productId, productName: product.name,
    amountVnd: PRODUCT_PRICE_VND, customerName: name, contact: contact, status: "REQUESTED",
    paymentVerifiedAt: "", paymentVerifiedBy: "", transactionReference: "",
    deliveryStatus: "NOT_SENT", fulfilledAt: "", deliveryError: "", adminNote: ""
  };

  // Fail visibly if the order cannot be persisted. Never show a success confirmation for an unsaved order.
  try {
    const saved = appendOrderToPrivateSheet_(order);
    if (!saved) throw new Error("GE4U_ORDERS_SHEET_ID is missing in Order Intake Script Properties.");
    auditOrderEvent_("ORDER_SAVED", orderId, "Order row appended to Orders.");
  } catch (err) {
    auditOrderEvent_("ORDER_SAVE_FAILED", orderId, String(err.message || err));
    return output_("Chưa ghi nhận được đơn hàng do lỗi kết nối Google Sheet. Vui lòng chưa thanh toán. Mã tham chiếu: " + orderId + ". Người quản trị cần kiểm tra Script Properties và tab Orders.");
  }

  const subject = "[GE4u] Yêu cầu mua mới " + orderId;
  const body = [
    "Có khách hàng vừa gửi yêu cầu mua sản phẩm GE4u.", "",
    "Mã yêu cầu: " + orderId,
    "Ngành: " + product.vi,
    "Sản phẩm: " + product.name,
    "Giá tham khảo: " + PRODUCT_PRICE_VND.toLocaleString("vi-VN") + " VND",
    "Tên khách: " + name,
    "Thông tin liên hệ khách cung cấp: " + contact,
    "Thời điểm: " + Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "dd/MM/yyyy HH:mm:ss"),
    "", "Đây chỉ là yêu cầu đặt mua, KHÔNG phải xác nhận thanh toán.",
    "Hãy kiểm tra tài khoản ngân hàng trực tiếp trước khi giao tài liệu."
  ].join("\n");

  try {
    MailApp.sendEmail({to: NOTIFICATION_EMAIL, subject: subject, body: body, name: "GE4u Order Notice"});
    auditOrderEvent_("ORDER_EMAIL_SENT", orderId, "MailApp accepted notification for " + NOTIFICATION_EMAIL);
  } catch (err) {
    auditOrderEvent_("ORDER_EMAIL_FAILED", orderId, String(err.message || err));
    return output_("Đã lưu yêu cầu " + orderId + " vào hệ thống nhưng chưa gửi được email thông báo. Người quản trị cần kiểm tra quyền gửi thư và Executions.");
  }

  return HtmlService.createHtmlOutput(
    '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<body style="font:16px/1.6 system-ui,sans-serif;max-width:650px;margin:48px auto;padding:20px;color:#173047">' +
    '<h1>Đã ghi nhận yêu cầu đặt mua</h1><p>Mã yêu cầu: <strong>' + escapeHtml_(orderId) + '</strong></p>' +
    '<p>Yêu cầu đã được lưu vào hệ thống. Đây chưa phải xác nhận thanh toán.</p>' +
    '<p>Vui lòng lưu mã yêu cầu để đối chiếu khi liên hệ.</p></body></html>'
  ).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doGet() {
  const sheetConfigured = Boolean(PropertiesService.getScriptProperties().getProperty("GE4U_ORDERS_SHEET_ID"));
  return ContentService.createTextOutput(
    "GE4u Order Intake diagnostic\n" +
    "Notification recipient configured in this deployed code: " + NOTIFICATION_EMAIL + "\n" +
    "GE4U_ORDERS_SHEET_ID configured: " + (sheetConfigured ? "YES" : "NO") + "\\n" +
    "This diagnostic does not create an order. Submit the website form to test POST."
  ).setMimeType(ContentService.MimeType.TEXT);
}

function output_(message) {
  return HtmlService.createHtmlOutput('<meta charset="utf-8"><p style="font:16px system-ui,sans-serif;padding:24px">' + escapeHtml_(message) + '</p>');
}
function escapeHtml_(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}


function auditOrderEvent_(eventName, orderId, details) {
  try {
    const sheetId = PropertiesService.getScriptProperties().getProperty("GE4U_ORDERS_SHEET_ID");
    if (!sheetId) return;
    const ss = SpreadsheetApp.openById(sheetId);
    let sh = ss.getSheetByName("AutomationLog");
    if (!sh) {
      sh = ss.insertSheet("AutomationLog");
      sh.appendRow(["timestamp","event","entityId","status","details"]);
    } else if (sh.getLastRow() === 0) {
      sh.appendRow(["timestamp","event","entityId","status","details"]);
    }
    sh.appendRow([new Date(), eventName, orderId || "", eventName.indexOf("FAILED") >= 0 || eventName === "ORDER_REJECTED" ? "ERROR" : "OK", String(details || "").slice(0, 1000)]);
  } catch (err) {
    console.error("Order audit logging failed: " + String(err.message || err));
  }
}

function appendOrderToPrivateSheet_(order) {
  const sheetId = PropertiesService.getScriptProperties().getProperty("GE4U_ORDERS_SHEET_ID");
  if (!sheetId) return false;
  const ss = SpreadsheetApp.openById(sheetId);
  let sh = ss.getSheetByName("Orders");
  if (!sh) throw new Error("Không tìm thấy tab Orders. Hãy chạy setupPrivateSheets trong dự án admin.");
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
  const required = ["orderId","createdAt","productId","productName","amountVnd","customerName","contact","status","paymentVerifiedAt","paymentVerifiedBy","transactionReference","deliveryStatus","fulfilledAt","deliveryError","adminNote"];
  required.forEach(function(h) { if (headers.indexOf(h) < 0) throw new Error("Thiếu cột " + h + " trong Orders."); });
  const row = headers.map(function(h) { return Object.prototype.hasOwnProperty.call(order, h) ? order[h] : ""; });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try { sh.appendRow(row); } finally { lock.releaseLock(); }
  return true;
}
