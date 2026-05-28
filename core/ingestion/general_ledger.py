import pandas as pd
from normalizer import normalize_date, deriver_month_year, assign_role_visibility, validate_schema
from pathlib import Path

def load_gl(path):

    df = pd.read_csv(path)
    df_filtered = df[df['transaction_type'] == 'expense'].copy()
    df_filtered = df_filtered.reset_index(drop=True)
    df_filtered = df_filtered[df_filtered['amount'] != 0]
    df_filtered.dropna(inplace=True, subset=['amount'])


    df_filtered['date'] = (df_filtered['date'].apply(normalize_date)).dt.strftime('%Y-%m-%d')

    df_filtered['month'], df_filtered['year'] = zip(*df_filtered['date'].apply(deriver_month_year))

    df_filtered['source'] = 'gl'
    df_filtered['role_visibility'] = df_filtered.apply(lambda row: assign_role_visibility(row['transaction_type'], row['department']),
    axis=1)

    df_filtered['gl_code'] = df_filtered['gl_code'].astype(str)

    df_filtered = validate_schema(df_filtered)

    print(df_filtered.shape)

    return df_filtered


if __name__ == '__main__':
    curr_dir = Path(__file__).parent
    path = curr_dir.parent.parent / "data/raw/general_ledger.csv"
    df = load_gl(path)
    print(df.head())