# main/admin.py

from django.contrib import admin
from .models import Fakultas, Prodi

@admin.register(Fakultas)
class FakultasAdmin(admin.ModelAdmin):
    list_display = ['id', 'nama']

@admin.register(Prodi)
class ProdiAdmin(admin.ModelAdmin):
    list_display = ['id', 'nama', 'fakultas']
    list_filter = ['fakultas']