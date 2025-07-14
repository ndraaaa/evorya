import csv
from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from main.models import *
from django.utils.timezone import localtime
from datetime import timedelta

class SuaraMencurigakanView(View):
    def get(self, request):
        suara_mencurigakan = Suara.objects.filter(is_suspicious=True).select_related('pemilihan', 'pemilih', 'kandidat')
        context = {
            'suara_mencurigakan': suara_mencurigakan
        }
        return render(request, 'admin/suara_mencurigakan.html', context)
    
class ExportSuaraMencurigakanCSVView(View):
    def get(self, request):
        # Ambil suara mencurigakan
        data = Suara.objects.filter(is_suspicious=True).select_related('pemilihan', 'pemilih', 'kandidat')

        # Siapkan response sebagai file CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suara_mencurigakan.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Waktu Vote', 'IP Address', 'User Agent',
            'Perbedaan IP', 'Perbedaan UA',
            'Selisih Waktu Token (detik)',
            'Jumlah IP Sama', 'Voting dalam 3 Menit',
            'Jam Vote', 'Label (1=mencurigakan)'
        ])

        for suara in data:
            waktu = localtime(suara.waktu)
            jam_vote = waktu.hour
            user = suara.pemilih
            pemilihan = suara.pemilihan
            ip = suara.ip_address
            ua = suara.user_agent

            # Perbedaan IP/UA
            ip_list = Suara.objects.filter(pemilihan=pemilihan, pemilih=user).values_list('ip_address', flat=True).distinct()
            ua_list = Suara.objects.filter(pemilihan=pemilihan, pemilih=user).values_list('user_agent', flat=True).distinct()
            is_ip_diff = int(len(set(ip_list)) > 1)
            is_ua_diff = int(len(set(ua_list)) > 1)

            # Token selisih waktu
            token = TokenVote.objects.filter(pemilihan=pemilihan, pemilih=user).first()
            delta_token = 0
            if token and token.waktu_dibuat:
                delta_token = (suara.waktu - token.waktu_dibuat).total_seconds()

            # Jumlah voting IP sama & dalam 3 menit
            ip_count = Suara.objects.filter(pemilihan=pemilihan, ip_address=ip).exclude(pemilih=user).count()
            recent_vote_count = Suara.objects.filter(
                ip_address=ip,
                pemilihan=pemilihan,
                waktu__gte=suara.waktu - timedelta(minutes=3)
            ).count()

            writer.writerow([
                waktu.strftime('%Y-%m-%d %H:%M:%S'),
                ip,
                ua,
                is_ip_diff,
                is_ua_diff,
                round(delta_token, 2),
                ip_count,
                recent_vote_count,
                jam_vote,
                1  # Label 1 karena semua data ini sudah mencurigakan
            ])

        return response
    
class ExportAllSuaraCSVView(View):
    def get(self, request):
        all_suara = Suara.objects.all().select_related('pemilihan', 'pemilih', 'kandidat')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="semua_data_suara.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Waktu Vote', 'IP Address', 'User Agent',
            'Perbedaan IP', 'Perbedaan UA',
            'Selisih Waktu Token (detik)',
            'Jumlah IP Sama', 'Voting dalam 3 Menit',
            'Jam Vote', 'Label (1=mencurigakan)'
        ])

        for suara in all_suara:
            waktu = localtime(suara.waktu)
            jam_vote = waktu.hour
            user = suara.pemilih
            pemilihan = suara.pemilihan
            ip = suara.ip_address
            ua = suara.user_agent

            # Cek IP/UA berubah
            ip_list = Suara.objects.filter(pemilihan=pemilihan, pemilih=user).values_list('ip_address', flat=True).distinct()
            ua_list = Suara.objects.filter(pemilihan=pemilihan, pemilih=user).values_list('user_agent', flat=True).distinct()
            is_ip_diff = int(len(set(ip_list)) > 1)
            is_ua_diff = int(len(set(ua_list)) > 1)

            # Selisih waktu token
            token = TokenVote.objects.filter(pemilihan=pemilihan, pemilih=user).first()
            delta_token = 0
            if token and token.waktu_dibuat:
                delta_token = (suara.waktu - token.waktu_dibuat).total_seconds()

            # Banyak IP yang sama digunakan
            ip_count = Suara.objects.filter(pemilihan=pemilihan, ip_address=ip).exclude(pemilih=user).count()

            # Voting dalam waktu singkat (3 menit terakhir dari IP yang sama)
            recent_vote_count = Suara.objects.filter(
                ip_address=ip,
                pemilihan=pemilihan,
                waktu__gte=suara.waktu - timedelta(minutes=3)
            ).count()

            writer.writerow([
                waktu.strftime('%Y-%m-%d %H:%M:%S'),
                ip,
                ua,
                is_ip_diff,
                is_ua_diff,
                round(delta_token, 2),
                ip_count,
                recent_vote_count,
                jam_vote,
                1 if suara.is_suspicious else 0
            ])

        return response