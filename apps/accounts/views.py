from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, SendCodeSerializer, ResetPasswordSerializer


class AuthViewSet(viewsets.GenericViewSet):
    """账号系统 —— 注册/登录/验证码/找回密码"""
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ['register', 'login', 'send_code', 'reset_password']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        mapping = {
            'register': RegisterSerializer,
            'login': LoginSerializer,
            'send_code': SendCodeSerializer,
            'reset_password': ResetPasswordSerializer,
            'me': UserSerializer,
        }
        return mapping.get(self.action, UserSerializer)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = self._get_tokens(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        from django.contrib.auth import authenticate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(email=serializer.validated_data['email'],
                            password=serializer.validated_data['password'])
        if not user:
            return Response({'detail': '邮箱或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        tokens = self._get_tokens(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        })

    @action(detail=False, methods=['post'])
    def send_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: 集成邮件服务发送验证码
        return Response({'message': '验证码已发送'})

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: 验证码校验 + 重置密码逻辑
        return Response({'message': '密码已重置'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            RefreshToken(refresh_token).blacklist()
        except Exception:
            pass
        return Response({'message': '已登出'})

    @action(detail=False, methods=['post'])
    def token_refresh(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        try:
            refresh = RT(request.data.get('refresh'))
            return Response({'access': str(refresh.access_token)})
        except Exception:
            return Response({'detail': 'Token 无效'}, status=status.HTTP_401_UNAUTHORIZED)

    def _get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}
