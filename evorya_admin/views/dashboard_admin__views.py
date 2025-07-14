from django.utils import timezone
from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from main.models import *

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class DashboardAdminView(View):
    def get(self, request):
        user = request.user
        total_suara_mencurigakan = Suara.objects.filter(is_suspicious=True).count()

        rekomendasi_ganti_password = False
        if not request.session.get('password_checked_admin'):
            if user.check_password(user.nim):
                rekomendasi_ganti_password = True
            request.session['password_checked_admin'] = True

        now = timezone.localtime(timezone.now())
        semua_pemilihan = Pemilihan.objects.all()

        total_pemilih = Account.objects.filter(is_superuser=False).count()
        total_suara = Suara.objects.count()
        partisipasi_total = (total_suara / total_pemilih * 100) if total_pemilih > 0 else 0

        pemilihan_aktif_qs = semua_pemilihan.filter(waktu_mulai__lte=now, waktu_selesai__gte=now)
        pemilihan_aktif = []

        for p in pemilihan_aktif_qs:
            jumlah_pemilih = p.pemilih.count()
            jumlah_suara = p.suara_list.count()
            partisipasi = (jumlah_suara / jumlah_pemilih * 100) if jumlah_pemilih > 0 else 0

            pemilihan_aktif.append({
                'id': p.id,
                'nama': p.nama,
                'waktu_mulai': p.waktu_mulai,
                'waktu_selesai': p.waktu_selesai,
                'partisipasi': round(partisipasi),
            })

        context = {
            'total_pemilih': total_pemilih,
            'jumlah_pemilihan_aktif': pemilihan_aktif_qs.count(),
            'total_suara': total_suara,
            'partisipasi_total': round(partisipasi_total),
            'pemilihan_aktif': pemilihan_aktif,
            'rekomendasi_ganti_password': rekomendasi_ganti_password,
            'total_kecurangan': total_suara_mencurigakan,
        }

        return render(request, 'admin/dashboard_admin.html', context)