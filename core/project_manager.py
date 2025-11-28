import pickle
import zlib
import shutil
from datetime import datetime
from pathlib import Path
from core.config import PROJECTS_DIR, SUPPORTED_EXTENSIONS

class VATProject:
    def __init__(self, name=None, folder=None):
        self.name = name or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.folder = folder or self.name
        self.created = datetime.now()
        self.modified = datetime.now()
        self.contracts = []  # Список контрактов в проекте
        self.settings = {
            'current_vat': 20.0,
            'future_vat': 22.0,
            'years': 5
        }
        self.results = None  # Кэш результатов
    
    @property
    def project_dir(self):
        """Директория проекта"""
        return PROJECTS_DIR / self.folder
    
    @property
    def contracts_dir(self):
        """Директория с контрактами проекта"""
        return self.project_dir / "contracts"
    
    @property
    def project_file(self):
        """Файл проекта"""
        return self.project_dir / "project.vat"
    
    def add_contract(self, file_path, contract_name=None):
        """Добавить контракт в проект"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Создаем директорию контрактов
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл в проект
        contract_file = self.contracts_dir / Path(file_path).name
        shutil.copy2(file_path, contract_file)
        
        contract_data = {
            'name': contract_name or Path(file_path).stem,
            'file_path': str(contract_file),
            'added_date': datetime.now(),
            'original_path': file_path
        }
        
        self.contracts.append(contract_data)
        self.modified = datetime.now()
        return contract_data
    
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
        """Сохранить проект"""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        data_to_save = {
            'name': self.name,
            'folder': self.folder,
            'created': self.created,
            'modified': self.modified,
            'contracts': self.contracts,
            'settings': self.settings,
            'results': self.results
        }
        
        compressed_data = zlib.compress(pickle.dumps(data_to_save))
        with open(self.project_file, 'wb') as f:
            f.write(compressed_data)
        
        return self.project_file
    
    @classmethod
    def load(cls, project_path):
        """Загрузить проект"""
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        with open(project_path, 'rb') as f:
            compressed_data = f.read()
        
        data = pickle.loads(zlib.decompress(compressed_data))
        
        project = cls(data['name'], data.get('folder', data['name']))
        project.created = data['created']
        project.modified = data['modified']
        project.contracts = data.get('contracts', [])
        project.settings = data.get('settings', {})
        project.results = data.get('results')
        
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
    
    def create_project(self, name, initial_contracts=None):
        """Создать новый проект"""
        project = VATProject(name)
        
        if initial_contracts:
            for contract in initial_contracts:
                project.add_contract(contract)
        
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
        
        self.projects.remove(project)