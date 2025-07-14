from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from main.models import *
import json

@method_decorator(login_required(login_url='main:login'), name='dispatch')
class HasilPemilihanView(TemplateView):
    template_name = 'admin/hasil_pemilihan.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        semua_pemilihan = Pemilihan.objects.all().order_by('-waktu_mulai')
        pemilihan_id = self.request.GET.get('pemilihan_id')

        pemilihan = None
        suara_kandidat = []
        total_suara = 0
        jumlah_pemilih = 0
        partisipasi = 0
        names = []
        values = []

        if pemilihan_id:
            pemilihan = get_object_or_404(Pemilihan, id=pemilihan_id)

            # Hitung jumlah suara per kandidat
            suara_dict = dict(
                Suara.objects.filter(pemilihan=pemilihan)
                .values_list('kandidat_id')
                .annotate(jumlah=Count('id'))
            )
            total_suara = sum(suara_dict.values())
            jumlah_pemilih = pemilihan.pemilih.count()
            partisipasi = (total_suara / jumlah_pemilih * 100) if jumlah_pemilih > 0 else 0

            # Ambil semua kandidat dari pemilihan
            kandidat_qs = Kandidat.objects.filter(pemilihan=pemilihan).select_related('ketua', 'wakil').order_by('nomor_urut')

            for kandidat in kandidat_qs:
                jumlah = suara_dict.get(kandidat.id, 0)
                persentase = (jumlah / total_suara * 100) if total_suara > 0 else 0

                # tambahkan atribut ke objek kandidat
                kandidat.jumlah = jumlah
                kandidat.persentase = round(persentase, 2)

                # untuk chart
                label_nama = kandidat.ketua.get_full_name()
                if kandidat.wakil:
                    label_nama += f" & {kandidat.wakil.get_full_name()}"

                names.append(label_nama)
                values.append(jumlah)

                suara_kandidat.append(kandidat)

        context.update({
            'semua_pemilihan': semua_pemilihan,
            'pemilihan': pemilihan,
            'suara_kandidat': suara_kandidat,
            'jumlah_pemilih': jumlah_pemilih,
            'total_suara': total_suara,
            'persentase_partisipasi': round(partisipasi, 2),
            'names': json.dumps(names),
            'values': json.dumps(values),
        })

        return context