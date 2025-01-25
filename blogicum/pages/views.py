from django.views.generic import TemplateView
from django.views.defaults import (page_not_found,
                                   server_error,
                                   permission_denied)


class AboutView(TemplateView):
    template_name = "pages/about.html"


class RulesView(TemplateView):
    template_name = "pages/rules.html"


def handle_page_not_found(request, exception):
    return page_not_found(
        request,
        exception,
        template_name="pages/404.html"
    )


def handle_server_error(request):
    return server_error(
        request,
        template_name="pages/500.html"
    )


def handle_permission_denied(request, exception):
    return permission_denied(
        request,
        exception,
        template_name="pages/403csrf.html"
    )
