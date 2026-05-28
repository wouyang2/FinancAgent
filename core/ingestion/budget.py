from pathlib import Path
import pandas as pd
from normalizer import assign_role_visibility, validate_schema

CATEGORY_TO_GL = {
    'Payroll & Benefits':       '6000',
    'Cloud Infrastructure':     '6100',
    'SaaS Tools & Subscriptions': '6200',
    'Sales & Marketing':        '6300',
    'Travel & Entertainment':   '6400',
    'Professional Services':    '6500',
    'Office & Facilities':      '6600',
    'R&D Expenses':             '6700',
}

def load_budget(path):
    df = pd.read_csv(path)

    df['date'] = pd.to_datetime(df['month'] + '-01').dt.strftime('%Y-%m-%d')
    df['gl_code'] = df['gl_category'].map(CATEGORY_TO_GL).fillna('9999')
    df['description'] = df.apply(lambda row: f"Budget allocation of ${row['budgeted_amount']:,.2f} "
                                            f"for {row['department']} department in {row['month']} "
                                            f"under {row['gl_category']} (GL {row['gl_code']})",axis=1)
    df['amount'] = df['budgeted_amount']
    df.drop(columns=['budgeted_amount'], inplace=True)

    df['transaction_type'] = 'budget'
    df['vendor'] = None
    df['source'] = 'budget'
    df['role_visibility'] = df.apply(lambda row: assign_role_visibility(row['transaction_type'], row['department']), axis=1)
    df['year'] = df['year'].astype(str)
    clean_df = validate_schema(df)

    print(f"✅ Budget: {len(clean_df)} rows loaded")

    print(clean_df.head())

    return clean_df

if __name__ == '__main__':
    curr_dir = Path(__file__).parent
    file_path = curr_dir.parent.parent / 'data/raw/budget.csv'

    load_budget(file_path)