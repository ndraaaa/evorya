from datetime import timedelta
from django.utils.timezone import now, localtime
from main.models import TokenVote, Suara

def deteksi_kecurangan(suara):
    """
    Fungsi untuk mendeteksi potensi kecurangan dalam voting.
    Parameter:
        suara: instance Suara
    Return:
        (bool, str) → status mencurigakan dan alasan dalam bentuk string
    """
    alasan = []
    mencurigakan = False

    waktu = localtime(suara.waktu)
    now_time = localtime(now())
    user = suara.pemilih
    ip = suara.ip_address
    ua = suara.user_agent
    pemilihan = suara.pemilihan

    # RULE 1: IP digunakan oleh lebih dari 3 akun
    count_ip = Suara.objects.filter(
        pemilihan=pemilihan,
        ip_address=ip
    ).exclude(pemilih=user).count()
    if count_ip >= 3:
        mencurigakan = True
        alasan.append("IP digunakan oleh lebih dari 3 akun berbeda.")

    # RULE 2: Token digunakan terlalu cepat setelah dikirim
    token = TokenVote.objects.filter(pemilihan=pemilihan, pemilih=user).first()
    if token and token.waktu_dibuat:
        waktu_token = localtime(token.waktu_dibuat)
        selisih = (waktu - waktu_token).total_seconds()
        if selisih < 5:
            mencurigakan = True
            alasan.append("Token digunakan terlalu cepat (<5 detik setelah dikirim).")

    # RULE 3: User-Agent berbeda dalam 1 pemilihan
    ua_list = Suara.objects.filter(
        pemilihan=pemilihan, pemilih=user
    ).values_list('user_agent', flat=True)
    if len(set(ua_list)) > 1:
        mencurigakan = True
        alasan.append("User agent berbeda-beda dalam 1 pemilihan.")

    # RULE 4: IP berubah-ubah dalam 1 pemilihan
    ip_list = Suara.objects.filter(
        pemilihan=pemilihan, pemilih=user
    ).values_list('ip_address', flat=True)
    if len(set(ip_list)) > 1:
        mencurigakan = True
        alasan.append("IP address berubah-ubah dalam 1 pemilihan.")

    # RULE 5: Waktu voting di luar jam wajar
    if waktu.hour < 5 or waktu.hour > 23:
        mencurigakan = True
        alasan.append("Voting dilakukan di luar jam wajar (05.00–23.00 WIB).")

    return mencurigakan, "; ".join(alasan) if alasan else None
