from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# from upload.views.views_a import *


from upload.views.views_a import stop_create,price_upload,file_delete,words_delete,brands_create,brands_delete,bd_create,price_create,download,BD_delete,BD_update,stop_words_upload

urlpatterns = [
    path("", price_upload, name="upload"),
    # path(r'^$', words_asJson, name='words-asJson'),
    path('delete/<int:id>', words_delete, name='delete-words'),
    # path('', words_delete, name='delete-words'),
    path('delpr/<int:id>', file_delete, name='delete-file'),
    # path(r'^delbr/(?P<id>[0-9]+)/$', brands_delete, name='brands-delete'),
    path('delbr/<int:id>', brands_delete, name='brands-delete'),
    path("brandscreate", brands_create, name="brands-create"),
    path("bd", bd_create, name="bd-create"),
    # path('loadpr/<int:id>', price_load, name='load-price'),
    path('lcreatepr/<int:id>', price_create, name='create-price'),
    path('download/', download, name='download'),
    # path('search/', SearchResultsView.as_view(), name='search_results'),
    # path("edit/<int:pk>/", Words_update, name="update"),
    path("bddel/<int:id>/", BD_delete, name="BD-delete"),
    path("admin/", admin.site.urls),
    path('edit/<int:pk>/', BD_update.as_view(), name='bd-update'),
    path('stopupload/', stop_words_upload, name='stop-upload')

    
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
