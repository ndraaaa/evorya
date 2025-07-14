from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from main.utils import deteksi_kecurangan
from main.models import *

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class VotePageView(View):
    def get(self, request, pemilihan_id):
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)
        
        # Cek apakah user berhak memilih
        if request.user not in pemilihan.pemilih.all():
            messages.error(request, "Anda tidak berhak memilih dalam pemilihan ini.")
            return redirect('voters:home')

        # Cek apakah sudah memilih
        if Suara.objects.filter(pemilihan=pemilihan, pemilih=request.user).exists():
            messages.warning(request, "Anda sudah memberikan suara.")
            return redirect('voters:hasil_pemilihan', pemilihan.id)

        kandidat_list = pemilihan.kandidat_list.all().order_by('nomor_urut')
        return render(request, 'voter/vote_page.html', {
            'pemilihan': pemilihan,
            'kandidat_list': kandidat_list,
        })

    def post(self, request, pemilihan_id):
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)
        kandidat_id = request.POST.get('kandidat')

        if not kandidat_id:
            messages.error(request, "Silakan pilih salah satu kandidat.")
            return redirect('voters:vote_page', pemilihan.id)

        kandidat = get_object_or_404(Kandidat, id=kandidat_id, pemilihan=pemilihan)

        # Cek ulang apakah sudah memilih
        if Suara.objects.filter(pemilihan=pemilihan, pemilih=request.user).exists():
            messages.warning(request, "Anda sudah memberikan suara.")
            return redirect('voters:hasil_pemilihan', pemilihan.id)

        # Simpan suara
        Suara.objects.create(
            pemilihan=pemilihan,
            pemilih=request.user,
            kandidat=kandidat,
        )

        messages.success(request, "Terima kasih, suara Anda telah terekam.")
        return redirect('voters:hasil_pemilihan', pemilihan.id)

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class SendTokenView(View):
    def get(self, request, pemilihan_id):
        user = request.user
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)

        if user not in pemilihan.pemilih.all():
            messages.error(request, "Anda tidak terdaftar sebagai pemilih pada pemilihan ini.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan_id)

        if pemilihan.status != 'Berlangsung':
            messages.error(request, "Pemilihan belum dimulai atau sudah selesai.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan_id)

        token_obj, created = TokenVote.objects.get_or_create(
            pemilihan=pemilihan,
            pemilih=user,
            defaults={'token': get_random_string(12).upper()}
        )

        if not created and token_obj.digunakan:
            messages.error(request, "Token Anda sudah digunakan.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan_id)

        try:
            vote_url = request.build_absolute_uri(
                reverse('voters:vote_page', args=[pemilihan.id]) + f"?token={token_obj.token}"
            )

            message = f"""
            Hai {user.full_name},

            Berikut adalah token untuk mengikuti pemilihan: {pemilihan.nama}

            🔐 Token Anda: {token_obj.token}

            Klik link berikut untuk langsung memilih:
            {vote_url}

            Token ini hanya bisa digunakan sekali dan berlaku hingga {pemilihan.waktu_selesai.strftime('%d %B %Y %H:%M')}.

            Jangan bagikan token ini kepada orang lain.

            Terima kasih,
            Panitia Pemira UNJAYA
            """

            send_mail(
                subject=f"Token Voting: {pemilihan.nama}",
                message=message.strip(),
                from_email='ip06102000@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
                )

            messages.success(request, "Token berhasil dikirim ke email Anda.")
        except Exception as e:
            messages.error(request, f"Gagal mengirim email: {str(e)}")

        return redirect('voters:vote_page', pemilihan_id=pemilihan_id)

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class SubmitVoteView(View):
    def post(self, request, pemilihan_id):
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)
        user = request.user
        token_input = request.POST.get('token')
        kandidat_id = request.POST.get('kandidat')

        # Validasi pemilih
        if not pemilihan.pemilih.filter(pk=user.pk).exists():
            messages.error(request, "Anda tidak terdaftar sebagai pemilih.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan.id)

        if Suara.objects.filter(pemilihan=pemilihan, pemilih=user).exists():
            messages.warning(request, "Anda sudah memberikan suara.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan.id)

        # Validasi token
        try:
            token = TokenVote.objects.get(pemilihan=pemilihan, pemilih=user, token=token_input)
        except TokenVote.DoesNotExist:
            messages.error(request, "Token tidak valid.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan.id)

        if token.digunakan:
            messages.error(request, "Token sudah digunakan.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan.id)

        if token.expired_at and timezone.now() > token.expired_at:
            messages.error(request, "Token sudah kedaluwarsa.")
            return redirect('voters:vote_page', pemilihan_id=pemilihan.id)

        # Validasi kandidat
        kandidat = get_object_or_404(Kandidat, id=kandidat_id, pemilihan=pemilihan)

        # Ambil informasi IP dan user-agent
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Simpan suara
        suara = Suara.objects.create(
            pemilihan=pemilihan,
            kandidat=kandidat,
            pemilih=user,
            ip_address=ip,
            user_agent=user_agent
        )

        # Tandai token digunakan
        token.digunakan = True
        token.waktu_digunakan = timezone.now()
        token.save()

        # Deteksi kecurangan
        kecurigaan, alasan = deteksi_kecurangan(suara)
        if kecurigaan:
            suara.is_suspicious = True
            suara.alasan_kecurangan = alasan
            suara.save()
            messages.warning(request, "Voting Anda berhasil, namun aktivitas Anda terdeteksi mencurigakan.")
        else:
            messages.success(request, "Suara Anda berhasil dikirim.")

        return redirect('voters:home')