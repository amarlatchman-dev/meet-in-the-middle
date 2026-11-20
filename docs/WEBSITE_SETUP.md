# Website setup: domain, HTTPS and tiles

Cost: about $10–15 a year for a .com domain. Everything else is free: GitHub Pages hosts the site and Cloudflare R2 hosts the map tiles.

Buying the domain from **Cloudflare Registrar** is simplest. It sells at cost with no markup, and the domain, DNS and R2 tiles all live in one Cloudflare account.

## 1. Pick and buy the domain (about 10 minutes)

1. Sign in at https://dash.cloudflare.com (the same account you use for R2).
2. Go to **Domain Registration**, then **Register Domains**, and search for names.
   Short, easy to say out loud and easy to type in a reel caption. A `.com` is best; `.app` and `.ca` are good too.
3. Buy it. Turn on **auto-renew** so it never lapses.

## 2. Point the domain at the site (GitHub Pages)

**In Cloudflare** (your domain, then **DNS**, then **Records**), add these. Set every one to **DNS only** (grey cloud, not orange) for now:

| Type | Name | Content |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |
| CNAME | `www` | `amarlatchman-dev.github.io` |

**Verify the domain with GitHub.** This stops anyone else from claiming it on GitHub.
1. On GitHub, open your profile picture, then **Settings**, then **Pages** (under "Code, planning, and automation").
2. Click **Add a domain**, type your domain, and GitHub shows a TXT record.
3. Add that TXT record in Cloudflare DNS, then click **Verify** on GitHub.

**Turn on the custom domain.**
1. Open the repo, then **Settings**, then **Pages**.
2. Under **Custom domain**, enter your domain (for example `yourname.com`) and click **Save**. GitHub checks DNS, which can take from a few minutes up to an hour.
3. When **Enforce HTTPS** becomes clickable, tick it.

The old `amarlatchman-dev.github.io/meet-in-the-middle` address will redirect to the new domain automatically.

## 3. Serve the tiles from your domain (R2)

Once the R2 bucket exists (see [R2_SETUP.md](R2_SETUP.md)):

1. Open the bucket, then **Settings**, then **Custom Domains**, then **Connect Domain**.
2. Enter `tiles.halfwise.app`. Cloudflare adds the DNS record itself.
3. Update the bucket's **CORS policy** so `AllowedOrigins` includes your domain:
   `["https://halfwise.app", "https://www.halfwise.app", "https://amarlatchman-dev.github.io"]`

A custom domain avoids the rate limits on the `r2.dev` address, and you can turn the r2.dev address off afterwards.

## 3b. Make hello@halfwise.app work (free)

The Contact page lists **hello@halfwise.app**. To receive those emails in your normal inbox:
1. In Cloudflare, open halfwise.app, then **Email**, then **Email Routing**, then **Get started**.
2. Create the address `hello` and choose your personal email as the destination. Confirm the verification email Cloudflare sends.
3. Let Cloudflare add the MX and TXT records it suggests.

## 4. Send Claude these

- The domain, and whether you want `yourdomain.com` or `www.yourdomain.com` as the main address
- The tiles address (`https://tiles.halfwise.app/`)
- Confirmation that the four R2 secrets are added in GitHub

## 5. What Claude does next (in the repo)

- Sets `TILE_BASE` to the tiles address, runs the map build, and checks it end to end
- **Pages for ad approval:** About and How it works, FAQ, Privacy policy, and Contact.
  Google AdSense rejects sites without these.
- **Sharing polish:** page title and description, a preview image for links shared in WhatsApp and iMessage, a favicon, and an app icon so it can be added to a phone home screen
- **Search basics:** `robots.txt` and a `sitemap.xml`
- **Ad slots:** one small banner in the results panel and one "Sponsored" row in the nearby list, never over the map

## 6. After the site is live (you)

1. **Google Search Console** (https://search.google.com/search-console): add the domain and submit the sitemap. Google then starts showing the site in search.
2. **Google AdSense** (https://adsense.google.com): apply with the domain.
   - Approval usually takes a few days to a few weeks. It goes better once the About, FAQ and Privacy pages exist and the site has some visitors, for example from your first reels.
   - In AdSense, turn on Google's own consent message (**Privacy & messaging**). It's needed for visitors from Europe and the UK.
3. **Optional:** a simple, privacy-friendly analytics tool, such as Cloudflare Web Analytics (free, in the same dashboard), to see how many people use it.

## Security notes

- The site has no server, accounts or database. Everything runs in the visitor's browser, so most server-side attacks don't apply.
- The map library (Leaflet) is hosted in `vendor/leaflet/` instead of a third-party CDN.
- Every page has a Content Security Policy listing the only servers it may contact. **When adding a new service** (for example Google AdSense), add its hosts to the policy in `index.html` and `tools/make_pages.py`, or the browser will block it.
- Keys (R2, Meta) live only in GitHub Actions secrets and never reach the website. No workflow runs on pull requests from outside contributors.
