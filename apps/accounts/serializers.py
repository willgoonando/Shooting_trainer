from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'avatar', 'gender',
                  'training_frequency', 'session_duration_minutes', 'focus_area',
                  'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    code = serializers.CharField(write_only=True, max_length=6)

    class Meta:
        model = User
        fields = ['email', 'password', 'code']

    def create(self, validated_data):
        validated_data.pop('code')
        password = validated_data.pop('password')
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class SendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=[('register', '注册'), ('reset_password', '重置密码')])


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)
