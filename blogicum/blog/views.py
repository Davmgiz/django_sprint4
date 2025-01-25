from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count
from .models import Post, Category, Comment
from .forms import PostForm, UserForm, CommentForm
from django.views import generic
from django.utils import timezone
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy


class DeleteCommentView(LoginRequiredMixin,
                        UserPassesTestMixin,
                        generic.DeleteView):
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user

    def get_success_url(self):
        post_id = self.get_object().post.id
        return reverse("blog:post_detail", kwargs={"post_id": post_id})


class EditUserProfileView(LoginRequiredMixin, generic.UpdateView):
    model = User
    form_class = UserForm
    template_name = "blog/user.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("blog:profile",
                            kwargs={"username": self.request.user.username})


class CategoryPostsListView(generic.ListView):
    template_name = "blog/category.html"
    context_object_name = "post_list"
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        self.category = get_object_or_404(
            Category.objects.filter(is_published=True), slug=category_slug
        )

        posts_in_category = Post.objects.filter(
            category=self.category,
            is_published=True,
            pub_date__lte=timezone.now()
        )
        annotated_posts = posts_in_category.annotate(
            comment_count=Count("comments")
        )
        return annotated_posts.order_by("-pub_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_category"] = self.category
        context["total_posts"] = context["paginator"].count
        context["is_paginated"] = context["is_paginated"]
        return context


class PostDetailsView(generic.DetailView):
    model = Post
    template_name = "blog/detail.html"
    pk_url_kwarg = "post_id"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        is_post_visible = post.is_published and post.category.is_published
        is_post_visible = is_post_visible and post.pub_date <= timezone.now()

        if not is_post_visible and post.author != self.request.user:
            raise Http404("Этот пост недоступен.")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = (
            self.object.comments
            .select_related("author")
            .order_by("created_at")
        )
        context.update({
            "form": CommentForm(),
            "comments": comments,
        })
        return context


class CreateCommentView(LoginRequiredMixin, generic.CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "includes/comments.html"

    def form_valid(self, form):
        related_post = get_object_or_404(Post, id=self.kwargs.get("post_id"))
        form.instance.post = related_post
        form.instance.author = self.request.user

        return super().form_valid(form)

    def get_success_url(self):
        post_id = self.kwargs.get("post_id")
        comment = f"#comment{self.object.id}"
        return (
            reverse("blog:post_detail", kwargs={"post_id": post_id}) + comment
        )


class UserProfileView(generic.ListView):
    template_name = "blog/profile.html"
    context_object_name = "page_obj"
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs["username"]
        self.profile = get_object_or_404(User, username=username)

        posts = Post.objects.filter(author=self.profile)

        if self.request.user == self.profile:
            visible_posts = posts
        else:
            visible_posts = posts.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )

        return (
            visible_posts
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        context["total_posts"] = Post.objects.filter(author=self.profile)
        context["total_posts"] = context["total_posts"].count()
        context["is_profile_owner"] = self.request.user == self.profile
        return context


class EditPostView(LoginRequiredMixin, generic.UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def get_object(self, queryset=None):
        try:
            post = super().get_object(queryset)
            if post.author != self.request.user:
                raise PermissionError("You are not allowed to edit this post.")
            return post
        except PermissionError as e:
            print(e)
            return None

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not post:
            return redirect("blog:post_detail", post_id=kwargs.get("post_id"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse_lazy("blog:post_detail",
                                   kwargs={"post_id": self.object.id})
        return success_url


class CreatePostView(LoginRequiredMixin, generic.CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        user_profile_url = reverse("blog:profile",
                                   kwargs={"username":
                                           self.request.user.username})
        return user_profile_url


class DeletePostView(LoginRequiredMixin,
                     UserPassesTestMixin,
                     generic.DeleteView):
    model = Post
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user

    def handle_no_permission(self):
        return redirect("blog:index")

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:index")


class ListPostsView(generic.ListView):
    template_name = "blog/index.html"
    context_object_name = "page_obj"
    paginate_by = 10

    def get_queryset(self):
        published_posts = Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

        posts_with_comment_count = published_posts.annotate(
            comment_count=Count("comments")
        )

        return posts_with_comment_count.order_by("-pub_date")


class EditCommentView(LoginRequiredMixin,
                      UserPassesTestMixin,
                      generic.UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user

    def get_success_url(self):
        post_id = self.get_object().post.id
        comment = f"#comment_{self.object.id}"
        return (
            reverse("blog:post_detail", kwargs={"post_id": post_id}) + comment
        )
