# ATS Scorer 🎯

Free, instant ATS (Applicant Tracking System) resume compatibility checker.
Upload a PDF or DOCX, get a detailed score simulating how a 2005-era ATS machine reads your resume.

**No accounts. No payments. Files never stored.**

---

## Features

- **ATS Score** — overall compatibility percentage
- **Readability Score** — can the ATS physically extract the text?
- **Structure Score** — can the ATS make sense of the layout?
- **ATS View** — see exactly what the parser outputs (character by character)
- **Text Block Map** — visual heat map of how the PDF was parsed (PDF only)
- **Section Detection** — which resume sections were found and what they contain
- **Issues List** — categorized by severity (Critical / High / Medium / Low)

---

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run
python run.py

# 3. Open http://localhost:8000
```

---

## Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

The `vercel.json` is pre-configured. No environment variables needed — this app has no database or external API keys.

---

## Project Structure

```
ats-scorer/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes
│   ├── extractor.py     # PDF/DOCX text extraction
│   └── scorer.py        # ATS scoring engine
├── frontend/
│   ├── index.html       # Single-page app
│   └── static/
│       ├── css/app.css
│       └── js/
│           ├── app.js      # Upload + orchestration
│           ├── results.js  # Results rendering
│           └── viewer.js   # Text block map visualizer
├── run.py               # Local dev entry point
├── vercel.json          # Vercel deployment config
└── requirements.txt
```

---

## Architecture

```
Browser ──upload──► POST /api/score
                         │
                    extractor.py
                    (pdfminer / python-docx)
                         │
                    scorer.py
                    (ATS simulation engine)
                         │
                    JSON response ──► JS renders results
```

---

## Scoring Methodology

### Readability Score (45% of overall)
Can the ATS physically extract text from your document?
- Text extraction success
- Special/smart character usage
- Image/graphic content ratio
- Font compatibility
- Encoding issues

### ATS Structure Score (55% of overall)
Can the ATS make sense of what it extracted?
- Single vs multi-column layout
- Table usage
- Header/footer placement
- Standard section headers
- Date format compatibility
- Contact info parseability
- Page count

### Grading
| Score | Grade | Label |
|-------|-------|-------|
| 90–100 | A | ATS Ready |
| 75–89 | B | Mostly Compatible |
| 60–74 | C | Needs Work |
| 45–59 | D | At Risk |
| 0–44 | F | ATS Will Reject |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Frontend app |
| GET | `/api/health` | Health check |
| POST | `/api/score` | Score a resume file |

### POST /api/score

**Request:** `multipart/form-data` with `file` field (PDF or DOCX, max 5MB)

**Response:**
```json
{
  "overall_score": 72,
  "readability_score": 85,
  "ats_score": 61,
  "grade": { "letter": "C", "label": "Needs Work", "color": "#d97706" },
  "issues": [...],
  "suggestions": [...],
  "positives": [...],
  "detected_sections": ["contact", "experience", "education"],
  "parsed_sections": { "experience": "...", ... },
  "ats_visible_text": "...",
  "text_blocks": [...],
  "metadata": { ... }
}
```

---

## Logo Assets

Place in `/logo/` folder:
- `logo-512.png` — 512×512px
- `logo-192.png` — 192×192px  
- `favicon.ico` — 32×32 + 16×16 multi-size
- `logo-og.png` — 1200×630px for OG tags

**Suggested design:** Document/page icon with a scan line or grid overlay, sky blue (#0ea5e9) on white, clean and readable at 32px.

---

## SEO Target Keywords

- "free ATS resume checker"
- "ATS resume score online"
- "ATS compatible resume test"
- "applicant tracking system resume check"
- "resume ATS compatibility checker"
