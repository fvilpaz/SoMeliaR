<div align="right">
  <img src="https://img.shields.io/badge/EN-1a6fc4?style=flat-square" alt="English">
  &nbsp;<a href="MANUAL.es.md"><img src="https://img.shields.io/badge/ES-555555?style=flat-square" alt="Español"></a>
</div>

# User Manual — SoMeliaR 🍷

Complete guide for sommeliers and cellar managers.

---

## Table of contents

1. [Access and user profile](#1-access-and-user-profile)
2. [Dashboard](#2-dashboard)
3. [Cellar — wine catalogue](#3-cellar--wine-catalogue)
4. [Stock movements](#4-stock-movements)
5. [Quick movement](#5-quick-movement)
6. [Suppliers](#6-suppliers)
7. [Orders](#7-orders)
8. [Order history](#8-order-history)
9. [Analyse Stock with AI](#9-analyse-stock-with-ai)
10. [Sommelier notes](#10-sommelier-notes)
11. [Tools (administrator only)](#11-tools-administrator-only)

---

## 1. Access and user profile

### Log in
Access the app with your username and password on the login screen.

### Your profile
Click your name or avatar at the bottom of the side menu to access your profile. From there you can:

- **Change your first and last name** — they will appear in the greeting and in the orders you send.
- **Change your email** — this is the address shown as the sender on orders.
- **Upload a profile picture** — it appears as your avatar in the side menu. If there is no photo, your initials are shown instead.

---

## 2. Dashboard

Home screen with a summary of the current state of the cellar:

- **Summary by family** — number of references and total stock grouped by wine type (domestic reds, whites, sparkling, etc.).
- **Minimum stock alerts** — list of wines whose current stock is below the configured minimum. These are the candidates for ordering.
- **Pending orders** — quick access to orders in draft or pending status.
- **Inventory value** — total stock value at cost price.
- **Stock chart** — visual distribution by family.

---

## 3. Cellar — wine catalogue

### View the catalogue
From the side menu, go to **Cellar**. You can view the wines in two modes:
- **Grid view** — cards with photo, stock and price.
- **List view** — compact table, useful on small screens.

### Filter and search
- Use the family buttons (Domestic Red, White, Sparkling...) to filter.
- Type in the search bar to filter by name, winery or denomination of origin.
- Sort by name, family or stock using the dropdown.

### Wine detail page
Click on the name or the ✦ icon on a card to view the full detail page. It contains:
- All the wine's data (winery, D.O., grape varieties, prices, locations where it is served).
- History of the most recent stock movements.
- AI-generated description section (see section 9).
- Form to upload the bottle photo manually.

### Add a new wine
Click the **New wine** button (top right). Fill in the data and save.

### Edit a wine
Click the pencil icon on the card or on the detail page. You can modify all the data, including the photo.

### Upload a wine photo
From the wine's detail page, in the image section, upload the photo of the bottle or label. The image is saved in the cloud and is visible to all users.

---

## 4. Stock movements

Every bottle entry or exit is recorded as a movement. The current stock is the sum of all movements.

### Record a movement
From a wine card, click **+ Movement**. Specify:
- **Type**: entry (purchase, return) or exit (consumption, breakage, shrinkage).
- **Quantity**: number of bottles.
- **Notes**: optional, to record the reason.

### Minimum stock
Each wine can have a minimum stock configured. When the current stock falls below it, an alert appears on the dashboard and the card is highlighted in red.

---

## 5. Quick movement

Accessible from the side menu. Allows you to record multiple stock movements quickly without having to open each wine's detail page. Ideal for end-of-day closing or for quick adjustments after a service.

---

## 6. Suppliers

### View suppliers
From the side menu, go to **Suppliers**. You will see the list of distributors with their contact email.

### Add or edit a supplier
From the list, click **New supplier** or the edit pencil.

### Wines linked to a supplier
On each supplier's detail page you can see which wines they supply and at what price.

---

## 7. Orders

An order goes through four statuses: **Draft → Pending → Sent → Received**.

### Create an order
1. Go to **Orders → New order**.
2. Choose the supplier.
3. Add order lines: select each wine and the quantity to order.
4. The order is saved in **Draft** status.

### Review and confirm
From the order page, you can edit the lines, add or remove wines. When it is ready, change it to **Pending** status.

### Send the order by email
When the order is in Pending status, the **Send order** button appears. When you click it:
1. The application automatically generates the email text with the details of the wines and quantities.
2. You can review and edit the text before sending.
3. You confirm the send and the email is sent to the supplier.
4. The order moves to **Sent** status.

> The email is sent from the email address configured in your user profile. You can always review the draft before sending — it is never sent without your confirmation.

### Record the receipt
When the goods arrive, go to the order and click **Mark as received**. The system automatically records stock entries for each wine in the order.

---

## 8. Order history

Accessible from **History** in the side menu. Shows all completed orders (Received status) organised by date. You can expand each order to view its details.

---

## 9. Analyse Stock with AI

From the side menu, **Analyse Stock (AI)**. The application uses artificial intelligence (Google Gemini) to:

- Analyse the current stock of all wines.
- Detect which references are close to the minimum or out of stock.
- Suggest what to order and in what quantities, taking into account the consumption history.
- Generate an automatic draft order that you can review and adjust before sending.

### Wine description with AI
On each wine's detail page, the **Generate description** button automatically creates a tasting description in Spanish for that wine. The description is saved and does not need to be regenerated every time (although you can force a new one if you want to update it).

---

## 10. Sommelier notes

Accessible from **Notes** in the side menu. A space to leave quick notes: incidents, reminders, observations about a service.

- **New note**: write the text and choose the priority (normal, high).
- **Voice dictation**: click the microphone icon to dictate the note by voice (requires browser permission).
- **Resolve**: mark a note as resolved to archive it.
- **Delete**: delete a note that is no longer needed.

---

## 11. Tools (administrator only)

This section is only visible to users with the administrator role (superuser).

### Import from Excel
Upload the **Cellar Book** in `.xls` or `.xlsx` format. The system automatically imports:
- All wines with their data (name, winery, D.O., prices, etc.).
- Suppliers and their relationship with the wines.
- Initial stock for each reference.

> If there is already data in the system, the import adds on top of it. If you want to start from scratch, use the **Clear database** option first.

### Sidebar logo
Upload a square image (minimum 200×200 px) that will appear in the side menu in place of the default logo. Recommended: the hotel logo or the F&B department logo.

### Login image
Upload the photo that appears as the circular logo on the login screen.

### Clear database
Deletes **all wines, movements, suppliers, orders and notes**. Users are not deleted. Use this only if you are going to re-import a completely new Excel file.

> This action cannot be undone. The system will ask for confirmation before executing it.

---

## Frequently asked questions

**Can I use the app from my phone?**
Yes. The design is fully responsive. On mobile, the side menu opens with the hamburger button (☰) in the top-left corner.

**Are the wine photos lost if the system is updated?**
No. The images are stored on Cloudinary, an external service. They do not depend on the server and persist at all times.

**Who receives the order email?**
The order email is sent to the supplier's address configured in their profile. The sender is the user who performs the send.

**What happens if the AI analysis is unavailable?**
If there is no connection or the Gemini API does not respond, the system will display an error message and you will be able to manage the order manually.

**How do I configure the minimum stock for a wine?**
From the wine's detail page, in the editing section, you will find the **Minimum stock** field. When the stock falls below that value, an alert will appear on the dashboard.

---

*Manual created for SoMeliaR — Meliá Hotels International.*  
*Developed by Fernando Vilas Paz.*
