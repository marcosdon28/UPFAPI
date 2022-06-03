
from django.urls import path, include
from django.urls import include, path, re_path
from django.views.generic import RedirectView, TemplateView
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordResetConfirmView,
    PasswordResetView, UserDetailsView,
)
from allauth.account.views import ConfirmEmailView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import EventsDetailView, EventsViewSet
from apiauth import views
from rest_framework import routers
router = routers.SimpleRouter()

schema_view = get_schema_view(
   openapi.Info(
      title="API DOCS",
      default_version='v1',
      description="La documentacion numa peshasho",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^dj-rest-auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$', PasswordResetConfirmView.as_view(),
            name='password_reset_confirm'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('verify-email/',
         VerifyEmailView.as_view(), name='rest_verify_email'),
    path('account-confirm-email/',
         VerifyEmailView.as_view(), name='account_email_verification_sent'),
    path('account-confirm-email/<str:key>/', ConfirmEmailView.as_view()),
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$',
         VerifyEmailView.as_view(), name='account_confirm_email'),

    #docs
    path('playground/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    #api
     path("events/<int:id>/", EventsDetailView.as_view(), name='Events_detail')

    
]

#api urls

router.register('events', EventsViewSet, basename='EventsModel')
urlpatterns += router.urls