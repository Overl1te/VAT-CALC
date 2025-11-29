from datetime import datetime
from dataclasses import dataclass
from core.config import get_current_vat, get_future_vat

@dataclass
class Contract:
    name: str = "Новый договор"
    number: str = ""                    # № договора
    total_cost_with_vat: float = 0.0    # Полная сумма договора
    remaining_cost: float = 0.0         # Остаток на 31.12.2025 (то, что будет облагаться новым НДС)
    start_year: int = None              # Год начала

    def __post_init__(self):
        if self.start_year is None:
            self.start_year = datetime.now().year

    def get_vat_difference(self) -> float:
        if self.remaining_cost <= 0:
            return 0.0
        
        # Получаем актуальные ставки НДС из конфига
        current_vat_rate = 1 + get_current_vat() / 100
        future_vat_rate = 1 + get_future_vat() / 100
        
        # Формула: remaining_cost * (1/current_vat_rate - 1/future_vat_rate)
        difference = self.remaining_cost * (1/current_vat_rate - 1/future_vat_rate)
        return round(difference, 2)