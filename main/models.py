from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

# Master Users (Admin & Voters)
class AccountManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, nim, password=None, **extra_fields):
        if not nim:
            raise ValueError('NIM tidak boleh kosong!')
        
        if self.model.objects.filter(nim=nim).exists():
            raise ValueError(f"Pengguna dengan NIM '{nim}' sudah ada.")
        
        user = self.model(nim=nim, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nim, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus bersifat staff')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus bersifat superuser')
        
        return self.create_user(nim, password, **extra_fields)

class Fakultas(models.Model):
    nama = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nama
    
class Prodi(models.Model):
    nama = models.CharField(max_length=100)
    fakultas = models.ForeignKey(Fakultas, on_delete=models.CASCADE, related_name='prodi_list')

    class Meta:
        unique_together = ('nama', 'fakultas')

    def __str__(self):
        return f"{self.nama} - {self.fakultas.nama}"
    
class Account(AbstractUser):
    nim = models.CharField(max_length=20, primary_key=True, unique=True)
    prodi = models.ForeignKey(Prodi, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(unique=True)
    photo_profile = models.ImageField(
        upload_to='profile/images/photo_profile/',
        null=True,
        blank=True,
        default='profile/images/photo_profile/default.png'
    )

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('voter', 'Voter'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='voter')

    username = None
    USERNAME_FIELD = 'nim'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'role']

    objects = AccountManager()

    def __str__(self):
        return f"{self.nim} - {self.full_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Master Pemilihan 
class Pemilihan(models.Model):
    nama = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True)
    waktu_mulai = models.DateTimeField()
    waktu_selesai = models.DateTimeField()
    pemilih = models.ManyToManyField(Account, related_name='pemilihan_diikuti', blank=True)

    def __str__(self):
        return self.nama

    @property
    def status(self):
        now = timezone.localtime(timezone.now())  # gunakan waktu lokal
        mulai = timezone.localtime(self.waktu_mulai)
        selesai = timezone.localtime(self.waktu_selesai)

        if mulai > now:
            return "Akan Datang"
        elif mulai <= now <= selesai:
            return "Berlangsung"
        else:
            return "Selesai"
    
    @property
    def get_kandidat_terurut(self):
        return self.kandidat_list.order_by('nomor_urut')

class Kandidat(models.Model):
    pemilihan = models.ForeignKey(Pemilihan, on_delete=models.CASCADE, related_name='kandidat_list')
    ketua = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='kandidat_ketua')
    wakil = models.ForeignKey(Account, on_delete=models.SET_NULL, related_name='kandidat_wakil', null=True, blank=True)
    visi = models.TextField()
    misi = models.TextField()
    proker = models.TextField()
    nomor_urut = models.PositiveIntegerField()
    foto = models.ImageField(
        upload_to='kandidat/',
        blank=True,
        null=True,
        default='kandidat/default.png')

    class Meta:
        unique_together = ('pemilihan', 'nomor_urut')

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return '/media/kandidat/default.png'
        
    def __str__(self):
        return f"{self.nomor_urut}. {self.ketua.full_name}"
    

class Suara(models.Model):
    pemilihan = models.ForeignKey(Pemilihan, on_delete=models.CASCADE, related_name='suara_list')
    kandidat = models.ForeignKey(Kandidat, on_delete=models.CASCADE, related_name='suara_kandidat')
    pemilih = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='suara_user')
    waktu = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    is_suspicious = models.BooleanField(default=False)
    alasan_kecurangan = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('pemilihan', 'pemilih')

    def __str__(self):
        return f"{self.pemilih.full_name} memilih {self.kandidat} di {self.pemilihan.nama}"
    

# Manajemen Token
class TokenVote(models.Model):
    pemilihan = models.ForeignKey(Pemilihan, on_delete=models.CASCADE)
    pemilih = models.ForeignKey(Account, on_delete=models.CASCADE)
    token = models.CharField(max_length=12, unique=True)
    digunakan = models.BooleanField(default=False)
    waktu_dibuat = models.DateTimeField(auto_now_add=True)
    waktu_digunakan = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField()

    class Meta:
        unique_together = ('pemilihan', 'pemilih')

    def is_expired(self):
        """Cek apakah token sudah kedaluwarsa."""
        return timezone.now() > self.expired_at

    def pakai_token(self):
        """Tandai token sudah digunakan dan simpan waktu penggunaannya."""
        self.digunakan = True
        self.waktu_digunakan = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        # Jika belum diset secara eksplisit, set expired_at sesuai waktu_selesai pemilihan
        if not self.expired_at and self.pemilihan:
            self.expired_at = self.pemilihan.waktu_selesai
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.token} - {self.pemilih.nim} ({'✓' if self.digunakan else '×'})"