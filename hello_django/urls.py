from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from upload.views import stop_create,image_upload,Words_update,file_delete

urlpatterns = [
    path("", image_upload, name="upload"),
    path(r'^delete/(?P<id>[0-9]+)/$', file_delete, name='delete_view'),
    path("stopcreate", stop_create, name="create"),
    path("edit/<int:pk>/", Words_update, name="update"),
    path("admin/", admin.site.urls),
    #path('edit/<int:pk>/', WordsUpdate.as_view(), name='stop-update')
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
