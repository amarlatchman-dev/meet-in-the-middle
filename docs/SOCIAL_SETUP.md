# Social media setup: Instagram, Facebook, YouTube

Brand files are in [`../brand/`](../brand/):

| File | Use |
|---|---|
| `profile-1080.png` | Profile picture on all three (Instagram crops it to a circle; the logo fits inside) |
| `youtube-banner-2560x1440.jpg` | YouTube channel banner (text sits in the strip phones show) |
| `facebook-cover-1640x624.jpg` | Facebook Page cover (text stays clear of the sides phones crop) |
| `sample-reel-gta.mp4` | First reel, 1080×1920, ready to post |

## Handles

Try `@halfwise` first, then `@halfwise.app`, `@halfwiseapp` or `@gethalfwise`. Use the same handle everywhere if you can.

## 1. Instagram (start here)

1. Create the account with the handle, then go to **Settings**, then **Account type and tools**, then **Switch to professional account**, and choose **Business**.
2. **Category:** choose **App Page**. If it isn't offered, use **Website** or **Internet Company**. Turn **Display category on profile** off, which looks cleaner.
3. **Name:** `Halfwise | Fair meeting spots`. The name field is searchable, so the words after the bar help people find you.
4. **Bio:**
   ```
   Find the fair place to meet 📍
   Up to 10 friends · real travel times
   Food, things to do & free spots nearby
   👇 Try it free
   ```
5. **Link:** `https://halfwise.app`
6. Profile picture: `profile-1080.png`.

## 2. Facebook Page

1. From your personal Facebook, go to **Pages**, then **Create new Page**.
2. **Name:** `Halfwise`. **Categories:** `App Page`, plus `Website` and `Travel & Transportation` if offered (up to three).
3. **Bio:** `Find the fair place to meet. Add up to 10 friends and Halfwise picks the spot with real drive, transit, bike and walking times.`
4. **Website:** `https://halfwise.app`. **Email:** `hello@halfwise.app`.
5. Upload `profile-1080.png` and `facebook-cover-1640x624.jpg`.
6. **Link Instagram:** on the Page, go to **Settings**, then **Linked accounts**, then **Instagram**, and connect. Then use **Meta Business Suite** (business.facebook.com) to post a reel once and publish it to both Instagram and Facebook.

## 3. YouTube (Shorts)

1. In YouTube, open your profile picture, then **Create a channel**. Name it `Halfwise`, with the handle `@halfwise` or the closest available.
2. Go to **YouTube Studio**, then **Customization**:
   - **Branding:** upload `profile-1080.png` and `youtube-banner-2560x1440.jpg`.
   - **Basic info:** description below, plus the link `https://halfwise.app`.
   ```
   Halfwise finds the fair place to meet. Add up to 10 friends, watch everyone flood out along the real streets, and see where it's fair to meet, with places to eat and things to do nearby. Free at halfwise.app
   ```
3. Upload the same vertical MP4s as **Shorts** (anything vertical and under 3 minutes counts).

## Making reels

**On your computer** (needs Node.js and ffmpeg), from the repo folder. The first time only:
```bash
npm install playwright && npx playwright install chromium
```
Then for each reel:
```bash
node tools/record_reel.js --people "Maya@43.5933,-79.6441|Jordan@43.7757,-79.2578|Leah@43.8255,-79.5385|Omar@43.6383,-79.4201" --city "Greater Toronto Area" --out gta.mp4
```
Get coordinates by right-clicking a spot in Google Maps; the first line of the menu is `lat, lon`. Add `--mode transit` or `--mode bike` for variety.

**Or record your phone screen** on `https://halfwise.app/?reel=1` after adding people.

Instagram, Facebook and YouTube all prefer music added inside their apps, so pick a trending sound when you post.

## Posting plan (first 2 weeks)

Post 4–5 reels a week, at the same time of day (evenings work well for social plans).

| # | Reel idea | Hook text (first second) |
|---|---|---|
| 1 | 4 friends across the GTA (`sample-reel-gta.mp4`) | "Where should 4 friends meet?" |
| 2 | Mississauga, Brampton, Markham, downtown | "The GTA can't agree where to eat" |
| 3 | Same group, Car vs Transit | "Driving vs the TTC: where do you meet?" |
| 4 | 10 friends | "10 friends, one fair spot" |
| 5 | Fairest vs Least total (one far-away friend) | "Why the 'middle' isn't always fair" |
| 6 | Ottawa, Hamilton or KW group | "Ottawa, where should you meet?" |
| 7 | Free filter results | "Hangout spots that cost $0" |
| 8 | Comment request | "Comment 3 neighbourhoods, we'll find your spot" (reply with a reel) |

**Caption template:**
```
Where should 4 friends in the GTA meet? 📍 Everyone floods out along the real streets, and the fair spot is where they meet.
Try it with your group: halfwise.app (link in bio)
#toronto #gta #mississauga #scarborough #torontofood #thingstodotoronto #friends #hangout #meetup
```
Swap the city hashtags for each reel. Keep 5–10 hashtags.

## Automatic daily posting

`.github/workflows/daily-social.yml` records one reel a day from [`social/schedule.json`](../social/schedule.json) and posts it to Instagram and the Facebook Page at about 5:37 pm Toronto time. It works through the list in order and starts over at the end. Edit the list to change what gets posted.

- Meta setup: the **halfwise.app** business portfolio has the app **Halfwise Poster** and the system user **Halfwise poster**, which has Content access to the Page and the Instagram account.
- The repository secret `META_TOKEN` holds that system user's token, which doesn't expire. If posting stops with an auth error, generate a new one in Business Suite (Settings, then System users) and replace the secret.
- To test, go to **Actions**, then **Daily social reel**, then **Run workflow**. Tick "Record only" to see the video without posting. Each run keeps the MP4 as a download for 14 days.
