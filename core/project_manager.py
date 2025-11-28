import pickle
import zlib
import shutil
from datetime import datetime
from pathlib import Path
from core.config import PROJECTS_DIR, SUPPORTED_EXTENSIONS
from core.contracts import Contract, ContractTask, VATChange

class VATProject:
    def __init__(self, name=None):
        self.name = name or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.created = datetime.now()
        self.modified = datetime.now()
        self.contracts = []  # Файловые контракты (объекты Contract)
        self.manual_contracts = []  # Ручные контракты (объекты Contract)
        self.settings = {
            'current_vat': 20.0,
            'future_vat': 22.0,
            'years': 5  # Оставляем, но не используем для расчёта
        }
        self.total_vat_difference = 0.0  # Новая: сумма разниц
    
    @property
    def folder_name(self):
        """Имя папки проекта (безопасное для файловой системы)"""
        # Заменяем недопустимые символы
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in self.name)
        return safe_name.strip()
    
    @property
    def project_dir(self):
        """Директория проекта"""
        return PROJECTS_DIR / self.folder_name
    
    @property
    def contracts_dir(self):
        """Директория с контрактами проекта"""
        return self.project_dir / "contracts"
    
    @property
    def project_file(self):
        """Файл проекта"""
        return self.project_dir / "project.vat"
    
    def rename_project(self, new_name):
        """Переименовать проект (с перемещением папки)"""
        if new_name == self.name:
            return
        
        old_dir = self.project_dir
        self.name = new_name
        new_dir = self.project_dir
        
        if old_dir.exists() and old_dir != new_dir:
            # Перемещаем папку если она существует и имя изменилось
            try:
                shutil.move(str(old_dir), str(new_dir))
                # Обновляем пути контрактов
                for contract in self.contracts:
                    old_contract_path = Path(contract['file_path'])
                    new_contract_path = new_dir / "contracts" / old_contract_path.name
                    contract['file_path'] = str(new_contract_path)
            except Exception as e:
                print(f"Ошибка перемещения папки проекта: {e}")
                # Если не удалось переместить, создаем новую папку
                self.project_dir.mkdir(parents=True, exist_ok=True)
    
    def add_contract(self, file_path, contract_name=None):
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Создаем директорию проекта и контрактов
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        original_file = Path(file_path)
        counter = 1
        new_filename = original_file.name
        while (self.contracts_dir / new_filename).exists():
            name_parts = original_file.stem, original_file.suffix
            new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
            counter += 1
        
        # Копируем файл в проект
        contract_file = self.contracts_dir / new_filename
        shutil.copy2(file_path, contract_file)
        
        # Парсим total_cost из файла
        from utils.excel_processor import read_input_excel_simple
        data = read_input_excel_simple(str(contract_file))
        total_cost = sum(float(row[1]) if len(row) > 1 and row[1] else 0 for row in data[1:])  # Сумма базовых стоимостей
        
        # Создаём Contract
        contract = Contract(
            contract_name or original_file.stem,
            total_cost,
            datetime.now().year,
            current_vat_rate=self.settings['current_vat']
        )
        
        self.contracts.append(contract)
        self.modified = datetime.now()
        return contract
    
    def add_manual_contract(self, contract_data):
        contract = Contract(
            name=contract_data['name'],
            total_cost_with_vat=contract_data['total_cost_with_vat'],
            start_year=contract_data['start_year'],
            duration=contract_data.get('duration', 1),
            current_vat_rate=self.settings.get('current_vat', 20.0)  # Дефолт из проекта
        )
        # Добавляем задачи и vat_changes из data
        for task_data in contract_data.get('tasks', []):
            task = contract.add_task(task_data['name'], task_data['year'], task_data['cost_with_vat'])
            task.completion = task_data.get('completion', 0.0)
            task.is_completed = task_data.get('is_completed', False)
        for vat_change in contract_data.get('vat_changes', []):
            contract.add_vat_change(vat_change['year'], vat_change['new_rate'])
        self.manual_contracts.append(contract)
        self.modified = datetime.now()
    
    def remove_manual_contract(self, contract_name):
        self.manual_contracts = [c for c in self.manual_contracts if c.name != contract_name]
        self.modified = datetime.now()
    
    def calculate_total_vat_difference(self):
        """Суммировать разницы от всех контрактов"""
        total = 0.0
        all_contracts = self.contracts + self.manual_contracts  # Объединяем
        for contract in all_contracts:
            total += contract.get_vat_difference()
        self.total_vat_difference = round(total, 2)
        return self.total_vat_difference
    
    def save(self):
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        manual_contracts_data = []
        for contract in self.manual_contracts:  # Из объектов в dict для pickle
            contract_data = {
                'name': contract.name,
                'total_cost_with_vat': contract.total_cost_with_vat,
                'start_year': contract.start_year,
                'duration': contract.duration,
                'current_vat_rate': contract.current_vat_rate,
                'tasks': [],  # Сериализуем задачи
                'vat_changes': []  # Сериализуем изменения
            }
            for task in contract.tasks:
                contract_data['tasks'].append({
                    'name': task.name,
                    'year': task.year,
                    'cost_with_vat': task.cost_with_vat,
                    'completion': task.completion,
                    'is_completed': task.is_completed
                })
            for vat_change in contract.vat_changes:
                contract_data['vat_changes'].append({
                    'year': vat_change.year,
                    'new_rate': vat_change.new_rate
                })
            manual_contracts_data.append(contract_data)
        
        contracts_data = []
        for contract in self.contracts:
            contract_data = {
                'name': contract.name,
                'total_cost_with_vat': contract.total_cost_with_vat,
                'start_year': contract.start_year,
                'duration': contract.duration,
                'current_vat_rate': contract.current_vat_rate,
                'tasks': [ {
                    'name': t.name,
                    'year': t.year,
                    'cost_with_vat': t.cost_with_vat,
                    'completion': t.completion,
                    'is_completed': t.is_completed
                } for t in contract.tasks ],
                'vat_changes': [ {
                    'year': v.year,
                    'new_rate': v.new_rate
                } for v in contract.vat_changes ]
            }
            contracts_data.append(contract_data)
        
        data_to_save = {
            'name': self.name,
            'created': self.created,
            'modified': self.modified,
            'contracts': contracts_data,
            'manual_contracts': manual_contracts_data,
            'settings': self.settings,
            'total_vat_difference': self.total_vat_difference
        }
        
        compressed_data = zlib.compress(pickle.dumps(data_to_save))
        with open(self.project_file, 'wb') as f:
            f.write(compressed_data)
        
        return self.project_file
    
    @classmethod
    def load(cls, project_path):
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        with open(project_path, 'rb') as f:
            compressed_data = f.read()
        
        data = pickle.loads(zlib.decompress(compressed_data))
        
        project_folder = project_path.parent.name
        project_name = data.get('name', project_folder)
        
        project = cls(project_name)
        project.created = data['created']
        project.modified = data['modified']
        project.settings = data.get('settings', {})
        project.total_vat_difference = data.get('total_vat_difference', 0.0)
        
        # Загружаем файловые контракты
        for contract_data in data.get('contracts', []):
            project.add_manual_contract(contract_data)  # Используем add_manual_contract для восстановления, но добавляем в self.contracts
            project.contracts.append(project.manual_contracts.pop())  # Хак, чтобы добавить в contracts
        
        # Загружаем ручные контракты
        manual_contracts_data = data.get('manual_contracts', [])
        for contract_data in manual_contracts_data:
            project.add_manual_contract(contract_data)
        
        return project
    
    @classmethod
    def list_projects(cls):
        """Список всех проектов"""
        projects = []
        for project_file in PROJECTS_DIR.glob("*/project.vat"):
            try:
                project = cls.load(project_file)
                projects.append(project)
            except Exception as e:
                print(f"Ошибка загрузки проекта {project_file}: {e}")
                continue
        return sorted(projects, key=lambda x: x.modified, reverse=True)
class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.projects = VATProject.list_projects()
    
    def create_project_in_memory(self, name):
        """Создать проект в памяти без сохранения на диск"""
        project = VATProject(name)
        return project
    
    def create_project(self, name):
        """Создать новый проект и сохранить на диск"""
        # Генерируем уникальное имя если нужно
        if not name or name.strip() == "":
            name = f"Проект_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Проверяем уникальность имени
        existing_names = [p.name for p in self.projects]
        counter = 1
        original_name = name
        while name in existing_names:
            name = f"{original_name}_{counter}"
            counter += 1
        
        project = VATProject(name)
        project.save()
        
        self.current_project = project
        self.projects.insert(0, project)
        return project
    
    def load_project(self, project):
        """Загрузить проект"""
        # Перезагружаем проект из файла
        reloaded_project = VATProject.load(project.project_file)
        self.current_project = reloaded_project
        return reloaded_project
    
    def delete_project(self, project):
        """Удалить проект (полностью с директорией)"""
        if project.project_dir.exists():
            shutil.rmtree(project.project_dir)
        
        if self.current_project == project:
            self.current_project = None
        
        if project in self.projects:
            self.projects.remove(project)