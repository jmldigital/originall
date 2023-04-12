from django.db import models



class StopWords(models.Model):
    words = models.CharField(max_length=40, verbose_name='стоп слова',blank=True,null=True)

class AddFiles(models.Model): 

    files = models.FileField(upload_to='',null=True,blank=True)
    oem_field = models.CharField(max_length=30, verbose_name='номер детали',blank=True,null=True)
    brend_field = models.CharField(max_length=70, verbose_name='бренд',blank=True,null=True)
    name_field = models.CharField(max_length=130, verbose_name='название детали',blank=True,null=True)
    weight_field = models.CharField(max_length=130, verbose_name='вес',blank=True,null=True)
    volume_field = models.CharField(max_length=130, verbose_name='объем',blank=True,null=True)

# def __str__(self):
#     return self.files

class Brands(models.Model):
    id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=40, verbose_name='бренды',blank=True,null=True)
    files = models.FileField(upload_to='',null=True,blank=True)


class OriginallBD(models.Model): 

  
    oem_field = models.CharField(max_length=30, verbose_name='номер детали',blank=True,null=True)
    brend_field = models.CharField(max_length=70, verbose_name='бренд',blank=True,null=True)
    name_field = models.CharField(max_length=130, verbose_name='название детали',blank=True,null=True)
    weight_field = models.CharField(max_length=130, verbose_name='вес',blank=True,null=True)
    volume_field = models.CharField(max_length=130, verbose_name='объем',blank=True,null=True)

def __str__(self):
    return self.brend_field
