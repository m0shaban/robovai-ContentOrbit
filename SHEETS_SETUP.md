# 📊 Google Sheets Control Room Setup

ContentOrbit now supports a "Control Room" mode where you can manage feeds, configuration, and logs directly from a Google Sheet.

## 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select existing).
3. Enable **Google Sheets API** and **Google Drive API**.
4. Go to **IAM & Admin > Service Accounts**.
5. Create a Service Account.
6. Create a JSON Key for this account.
7. Save the key file as `service_account.json` in the `data/` folder of your bot:
   - `data/service_account.json`

## 2. Create the Control Room Sheet

1. Create a new Google Sheet named **"ContentOrbit Control Room"**.
2. Create 3 tabs (sheets) at the bottom:
   - **Configuration**
   - **Feeds**
   - **Logs**

## 3. Import Templates

We have provided CSV templates in the `data/` folder to get you started.

1. **Import `data/google_sheet_template_config.csv`** into the **Configuration** tab.
   - *File > Import > Upload > Select file > Replace current sheet*
2. **Import `data/google_sheet_template_feeds.csv`** into the **Feeds** tab.
   - *This contains 200+ curated tech sources!*
3. **Import `data/google_sheet_template_logs.csv`** into the **Logs** tab.

## 4. Connect the Bot

1. Open your `service_account.json` file and copy the `client_email` address (e.g., `content-bot@project-123.iam.gserviceaccount.com`).
2. Go to your Google Sheet > **Share** button.
3. Paste the email address and give it **Editor** access.
4. Ensure your `data/config.json` has the correct sheet name:
   ```json
   "google_sheet_name": "ContentOrbit Control Room"
   ```

## 5. Verify

Run the bot in test mode:
```bash
python unified_bot.py --test-mode
```
You should see output indicating it successfully connected to the Google Sheet.

## 🔄 Dynamic Updates

- **Feeds**: Add/Remove rows in the **Feeds** tab. The bot reloads this every cycle.
- **Config**: Change `prompts`, `cta_url`, etc., in the **Configuration** tab.
- **Logs**: Watch the **Logs** tab populate with live publishing data!
