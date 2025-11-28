import pickle
import zlib
import shutil
from datetime import datetime
from pathlib import Path
from core.config import PROJECTS_DIR, SUPPORTED_EXTENSIONS

class VATProject:
    def __init__(self, name=None):
        self.name = name or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.created = datetime.now()
        self.modified = datetime.now()
        self.contracts = []  # Список контрактов в проекте
        self.manual_contracts = []  # Новый список для ручных контрактов
        self.settings = {
            'current_vat': 20.0,
            'future_vat': 22.0,
            'years': 5
        }
        self.results = None
    
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
        """Добавить контракт в проект"""
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
        
        contract_data = {
            'name': contract_name or original_file.stem,
            'file_path': str(contract_file),
            'original_filename': original_file.name,
            'added_date': datetime.now(),
            'original_path': file_path
        }
        
        self.contracts.append(contract_data)
        self.modified = datetime.now()
        return contract_data
    
    def add_manual_contract(self, contract_data):
        """Добавить ручной контракт"""
        from contracts import Contract
        
        # Создаем объект контракта из данных
        contract = Contract(
            name=contract_data['name'],
            total_cost_with_vat=contract_data['total_cost_with_vat'],
            start_year=contract_data['start_year'],
            duration=contract_data.get('duration', 1)
        )
        
        # Устанавливаем текущий НДС
        contract.current_vat_rate = contract_data.get('current_vat_rate', self.settings['current_vat'])
        
        # Добавляем задачи
        for task_data in contract_data.get('tasks', []):
            task = contract.add_task(
                name=task_data['name'],
                year=task_data['year'],
                cost_with_vat=task_data['cost_with_vat']
            )
            task.completion = task_data.get('completion', 0)
            task.is_completed = task_data.get('is_completed', False)
        
        # Добавляем изменения НДС
        for vat_change_data in contract_data.get('vat_changes', []):
            contract.add_vat_change(
                year=vat_change_data['year'],
                new_rate=vat_change_data['new_rate']
            )
        
        self.manual_contracts.append(contract)
        self.modified = datetime.now()
        return contract
    
    def update_manual_contract(self, old_name, contract_data):
        """Обновить ручной контракт"""
        contract = next((c for c in self.manual_contracts if c.name == old_name), None)
        if not contract:
            return self.add_manual_contract(contract_data)
        
        # Обновляем основные данные
        contract.name = contract_data['name']
        contract.total_cost_with_vat = contract_data['total_cost_with_vat']
        contract.start_year = contract_data['start_year']
        contract.duration = contract_data.get('duration', 1)
        contract.current_vat_rate = contract_data.get('current_vat_rate', self.settings['current_vat'])
        
        # Обновляем задачи
        contract.tasks = []
        for task_data in contract_data.get('tasks', []):
            task = contract.add_task(
                name=task_data['name'],
                year=task_data['year'],
                cost_with_vat=task_data['cost_with_vat']
            )
            task.completion = task_data.get('completion', 0)
            task.is_completed = task_data.get('is_completed', False)
        
        # Обновляем изменения НДС
        contract.vat_changes = []
        for vat_change_data in contract_data.get('vat_changes', []):
            contract.add_vat_change(
                year=vat_change_data['year'],
                new_rate=vat_change_data['new_rate']
            )
        
        self.modified = datetime.now()
        return contract
    
    def remove_manual_contract(self, contract_name):
        """Удалить ручной контракт"""
        self.manual_contracts = [c for c in self.manual_contracts if c.name != contract_name]
        self.modified = datetime.now()
    
    def get_manual_contract(self, contract_name):
        """Получить ручной контракт по имени"""
        return next((c for c in self.manual_contracts if c.name == contract_name), None)
    
    def get_all_contracts_data(self):
        """Получить данные всех контрактов (объединяем файловые и ручные)"""
        all_data = []
        
        # Данные из файловых контрактов
        for contract in self.contracts:
            try:
                data = self.get_contract_data(contract['name'])
                for row in data:
                    if isinstance(row, dict):
                        row['Имя_контракта'] = contract['name']
                        row['Тип_контракта'] = 'file'
                    elif isinstance(row, list) and len(row) > 0:
                        row.insert(0, contract['name'])
                        row.insert(1, 'file')
                all_data.extend(data)
            except Exception as e:
                print(f"Ошибка загрузки контракта {contract['name']}: {e}")
        
        # Данные из ручных контрактов
        for contract in self.manual_contracts:
            try:
                contract_data = self.convert_manual_contract_to_dict(contract)
                all_data.extend(contract_data)
            except Exception as e:
                print(f"Ошибка конвертации ручного контракта {contract.name}: {e}")
        
        return all_data
    
    def convert_manual_contract_to_dict(self, contract):
        """Конвертировать ручной контракт в словарь для расчетов"""
        data = []
        yearly_breakdown = contract.calculate_yearly_breakdown()
        
        for year_data in yearly_breakdown:
            data.append({
                'Имя_контракта': contract.name,
                'Тип_контракта': 'manual',
                'Название': contract.name,
                'Базовая стоимость': contract.base_cost,
                'Год начала': contract.start_year,
                'Год': year_data['year'],
                'Ставка НДС': year_data['vat_rate'],
                'Стоимость_с_НДС': year_data['planned_cost'],
                'Выполнено': year_data['completed_cost'],
                'Остаток': year_data['remaining_cost'],
                'Влияние_НДС': year_data['vat_impact'],
                'Длительность': contract.duration
            })
        
        return data

    def remove_contract(self, contract_name):
        """Удалить контракт из проекта"""
        contract = next((c for c in self.contracts if c['name'] == contract_name), None)
        if not contract:
            raise ValueError(f"Контракт не найден: {contract_name}")
        
        # Удаляем файл
        contract_file = Path(contract['file_path'])
        if contract_file.exists():
            contract_file.unlink()
        
        # Удаляем из списка
        self.contracts = [c for c in self.contracts if c['name'] != contract_name]
        self.modified = datetime.now()
        
        # Если контрактов не осталось, обновляем результаты
        if not self.contracts:
            self.results = None
    
    def get_contract_data(self, contract_name):
        """Получить данные контракта"""
        from utils.excel_processor import read_input_excel
        
        contract = next((c for c in self.contracts if c['name'] == contract_name), None)
        if not contract:
            raise ValueError(f"Контракт не найден: {contract_name}")
        
        return read_input_excel(contract['file_path'])
    
    def get_all_contracts_data(self):
        """Получить данные всех контрактов"""
        all_data = []
        for contract in self.contracts:
            try:
                data = self.get_contract_data(contract['name'])
                # Добавляем имя контракта к данным
                for row in data:
                    if isinstance(row, dict):
                        row['Имя_контракта'] = contract['name']
                    elif isinstance(row, list) and len(row) > 0:
                        # Добавляем имя контракта как первый элемент
                        row.insert(0, contract['name'])
                all_data.extend(data)
            except Exception as e:
                print(f"Ошибка загрузки контракта {contract['name']}: {e}")
        return all_data
    
    def calculate_results(self):
        """Пересчитать результаты проекта"""
        from core.calculator import project_costs_vectorized
        
        all_data = self.get_all_contracts_data()
        if not all_data:
            self.results = []
            return []
        
        self.results = project_costs_vectorized(
            all_data,
            self.settings['current_vat'],
            self.settings['future_vat'],
            self.settings['years']
        )
        self.modified = datetime.now()
        return self.results
    
    def save(self):
        """Сохранить проект (обновленная версия)"""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Конвертируем ручные контракты в сериализуемый формат
        manual_contracts_data = []
        for contract in self.manual_contracts:
            contract_data = {
                'name': contract.name,
                'total_cost_with_vat': contract.total_cost_with_vat,
                'start_year': contract.start_year,
                'duration': contract.duration,
                'current_vat_rate': contract.current_vat_rate,
                'tasks': [],
                'vat_changes': []
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
        
        data_to_save = {
            'name': self.name,
            'created': self.created,
            'modified': self.modified,
            'contracts': self.contracts,
            'manual_contracts': manual_contracts_data,  # Сохраняем ручные контракты
            'settings': self.settings,
            'results': self.results
        }
        
        compressed_data = zlib.compress(pickle.dumps(data_to_save))
        with open(self.project_file, 'wb') as f:
            f.write(compressed_data)
        
        return self.project_file
    
    @classmethod
    def load(cls, project_path):
        """Загрузить проект (обновленная версия)"""
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
        project.contracts = data.get('contracts', [])
        project.settings = data.get('settings', {})
        project.results = data.get('results')
        
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