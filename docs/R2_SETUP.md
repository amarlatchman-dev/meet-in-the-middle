# Cloudflare R2 setup for map tiles

The "Build road maps" GitHub Action builds road and place tiles for every region in
`tools/regions.json` and uploads them to a Cloudflare R2 bucket. The app reads them
from the bucket's public URL. R2's free tier includes 10 GB of storage and has no
download (egress) fees, so the expected cost is about $0.

## 1. Create the bucket (Cloudflare dashboard)

1. Sign in at https://dash.cloudflare.com, then open **R2 Object Storage** in the sidebar.
   Cloudflare asks for a payment method to turn on R2, even on the free tier.
2. Click **Create bucket**. Name it `meet-in-the-middle-tiles`, leave the location on Automatic, and click **Create bucket**.

## 2. Make it publicly readable

1. Open the bucket, go to **Settings**, then **Public access**.
2. Under **R2.dev subdomain**, click **Allow access** and confirm.
3. Copy the **Public R2.dev Bucket URL**. It looks like `https://pub-xxxxxxxx.r2.dev`.
   (You can connect your own domain here later. Cloudflare recommends that for heavy traffic.)

## 3. Allow the website to read it (CORS)

In the bucket's **Settings**, find **CORS Policy**, click **Add CORS policy** (or **Edit**), and paste:

```json
[
  {
    "AllowedOrigins": ["https://amarlatchman-dev.github.io"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }
]
```

## 4. Create an upload key for GitHub

1. Go back to **R2 Object Storage** (the overview page). On the right, note your **Account ID**.
2. Click **Manage API tokens**, then **Create API token** (an "Account API token" is fine).
3. Permissions: **Object Read & Write**. Under specific buckets, choose `meet-in-the-middle-tiles` only.
4. Click **Create**, then copy the **Access Key ID** and **Secret Access Key**. The secret is shown only once.

## 5. Add the secrets to GitHub

In the repo, go to **Settings**, then **Secrets and variables**, then **Actions**, and click **New repository secret**.
Add these four:

| Name | Value |
|---|---|
| `R2_ACCOUNT_ID` | Account ID from step 4 |
| `R2_ACCESS_KEY_ID` | Access Key ID from step 4 |
| `R2_SECRET_ACCESS_KEY` | Secret Access Key from step 4 |
| `R2_BUCKET` | `meet-in-the-middle-tiles` |

## 6. Run the build and point the app at R2

1. Go to **Actions**, then **Build road maps**, then **Run workflow**. All regions build in parallel, then upload to R2.
2. Set `TILE_BASE` near the top of the map code in `index.html` to your public URL with a trailing slash:
   `const TILE_BASE = "https://pub-xxxxxxxx.r2.dev/";`
3. Once it works, the old `data/` folder in the repo can be deleted.

To add a region, add it to `tools/regions.json` (the `path` matches Geofabrik's folder names) and run the build.
