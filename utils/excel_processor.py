import pandas as pd

def read_input_excel(path):
    df = pd.read_excel(path, engine='openpyxl')
    return df

def write_output_excel(df, path):
    df.to_excel(path, index=False, engine='openpyxl')
