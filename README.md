# CoachNote

**AI post-game recaps and practice plans for youth sports coaches.**

Live: [coachnote-zeta.vercel.app](https://coachnote-zeta.vercel.app)

---

## What it does

Describe your game in 2 minutes. CoachNote generates two things instantly:

1. **Parent message** - A warm, positive update for your team group chat (TeamSnap, Band, GroupMe, email). Covers the result, key highlights, one growth area, and next event.
2. **Practice plan** - A 60-minute session plan that directly targets the weaknesses you observed in the game. Not generic drills - a plan that knows what your team struggled with.

Both are downloadable as PDF.

## Supported sports

Soccer, Basketball, Baseball, Softball, Volleyball, Flag Football, Lacrosse, Hockey, Tennis, Swim Meet, Track & Field, Wrestling

## How to use

1. Go to [coachnote-zeta.vercel.app](https://coachnote-zeta.vercel.app)
2. Enter your Anthropic API key in Settings (get one free at [console.anthropic.com](https://console.anthropic.com/settings/keys))
3. Fill in game details - takes under 2 minutes
4. Hit Generate

Your API key stays in your browser (localStorage). Game data goes directly to Anthropic - nothing is stored on any server.

## Architecture

- Pure vanilla HTML/CSS/JS frontend
- Calls Anthropic Claude Haiku API directly from the browser (BYOK)
- jsPDF for client-side PDF generation
- Deployed as static site on Vercel
- No backend, no database, no accounts

## Revenue path

| Path | Mechanism |
|------|-----------|
| Current | Free (BYOK) - drives adoption |
| Future Pro | $4.99/month hosted key, no API setup needed |
| Team tier | $9.99/month shared team account + season stats |

## Who this is for

Volunteer parents and part-time coaches who run U6-U16 recreational and travel teams. They have 30-60 minutes of admin per week: writing the post-game message and planning the next practice. CoachNote cuts that to under 5 minutes.

---

Built with Claude claude-haiku-4-5-20251001 | BYOK | MIT License
