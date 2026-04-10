from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from .models import Project, Skill

User = get_user_model()
JSON_CONTENT_TYPE = "application/json"


class TeamFinderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="a@a.com",
            password="pass12345",
            name="Ann",
            surname="Smith",
        )
        self.other = User.objects.create_user(
            email="b@b.com",
            password="pass12345",
            name="Bob",
            surname="Jones",
        )

    def test_project_list_ok(self):
        Project.objects.create(
            name="P1",
            description="d",
            owner=self.user,
            status=Project.Status.OPEN,
        )
        r = self.client.get("/projects/list/")
        self.assertEqual(r.status_code, HTTPStatus.OK)

    def test_register_login_flow(self):
        r = self.client.post(
            "/users/register/",
            {
                "name": "X",
                "surname": "Y",
                "email": "new@new.com",
                "password": "secret123",
            },
            follow=True,
        )
        self.assertEqual(r.status_code, HTTPStatus.OK)
        u = User.objects.get(email="new@new.com")
        self.assertTrue(u.check_password("secret123"))

    def test_skill_filter_users(self):
        s = Skill.objects.create(name="Django")
        self.user.skills.add(s)
        r = self.client.get("/users/list/", {"skill": "Django"})
        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertContains(r, "Ann")

    def test_toggle_participate(self):
        p = Project.objects.create(
            name="Open",
            description="",
            owner=self.other,
            status=Project.Status.OPEN,
        )
        p.participants.add(self.other)
        self.client.login(username="a@a.com", password="pass12345")
        r = self.client.post(
            f"/projects/{p.pk}/toggle-participate/",
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertTrue(p.participants.filter(pk=self.user.pk).exists())
