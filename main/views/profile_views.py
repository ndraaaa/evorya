from django.contrib.auth import update_session_auth_hash
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from main.models import Account

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class ProfileView(View):
    def get(self, request, nim):
        if request.user.nim != nim:
            messages.error(request, "Anda tidak diizinkan mengakses profil ini.")
            return redirect('voters:home')

        user_obj = get_object_or_404(Account, nim=nim)
        show_password_modal = request.path.endswith('/ubah-password/')
        return render(request, 'main/profile.html', {
            'user_obj': user_obj,
            'show_password_modal': show_password_modal
        })

    def post(self, request, nim):
        if request.user.nim != nim:
            messages.error(request, "Akses ditolak.")
            return redirect('voters:home')

        user = get_object_or_404(Account, nim=nim)

        # Deteksi aksi: ubah profil atau ubah password
        if 'first_name' in request.POST:
            # Ubah profil
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            if request.FILES.get('photo_profile'):
                user.photo_profile = request.FILES['photo_profile']
            user.save()
            messages.success(request, "Profil berhasil diperbarui.")
            return redirect('main:user_profile', nim=nim)

        elif 'current_password' in request.POST:
            # Ubah password
            current = request.POST.get('current_password')
            new = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')

            if not user.check_password(current):
                messages.error(request, "Password saat ini salah.")
            elif new != confirm:
                messages.error(request, "Password baru tidak cocok.")
            else:
                user.set_password(new)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password berhasil diubah.")
            return redirect('main:user_profile', nim=nim)

        # Fallback redirect jika tidak ada data
        return redirect('main:user_profile', nim=nim)
