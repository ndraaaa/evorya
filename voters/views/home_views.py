from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from main.models import *

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class HomeView(View):
    def get(self, request, *args, **kwargs):
        user = request.user

        rekomendasi_ganti_password = False
        if user.check_password(user.nim):
            rekomendasi_ganti_password = True

        semua_pemilihan = user.pemilihan_diikuti.all().order_by('-waktu_mulai')

        data = []
        for p in semua_pemilihan:
            sudah_memilih = Suara.objects.filter(pemilihan=p, pemilih=user).exists()
            total_suara = Suara.objects.filter(pemilihan=p).count()

            kandidat_suara = []
            for k in p.kandidat_list.all():
                jumlah_suara = Suara.objects.filter(kandidat=k).count()
                persen = round((jumlah_suara / total_suara) * 100, 2) if total_suara > 0 else 0
                kandidat_suara.append({
                    'kandidat': k,
                    'jumlah_suara': jumlah_suara,
                    'persen': persen,
                })

            data.append({
                'pemilihan': p,
                'status': p.status,
                'sudah_memilih': sudah_memilih,
                'kandidat_suara': kandidat_suara,
                'total_suara': total_suara,
            })

        grouped = {
            'Berlangsung': [],
            'Akan Datang': [],
            'Selesai': [],
        }
        for item in data:
            grouped[item['status']].append(item)

        grouped_pemilihan = [
            ('Berlangsung', grouped['Berlangsung']),
            ('Akan Datang', grouped['Akan Datang']),
            ('Selesai', grouped['Selesai']),
        ]

        total_pemilihan = len(semua_pemilihan)

        return render(request, 'voter/home.html', {
            'grouped_pemilihan': grouped_pemilihan,
            'total_pemilihan': total_pemilihan,
            'rekomendasi_ganti_password': rekomendasi_ganti_password,
        })