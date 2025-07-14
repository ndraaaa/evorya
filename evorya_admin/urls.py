from django.urls import path, include
from .views import *

app_name = 'admin'
urlpatterns = [
    path('', include([
        path('dashboard-admin/', dashboard_admin__views.DashboardAdminView.as_view(), name='dashboard_admin'),
	])),

    path('account/', include([
        path('', UserListView.as_view(), name='user_list'),
        path('add-user/', AddUserView.as_view(), name='add_user'),
        path('edit-user/', EditUserView.as_view(), name='edit_user'),
        path('delete/<str:nim>/', DeleteUserView.as_view(), name='delete_user'),
        path('import/', ImportUserView.as_view(), name='import_user'),
    ])),

    path('pemilihan/', include([
        path('', PemilihanListView.as_view(), name='pemilihan_list'),
        path('add-voting/', AddPemilihanView.as_view(), name='add_pemilihan'),
        path('edit-voting/', EditPemilihanView.as_view(), name='edit_pemilihan'),
        path('delete/<int:id>/', DeletePemilihanView.as_view(), name='delete_pemilihan'),
        path('<int:pemilihan_id>/kandidat/', TambahKandidatView.as_view(), name='tambah_kandidat'),
        path('<int:pemilihan_id>/kandidat/<int:pk>/edit/', EditKandidatView.as_view(), name='edit_kandidat'),
        path('<int:pemilihan_id>/kandidat/<int:pk>/delete/', DeleteKandidatView.as_view(), name='delete_kandidat'),
        path('<int:pemilihan_id>/atur-pemilih', AturPemilihView.as_view(), name='atur_pemilih'),
    ])),

    path('hasil-pemilihan/', include([
        path('', HasilPemilihanView.as_view(), name='hasil_pemilihan'),
    ])),

    path('suara-mencurigkan/', include([
        path('', SuaraMencurigakanView.as_view(), name='suara_mencurigakan'),
        path('export-mencurigakan/', ExportSuaraMencurigakanCSVView.as_view(), name='export_suara_mencurigakan_csv'),
        path('export/all', ExportSuaraMencurigakanCSVView.as_view(), name='export_all'),
    ]))
]