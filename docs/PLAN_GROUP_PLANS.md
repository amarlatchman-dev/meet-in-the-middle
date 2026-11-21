# Plan: "Group plans, solved" (Mon Nov 23 – Wed Nov 25)

Goal: turn Halfwise from "find the middle" into "get the group from *we should hang out* to *we're going to X at 7*".

| Day | Theme | Ships |
|---|---|---|
| Mon | **1. Venue-first results** | Top 5 places that are fair for everyone, not just a pin |
| Tue | **2. Decide together** | Live group links: everyone adds themselves, votes, gets a calendar invite |
| Wed | **5. Reasons to come back** | Saved groups, "plan again", polish, launch reels |

All times are Eastern. Each day ends with a working version pushed to halfwise.app.

## Before Monday (you, about 15 minutes)

Tuesday needs a small backend on **Cloudflare Workers** (the free tier covers this):

1. In Cloudflare, go to **My Profile**, then **API Tokens**, then **Create Token**, and use the **Edit Cloudflare Workers** template. Copy the token.
2. In GitHub, go to the repo, then **Settings**, then **Secrets and variables**, then **Actions**, and add two secrets:
   - `CLOUDFLARE_API_TOKEN`: the token
   - `CLOUDFLARE_ACCOUNT_ID`: shown on the Cloudflare dashboard's right side
3. Optional but useful: finish the R2 setup (`docs/R2_SETUP.md`), so the whole of North America is live for the launch reels.

## Monday: venue-first results

**10:00–12:00 · Ranking engine**
- **What are you looking for?** A new picker before searching: Food, Drinks, Coffee & dessert, Activity, Free, Anything. Optional cuisine or activity type.
- **Per-venue travel times:** snap each candidate place onto the road network and read everyone's exact travel time from the flood we already compute. That costs nothing extra in the pre-built areas.
- **Score each venue by:**
  - fairness (using the chosen Fairest, Balanced or Least total rule)
  - open at the meeting time
  - matches what you asked for
  - has useful details (hours, website, cuisine)
  - a small penalty for being far from the ideal spot

**13:00–15:00 · Results redesign**
- **Venue cards at the top:** the top 5 venue cards replace "Meet near X" as the headline. Each card shows:
  - the name, type, and open or closed status
  - every person's minutes ("Maya 22 · Omar 19 · Leah 24")
  - a Directions button and a **Pick this** button
- **Numbered map pins** for the 5 venues. The fairness comparison and the existing filters move below the cards.

**15:00–17:00 · Fallback, test, ship**
- **Outside the pre-built areas:** venue times come from one OSRM table request.
- **Testing:** phone and desktop, and all four travel modes.
- **Ship** it, then record a reel: "4 friends, 1 restaurant, 0 arguments".

## Tuesday: decide together (live group plans)

**10:00–12:30 · Backend (Cloudflare Worker + Durable Objects at `api.halfwise.app`)**
- **Plan storage:** create a plan, join, update your location, vote, and finalise.
- **Plan IDs:** long and random, so links can't be guessed.
- **Expiry:** plans auto-delete after 7 days.
- **What's stored:** only names and rounded locations. No accounts, no emails.
- **Abuse limits:** rate limits per IP, maximum 10 people, size caps on everything.
- **Deploys** automatically from GitHub Actions, using the secrets above.

**13:30–15:30 · Plan page**
- **Start a group plan:** the host gets a link (`halfwise.app/#plan=…`) to drop in the group chat.
- **Joining:** friends open the link, type their name, and tap "Use my location" or search. No sign-up.
- **Live updates:** everyone sees who's joined; the meeting spot and top venues update as people arrive.
- **Voting:** each person votes on the top 5. Live tallies show who picked what.

**15:30–17:00 · Finalise and invite**
- **Locking it in:** the host taps **Lock it in**, and everyone sees the chosen place and time.
- **Calendar invite:** an **Add to calendar** button gives an .ics file for Apple and Outlook, plus a Google Calendar link.
- **Share message:** "We're going to Pai Thai, Fri 7:00 PM. Leave by 6:38."
- **Privacy and security:** update the privacy policy and FAQ, and add `api.halfwise.app` to the security policy.

## Wednesday: reasons to come back, plus launch

**10:00–12:00 · Saved groups (no account needed)**
- **Save as a group:** "Friday crew", "Family", "Work lunch". This stores members, usual travel modes and preferences in the browser.
- **Your groups** on the home screen, with one-tap **Plan again**. It starts a new live plan with the same people, and everyone gets a fresh link.
- **Recent plans:** see past picks, so the group doesn't repeat the same place.

**13:00–15:00 · Polish**
- **First-visit walkthrough:** three short steps.
- **Empty and error states:** someone hasn't joined, no places found, and so on.
- **Funnel tracking** in GoatCounter: search → plan created → people joined → vote → locked in → directions opened.
- **Update the About and FAQ pages**, plus the link preview image.

**15:00–17:00 · Launch content**
- **Three reels:**
  - "Stop arguing in the group chat"
  - "We voted on where to eat"
  - "Our friend group's fair spot"
- **Updated bios:** "Group plans, solved."
- **Final test** on real phones, then push.

## How we'll know it worked (first 2 weeks)

- **Searches:** share of visitors who run a search.
- **Group plans:** share of searches that become a group plan, and the average number of people who join one.
- **Decisions:** share of plans that get locked in, plus Directions clicks.
- **Retention:** share of people who come back and use **Plan again**.
