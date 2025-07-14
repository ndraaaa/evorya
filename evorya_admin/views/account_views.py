from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from main.models import *
import pandas as pd

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class UserListView(View):
    def get(self, request):
        search_query = request.GET.get('q', '')
        sort_by = request.GET.get('sort', 'nim')
        direction = request.GET.get('dir', 'asc')
        selected_angkatan = request.GET.get('angkatan', '')
        order = sort_by if direction == 'asc' else f'-{sort_by}'

        users = Account.objects.exclude(is_superuser=1).select_related('prodi__fakultas')

        if search_query:
            users = users.filter(
                Q(nim__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(role__icontains=search_query) |
                Q(prodi__nama__icontains=search_query) |
                Q(prodi__fakultas__nama__icontains=search_query)
            )

        if selected_angkatan:
            users = users.filter(nim__startswith=selected_angkatan)

        users = users.order_by(order)
        per_page = request.GET.get('per_page', '10')
        paginator = Paginator(users, int(per_page))
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        angkatan_list = (
            Account.objects.exclude(is_superuser=1)
            .values_list('nim', flat=True)
        )
        angkatan_list = sorted(set(nim[:2] for nim in angkatan_list if len(nim) >= 2))


        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'sort_by': sort_by,
            'direction': direction,
            'field_labels': [
                ('nim', 'NIM'),
                ('first_name', 'Nama Lengkap'),
                ('email', 'Email'),
                ('role', 'Role'),
                ('prodi__nama', 'Prodi - Fakultas'),
                ('is_active', 'Status')
            ],
            "prodis": Prodi.objects.select_related("fakultas").all(),
            "angkatan_list": angkatan_list,
            "selected_angkatan": selected_angkatan,
            "per_page": per_page,
            'total_users': users.count(),
            "total_all_users": Account.objects.exclude(is_superuser=1).count(),
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'admin/partials/user_table.html', context)

        return render(request, 'admin/user_list.html', context)
    
@method_decorator(login_required(login_url='main:login'), name='dispatch')
class AddUserView(View):
    def post(self, request):
        nim = request.POST.get('nim')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        prodi_id = request.POST.get('prodi')

        if Account.objects.filter(nim=nim).exists():
            messages.error(request, f"NIM '{nim}' sudah terdaftar. Tidak dapat menambahkan pengguna yang sama.")
            return redirect('admin:user_list')

        try:
            Account.objects.create_user(
                nim=nim,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                prodi_id=prodi_id
            )
            messages.success(request, "User berhasil ditambahkan.")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan user: {e}")

        return redirect('admin:user_list')
    
@method_decorator(login_required(login_url='main:login'), name='dispatch')
class EditUserView(View):
    def post(self, request):
        nim = request.POST.get('nim')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        prodi_id = request.POST.get('prodi')
        is_active = request.POST.get('is_active') == 'on'

        try:
            user = Account.objects.get(nim=nim)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.prodi_id = prodi_id
            user.is_active = is_active
            user.save()

            messages.success(request, "User berhasil diperbarui.")
        except Account.DoesNotExist:
            messages.error(request, "User tidak ditemukan.")
        except Exception as e:
            messages.error(request, f"Gagal mengedit user: {e}")

        return redirect('admin:user_list')


@method_decorator(login_required(login_url='main:login'), name='dispatch')
class DeleteUserView(View):
    def get(self, request, nim):
        try:
            user = Account.objects.get(nim=nim)
            user.delete()
            messages.success(request, "User berhasil dihapus.")
        except Account.DoesNotExist:
            messages.error(request, "User tidak ditemukan.")
        except Exception as e:
            messages.error(request, f"Gagal menghapus user: {e}")

        return redirect('admin:user_list')
    
@method_decorator(login_required(login_url='main:login'), name='dispatch')
class ImportUserView(View):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "File tidak ditemukan.")
            return redirect('admin:user_list')

        try:
            df = pd.read_excel(file) if file.name.endswith(('.xls', '.xlsx')) else pd.read_csv(file)
            sukses = 0
            dilewati = 0

            for _, row in df.iterrows():
                nim = str(row['NIM']).strip()
                email = row['Email'].strip()
                nama_lengkap = row['Nama Lengkap'].strip()
                nama_parts = nama_lengkap.split()
                first_name = nama_parts[0]
                last_name = " ".join(nama_parts[1:]) if len(nama_parts) > 1 else ""

                prodi_nama = row['Prodi'].strip()
                try:
                    prodi = Prodi.objects.get(nama__iexact=prodi_nama)
                except Prodi.DoesNotExist:
                    messages.warning(request, f"Prodi '{prodi_nama}' tidak ditemukan.")
                    continue

                if Account.objects.filter(nim=nim).exists():
                    dilewati += 1
                    continue

                Account.objects.create_user(
                    nim=nim,
                    email=email,
                    password=nim,
                    first_name=first_name,
                    last_name=last_name,
                    role='voter',
                    prodi=prodi
                )
                sukses += 1
            messages.success(request, f"Berhasil mengimpor {sukses} data pengguna. {dilewati} data dilewati karena NIM sudah ada.")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat impor: {e}")

        return redirect('admin:user_list')