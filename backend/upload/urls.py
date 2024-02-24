from django.urls import include, path
from upload import views

urlpatterns = [
    path('photo/', views.upload_photo, name='upload_image'),
    path(
        'json/',
        include([
            path('image-uploaded/', views.ImageAsUploaded.as_view(), name='json_image_uploaded'),
            path('get-image-load-meta/', views.GetImagesLoadMeta.as_view(), name='json_get_image_load_meta'),
        ])
    ),
]
