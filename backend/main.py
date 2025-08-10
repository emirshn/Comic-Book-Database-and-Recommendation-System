from fastapi import FastAPI, Query, HTTPException, Path
from typing import Optional
import pandas as pd
import math
import os

app = FastAPI(title="Marvel Comics Issues API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df_original = pd.read_csv(os.path.join(BASE_DIR, "original_issues.csv"))
df_variant = pd.read_csv(os.path.join(BASE_DIR, "variant_issues.csv"))

for df in [df_original, df_variant]:
    df["release_date"] = pd.to_datetime(df["release_date"], errors='coerce')

# Add explicit is_variant flag to original dataset (False)
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

    # Add original issue first, mark it as original_variant for frontend use
    original_rec = clean_record(original.iloc[0].to_dict())
    original_rec["dataset"] = "original"
    original_rec["is_original_variant"] = True  # custom flag for frontend
    records.append(original_rec)

    # Add variants, mark as not original_variant
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

