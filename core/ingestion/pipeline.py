"""
pipeline.py
───────────
Orchestrates all four ingestion loaders, concatenates into a unified
dataframe, saves to processed/, and indexes into ChromaDB.
"""

import os
import pandas as pd
from pathlib import Path

from general_ledger import load_gl
from payroll import load_payroll
from budget import load_budget
from invoices import load_invoices
from normalizer import format_document

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

import dotenv
dotenv.load_dotenv()


def run_pipeline(data_dir: Path, output_dir: Path, persist_dir: Path):

    print("🚀 Starting TechFlow Inc. ingestion pipeline...\n")

    # ── Load all sources ──────────────────────────────────────────────────────
    gl_df      = load_gl(data_dir / 'general_ledger.csv')
    payroll_df = load_payroll(data_dir / 'payroll.csv')
    budget_df  = load_budget(data_dir / 'budget.csv')
    invoice_df = load_invoices(data_dir / 'invoice.csv')

    # ── Concatenate into unified ledger ───────────────────────────────────────
    unified = pd.concat(
        [gl_df, payroll_df, budget_df, invoice_df],
        ignore_index=True
    )

    print(f"\n📊 Unified ledger: {len(unified)} total rows")
    print(f"   Sources: {unified['source'].value_counts().to_dict()}")
    print(f"   Transaction types: {unified['transaction_type'].value_counts().to_dict()}")
    print(f"   Date range: {unified['date'].min()} → {unified['date'].max()}")

    # ── Save unified CSV ──────────────────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'unified_ledger.csv'
    unified.to_csv(output_path, index=False)
    print(f"\n✅ Saved unified ledger to: {output_path}")

    # ── Build ChromaDB documents ──────────────────────────────────────────────
    documents   = [format_document(row) for row in unified.to_dict('records')]
    ids         = [f"txn_{i}" for i in range(len(unified))]

    # ChromaDB metadata — all fields except role_visibility list
    metadatas = []
    for _, row in unified.iterrows():
        metadatas.append({
            'date':             str(row['date']),
            'month':            str(row['month']),
            'year':             str(row['year']),
            'department':       str(row['department']),
            'gl_code':          str(row['gl_code']),
            'gl_category':      str(row['gl_category']),
            'transaction_type': str(row['transaction_type']),
            'amount':           float(row['amount']),
            'source':           str(row['source']),
            'vendor':           str(row['vendor']) if pd.notna(row['vendor']) else '',
            'role_visibility':  str(row['role_visibility']),  # comma-separated string
        })

    # ── Index into ChromaDB ───────────────────────────────────────────────────
    print("\n🔍 Indexing into ChromaDB...")

    embed = OpenAIEmbeddings(model='text-embedding-3-small')

    vs = Chroma(
        collection_name='company_transactions',
        embedding_function=embed,
        persist_directory=str(persist_dir)
    )

    # Reset collection to avoid duplicate IDs on re-run
    vs.reset_collection()

    BATCH_SIZE = 1000
    total = len(documents)

    for i in range(0, total, BATCH_SIZE):

        batch_docs = documents[i:min(i+BATCH_SIZE, total)]
        batch_metadatas = metadatas[i:min(i+BATCH_SIZE, total)]
        batch_ids = ids[i:min(i+BATCH_SIZE, total)]


        vs.add_texts(
            texts=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

        print(f"   Indexed batch {i // BATCH_SIZE + 1}/{(total + BATCH_SIZE - 1) // BATCH_SIZE} "
              f"({min(i + BATCH_SIZE, total)}/{total} documents)")

    print(f"✅ Indexed {len(documents)} documents into ChromaDB")
    print(f"   Collection: company_transactions")
    print(f"   Persist dir: {persist_dir}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "─" * 50)
    print("✅ Pipeline complete")
    print(f"   Total rows:    {len(unified):,}")
    print(f"   Total spend:   ${unified[unified['transaction_type'].isin(['expense', 'payroll'])]['amount'].sum():,.0f}")
    print(f"   Total revenue: ${unified[unified['transaction_type'] == 'revenue']['amount'].sum():,.0f}")
    print(f"   Total budgeted: ${unified[unified['transaction_type'] == 'budget']['amount'].sum():,.0f}")

    return unified


if __name__ == '__main__':
    curr_dir = Path(__file__).parent
    root_dir = curr_dir.parent.parent

    run_pipeline(
        data_dir   = root_dir / 'data/raw',
        output_dir = root_dir / 'data/processed',
        persist_dir= root_dir / 'chroma_db'
    )