from django.core.management.base import BaseCommand

from main.models import Project, Skill, User

PROJECT_STATUS_OPEN = Project.Status.OPEN

class Command(BaseCommand):
    help = "Создаёт тестовых пользователей, навыки и проекты"

    def handle(self, *args, **options):
        skills_data = [
            "Python", "Django", "JavaScript", "React",
            "PostgreSQL", "Docker", "HTML/CSS", "Git",
        ]
        skills = {}
        for name in skills_data:
            skill, _ = Skill.objects.get_or_create(name=name)
            skills[name] = skill

        users_data = [
            {
                "email": "maria@yandex.ru",
                "password": "password",
                "name": "Мария",
                "surname": "Иванова",
                "phone": "+70000000001",
                "about": "Backend-разработчик, люблю Python и Django",
                "skills": ["Python", "Django", "PostgreSQL"],
            },
            {
                "email": "alex@yandex.ru",
                "password": "password",
                "name": "Алексей",
                "surname": "Петров",
                "phone": "+70000000002",
                "about": "Fullstack-разработчик",
                "skills": ["JavaScript", "React", "Docker"],
            },
            {
                "email": "elena@yandex.ru",
                "password": "password",
                "name": "Елена",
                "surname": "Сидорова",
                "phone": "+70000000003",
                "about": "Frontend-разработчик",
                "skills": ["JavaScript", "React", "HTML/CSS"],
            },
        ]

        created_users = []
        for data in users_data:
            user_skills = data.pop("skills")
            if User.objects.filter(email=data["email"]).exists():
                self.stdout.write(f"Пользователь {data['email']} уже существует")
                created_users.append(
                    User.objects.get(email=data["email"])
                )
                continue
            password = data.pop("password")
            user = User.objects.create_user(password=password, **data)
            user.skills.set([skills[s] for s in user_skills])
            created_users.append(user)
            self.stdout.write(
                self.style.SUCCESS(f"Создан пользователь: {user.email}")
            )

        projects_data = [
            {
                "name": "TeamFinder",
                "description": (
                    "Платформа для поиска единомышленников "
                    "для совместной работы над pet-проектами."
                ),
                "owner": created_users[0],
                "status": PROJECT_STATUS_OPEN,
            },
            {
                "name": "Code Review Bot",
                "description": (
                    "Telegram-бот для автоматического ревью "
                    "pull-request'ов с использованием AI."
                ),
                "owner": created_users[1],
                "status": PROJECT_STATUS_OPEN,
            },
            {
                "name": "Портфолио-генератор",
                "description": (
                    "Сервис, который генерирует красивое "
                    "портфолио из GitHub-профиля разработчика."
                ),
                "owner": created_users[2],
                "status": PROJECT_STATUS_OPEN,
            },
        ]

        for data in projects_data:
            if Project.objects.filter(
                name=data["name"], owner=data["owner"]
            ).exists():
                self.stdout.write(f"Проект «{data['name']}» уже существует")
                continue
            owner = data["owner"]
            project = Project.objects.create(**data)
            project.participants.add(owner)
            self.stdout.write(
                self.style.SUCCESS(f"Создан проект: {project.name}")
            )

        self.stdout.write(self.style.SUCCESS("Готово!"))
