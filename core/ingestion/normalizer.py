import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaError
from pandera.typing.pandas import Series
from requests_toolbelt.multipart.encoder import coerce_data


class UnifiedSchema(pa.DataFrameModel):

    date : Series[str]  # YYYY-MM-DD
    month : Series[str]  # YYYY-MM
    year : Series[str]  # YYYY
    department : Series[str]
    gl_code : Series[str]     # e.g. "6100"
    gl_category : Series[str]  # e.g. "Cloud Infrastructure"
    description : Series[str]  # natural language description
    transaction_type : Series[str]     # expense | revenue | payroll | budget
    amount : Series[float]  = pa.Field(ge=0)   # always positive
    vendor : Series[str] = pa.Field(nullable=True, coerce=True)
    source : Series[str]   # which file this came from
    role_visibility : Series[list] # which roles can see this record

def normalize_date(date: str):
    return pd.to_datetime(date, format = 'mixed')

def deriver_month_year(date_str) -> tuple:

    dt = normalize_date(date_str)
    month = dt.strftime('%Y-%m')
    year = dt.strftime('%Y')
    return month, year

def format_document(row):
    source = row.get('source', '')
    date = row.get('date', '')
    amount = f"${row['amount']:,.2f}"
    dept = row.get('department', '')

    if source == 'gl':
        return (f"{amount} {row['transaction_type']} on {row['description']} "
                f"by {dept} department in {row['month']}, "
                f"GL code {row['gl_code']} ({row['gl_category']}), "
                f"vendor: {row.get('vendor', 'N/A')}")

    elif source == 'payroll':
        return (f"{amount} payroll cost for {dept} department "
                f"in {row['month']}, covering {row.get('headcount', 'N/A')} employees, "
                f"GL code 6000 (Payroll & Benefits)")

    elif source == 'budget':
        return (f"{amount} budgeted for {dept} department "
                f"in {row['month']} under {row['gl_category']}, "
                f"GL code {row['gl_code']}")

    elif source == 'invoices':
        inv_type = 'revenue from' if row['transaction_type'] == 'revenue' else 'invoice from'
        return (f"{amount} {inv_type} {row.get('vendor', 'customer')} "
                f"in {row['month']}, status: {row.get('status', 'N/A')}, "
                f"department: {dept}")

    else:
        return (f"{amount} {row.get('transaction_type', '')} "
                f"for {dept} in {row['month']}")

def assign_role_visibility(transaction_type, department):
    if transaction_type == 'payroll':
        return ['CEO', 'CFO', 'Finance Analyst']
    elif transaction_type == 'expense':
        return ['CEO', 'CFO', 'Finance Analyst', 'Department Head', department]
    elif transaction_type == 'budget':
        return ['CEO', 'CFO', 'Finance Analyst', 'Department Head', department]
    elif transaction_type == 'revenue':
        return ['CEO', 'CFO', 'Finance Analyst']
    else:
        return 'CEO,CFO'

def validate_schema(df):

    try:
        clean_df = UnifiedSchema.validate(df)
        return clean_df

    except SchemaError as e:
        print(e)
        raise



if __name__ == '__main__':
    print(normalize_date('2024-01-01'))
    print(deriver_month_year('2024-01-01'))