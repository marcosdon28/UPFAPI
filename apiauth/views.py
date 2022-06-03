from django.shortcuts import get_object_or_404, render
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import complete_signup, send_email_confirmation
from allauth.account.views import ConfirmEmailView
from allauth.account.models import EmailAddress
from allauth.socialaccount import signals
from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status, viewsets
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Event
from rest_framework.permissions import IsAuthenticated

#docs

from dj_rest_auth.app_settings import (
    JWTSerializer, TokenSerializer, create_token,
)
from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import (
    SocialAccountSerializer, SocialConnectSerializer, SocialLoginSerializer,
    VerifyEmailSerializer, ResendEmailVerificationSerializer
)
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.views import LoginView

from apiauth.serializers import EventsSerializer




sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password1', 'password2'),
)




#api 

class EventsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    """
    GET ver todos los eventos existentes
    """
    def list(self, request):
        queryset = Event.objects.all()
        serializer = EventsSerializer(queryset, many=True)
        return Response(serializer.data)

    """
    POST para postear un nuevo evento
    """
    def post(self, request, *args, **kwargs):
        serializer = EventsSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    """
     GET de un objeto, PUT a un objeto, DELETE a un objeto (PK como parametro)
    """

class EventsDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = EventsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field =  "id"
    
    def get_queryset(self):
        return Event.objects.filter()


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class VerifyEmailView(APIView, ConfirmEmailView):
    permission_classes = (AllowAny,)
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def get_serializer(self, *args, **kwargs):
        return VerifyEmailSerializer(*args, **kwargs)

    def get(self, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.kwargs['key'] = serializer.validated_data['key']
        confirmation = self.get_object()
        confirmation.confirm(self.request)
        return Response({'detail': _('ok')}, status=status.HTTP_200_OK)


class ResendEmailVerificationView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResendEmailVerificationSerializer
    queryset = EmailAddress.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = EmailAddress.objects.filter(**serializer.validated_data).first()
        if email and not email.verified:
            email.send_confirmation(request)

        return Response({'detail': _('ok')}, status=status.HTTP_200_OK)


class SocialLoginView(LoginView):
    """
    class used for social authentications
    example usage for facebook with access_token
    -------------
    from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

    class FacebookLogin(SocialLoginView):
        adapter_class = FacebookOAuth2Adapter
    -------------

    example usage for facebook with code

    -------------
    from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.client import OAuth2Client

    class FacebookLogin(SocialLoginView):
        adapter_class = FacebookOAuth2Adapter
        client_class = OAuth2Client
        callback_url = 'localhost:8000'
    -------------
    """
    serializer_class = SocialLoginSerializer

    def process_login(self):
        get_adapter(self.request).login(self.request, self.user)


class SocialConnectView(LoginView):
    """
    class used for social account linking

    example usage for facebook with access_token
    -------------
    from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

    class FacebookConnect(SocialConnectView):
        adapter_class = FacebookOAuth2Adapter
    -------------
    """
    serializer_class = SocialConnectSerializer
    permission_classes = (IsAuthenticated,)

    def process_login(self):
        get_adapter(self.request).login(self.request, self.user)


class SocialAccountListView(ListAPIView):
    """
    List SocialAccounts for the currently logged in user
    """
    serializer_class = SocialAccountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user)


class SocialAccountDisconnectView(GenericAPIView):
    """
    Disconnect SocialAccount from remote service for
    the currently logged in user
    """
    serializer_class = SocialConnectSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        accounts = self.get_queryset()
        account = accounts.filter(pk=kwargs['pk']).first()
        if not account:
            raise NotFound

        get_social_adapter(self.request).validate_disconnect(account, accounts)

        account.delete()
        signals.social_account_removed.send(
            sender=SocialAccount,
            request=self.request,
            socialaccount=account,
        )

        return Response(self.get_serializer(account).data)