from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class UserRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        label="ФИО",
        widget=forms.TextInput(attrs={"placeholder": "Иванов Иван Иванович"})
    )
    username = forms.CharField(
        max_length=50,
        label="Логин",
        widget=forms.TextInput(attrs={"placeholder": "ivanov-ivan"})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "user@example.com"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль"}),
        label="Пароль"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Повторите пароль"}),
        label="Повтор пароля"
    )
    consent = forms.BooleanField(
        required=True,
        label="Согласие на обработку персональных данных"
    )

    def clean_full_name(self):
        full_name = self.cleaned_data['full_name']
        if not re.fullmatch(r"[а-яА-ЯёЁ\s\-]+", full_name):
            raise ValidationError("ФИО должно содержать только кириллические буквы, пробелы и дефисы.")
        return full_name

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.fullmatch(r"[a-zA-Z\-]+", username):
            raise ValidationError("Логин должен содержать только латинские буквы и дефис.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise ValidationError("Пароли не совпадают.")
        return password2

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"]
        )
        user.first_name = self.cleaned_data["full_name"]
        user.save()
        return user