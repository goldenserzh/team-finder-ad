import random
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from .utils import generate_avatar_image_file, normalize_phone

PHONE_PLACEHOLDER_ATTEMPTS = 500
PHONE_DIGITS_COUNT = 10
PHONE_PREFIX = "+7"
PROJECT_STATUS_MAX_LENGTH = 6


class UserManager(BaseUserManager):
    def _unique_placeholder_phone(self):
        for _ in range(PHONE_PLACEHOLDER_ATTEMPTS):
            digits = "".join(str(random.randint(0, 9)) for _ in range(PHONE_DIGITS_COUNT))
            candidate = f"{PHONE_PREFIX}{digits}"
            if not User.objects.filter(phone=candidate).exists():
                return candidate
        raise RuntimeError("Could not allocate unique phone placeholder")

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("email required")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if not extra_fields.get("phone"):
            extra_fields["phone"] = self._unique_placeholder_phone()
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("is_staff must be True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("is_superuser must be True")
        if not extra_fields.get("phone"):
            extra_fields["phone"] = self._unique_placeholder_phone()
        return self.create_user(email, password, **extra_fields)


class Skill(models.Model):
    name = models.CharField(max_length=124, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/")
    phone = models.CharField(max_length=12)
    github_url = models.URLField(blank=True)
    about = models.TextField(blank=True, max_length=256)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    skills = models.ManyToManyField(Skill, blank=True, related_name="users")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar or not getattr(self.avatar, "name", None):
            self.avatar.save(
                f"avatar_{uuid.uuid4().hex}.png",
                generate_avatar_image_file(self.name),
                save=False,
            )
        super().save(*args, **kwargs)


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="participated_projects",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


