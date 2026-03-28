from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index_redirect, name="index"),
    path("projects/list/", views.project_list, name="project_list"),
    path("projects/create-project/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/complete/", views.project_complete, name="project_complete"),
    path(
        "projects/<int:pk>/toggle-participate/",
        views.project_toggle_participate,
        name="project_toggle_participate",
    ),
    path("users/register/", views.register_view, name="register"),
    path("users/login/", views.login_view, name="login"),
    path("users/logout/", views.logout_view, name="logout"),
    path("users/list/", views.users_list, name="users_list"),
    path("users/edit-profile/", views.edit_profile, name="edit_profile"),
    path("users/change-password/", views.change_password, name="change_password"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/skills/", views.skills_autocomplete, name="skills_autocomplete"),
    path(
        "users/<int:user_id>/skills/add/",
        views.user_skill_add,
        name="user_skill_add",
    ),
    path(
        "users/<int:user_id>/skills/<int:skill_id>/remove/",
        views.user_skill_remove,
        name="user_skill_remove",
    ),
]
