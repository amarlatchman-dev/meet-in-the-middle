#!/usr/bin/env python3
"""Generate Halfwise's content pages (about, faq, privacy, contact) from one template."""
import datetime

UPDATED = "November 20, 2026"
NAV = [("about.html", "How it works"), ("faq.html", "FAQ"), ("privacy.html", "Privacy"), ("contact.html", "Contact")]


def page(fname, title, desc, body):
    nav = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == fname else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} · Halfwise</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://halfwise.app/{fname}">
<meta name="theme-color" content="#05080b">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon-192.png">
<meta property="og:title" content="{title} · Halfwise">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://halfwise.app/og.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=Inter:wght@400;600&display=swap">
<link rel="stylesheet" href="pages.css">
</head>
<body>
<header class="top">
  <a class="brand" href="./"><img src="icon.svg" alt=""><span>Half<b>wise</b></span></a>
  <nav aria-label="Site">{nav}</nav>
  <a class="cta" href="./">Open Halfwise</a>
</header>
<main>
{body}
</main>
<footer class="site">
  <span>© {datetime.date.today().year} Halfwise</span>
  {"".join(f'<a href="{h}">{t}</a>' for h, t in NAV)}
  <span>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors</span>
</footer>
</body>
</html>
"""


ABOUT = """<h1>Find the fair place to meet</h1>
<p class="lead">Halfwise picks a meeting spot that's fair for everyone, using real travel times instead of a straight line on a map. Then it shows places to eat, things to do, and free spots nearby.</p>

<h2>How it works</h2>
<ol class="steps">
  <li><strong>Add everyone.</strong> Up to 10 people. Search an address, drop a pin, or use your current location. Or send the group an invite link so each person adds themselves.</li>
  <li><strong>Pick how you're travelling.</strong> Car, transit, bike or walking, and when you're meeting.</li>
  <li><strong>Watch the floods.</strong> Each person's location floods outward along the real streets, first one by one and then all at once. Where they meet is where it's fair to meet.</li>
  <li><strong>Choose your spot.</strong> Halfwise shows three options and how they compare, plus a route and a leave-at time for each person so you all arrive together.</li>
  <li><strong>Find something to do.</strong> Restaurants by cuisine, cafés, bars, activities, parks and free public spaces near the spot, filtered to what's open when you meet.</li>
</ol>

<h2>Three ways to be fair</h2>
<div class="table-wrap"><table>
  <thead><tr><th>Choice</th><th>What it does</th><th>Good for</th></tr></thead>
  <tbody>
    <tr><td><strong>Fairest</strong></td><td>Makes the longest trip as short as possible.</td><td>Nobody wants to be the one driving an hour.</td></tr>
    <tr><td><strong>Balanced</strong></td><td>A weighted average of everyone's travel time, where long trips count extra.</td><td>Most groups. Leans toward where most people are without stranding anyone.</td></tr>
    <tr><td><strong>Least total</strong></td><td>Keeps everyone's combined travel as low as possible.</td><td>Saving the most time overall, even if one person travels more.</td></tr>
  </tbody>
</table></div>

<h2>Where the data comes from</h2>
<p>Roads, transit lines and places come from <a href="https://www.openstreetmap.org/">OpenStreetMap</a>, the free map built by volunteers. Halfwise pre-builds the road network for major North American regions so results appear in a second or two. Outside those regions it asks the free OpenStreetMap routing service (OSRM) for travel times.</p>
<p>Travel times are estimates. Driving times don't include live traffic. Transit estimates use subway, LRT, streetcar and commuter rail lines with average waits; buses and exact timetables aren't included yet.</p>

<p><a class="cta" href="./">Find your spot</a></p>
"""

FAQ_ITEMS = [
    ("Is Halfwise free?", "Yes. There's no account and no paywall. The site may show a small number of ads to cover its costs."),
    ("How many people can I add?", "Up to 10 starting points."),
    ("How is this different from picking the halfway point on a map?",
     "A straight-line midpoint ignores roads, highways, rivers and transit. Halfwise uses real travel times along the street network, so the spot is fair in minutes, not just in distance."),
    ("What do Fairest, Balanced and Least total mean?",
     "Fairest makes the longest trip as short as possible. Balanced is a weighted average of everyone's travel time where long trips count extra. Least total keeps everyone's combined travel lowest. Halfwise shows all three so you can compare."),
    ("How does the invite link work?",
     "Tap Invite friends to share a link that contains the group: names, approximate locations, travel mode and meeting time. A friend opens it, adds their own location, and shares the updated link back to the group. Anyone with the link can see those locations, so only share it with people you trust."),
    ("How accurate are the travel times?",
     "They're estimates. Driving uses speed limits and road types without live traffic. Transit uses rapid transit lines with average waits; buses and exact timetables aren't included yet. Use the Route links to check a trip in Google Maps before you leave."),
    ("Which areas are covered?",
     "Major North American metros have a pre-built street map for instant results, including Toronto, Ottawa, Montreal, Vancouver, Calgary, New York, Chicago, Los Angeles, Houston, Dallas and many more. Elsewhere, Halfwise uses the free OpenStreetMap routing service. Transit mode only works inside the pre-built areas."),
    ("Why is a restaurant missing, or its hours wrong?",
     "Places and opening hours come from OpenStreetMap, which volunteers keep up to date. You can add or fix a place yourself at openstreetmap.org, and it will appear in Halfwise after the next monthly update."),
    ("Do you store my location?", "No. Everything is calculated in your browser, and Halfwise has no accounts or database of users. See the privacy policy for the services your browser talks to."),
    ("Can I install it on my phone?", "Yes. Open halfwise.app in your phone's browser and choose Add to Home Screen (Safari) or Install app (Chrome)."),
]
FAQ = "<h1>Frequently asked questions</h1>\n<p class=\"lead\">Quick answers about how Halfwise works.</p>\n" + "\n".join(
    f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ_ITEMS)

PRIVACY = f"""<h1>Privacy policy</h1>
<p class="muted">Last updated {UPDATED}</p>
<p class="lead">Halfwise is built to work without knowing who you are. There are no accounts, and the locations you enter are processed in your browser.</p>

<h2>What stays on your device</h2>
<p>The people, locations, travel settings and meeting time you enter are saved in your browser's local storage so they're still there next time. They aren't sent to a Halfwise server, because Halfwise doesn't run one. Clearing your browser's site data removes them.</p>

<h2>Services your browser talks to</h2>
<p>To work, the site loads data from these services. Each receives the request your browser makes (including your IP address) under its own privacy policy:</p>
<ul>
  <li><strong>Map tiles and pre-built road data:</strong> GitHub Pages and Cloudflare host the site and its map files. Esri provides the background map images.</li>
  <li><strong>Address search and place names:</strong> Photon by Komoot (and OpenStreetMap Nominatim as a backup) receives what you type in the search box, and the coordinates of pins and meeting spots so they can be named.</li>
  <li><strong>Travel times outside the pre-built areas:</strong> the OpenStreetMap routing service (OSRM) at routing.openstreetmap.de and router.project-osrm.org receives the coordinates of your group and candidate meeting spots.</li>
  <li><strong>Nearby places outside the pre-built areas:</strong> Overpass API servers receive the coordinates of the meeting spot.</li>
  <li><strong>Fonts:</strong> Google Fonts.</li>
</ul>

<h2>Your location</h2>
<p>If you tap Use my location, your browser asks for permission first. The position is used to add you to the group and isn't stored anywhere except your own browser.</p>

<h2>Invite links</h2>
<p>An invite link contains the group's names, locations (rounded to about 10 metres), travel mode and meeting time, encoded in the link itself. Anyone who has the link can read them. Only share it with people you'd tell where you're coming from.</p>

<h2>Ads and analytics</h2>
<p>Halfwise may show ads from Google AdSense. Google and its partners may use cookies or similar technology to show ads based on your visits to this and other sites. You can manage personalised ads at <a href="https://adssettings.google.com">Google Ad Settings</a> and learn more at <a href="https://policies.google.com/technologies/ads">How Google uses information from sites that use its services</a>. Visitors in regions that require it are asked for consent first.</p>
<p>Halfwise may use privacy-friendly visit counts (such as Cloudflare Web Analytics) that don't use cookies or track you across sites.</p>

<h2>Children</h2>
<p>Halfwise isn't directed at children under 13 and doesn't knowingly collect their information.</p>

<h2>Changes and contact</h2>
<p>If this policy changes, the date at the top will change too. Questions? <a href="contact.html">Contact us</a>.</p>
"""

CONTACT = """<h1>Contact</h1>
<p class="lead">Questions, feedback, a city you'd like covered, or a bug to report? Send an email.</p>
<p class="email">hello@halfwise.app</p>
<p class="muted">We read everything, and usually reply within a few days.</p>
<h2>Fixing map data</h2>
<p>Roads, transit lines, places and opening hours come from OpenStreetMap. If something's missing or wrong, the fastest fix is to edit it at <a href="https://www.openstreetmap.org/">openstreetmap.org</a>. Changes show up in Halfwise after the next update.</p>
<h2>Business enquiries</h2>
<p>Interested in featuring your venue near popular meeting spots, or using Halfwise for events or a team? Email us at the address above.</p>
"""

PAGES = [
    ("about.html", "How it works", "How Halfwise finds a fair meeting spot for up to 10 people using real travel times, and finds things to do nearby.", ABOUT),
    ("faq.html", "FAQ", "Answers to common questions about Halfwise: coverage, accuracy, invite links, privacy and more.", FAQ),
    ("privacy.html", "Privacy policy", "How Halfwise handles your data: no accounts, locations processed in your browser.", PRIVACY),
    ("contact.html", "Contact", "Get in touch with Halfwise.", CONTACT),
]

if __name__ == "__main__":
    for fname, title, desc, body in PAGES:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(page(fname, title, desc, body))
        print("wrote", fname)
