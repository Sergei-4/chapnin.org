# CHAPNIN.ORG FINAL BUILD — DEPLOYMENT GUIDE

## What's New

✅ **Homepage** — Book section with NEW BOOK 2026 badge + Rowan Williams quote  
✅ **Menu** — Renamed "About" → "Bio", "For You" → "Collaborate"  
✅ **Writings** — Filter tabs (Essays, Policy Papers, Interviews, Academic Articles) + 6 academic articles  
✅ **Collaborate** — Reordered sections (1-7) + details about languages, exhibition duration, calendar print run + contact form  
✅ **Photos** — Filter order: Portraiture → Reportage → Landscape  
✅ **Sitemap** — Updated with new URLs

## Files in This Archive

```
chapnin-org-final/
├── index.html ................... NEEDS UPDATE (add book block)
├── bio/index.html ............... NO CHANGE
├── writings/index.html .......... NEEDS UPDATE (add tabs + articles)
├── collaborate/index.html ....... NEW (renamed from for-you, reordered)
├── talks/index.html ............ NO CHANGE
├── exhibitions/index.html ....... NO CHANGE
├── photos/index.html ........... NEEDS UPDATE (filter order)
├── books/
├── images/
├── sitemap.xml ................. ✅ UPDATED
├── robots.txt .................. NO CHANGE
├── CNAME ....................... NO CHANGE
└── UPDATES.txt ................. Change summary
```

## Deployment Steps

### Step 1: Local Updates

You need to manually update 3 files with detailed HTML changes:
- **index.html** — Add book section (see UPDATES.txt for details)
- **writings/index.html** — Add filter tabs + 6 new articles
- **photos/index.html** — Change filter tab order

**OR** — Use the GitHub web editor to make these changes directly to your live repo:
1. Go to https://github.com/Sergei-4/chapnin.org
2. Click pencil icon on each file
3. Copy-paste the new content from the detailed guides in UPDATES.txt
4. Commit each change

### Step 2: Add Images to /images/for-you/

Upload these 7 files via GitHub web interface:
- book-church-revival.jpg
- almanac-cover-04.jpg
- almanac-cover-05.jpg
- almanac-cover-06.jpg
- calendar-icons.jpg
- exhibition-ammo-boxes.jpg
- catalog-saints.jpg

### Step 3: Push to GitHub

```bash
cd ~/Downloads/chapnin.org
git add .
git commit -m "Final update: book section, Collaborate page, Writings tabs, photo reorder"
git push origin main
```

### Step 4: Wait & Verify

⏳ GitHub Pages rebuilds in 1-3 minutes
✅ Visit https://chapnin.org
🔄 Hard refresh (Cmd+Shift+R on Mac)

## Key Content Changes

### Homepage Book Block
- Cover image (280×450px)
- "NEW BOOK 2026" badge
- Title + subtitle
- Description
- Rowan Williams quote (★★★★★)

### Writings — Filter Tabs
```
Essays | Policy Papers | Interviews | Academic Articles
```

NEW articles:
- FAITH UNDER PRESSURE (Policy Paper, Aug 25, 2026)
- Fixed First Things date (JANUARY 6, 2016)
- 4 Academic Articles with DOI/ISSN

### Collaborate Page Order
1. Lecture/conversation (EN or RU)
2. Exhibition space (2-3 days OR 3-6 months)
3. Icon calendar (300+ copy print run)
4. Exhibition catalogs (100 iconographers, 15 countries)
5. Contemporary Christian culture (illustrated almanac)
6. Russian book (Church Resurrection, 2018)
7. Newsletter (Substack)

Contact form at bottom for items 1-6.

### Photos Filter
Before: All Photos | Landscape | Portraiture | Reportage  
After: Portraiture | Reportage | Landscape

## Support

For detailed HTML, see UPDATES.txt or contact with specific questions.

Good luck! 🚀
