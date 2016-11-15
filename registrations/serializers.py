from django.contrib.auth.models import User, Group
from .models import Source, Registration
from rest_framework import serializers
from rest_hooks.models import Hook


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class SourceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Source
        read_only_fields = ('created_at', 'updated_at')
        fields = ('url', 'id', 'name', 'user', 'authority', 'created_at',
                  'updated_at')


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registration
        read_only_fields = ('validated', 'created_by', 'updated_by',
                            'created_at', 'updated_at')
        fields = ('id', 'reg_type', 'registrant_id', 'validated', 'data',
                  'source', 'created_at', 'updated_at', 'created_by',
                  'updated_by')

    def validate(self, attrs):
        instance = Registration(**attrs)
        instance.clean()
        return attrs


class HookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hook
        read_only_fields = ('user',)
