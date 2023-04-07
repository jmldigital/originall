from django.db import models



class StopWords(models.Model):
    words = models.TextField()


class AddFiles(models.Model): 

    words = models.ForeignKey(StopWords, on_delete = models.CASCADE, limit_choices_to={'id': 1},null=True)
    files = models.FileField(upload_to='',null=True)
    oem_field = models.CharField(max_length=30, verbose_name='номер детали',blank=True,null=True)
    brend_field = models.CharField(max_length=70, verbose_name='бренд',blank=True,null=True)
    name_field = models.CharField(max_length=130, verbose_name='название детали',blank=True,null=True)
    weight_field = models.CharField(max_length=130, verbose_name='вес',blank=True,null=True)
    volume_field = models.CharField(max_length=130, verbose_name='объем',blank=True,null=True)

def __str__(self):
    return self.words