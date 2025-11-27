def validate_input_df(df):
    required = ['Название', 'Базовая стоимость', 'Год начала']
    missing = [c for c in required if c not in df.columns]
    return missing
