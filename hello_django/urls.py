from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from upload.views import stop_create,image_upload,Words_update,file_delete,words_delete,brands_create,brands_delete,bd_create

urlpatterns = [
    path("", image_upload, name="upload"),
    # path(r'^$', words_asJson, name='words-asJson'),
    path('delete/<int:id>', words_delete, name='delete-words'),
    # path('', words_delete, name='delete-words'),
    path('delpr/<int:id>', file_delete, name='delete-file'),
    # path(r'^delbr/(?P<id>[0-9]+)/$', brands_delete, name='brands-delete'),
    path('delbr/<int:id>', brands_delete, name='brands-delete'),
    path("brandscreate", brands_create, name="brands-create"),
    path("bd", bd_create, name="bd-create"),
    # path('search/', SearchResultsView.as_view(), name='search_results'),
    path("edit/<int:pk>/", Words_update, name="update"),
    path("admin/", admin.site.urls),
    #path('edit/<int:pk>/', WordsUpdate.as_view(), name='stop-update')
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
