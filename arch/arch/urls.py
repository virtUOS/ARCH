"""arch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from arch_app.views import CustomLoginView
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
# import debug_toolbar

# urlpatterns = [
#     path('', include('arch_app.urls')),
#     path('admin/', admin.site.urls),
# ]

urlpatterns = i18n_patterns(
    path('accounts/password_reset/', PasswordResetView.as_view(
        html_email_template_name='registration/password_reset_email.html'
    )),
    path('accounts/login/', CustomLoginView.as_view()),  # override login page
    path('accounts/', include('django.contrib.auth.urls')),  # build-in login and logout page
    path('', include('arch_app.urls')),
    path('admin/', admin.site.urls),
    # path('__debug__/', include('debug_toolbar.urls')),
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
