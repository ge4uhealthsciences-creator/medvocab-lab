# GE4u Admin Dashboard — Requirements

## Security
This document is a specification, not a live dashboard. Do not store financial/customer data in the public GitHub Pages repository. The public website must never expose admin credentials, access tokens, private customer details, or transaction records.

## Dashboard modules
1. Overview: verified receipts, pending orders, pending payment confirmations, fulfilled orders, refunds, expenses, net cash flow, and best-selling products.
2. Order confirmation: view order ID, product/discipline, requested contact, submission time, and current status; confirm/reject/cancel a request; record admin note.
3. Payment confirmation: mark payment as pending, verified, under review, rejected/unmatched, refunded. Mark PAID_VERIFIED only after checking the actual receiving account statement or transaction record. A submitted form, email, screenshot, or customer assertion is not sufficient proof by itself.
4. Delivery confirmation: record the product/version delivered, delivery time, method, and status. Never mark fulfilled until delivery is completed.
5. Products: manage 12 disciplines, product titles, price, active/draft status, version, included assets, sample/practice URLs.
6. Income: date, order ID, amount received, payment channel, transaction reference, verification status.
7. Expenses: date, category, vendor, description, amount, recurring flag, receipt/reference.
8. Automation log: content generation, deployment status, social publishing status, last successful run and errors.
9. Reports: sales by discipline, monthly revenue and expenses, refunds, conversion rate, pending orders and fulfilment backlog.

## Canonical order lifecycle
- REQUESTED: form submitted; not yet reviewed.
- CONFIRMED: request reviewed and accepted by the seller; not a payment confirmation.
- PAYMENT_PENDING: payment instructions sent; no receipt verified.
- PAID_VERIFIED: payment verified against the actual receiving account.
- FULFILLED: correct product delivered and delivery recorded.
- CANCELLED: request/order cancelled.
- PAYMENT_REVIEW: transaction needs manual investigation.
- REFUNDED: refund actually issued.

Keep order confirmation, payment confirmation, and delivery confirmation as three separate actions and timestamps.

## Finance rules
- Dashboard revenue = verified receipts, not order requests or advertised prices.
- Expenses require amount, date, category, and evidence/reference where available.
- Net cash flow = verified receipts - recorded cash expenses - actual refunds.
- Show gross order value, received cash, refunds, expenses, and net cash flow separately.
- Never store bank login credentials, card data, passwords, or OTPs.

## Product model
Use `data/ge4u-product-catalog.json` as the public catalogue. A private admin backend should own commercial price, sale status, delivery assets, and internal notes. Do not place private delivery links or unreleased product files in public JSON.

## Recommended architecture
- Public website: GitHub Pages, public catalogue and sample lessons only.
- Order intake: current Google Apps Script endpoint, extended to write a minimal order record to a private Google Sheet.
- Private data store: Google Sheet owned by the brand operator, access restricted to authorized accounts.
- Admin UI: separate Apps Script web app restricted to the owner's authorized Google account. Never expose the admin route through the public `Anyone` order endpoint.
- Audit trail: log status changes, timestamp, and administrator identity where available.
- Automation: order notification; reminders for unconfirmed requests and unpaid orders; weekly summary of verified receipts, expenses and net cash flow.
- Recovery: enable 2-step verification; never share credentials or OTPs in code or chat.

## Private sheet tabs
Products, Orders, Income, Expenses, AutomationLog. Restrict access and do not link the sheet publicly.

## Activation prerequisites
1. Create a private Google Sheet.
2. Set its ID in Apps Script Script Properties; never commit it to the public repository.
3. Configure the authorized admin email and deploy a separate restricted admin web app.
4. Keep public order intake separate; test with dummy orders.
5. Verify unauthorized accounts cannot read admin data or change records.
6. Test order confirmation, payment verification, cancellation/refund and delivery states before any automation.

## Current implementation status
- Public catalogue for 12 disciplines: exists.
- Order-request form and email notification: exists; a form submission is not proof of payment.
- Private financial database: not configured.
- Authenticated admin dashboard: not implemented.
- Order/payment/delivery confirmation workflow: not implemented.
- Verified payment reconciliation and automated delivery: not implemented.
