from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path(
        "profile/<str:username>/",
        views.UserProfileView.as_view(),
        name="profile"
    ),
    path(
        "edit_profile/",
        views.EditUserProfileView.as_view(),
        name="edit_profile"
    ),
    path(
        "category/<slug:category_slug>/",
        views.CategoryPostsListView.as_view(),
        name="category_posts",
    ),
    path(
        "posts/<int:post_id>/",
        views.PostDetailsView.as_view(),
        name="post_detail"
    ),
    path(
        "posts/<int:post_id>/edit/",
        views.EditPostView.as_view(),
        name="edit_post"
    ),
    path(
        "posts/<int:post_id>/delete/",
        views.DeletePostView.as_view(),
        name="delete_post",
    ),
    path(
        "posts/create/",
        views.CreatePostView.as_view(),
        name="create_post"
    ),
    path(
        "posts/<int:post_id>/add_comment/",
        views.CreateCommentView.as_view(),
        name="add_comment",
    ),
    path(
        "posts/<int:post_id>/comment/<int:comment_id>/edit_comment/",
        views.EditCommentView.as_view(),
        name="edit_comment",
    ),
    path(
        "posts/<int:post_id>/comment/<int:comment_id>/delete_comment/",
        views.DeleteCommentView.as_view(),
        name="delete_comment",
    ),
    path(
        "",
        views.ListPostsView.as_view(),
        name="index",
    ),
]
