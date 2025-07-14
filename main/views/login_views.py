from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

from django.views import View

class RedirectToLoginView(View):
    def get(self, request):
        return redirect('main:login')

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.role == 'admin':
                return redirect('admin:dashboard_admin')
            elif request.user.role == 'voter':
                return redirect('voters:home')
        return render(request, 'main/login.html')

    def post(self, request):
        nim = request.POST.get('nim')
        password = request.POST.get('password')
        user = authenticate(request, nim=nim, password=password)

        if user is not None:
            login(request, user)
            request.session.set_expiry(18000)  # 5 jam

            request.session['nim'] = user.nim
            request.session['role'] = user.role
            request.session['full_name'] = user.full_name

            if user.role == 'admin':
                return redirect('admin:dashboard_admin')
            elif user.role == 'voter':
                return redirect('voters:home')
        else:
            messages.error(request, 'NIM atau Password salah')

        return render(request, 'main/login.html')

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('main:login')