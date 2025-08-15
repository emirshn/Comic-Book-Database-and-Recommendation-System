from sentence_transformers import SentenceTransformer
import pandas as pd
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df_original = pd.read_csv(os.path.join(BASE_DIR, "original_issues.csv"))
df_variant = pd.read_csv(os.path.join(BASE_DIR, "variant_issues.csv"))

df_all = pd.concat([df_original, df_variant], ignore_index=True)
df_all = df_all[df_all["summary"].notna()].reset_index(drop=True)

all_summaries = df_all["summary"].tolist()

model = SentenceTransformer('all-MiniLM-L6-v2')
print("Computing embeddings for all summaries...")
summary_embeddings = model.encode(all_summaries, convert_to_tensor=False, show_progress_bar=True)

np.save(os.path.join(BASE_DIR, "summary_embeddings.npy"), summary_embeddings)
df_all[["series_id", "series_title", "summary"]].to_csv(os.path.join(BASE_DIR, "series_metadata.csv"), index=False)

print("Embeddings and metadata saved.")
