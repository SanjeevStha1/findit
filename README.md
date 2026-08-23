# FindIt — AI-Powered Lost & Found Platform

FindIt is a full-stack web application that helps people report, discover,
and recover lost belongings in Kathmandu. It combines structured reporting
(category, location, date, photos) with an AI-driven hybrid matching engine
that automatically surfaces likely lost/found pairs across the city.

This repository contains the **backend** (Django REST API). The frontend
(React) lives in a separate repository: [findit-frontend](https://github.com/SanjeevStha1/findit-frontend).

## Live Demo
- Frontend: _[add your deployed URL here once live]_
- Backend API: _[add your deployed URL here once live]_

## Problem & Motivation

Lost & found today is fragmented — physical lost-and-found desks, scattered
Facebook posts, WhatsApp chains — with no central system connecting a
lost report to a found report of the same item. FindIt centralizes this
into one platform and uses AI to do the matching automatically, rather
than relying on both parties happening to see the same post.

## Core Features

- **Auth**: JWT-based registration/login with automatic silent token refresh
- **Report Lost/Found**: category, description, date/time, map-based
  location picker, photo upload, and private verification notes (visible
  only to the reporter, used to cross-check claims)
- **Browse**: list and interactive map views with server-side filtering
  (type, category)
- **Location privacy**: exact coordinates are stored, but only a randomly
  fuzzed (~150m offset) location is ever shown publicly; exact location is
  never exposed via the API
- **AI-powered matching engine** (see below)
- **Claims**: structured claim submission with anti-fraud protections
  (minimum answer length, rate limiting, self-claim prevention), and a
  finder-side approve/reject inbox
- **Notifications**: automatic, in-app notifications for new matches and
  claim activity (submission, approval, rejection), with an unread badge
- **Dashboard**: unified view of a user's own reports and notifications

## AI / Machine Learning Approach

A key goal of this project was to make AI a *functional* part of the
matching system, not a superficial add-on. The matching engine evolved
through two stages:

### 1. Baseline (non-AI) matching
A transparent, rule-based scorer combining:
- Category match (exact match / no match)
- Geographic distance (via PostGIS geography queries)
- Date proximity
- Text overlap (Jaccard similarity — naive word-set intersection)

This baseline is fully explainable but fails on real language: two
descriptions of the same item using different vocabulary (e.g. "wallet"
vs. "bifold purse") score close to 0% text similarity despite describing
the same object.

### 2. AI-enhanced hybrid matching
The text and image signals were upgraded to use real pretrained deep
learning models, run entirely via **local inference** (no external AI
API calls):

- **Text similarity**: `sentence-transformers` (`all-MiniLM-L6-v2`)
  generates 384-dimensional semantic embeddings for each report's
  description. Similarity is computed via cosine similarity between
  embeddings, stored using `pgvector` in PostgreSQL.
- **Image similarity**: CLIP (`clip-ViT-B-32`, via `sentence-transformers`)
  generates 512-dimensional embeddings from uploaded photos, enabling
  visual similarity comparison between item images, independent of exact
  file matching.
- **Hybrid score**: category, distance, date, text similarity, and image
  similarity are combined into one weighted confidence score, with full
  transparency — every match shows its complete score breakdown to the
  user (no black-box percentage).

**Measured improvement**: for a real test pair — "Black leather wallet
with student ID inside" vs. "Found a dark brown bifold purse with someone
student card inside" — the baseline Jaccard method scored ~5-10% text
similarity; the sentence-transformer embedding approach scored **59.8%**,
correctly recognizing the semantic relationship despite near-zero word
overlap. This directly demonstrates the value of embedding-based
similarity over lexical matching for this problem domain.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django, Django REST Framework |
| Database | PostgreSQL + PostGIS (geographic queries) + pgvector (embedding storage) |
| Auth | JWT (`djangorestframework-simplejwt`) |
| AI/ML | `sentence-transformers` (text & CLIP image embeddings) |
| Image storage | Cloudinary (direct browser-to-cloud upload) |
| Frontend | React (Vite), Tailwind CSS, React Router |
| Maps | Leaflet + OpenStreetMap |

## Architecture
React Frontend ──HTTPS/JSON──► Django REST API ──────► PostgreSQL + PostGIS + pgvector
│
├──► sentence-transformers (text embeddings)
├──► CLIP (image embeddings)
└──► Cloudinary (image URLs only; uploads go
directly from browser to Cloudinary)


The AI matching logic runs inside the Django process itself (not as a
separate microservice) — a deliberate simplification appropriate for this
project's scale, avoiding unnecessary infrastructure complexity while
still being cleanly separated into its own module (`reports/matching.py`,
`reports/embeddings.py`) for clarity and testability.

## Database Schema (key models)

- `Item` — unified model for both lost and found reports (`report_type`
  field distinguishes them), includes `text_embedding` (vector field) and
  a fuzzed `location_display` separate from the real `location`
- `ItemImage` — supports multiple photos per item, each with its own
  `image_embedding`
- `Match` — stores computed match pairs with full `score_breakdown` JSON
- `Claim` — claim requests with verification answers and status lifecycle
- `Notification` — in-app notifications, typed (match / claim_update / system)

## Setup / Running Locally

### Prerequisites
- Python 3.10+
- A PostgreSQL database with PostGIS and pgvector extensions enabled
  (this project uses [Supabase](https://supabase.com)'s free tier)
- A [Cloudinary](https://cloudinary.com) account (free tier)
- GDAL/GEOS installed locally (required by GeoDjango)

### Steps

```bash
git clone https://github.com/SanjeevStha1/findit.git
cd findit
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root:


```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py backfill_embeddings          # only needed if importing existing data
python manage.py backfill_image_embeddings    # only needed if importing existing data
python manage.py runserver
```

API will be available at `http://127.0.0.1:8000/api/`.

## Known Limitations & Future Work

Scoped deliberately for a solo, time-boxed final-year project:

- **Claim verification** currently uses free-text answers reviewed
  manually by the finder. A stronger version would use finder-defined
  structured questions and further redact identifying details from
  public descriptions.
- **No trust/reputation score** yet — claims and reports are treated
  equally regardless of account history.
- **No fraud-risk scoring** — duplicate/suspicious report detection is
  not yet automated.
- **Matching runs synchronously**, computed on-demand rather than via a
  background task queue — acceptable at current data scale, would need
  revisiting (e.g. Celery) at production scale.
- **"Items along my route"** location-history matching (opt-in) was
  scoped out of MVP for privacy-complexity/time reasons.

## Author
Sanjeev — final-year AI and Data Science project.
