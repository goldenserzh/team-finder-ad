import json
from http import HTTPStatus

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
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
from .utils import paginate_queryset

SKILLS_AUTOCOMPLETE_LIMIT = 10
JSON_CONTENT_TYPE = "application/json"
EMPTY_JSON_OBJECT = "{}"
RESPONSE_STATUS_KEY = "status"
RESPONSE_ERROR = "error"
RESPONSE_OK = "ok"
ERROR_FORBIDDEN = "forbidden"
ERROR_BAD_REQUEST = "bad request"
ERROR_NOT_FOUND = "not found"


def index_redirect(request):
    return redirect("main:project_list")


def project_list(request):
    qs = Project.objects.select_related("owner").prefetch_related("participants").order_by(
        "-created_at"
    )
    page = paginate_queryset(request, qs)
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
    if project.owner_id != request.user.id or project.status != Project.Status.OPEN:
        return JsonResponse({RESPONSE_STATUS_KEY: RESPONSE_ERROR}, status=HTTPStatus.FORBIDDEN)
    project.status = Project.Status.CLOSED
    project.save(update_fields=[RESPONSE_STATUS_KEY])
    return JsonResponse(
        {RESPONSE_STATUS_KEY: RESPONSE_OK, "project_status": Project.Status.CLOSED}
    )


@require_POST
@login_required
def project_toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id == request.user.id:
        return JsonResponse(
            {RESPONSE_STATUS_KEY: RESPONSE_ERROR}, status=HTTPStatus.BAD_REQUEST
        )
    if project.status != Project.Status.OPEN:
        return JsonResponse(
            {RESPONSE_STATUS_KEY: RESPONSE_ERROR}, status=HTTPStatus.BAD_REQUEST
        )
    user = request.user
    if project.participants.filter(pk=user.pk).exists():
        project.participants.remove(user)
        return JsonResponse({RESPONSE_STATUS_KEY: RESPONSE_OK, "participant": False})
    project.participants.add(user)
    return JsonResponse({RESPONSE_STATUS_KEY: RESPONSE_OK, "participant": True})


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
    page = paginate_queryset(request, qs)
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
    qs = qs.order_by("name")[:SKILLS_AUTOCOMPLETE_LIMIT]
    return JsonResponse([{"id": s.pk, "name": s.name} for s in qs], safe=False)


def _parse_skill_post(request):
    if request.content_type and JSON_CONTENT_TYPE in request.content_type:
        try:
            return json.loads(request.body.decode() or EMPTY_JSON_OBJECT)
        except json.JSONDecodeError:
            return {}
    return request.POST


@require_POST
@login_required
def user_skill_add(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk != request.user.pk:
        return JsonResponse({"error": ERROR_FORBIDDEN}, status=HTTPStatus.FORBIDDEN)
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
            return JsonResponse({"error": ERROR_BAD_REQUEST}, status=HTTPStatus.BAD_REQUEST)
        skill = Skill.objects.filter(pk=sid).first()
        if not skill:
            return JsonResponse({"error": ERROR_NOT_FOUND}, status=HTTPStatus.NOT_FOUND)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({"error": ERROR_BAD_REQUEST}, status=HTTPStatus.BAD_REQUEST)

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
        return JsonResponse({"error": ERROR_FORBIDDEN}, status=HTTPStatus.FORBIDDEN)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not target.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"error": ERROR_NOT_FOUND}, status=HTTPStatus.NOT_FOUND)
    target.skills.remove(skill)
    return JsonResponse({RESPONSE_STATUS_KEY: RESPONSE_OK})
