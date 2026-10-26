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
  const website = String(p.website || "").trim(); // honeypot field
  if (website) return output_("Yêu cầu không hợp lệ.");
  if (!name || !contact || !consent || !product) return output_("Vui lòng nhập tên, thông tin liên hệ và đồng ý xử lý thông tin để gửi yêu cầu.");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact) && contact.length < 8) {
    return output_("Vui lòng kiểm tra thông tin liên hệ.");
  }

  const now = new Date();
  const orderId = "GE4U-" + Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "yyMMdd-HHmmss") + "-" + Utilities.getUuid().slice(0, 6).toUpperCase();
  const subject = "[GE4u] Yêu cầu mua mới " + orderId;
  const body = [
    "Có khách hàng vừa gửi yêu cầu mua sản phẩm GE4u.",
    "",
    "Mã yêu cầu: " + orderId,
    "Ngành: " + product.vi,
    "Sản phẩm: " + product.name,
    "Giá tham khảo: " + PRODUCT_PRICE_VND.toLocaleString("vi-VN") + " VND",
    "Tên khách: " + name,
    "Thông tin liên hệ khách cung cấp: " + contact,
    "Thời điểm: " + Utilities.formatDate(new Date(), "Asia/Ho_Chi_Minh", "dd/MM/yyyy HH:mm:ss"),
    "",
    "Đây chỉ là yêu cầu đặt mua, KHÔNG phải xác nhận thanh toán.",
    "Hãy kiểm tra tài khoản ngân hàng trực tiếp trước khi giao tài liệu.",
    "Chỉ phản hồi khách qua kênh liên hệ do khách cung cấp."
  ].join("\n");

  // Persist minimal order data to the private Sheet if configured. Never expose Sheet contents.
  let savedToSheet = false;
  try {
    savedToSheet = appendOrderToPrivateSheet_({
      orderId: orderId,
      createdAt: now,
      productId: productId,
      productName: product.name,
      amountVnd: PRODUCT_PRICE_VND,
      customerName: name,
      contact: contact,
      status: "REQUESTED",
      paymentVerifiedAt: "",
      paymentVerifiedBy: "",
      transactionReference: "",
      deliveryStatus: "NOT_SENT",
      fulfilledAt: "",
      deliveryError: "",
      adminNote: ""
    });
  } catch (err) {
    // Do not silently pretend the order was saved. Include the persistence error in the alert.
    body += "\\n\\nCẢNH BÁO: Không lưu được vào Orders sheet: " + String(err.message || err);
  }
  body += savedToSheet
    ? "\\n\\nĐã ghi vào private Orders sheet."
    : "\\n\\nCẢNH BÁO: Chưa ghi vào private Orders sheet; cần cấu hình GE4U_ORDERS_SHEET_ID.";
  MailApp.sendEmail({to: NOTIFICATION_EMAIL, subject: subject, body: body, name: "GE4u Order Notice"});
  return HtmlService.createHtmlOutput(
    '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<body style="font:16px/1.6 system-ui,sans-serif;max-width:650px;margin:48px auto;padding:20px;color:#173047">' +
    '<h1>Đã gửi yêu cầu đặt mua</h1><p>Mã yêu cầu: <strong>' + orderId + '</strong></p>' +
    '<p>Yêu cầu đã được gửi. Đây chưa phải xác nhận thanh toán hoặc đơn hàng đã thanh toán.</p>' +
    '<p>Bạn hãy làm theo hướng dẫn thanh toán trên trang GE4u và lưu lại mã yêu cầu.</p></body></html>'
  ).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doGet() {
  return ContentService.createTextOutput("GE4u order endpoint is running. Submit orders using the website form.");
}

function output_(message) {
  return HtmlService.createHtmlOutput('<meta charset="utf-8"><p style="font:16px system-ui,sans-serif;padding:24px">' + escapeHtml_(message) + '</p>');
}
function escapeHtml_(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
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
