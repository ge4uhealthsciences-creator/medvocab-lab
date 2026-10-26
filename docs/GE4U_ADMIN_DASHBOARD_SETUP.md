# GE4u Admin Dashboard — Setup Guide

This is a source-code scaffold, not a live deployment. It is deliberately separate from the public order endpoint.

## Architecture

- Public site: GitHub Pages; public product/sample information only.
- Public order intake: existing Apps Script project in `google-apps-script/Code.gs`.
- Private data: a Google Sheet owned by the operator.
- Private dashboard: a separate Apps Script project using `google-apps-script-admin/Code.gs` and `google-apps-script-admin/Admin.html`.

**Never publish the private dashboard URL as a public navigation link. Never deploy the admin app with access set to “Anyone”.**

## 1. Create a private spreadsheet

1. Sign in to the Google account that should own GE4u operations.
2. Create a new Google Sheet named `GE4u Private Operations`.
3. Keep General access set to **Restricted**. Do not share it publicly.
4. Copy the spreadsheet ID from its URL (the value between `/d/` and `/edit`). Do not commit or send the ID publicly.

## 2. Create the private Apps Script project

1. Open `https://script.google.com/` while signed in to the intended admin Google account.
2. Create a **new standalone project** named `GE4u Private Admin`.
3. Copy `google-apps-script-admin/Code.gs` into its `Code.gs` file.
4. Add an HTML file named exactly `Admin` and copy `google-apps-script-admin/Admin.html` into it.
5. In **Project Settings → Script properties**, add:
   - Property: `GE4U_ORDERS_SHEET_ID`
   - Value: the private spreadsheet ID from step 1.
6. In the editor, select and run `setupPrivateSheets` once. Review and grant the requested Google permissions.

## 3. Configure products and delivery

In the private Sheet's `Products` tab, add one row per product with these columns:

`productId | productName | priceVnd | active | version | deliveryLink | deliveryEmailSubject | deliveryEmailBody`

Use the product IDs from `data/ge4u-product-catalog.json` (e.g. `dentistry`, `medical`, `pharmacy`, `nursing`, `midwifery`, `social-work`, `pharmaceutical-chemistry`, `pharmaceutical-technology`, `traditional-medicine`, `public-health`, `psychology`, `nutrition`).

- Do not enter a delivery link until the product is ready and access has been tested.
- Do not use links to private Drive files unless the buyer's access is configured to work. Anyone-with-link delivery links can be forwarded; consider that trade-off before using them.
- The current checkout form accepts one contact field. The automatic delivery function requires that field to be a valid email address. A phone number alone is not enough; collect a delivery email before using automated delivery.
- Product prices are provisional until you set and confirm the actual price. The existing intake script currently uses a pilot amount of 99,000 VND.

## 4. Deploy the dashboard privately

1. In the private Apps Script project choose **Deploy → New deployment → Web app**.
2. Execute as: **User accessing the web app**.
3. Who has access: **Only myself** (or the narrowest supported authorized-account option for your use case).
4. Deploy and open the URL while signed in to the authorized Google account.
5. Do not embed this URL in the public GitHub Pages site.

## 5. Connect public orders to the private Sheet

The current public intake endpoint sends an email notification but does **not yet persist orders in the private Sheet**. The dashboard will remain empty until the intake script is extended and redeployed to append order rows. The public intake script must only append a validated order and send an alert; it must never return sheet data or expose admin functions. Store the private sheet ID in that public script's Script Properties, not in source code.

Do not accept real orders as fully automated until this integration is deployed and tested.

## 6. Safe test checklist

Use dummy data and a test email first:

- Submit an order and confirm one row appears in Orders with status `REQUESTED`.
- Verify an unrelated Google account cannot open the admin web app.
- Verify the admin sees only expected order fields.
- Enter a test transaction reference and confirm the warning dialog appears.
- Confirm no order can be delivered without a configured delivery link.
- Confirm an order is not marked `FULFILLED` if email sending fails.
- Confirm a second click does not automatically resend an already fulfilled order.
- Confirm the Income row is created once and the amount matches the verified bank receipt.
- Confirm cancelled/refunded orders cannot be delivered.
- Test that customer contact is a valid email before delivery.

## Important implementation note

This is an initial implementation scaffold and has not been deployed to the user's Google account or tested against a real private Sheet. Manual payment verification remains the operator's responsibility. If email delivery fails, inspect the order's status and error log before any retry; do not blindly click the confirmation button again.
