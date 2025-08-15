# Comic Book Database & Recommendation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-green)](https://vuejs.org/)

A web application and API for browsing, searching, and recommending Marvel comic book series.

<img width="1563" height="763" alt="image" src="https://github.com/user-attachments/assets/fbbaf39b-cadc-4dd4-8ac2-56c1b488827b" />

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
- [API Endpoints](#api-endpoints)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview

This project provides a full-stack solution for comic book fans to explore, filter, and discover Marvel comics. It includes:

- **FastAPI backend** serving comic book data and recommendations.  
- **Vue.js frontend** for browsing series, issues, creators, and recommendations.  
- Recommendation system based on **creators, series summaries, and title similarity**.  

---

## Features

- Browse and filter comic issues by **series, year, and variant status**.  
- Search for **series** using prefix matching.  
- Get detailed recommendations for issues based on:
  - Same creators  
  - Series summaries (semantic similarity)  
  - Title similarity (fuzzy matching)  
- View issue metadata: **release dates, images, creators, variant covers and much more**.
- Check interesting stats about Marvel Comics
- Fast and responsive **web interface**.  
- Fully containerizable and deployable to **Render** (backend) and **Netlify** (frontend).  
---

## Capabilities

- Handle **large datasets** efficiently (e.g., 50+ issues).  
- Automatic **CORS configuration** based on environment (`development` or `production`).  
- Support for **environment variables** to configure frontend URLs, datasets, and server behavior.  
- Provides **JSON API endpoints** consumable by any frontend.
  
---

## Tech Stack

- **Backend**: Python, FastAPI, Pandas, NumPy, Sentence Transformers, Scikit-learn  
- **Frontend**: Vue 3, Vue Router, State Management  
- **Deployment**: Render (backend), Netlify (frontend)
  
---

## Installation

### Backend

1. Clone the repository:

```bash
git clone https://github.com/yourusername/comic-book-db.git
cd comic-book-db/backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt

```

3. Edit .env file according to your needs:
If you set environment to "production" it will use url you entered for CORS.
For local just leave it empty or "development".
```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:8080

```
4. Start the Backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

```
### Frontend
1. Install dependencies:
```bash
npm install

```
3. Edit .env file for managing API calls:
URL entered here will be used by frontend for API calls so be careful and put correct one.
```bash
VUE_APP_API_URL=http://127.0.0.1:8000

```
5. Run development server:
```bash
npm run dev

```

## Usage
1. Visit http://localhost:8080 to browse the frontend.
2. Use search and filter bars to find comics, creators, and series.
3. Click on issues to see variants and recommended series.
4. Access raw JSON API at http://localhost:8000 if you want to use API.

## API Endpoints
1. GET /issues/ — list issues with optional filters (dataset, series_title, year, is_variant, limit)
2. GET /issues/{issue_id} — get a single issue by ID
3. GET /issues/{issue_id}/variants — list variant issues
4. GET /issues/{variant_id}/original — get the original issue for a variant
5. GET /series/ — list series titles
6. GET /creators/ — list creators
7. GET /stats/ — get dataset statistics
8. GET /issues/{issue_id}/recommended_series — get recommended series for a given issue
