from urllib.parse import urlparse

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import PHONE_RE, Project, User, normalize_phone


def validate_github_host(value: str) -> None:
    if not value:
        return
    host = (urlparse(value).netloc or "").lower()
    if "github.com" not in host:
        raise ValidationError("Ссылка должна вести на GitHub.")


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=124, label="Имя")
    surname = forms.CharField(max_length=124, label="Фамилия")
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")

    def clean_phone(self):
        raw = self.cleaned_data["phone"].strip()
        if not PHONE_RE.match(raw):
            raise ValidationError("Номер должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX.")
        normalized = normalize_phone(raw)
        qs = User.objects.filter(phone=normalized).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Этот номер уже используется другим пользователем.")
        return normalized

    def clean_github_url(self):
        value = self.cleaned_data.get("github_url") or ""
        validate_github_host(value)
        return value


class ProjectForm(forms.ModelForm):
    STATUS_CHOICES = (
        ("open", "Открыт"),
        ("closed", "Закрыт"),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Статус")

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")

    def clean_github_url(self):
        value = self.cleaned_data.get("github_url") or ""
        validate_github_host(value)
        return value


class UserPasswordChangeForm(PasswordChangeForm):
    pass
