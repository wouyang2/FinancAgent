from pathlib import Path
from normalizer import assign_role_visibility, validate_schema
import pandas as pd

def load_invoices(path):

    df = pd.read_csv(path)
    ar_df = df[df['type'] == 'AR'].copy().reset_index(drop=True) # revenue
    ap_df = df[df['type'] == 'AP'].copy().reset_index(drop=True) # bills

    for frame in [ar_df, ap_df]:
        frame['date'] = pd.to_datetime(frame['date']).dt.strftime('%Y-%m-%d')
        frame['month'] = pd.to_datetime(frame['date']).dt.strftime('%Y-%m')
        frame['year'] = pd.to_datetime(frame['date']).dt.year.astype(str)

    # Process AR
    ar_df['transaction_type'] = 'revenue'
    ar_df['gl_code'] = '8000'
    ar_df['gl_category'] = 'Accounts Receivable'
    ar_df['vendor'] = ar_df['vendor_or_customer']
    ar_df['description'] = ar_df.apply(
        lambda row: f"Revenue invoice of ${row['amount']:,.2f} "
                    f"from {row['vendor_or_customer']} "
                    f"in {row['month']}, status: {row['status']}",
        axis=1
    )
    ar_df['role_visibility'] = ar_df.apply(
        lambda row: assign_role_visibility('revenue', row['department']),
        axis=1
    )

    # Process AP
    ap_df['transaction_type'] = 'expense'
    ap_df['gl_code'] = '2000'
    ap_df['gl_category'] = 'Accounts Payable'
    ap_df['vendor'] = ap_df['vendor_or_customer']
    ap_df['description'] = ap_df.apply(
        lambda row: f"Invoice of ${row['amount']:,.2f} "
                    f"from vendor {row['vendor_or_customer']} "
                    f"for {row['department']} in {row['month']}, "
                    f"status: {row['status']}, due: {row.get('due_date', 'N/A')}",
        axis=1
    )
    ap_df['role_visibility'] = ap_df.apply(
        lambda row: assign_role_visibility('expense', row['department']),
        axis=1
    )

    ar_df['source'] = 'invoices'
    ap_df['source'] = 'invoices'

    combined = pd.concat([ar_df, ap_df]).reset_index(drop=True)

    combined = combined.drop(columns=[
        'type',
        'vendor_or_customer',
        'due_date',
        'paid_date',
        'invoice_id'
    ])


    clear_df = validate_schema(combined)
    print(f"✅ Invoice: {len(clear_df)} rows loaded.")
    return clear_df


if __name__ == "__main__":

    curr_dir = Path(__file__).parent
    file_path = curr_dir.parent.parent / "data/raw/invoice.csv"
    load_invoices(file_path)