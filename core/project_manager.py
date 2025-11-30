# core/project_manager.py
import pickle
import zlib
import shutil
from datetime import datetime
from pathlib import Path
from core.config import get_projects_dir
from core.contracts import Contract


class VATProject:
    def __init__(self, name=None):
        self.name = name or f"Проект_{datetime.now():%Y%m%d_%H%M%S}"
        self.created = datetime.now()
        self.modified = datetime.now()
        self.contracts = []  # List[Contract]
        self.settings = {'current_vat': 20.0, 'future_vat': 22.0}

    @property
    def folder_name(self):
        """Безопасное имя папки проекта."""
        from core.config import sanitize_project_name
        return sanitize_project_name(self.name)
    
    @property
    def project_dir(self):
        return get_projects_dir() / self.folder_name

    @property
    def project_file(self):
        return self.project_dir / "project.vat"

    def save(self):
        self.project_dir.mkdir(parents=True, exist_ok=True)
        data = {
            'name': self.name,
            'created': self.created,
            'modified': self.modified,
            'contracts': [c.__dict__ for c in self.contracts],
            'settings': self.settings
        }
        compressed = zlib.compress(pickle.dumps(data))
        with open(self.project_file, "wb") as f:
            f.write(compressed)

    @classmethod
    def load(cls, project_path: Path):
        with open(project_path, "rb") as f:
            data = pickle.loads(zlib.decompress(f.read()))

        project = cls(data.get("name", "Без имени"))
        project.created = data.get("created", datetime.now())
        project.modified = data.get("modified", datetime.now())
        project.settings = data.get("settings", {})

        for c in data.get("contracts", []):
            contract = Contract(
                name=c.get("name", "Договор"),
                number=c.get("number", ""),
                total_cost_with_vat=c.get("total_cost_with_vat", 0.0),
                remaining_cost=c.get("remaining_cost", 0.0),
            )
            project.contracts.append(contract)
        return project

    @classmethod
    def list_projects(cls):
        projects = []
        for proj_file in get_projects_dir().glob("*/project.vat"):
            try:
                projects.append(cls.load(proj_file))
            except:
                continue
        return sorted(projects, key=lambda p: p.modified, reverse=True)

    def get_export_data(self):
        """
        Возвращает список словарей для экспорта в Excel с расширенными расчётами
        """
        data = []
        total_diff = 0.0

        for contract in self.contracts:
            diff = contract.get_vat_difference()
            total_diff += diff

            data.append({
                "Название договора": contract.name,
                "№ договора": contract.number or "",
                "Сумма договора": contract.total_cost_with_vat,
                "Факт на 31.12.2025": contract.remaining_cost,
                "Остаток": contract.get_difference(),
                "Остаток без НДС": contract.get_without(),
                "НДС текущий": contract.getVAT(),
                "НДС будущий": contract.getVATfut(),
                "Остаток с новым НДС": contract.getDiffWith(),
                "Дополнительный НДС": diff,
            })

        # Итоговая строка
        data.append({
            "Название договора": "ИТОГО",
            "№ договора": "",
            "Сумма договора": "",
            "Факт на 31.12.2025": "",
            "Остаток": "",
            "Остаток без НДС": "",
            "НДС текущий": "",
            "НДС будущий": "",
            "Остаток с новым НДС": "",
            "Дополнительный НДС": total_diff,
        })

        return data


class ProjectManager:
    def __init__(self):
        self.projects = VATProject.list_projects()
        self.current_project = None

    def create_project_in_memory(self, name="Новый проект"):
        return VATProject(name)

    def create_project(self, name):
        project = VATProject(name)
        project.save()
        self.projects.insert(0, project)
        self.current_project = project
        return project

    def load_project(self, project):
        reloaded = VATProject.load(project.project_file)
        self.current_project = reloaded
        return reloaded

    def delete_project(self, project):
        if project.project_dir.exists():
            shutil.rmtree(project.project_dir)
        if project in self.projects:
            self.projects.remove(project)
        if self.current_project == project:
            self.current_project = None