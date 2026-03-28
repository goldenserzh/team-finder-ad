import json

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    EditProfileForm,
    LoginForm,
    ProjectForm,
    RegisterForm,
    UserPasswordChangeForm,
)
from .models import Project, Skill, User


def index_redirect(request):
    return redirect("main:project_list")


def project_list(request):
    qs = Project.objects.select_related("owner").prefetch_related("participants").order_by(
        "-created_at"
    )
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get("page") or 1)
    return render(request, "projects/project_list.html", {"projects": page, "page_obj": page})


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@require_POST
@login_required
def project_complete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id or project.status != "open":
        return JsonResponse({"status": "error"}, status=403)
    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@require_POST
@login_required
def project_toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id == request.user.id:
        return JsonResponse({"status": "error"}, status=400)
    if project.status != "open":
        return JsonResponse({"status": "error"}, status=400)
    user = request.user
    if project.participants.filter(pk=user.pk).exists():
        project.participants.remove(user)
        return JsonResponse({"status": "ok", "participant": False})
    project.participants.add(user)
    return JsonResponse({"status": "ok", "participant": True})


@login_required
@require_http_methods(["GET", "POST"])
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user
            p.save()
            p.participants.add(request.user)
            return redirect("main:project_detail", pk=p.pk)
    else:
        form = ProjectForm()
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id and not request.user.is_staff:
        return redirect("main:project_detail", pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("main:project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("main:project_list")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                name=data["name"],
                surname=data["surname"],
            )
            login(request, user)
            return redirect("main:project_list")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("main:project_list")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password"]
            user = User.objects.filter(email__iexact=email).first()
            if user and user.check_password(password):
                login(request, user)
                return redirect("main:project_list")
            form.add_error(None, "Неверный имейл или пароль")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("main:project_list")


def user_detail(request, pk):
    user = get_object_or_404(User.objects.prefetch_related("skills", "owned_projects"), pk=pk)
    return render(request, "users/user-details.html", {"user": user})


def users_list(request):
    qs = User.objects.order_by("-id")
    skill = request.GET.get("skill")
    if skill:
        qs = qs.filter(skills__name=skill).distinct()
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get("page") or 1)
    all_skills = Skill.objects.order_by("name")
    return render(
        request,
        "users/participants.html",
        {
            "participants": page,
            "page_obj": page,
            "all_skills": all_skills,
            "active_skill": skill,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("main:user_detail", pk=request.user.pk)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == "POST":
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:user_detail", pk=request.user.pk)
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


@require_GET
def skills_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    qs = Skill.objects.all()
    if q:
        qs = qs.filter(name__istartswith=q)
    qs = qs.order_by("name")[:10]
    return JsonResponse([{"id": s.pk, "name": s.name} for s in qs], safe=False)


def _parse_skill_post(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


@require_POST
@login_required
def user_skill_add(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk != request.user.pk:
        return JsonResponse({"error": "forbidden"}, status=403)
    data = _parse_skill_post(request)
    raw_skill_id = data.get("skill_id")
    name = (data.get("name") or "").strip()
    created = False
    added = False
    skill = None
    if raw_skill_id is not None and raw_skill_id != "":
        try:
            sid = int(raw_skill_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "bad request"}, status=400)
        skill = Skill.objects.filter(pk=sid).first()
        if not skill:
            return JsonResponse({"error": "not found"}, status=404)
    elif name:
        try:
            skill, created = Skill.objects.get_or_create(name=name)
        except IntegrityError:
            skill = Skill.objects.get(name=name)
            created = False
    else:
        return JsonResponse({"error": "bad request"}, status=400)

    if target.skills.filter(pk=skill.pk).exists():
        added = False
    else:
        target.skills.add(skill)
        added = True
    return JsonResponse(
        {
            "skill_id": skill.pk,
            "created": created,
            "added": added,
        }
    )


@require_POST
@login_required
def user_skill_remove(request, user_id, skill_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk != request.user.pk:
        return JsonResponse({"error": "forbidden"}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not target.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"error": "not found"}, status=404)
    target.skills.remove(skill)
    return JsonResponse({"status": "ok"})
