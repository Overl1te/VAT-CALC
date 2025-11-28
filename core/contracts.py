from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ContractTask:
    """Задача контракта"""
    name: str
    year: int
    cost_with_vat: float  # Стоимость с НДС
    completion: float = 0.0  # Процент выполнения (0-100)
    is_completed: bool = False
    
    @property
    def completed_cost(self) -> float:
        """Выполненная стоимость"""
        return self.cost_with_vat * (self.completion / 100.0)

@dataclass
class VATChange:
    """Изменение ставки НДС"""
    year: int
    new_rate: float

class Contract:
    def __init__(self, name: str, total_cost_with_vat: float, start_year: int, duration: int = 1, current_vat_rate: float = 20.0):
        self.name = name
        self.total_cost_with_vat = total_cost_with_vat  # Полная стоимость с НДС
        self.start_year = start_year
        self.duration = duration
        self.tasks: List[ContractTask] = []
        self.vat_changes: List[VATChange] = []
        self.current_vat_rate = current_vat_rate  # Текущий НДС (может быть из проекта)
        
    @property
    def end_year(self) -> int:
        return self.start_year + self.duration - 1
    
    @property
    def base_cost(self) -> float:
        """Базовая стоимость без НДС"""
        return self.total_cost_with_vat / (1 + self.current_vat_rate / 100.0)
    
    @property
    def vat_amount(self) -> float:
        """Сумма НДС в контракте"""
        return self.total_cost_with_vat - self.base_cost
    
    def add_task(self, name: str, year: int, cost_with_vat: float) -> ContractTask:
        task = ContractTask(name=name, year=year, cost_with_vat=cost_with_vat)
        self.tasks.append(task)
        return task
    
    def add_vat_change(self, year: int, new_rate: float):
        self.vat_changes.append(VATChange(year=year, new_rate=new_rate))
        self.vat_changes.sort(key=lambda x: x.year)
    
    def get_vat_rate_for_year(self, year: int) -> float:
        rate = self.current_vat_rate
        for change in self.vat_changes:
            if year >= change.year:
                rate = change.new_rate
        return rate
    
    def get_tasks_for_year(self, year: int) -> List[ContractTask]:
        return [task for task in self.tasks if task.year == year]
    
    def calculate_remaining_cost(self, up_to_year: Optional[int] = None) -> float:
        if up_to_year is None:
            up_to_year = datetime.now().year - 1  # До конца текущего года (предполагаем изменение в следующем)
        
        total_completed = sum(task.completed_cost for task in self.tasks if task.year <= up_to_year)
        return self.total_cost_with_vat - total_completed
    
    def get_vat_difference(self, target_year: Optional[int] = None) -> float:
        """Вычислить разницу НДС (основной метод, возвращает additional_cost)"""
        if target_year is None:
            target_year = datetime.now().year  # Год изменения
        
        # Оставшаяся стоимость с НДС на начало target_year
        remaining_cost = self.calculate_remaining_cost(target_year - 1)
        
        if remaining_cost <= 0:
            return 0.0
        
        old_vat_rate = self.get_vat_rate_for_year(target_year - 1)
        new_vat_rate = self.get_vat_rate_for_year(target_year)
        
        if old_vat_rate == new_vat_rate:
            return 0.0
        
        remaining_base = remaining_cost / (1 + old_vat_rate / 100.0)
        old_vat_amount = remaining_base * (old_vat_rate / 100.0)
        new_vat_amount = remaining_base * (new_vat_rate / 100.0)
        
        vat_difference = new_vat_amount - old_vat_amount  # Разница (дополнительная стоимость)
        
        return round(vat_difference, 2)  # Округляем до копеек
    
    def calculate_vat_impact(self, target_year: int) -> Dict:
        """Старый метод для детализации, но теперь возвращаем dict с разницей"""
        diff = self.get_vat_difference(target_year)
        return {
            'year': target_year,
            'additional_cost': diff,
            # ... (остальные поля, если нужны для UI)
        }

    def calculate_yearly_breakdown(self) -> List[Dict]:
        """Получить детализацию по годам"""
        result = []
        
        for year in range(self.start_year, self.end_year + 1):
            year_tasks = self.get_tasks_for_year(year)
            planned_cost = sum(task.cost_with_vat for task in year_tasks)
            completed_cost = sum(task.completed_cost for task in year_tasks)
            
            vat_impact = self.calculate_vat_impact(year)
            
            result.append({
                'year': year,
                'planned_cost': planned_cost,
                'completed_cost': completed_cost,
                'remaining_cost': self.calculate_remaining_cost(year),
                'vat_rate': self.get_vat_rate_for_year(year),
                'vat_impact': vat_impact['additional_cost'],
                'tasks_count': len(year_tasks),
                'completion_percentage': (completed_cost / planned_cost * 100) if planned_cost > 0 else 0
            })
        
        return result