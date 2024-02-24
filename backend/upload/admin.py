from django.contrib import admin
from upload.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass
