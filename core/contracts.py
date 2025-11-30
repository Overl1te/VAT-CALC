from dataclasses import dataclass
from core.config import get_current_vat, get_future_vat

@dataclass
class Contract:
    name: str = "Новый договор"
    number: str = ""                    # № договора
    total_cost_with_vat: float = 0.0    # Полная сумма договора
    remaining_cost: float = 0.0         # Факт на 31.12.2025 (то, что будет облагаться новым НДС)
    current_vat_rate = 1 + get_current_vat() / 100
    future_vat_rate = 1 + get_future_vat() / 100

    def get_without(self) -> float:
        return self.get_difference() / self.current_vat_rate

    def getVATfut(self) -> float:
        return self.get_without() * (self.future_vat_rate - 1)

    def getDiffWith(self) -> float:
        return self.get_without() + self.getVATfut()

    def get_difference(self) -> float:
        return self.total_cost_with_vat - self.remaining_cost

    def getVAT(self) -> float:
        return self.get_difference() - self.get_without()

    def get_vat_difference(self) -> float:
        difference = self.getVATfut() - self.getVAT()
        return round(difference, 2)