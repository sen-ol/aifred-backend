from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model  = User
        fields = ("id","email","password","first_name","last_name","role")
        extra_kwargs = {"role": {"read_only": True}}   # kayıt hep "guest"
    def validate_password(self,v): password_validation.validate_password(v); return v
    def create(self,d): pwd=d.pop("password"); return User.objects.create_user(password=pwd,**d)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta: model=User; fields=("id","email","first_name","last_name","date_joined")
