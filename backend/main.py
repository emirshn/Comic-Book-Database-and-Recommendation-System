from fastapi import FastAPI, Query, HTTPException, Path
from typing import Optional
import pandas as pd
import math
import os
import numpy as np
from dotenv import load_dotenv

app = FastAPI(title="Marvel Comics Issues API")

from pathlib import Path as FSPath
BASE_DIR = FSPath(__file__).parent.resolve()
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)

from fastapi.middleware.cors import CORSMiddleware

environment = os.getenv("ENVIRONMENT", "development")
frontend_url = os.getenv("FRONTEND_URL")

if environment == "production" and frontend_url:
    allow_origins = [
        frontend_url,
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
else:
    allow_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

environment = os.getenv("ENVIRONMENT", "development")
frontend_url = os.getenv("FRONTEND_URL")


app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df_original = pd.read_csv(os.path.join(BASE_DIR, "original_issues.csv"))
df_variant = pd.read_csv(os.path.join(BASE_DIR, "variant_issues.csv"))


SUMMARY_EMBEDDINGS_PATH = os.path.join(BASE_DIR, "summary_embeddings.npy")
SERIES_METADATA_PATH = os.path.join(BASE_DIR, "series_metadata.csv")

summary_embeddings = np.load(SUMMARY_EMBEDDINGS_PATH)  
series_metadata = pd.read_csv(SERIES_METADATA_PATH)  

series_id_to_index = {sid: idx for idx, sid in enumerate(series_metadata["series_id"].values)}

for df in [df_original, df_variant]:
    df["release_date"] = pd.to_datetime(df["release_date"], errors='coerce')

if 'is_variant' not in df_original.columns:
    df_original['is_variant'] = False

def clean_record(rec):
    cleaned = {}
    for k, v in rec.items():
        if isinstance(v, float):
            if math.isnan(v) or not math.isfinite(v):
                cleaned[k] = None
            else:
                cleaned[k] = v
        else:
            cleaned[k] = v
    return cleaned

@app.get("/")
def read_root():
    return {"message": "Welcome to the Marvel Comics Issues API"}

@app.get("/issues/")
async def get_issues(
    dataset: str = Query("original", regex="^(original|variant|all)$", description="Choose dataset: original, variant, or all"),
    series_title: Optional[str] = Query(None, description="Filter by series title substring, case-insensitive"),
    series_id: Optional[int] = Query(None, description="Filter by exact series ID"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    is_variant: Optional[bool] = Query(None, description="Filter by variant flag"),
    limit: Optional[int] = Query(1000, description="Limit number of results"),  
):
    if dataset == "original":
        df = df_original
    elif dataset == "variant":
        df = df_variant
    else:  # all
        df = pd.concat([df_original, df_variant], ignore_index=True)

    filtered = df

    if series_id is not None:
        filtered = filtered[filtered['series_id'] == series_id]
    elif series_title:
        filtered = filtered[filtered['series_title'].str.contains(series_title, case=False, na=False)]

    if year:
        filtered = filtered[filtered['release_date'].dt.year == year]

    if is_variant is not None and 'is_variant' in filtered.columns:
        filtered = filtered[filtered['is_variant'] == is_variant]

    filtered = filtered.copy()
    if dataset == "all":
        filtered['dataset'] = filtered['is_variant'].apply(lambda v: "variant" if v else "original")
    else:
        filtered['dataset'] = dataset

    filtered = filtered.head(limit)

    records = filtered.to_dict(orient="records")
    cleaned_records = [clean_record(r) for r in records]
    return cleaned_records

@app.get("/issues/{issue_id}")
async def get_issue_by_id(
    issue_id: int = Path(..., description="Unique issue ID"),
    is_variant: Optional[bool] = Query(None, description="Filter dataset by variant flag"),
):
    if is_variant is None:
        df = df_original
        issue = df[df["issue_id"] == issue_id]
        if issue.empty:
            df = df_variant
            issue = df[df["issue_id"] == issue_id]
            if issue.empty:
                raise HTTPException(status_code=404, detail=f"Issue ID {issue_id} not found in any dataset")
        dataset = "variant" if df is df_variant else "original"
    else:
        df = df_variant if is_variant else df_original
        issue = df[df["issue_id"] == issue_id]
        if issue.empty:
            raise HTTPException(status_code=404, detail=f"Issue ID {issue_id} not found in { 'variant' if is_variant else 'original' } dataset")
        dataset = "variant" if is_variant else "original"

    record = clean_record(issue.iloc[0].to_dict())
    record["dataset"] = dataset
    return record

@app.get("/issues/{original_issue_id}/variants")
async def get_variants_by_original(
    original_issue_id: int = Path(..., description="Original issue ID to find variants for"),
):
    original = df_original[df_original["issue_id"] == original_issue_id]
    if original.empty:
        raise HTTPException(status_code=404, detail=f"Original issue ID {original_issue_id} not found")

    variants = df_variant[df_variant["original_issue_id"] == original_issue_id]

    records = []

    original_rec = clean_record(original.iloc[0].to_dict())
    original_rec["dataset"] = "original"
    original_rec["is_original_variant"] = True  
    records.append(original_rec)

    for rec in variants.to_dict(orient="records"):
        cleaned = clean_record(rec)
        cleaned["dataset"] = "variant"
        cleaned["is_original_variant"] = False
        records.append(cleaned)

    return records

@app.get("/issues/{variant_issue_id}/original")
async def get_original_by_variant(
    variant_issue_id: int = Path(..., description="Variant issue ID"),
):
    variant = df_variant[df_variant["issue_id"] == variant_issue_id]
    if variant.empty:
        raise HTTPException(status_code=404, detail=f"Variant issue ID {variant_issue_id} not found")

    original_id = variant.iloc[0]["original_issue_id"]
    original = df_original[df_original["issue_id"] == original_id]
    if original.empty:
        raise HTTPException(status_code=404, detail=f"Original issue ID {original_id} not found")

    record = clean_record(original.iloc[0].to_dict())
    record["dataset"] = "original"
    return record

@app.get("/series/")
async def list_series_titles(
    prefix: Optional[str] = Query(None, description="Filter series titles starting with this prefix"),
    limit: int = Query(50, description="Max number of series titles to return"),
):
    all_series = pd.concat([df_original["series_title"], df_variant["series_title"]]).dropna().unique()

    if prefix:
        filtered = [s for s in all_series if s.lower().startswith(prefix.lower())]
    else:
        filtered = list(all_series)

    return {"series_titles": filtered[:limit]}

@app.get("/creators/")
async def list_creators(
    prefix: Optional[str] = Query(None, description="Filter creators starting with this prefix"),
    limit: int = Query(50, description="Max number of creators to return"),
):
    creators_orig = df_original["creators"].dropna().unique()
    creators_var = df_variant["creators"].dropna().unique()

    all_creators = pd.Series(list(creators_orig) + list(creators_var)).unique()

    if prefix:
        filtered = [c for c in all_creators if c.lower().startswith(prefix.lower())]
    else:
        filtered = list(all_creators)

    return {"creators": filtered[:limit]}

@app.get("/stats/")
async def get_stats():
    return {
        "total_originals": len(df_original),
        "total_variants": len(df_variant),
        "total_issues": len(df_original) + len(df_variant),
        "series_count_originals": df_original["series_title"].nunique(),
        "series_count_variants": df_variant["series_title"].nunique(),
    }

import pandas as pd
import re
from rapidfuzz import fuzz

def parse_creators(creators_str):
    if pd.isna(creators_str) or not creators_str.strip():
        return {}

    entries = [e.strip() for e in creators_str.split(";") if e.strip()]
    creators_by_role = {}

    for entry in entries:
        entry = re.sub(r'\s*(\(\d+\)|\[\d+\])$', '', entry).strip()

        m = re.match(r'^([^:]+):\s*(.+)$', entry)
        if m:
            role = m.group(1).strip()
            names_str = m.group(2).strip()
            names = [n.strip() for n in names_str.split(",") if n.strip()]
            for name in names:
                creators_by_role.setdefault(role, []).append(name)
            continue

        m = re.match(r'^(.+?)\s*\(([^)]+)\)$', entry)
        if m:
            name, role = m.group(1).strip(), m.group(2).strip()
            creators_by_role.setdefault(role, []).append(name)
            continue

        creators_by_role.setdefault("Unknown", []).append(entry)

    return creators_by_role

def filter_story_creators(creators_by_role):
    if not creators_by_role:
        return {}

    filtered = {}
    for role, names in creators_by_role.items():
        role_lc = role.lower()
        if role_lc == "writer" or role_lc == "penciller":
            filtered[role] = names
    return filtered

def creators_to_set(creators_by_role):
    all_names = set()
    for names in creators_by_role.values():
        all_names.update([name.lower() for name in names])
    return all_names

from sklearn.metrics.pairwise import cosine_similarity

def get_summary_recommendations(issue_summary: str, issue_series_id: int, top_k=50):
    if not issue_summary or not issue_summary.strip():
        print("Empty summary input")
        return []

    if 'model' not in globals():
        from sentence_transformers import SentenceTransformer
        global model
        model = SentenceTransformer('all-MiniLM-L6-v2')

    issue_emb = model.encode([issue_summary], convert_to_tensor=False)

    sims = cosine_similarity(issue_emb, summary_embeddings)[0]

    sim_df = pd.DataFrame({
        "series_id": series_metadata["series_id"],
        "series_title": series_metadata["series_title"],
        "similarity": sims,
        "summary": series_metadata["summary"]
    })

    sim_df = sim_df[sim_df["series_id"] != issue_series_id]

    top_similar = sim_df.sort_values("similarity", ascending=False).head(top_k)

    results = []
    for _, row in top_similar.iterrows():
        results.append({
            "series_id": int(row["series_id"]),
            "title": row["series_title"],
            "similarity_score": float(row["similarity"]),
        })

    return results

@app.get("/issues/{issue_id}/recommended_series")
async def get_recommended_series(issue_id: int):
    issue = df_original[df_original["issue_id"] == issue_id]
    dataset = "original"
    if issue.empty:
        issue = df_variant[df_variant["issue_id"] == issue_id]
        dataset = "variant"
    if issue.empty:
        raise HTTPException(status_code=404, detail=f"Issue ID {issue_id} not found")

    issue = issue.iloc[0]
    df_all = pd.concat([df_original, df_variant], ignore_index=True)

    def cover_image_for_series(series_id):
        first_issue = df_all[df_all["series_id"] == series_id].sort_values("release_date").head(1)
        if not first_issue.empty and "image_url" in first_issue.columns:
            return first_issue.iloc[0]["image_url"]
        return None

    recommendations = {
        "sameCreators": [],
        "fromSummary": [],
        "titleSimilarity": []
    }

    #  1. Same Creators 
    issue_creators_parsed = parse_creators(issue.get("creators", ""))
    issue_story_creators = filter_story_creators(issue_creators_parsed)
    issue_creator_names_set = creators_to_set(issue_story_creators)

    if issue_creator_names_set:
        same_creator_df = df_all[
            (df_all["series_id"] != issue["series_id"]) &
            (df_all["creators"].notna()) &
            (df_all["creators"].str.lower() != "nan")
        ].copy()

        def creator_match_score(creators_str):
            other_parsed = parse_creators(creators_str)
            other_story_creators = filter_story_creators(other_parsed)
            other_names_set = creators_to_set(other_story_creators)
            common = issue_creator_names_set & other_names_set
            return len(common)

        same_creator_df["match_score"] = same_creator_df["creators"].apply(creator_match_score)
        same_creator_df = same_creator_df[same_creator_df["match_score"] > 0]
        same_creator_df = same_creator_df.sort_values(by="match_score", ascending=False)

        matched_series = same_creator_df[["series_id", "series_title", "match_score"]]
        matched_series = matched_series.drop_duplicates(subset=["series_id"])

        for sid, title, score in matched_series.values:
            recommendations["sameCreators"].append({
                "series_id": int(sid),
                "title": title,
                "image_url": cover_image_for_series(sid),
                "match_score": int(score)
            })

    else:
        print(f"No story creators found for issue_id={issue_id}")

    #  2. From Summary 
    print(f"Input summary for issue_id={issue_id} is: {issue['summary'][:100]}")
    if pd.notna(issue.get("summary")) and issue["summary"].strip():
        recommendations["fromSummary"] = get_summary_recommendations(issue["summary"], issue["series_id"])

    for rec in recommendations["fromSummary"]:
        rec["image_url"] = cover_image_for_series(rec["series_id"])

    if recommendations["fromSummary"]:
        df_from_summary = pd.DataFrame(recommendations["fromSummary"])
        df_from_summary = df_from_summary.drop_duplicates(subset=["series_id"], keep="first")
        recommendations["fromSummary"] = df_from_summary.to_dict(orient="records")

    #  3. Title Similarity with fuzzy scoring 
    if pd.notna(issue.get("series_title")) and issue["series_title"].strip():
        issue_title = str(issue["series_title"]).strip()
        
        candidates = df_all[df_all["series_id"] != issue["series_id"]].copy()

        def fuzzy_score(title):
            return fuzz.token_set_ratio(issue_title, title)

        candidates["fuzzy_score"] = candidates["series_title"].apply(fuzzy_score)

        candidates = candidates[candidates["fuzzy_score"] >= 50]

        candidates = candidates.sort_values(by="fuzzy_score", ascending=False)

        candidates = candidates.drop_duplicates(subset=["series_id"])

        top_candidates = candidates.head(50)

        for sid, title, score in top_candidates[["series_id", "series_title", "fuzzy_score"]].values:
            recommendations["titleSimilarity"].append({
                "series_id": int(sid),
                "title": title,
                "image_url": cover_image_for_series(sid),
                "match_score": int(score)
            })
            
    return recommendations
