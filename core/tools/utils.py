import pandas as pd
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Load unified ledger
df = pd.read_csv('data/processed/unified_ledger.csv')

# Separate views for convenience
expense_df = df[df['transaction_type'].isin(['expense', 'payroll'])]
budget_df  = df[df['transaction_type'] == 'budget']
revenue_df = df[df['transaction_type'] == 'revenue']

# ChromaDB
embedding_func = OpenAIEmbeddings()
vs_dir = Path(__file__).parent.parent / 'chroma_db'
vs = Chroma(collection_name='company_transactions', embedding_function=embedding_func, persist_directory=str(vs_dir))

def apply_filters(df, departments, gl_categories, user_role, user_department):

    # Role-based access — Department Head sees only their dept
    if user_role == 'Department Head':
        df = df[df['department'] == user_department]
    else:
        if departments:
            df = df[df['department'].isin(departments)]

    if gl_categories:
        df = df[df['gl_category'].isin(gl_categories)]

    return df