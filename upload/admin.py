from django.contrib import admin
from .models import StopWords,AddFiles,Brands,OriginallBD
# Register your models here.




admin.site.register(OriginallBD)
admin.site.register(StopWords)
admin.site.register(AddFiles)
admin.site.register(Brands)
