from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from main.models import *

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class PemilihanListView(View):
    def get(self, request):
        search_query = request.GET.get('q', '')
        sort_by = request.GET.get('sort', 'waktu_mulai')
        direction = request.GET.get('dir', 'desc')
        order = sort_by if direction == 'asc' else f'-{sort_by}'

        pemilihan_qs = Pemilihan.objects.annotate(jumlah_pemilih=Count('pemilih'))

        if search_query:
            pemilihan_qs = pemilihan_qs.filter(
                Q(nama__icontains=search_query) |
                Q(deskripsi__icontains=search_query)
            )

        pemilihan_qs = pemilihan_qs.order_by(order)

        per_page = request.GET.get('per_page', '10')
        paginator = Paginator(pemilihan_qs, int(per_page))
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        semua_mahasiswa = Account.objects.exclude(is_superuser=True)
        prodi_list = sorted(
            set(m.prodi for m in semua_mahasiswa if m.prodi),
            key=lambda p: (p.fakultas.nama, p.nama)
        )

        angkatan_list = sorted(set(mahasiswa.nim[:2] for mahasiswa in semua_mahasiswa if mahasiswa.nim and len(mahasiswa.nim) >= 2), key=lambda x: int(x))


        context = {
            'daftar_pemilihan': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'sort_by': sort_by,
            'direction': direction,
            'per_page': per_page,
            'field_labels': [
                ('nama', 'Nama'),
                ('waktu_mulai', 'Mulai'),
                ('waktu_selesai', 'Selesai'),
                ('status', 'Status'),
            ],
            'semua_mahasiswa': semua_mahasiswa,
            'angkatan_list': angkatan_list,
            'prodi_list': prodi_list,
        }

        return render(request, 'admin/pemilihan_list.html', context)


@method_decorator(login_required(login_url='main:login'), name='dispatch')
class AddPemilihanView(View):
    def post(self, request):
        nama = request.POST.get('nama')
        deskripsi = request.POST.get('deskripsi')
        waktu_mulai = request.POST.get('waktu_mulai')
        waktu_selesai = request.POST.get('waktu_selesai')

        try:
            Pemilihan.objects.create(
                nama=nama,
                deskripsi=deskripsi,
                waktu_mulai=waktu_mulai,
                waktu_selesai=waktu_selesai
            )
            messages.success(request, "Pemilihan berhasil ditambahkan.")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan pemilihan: {e}")

        return redirect('admin:pemilihan_list')


@method_decorator(login_required(login_url='main:login'), name='dispatch')
class EditPemilihanView(View):
    def post(self, request):
        id = request.POST.get('id')
        nama = request.POST.get('nama')
        deskripsi = request.POST.get('deskripsi')
        waktu_mulai = request.POST.get('waktu_mulai')
        waktu_selesai = request.POST.get('waktu_selesai')

        try:
            pemilihan = Pemilihan.objects.get(id=id)
            pemilihan.nama = nama
            pemilihan.deskripsi = deskripsi
            pemilihan.waktu_mulai = waktu_mulai
            pemilihan.waktu_selesai = waktu_selesai
            pemilihan.save()

            messages.success(request, "Pemilihan berhasil diperbarui.")
        except Pemilihan.DoesNotExist:
            messages.error(request, "Pemilihan tidak ditemukan.")
        except Exception as e:
            messages.error(request, f"Gagal mengedit pemilihan: {e}")

        return redirect('admin:pemilihan_list')


@method_decorator(login_required, name='dispatch')
class DeletePemilihanView(View):
    def get(self, request, id):
        try:
            pemilihan = Pemilihan.objects.get(id=id)
            pemilihan.delete()
            messages.success(request, "Pemilihan berhasil dihapus.")
        except Pemilihan.DoesNotExist:
            messages.error(request, "Pemilihan tidak ditemukan.")
        except Exception as e:
            messages.error(request, f"Gagal menghapus pemilihan: {e}")

        return redirect('admin:pemilihan_list')
    

# Manajemen Kandidat  
@method_decorator(login_required(login_url='main:login'), name='dispatch') 
class TambahKandidatView(View):
    def post(self, request, pemilihan_id):
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)
        ketua_nim = request.POST.get('ketua')
        wakil_nim = request.POST.get('wakil')
        nomor_urut = request.POST.get('nomor_urut')
        visi = request.POST.get('visi')
        misi = request.POST.get('misi')
        proker = request.POST.get('proker')
        foto = request.FILES.get('foto')

        # Validasi nomor urut wajib angka positif
        if not nomor_urut or not nomor_urut.isdigit() or int(nomor_urut) <= 0:
            messages.error(request, "Nomor urut harus berupa angka positif.")
            return redirect('admin:pemilihan_list')

        nomor_urut = int(nomor_urut)

        try:
            ketua = Account.objects.get(nim=ketua_nim)
        except Account.DoesNotExist:
            messages.error(request, f"NIM Ketua '{ketua_nim}' tidak ditemukan.")
            return redirect('admin:pemilihan_list')

        wakil = None
        if wakil_nim:
            if wakil_nim == ketua_nim:
                messages.error(request, "NIM Ketua dan Wakil tidak boleh sama.")
                return redirect('admin:pemilihan_list')
            try:
                wakil = Account.objects.get(nim=wakil_nim)
            except Account.DoesNotExist:
                messages.error(request, f"NIM Wakil '{wakil_nim}' tidak ditemukan.")
                return redirect('admin:pemilihan_list')

        # Cek apakah nomor urut sudah dipakai di pemilihan ini
        if Kandidat.objects.filter(pemilihan=pemilihan, nomor_urut=nomor_urut).exists():
            messages.error(request, f"Nomor urut {nomor_urut} sudah digunakan dalam pemilihan ini.")
            return redirect('admin:pemilihan_list')

        # Cek apakah ketua/wakil sudah pernah didaftarkan
        if Kandidat.objects.filter(pemilihan=pemilihan).filter(ketua=ketua).exists() or \
           Kandidat.objects.filter(pemilihan=pemilihan).filter(wakil=ketua).exists():
            messages.error(request, f"Ketua dengan NIM '{ketua_nim}' sudah menjadi kandidat.")
            return redirect('admin:pemilihan_list')

        if wakil and (Kandidat.objects.filter(pemilihan=pemilihan).filter(ketua=wakil).exists() or \
                      Kandidat.objects.filter(pemilihan=pemilihan).filter(wakil=wakil).exists()):
            messages.error(request, f"Wakil dengan NIM '{wakil_nim}' sudah menjadi kandidat.")
            return redirect('admin:pemilihan_list')

        Kandidat.objects.create(
            pemilihan=pemilihan,
            ketua=ketua,
            wakil=wakil,
            nomor_urut=nomor_urut,
            visi=visi,
            misi=misi,
            proker=proker,
            foto=foto
        )
        messages.success(request, "Kandidat berhasil ditambahkan.")
        return redirect(f"{reverse('admin:pemilihan_list')}?open={pemilihan.id}")

@method_decorator(login_required(login_url='main:login'), name='dispatch') 
class EditKandidatView(View):
    def post(self, request, pemilihan_id, pk):
        kandidat = get_object_or_404(Kandidat, pk=pk, pemilihan_id=pemilihan_id)

        ketua_nim = request.POST.get('ketua')
        wakil_nim = request.POST.get('wakil')
        nomor_urut = request.POST.get('nomor_urut')
        visi = request.POST.get('visi')
        misi = request.POST.get('misi')
        proker = request.POST.get('proker')
        foto = request.FILES.get('foto')

        try:
            ketua = Account.objects.get(nim=ketua_nim)
            wakil = Account.objects.get(nim=wakil_nim) if wakil_nim else None

            # Validasi nomor urut unik
            if Kandidat.objects.filter(pemilihan_id=pemilihan_id, nomor_urut=nomor_urut).exclude(pk=pk).exists():
                messages.error(request, "Nomor urut sudah digunakan oleh kandidat lain.")
                return redirect(reverse('admin:pemilihan_list') + f"#kandidat-{pemilihan_id}")

            kandidat.ketua = ketua
            kandidat.wakil = wakil
            kandidat.nomor_urut = nomor_urut
            kandidat.visi = visi
            kandidat.misi = misi
            kandidat.proker = proker
            if foto:
                kandidat.foto = foto
            kandidat.save()
            messages.success(request, "Kandidat berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal mengedit kandidat: {e}")

        return redirect(f"{reverse('admin:pemilihan_list')}?open={pemilihan_id}")

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class DeleteKandidatView(View):
    def post(self, request, pemilihan_id, pk):
        kandidat = get_object_or_404(Kandidat, pk=pk, pemilihan_id=pemilihan_id)
        kandidat.delete()
        messages.success(request, "Kandidat berhasil dihapus.")
        return redirect(f"{reverse('admin:pemilihan_list')}?open={pemilihan_id}")
    

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class AturPemilihView(View):
    def post(self, request, pemilihan_id):
        pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)
        pemilih_nim_list = request.POST.getlist('pemilih')
        pemilih_qs = Account.objects.filter(nim__in=pemilih_nim_list)
        pemilihan.pemilih.set(pemilih_qs)
        messages.success(request, "Daftar pemilih berhasil diperbarui.")
        return redirect(f"{reverse('admin:pemilihan_list')}?open={pemilihan_id}")