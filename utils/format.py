# utils/format.py
def format_money(value: float) -> str:
    """Форматирует число: 1234567.89 → 1 234 567,89"""
    if value == 0:
        return "0,00"
    return f"{value:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")  # неразрывный пробел