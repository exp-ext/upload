import base64
import io
import uuid
from typing import Any, Dict, List

from botocore.exceptions import ClientError
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from PIL import Image as PIL_Image
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.celery import app
from upload.models import Image
from upload.serializers import (GetImageMetaSerializer,
                                ImageAsUploadedSerializer)

client = settings.S3_CLIENT
BUCKET_NAME = settings.MEDIA_BUCKET_NAME


def upload_photo(request):
    context = {}
    return render(request, 'upload/example.html', context)


@app.task(ignore_result=True)
def create_full_set_images(request_json):
    try:
        instance = HandlingImages(request_json)
        instance.create_full_set()
        return {'status': 'success', 'message': 'Full set of images created successfully.'}
    except ValueError as ve:
        return {'status': 'error', 'message': str(ve)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


class HandlingImages():
    """
    Приведение изображения к форматам: webp, raw, crop 64x64 и сохранение их в БД.
    """
    def __init__(self, request_json):

        self.key = request_json.get('key')
        self.img_id = request_json.get('django_id')
        if not self.key or not self.img_id:
            raise ValueError("Missing 'key' or 'django_id' in request_json")
        self.img = self.get_img()

    def get_img(self) -> PIL_Image:
        """
        Получает изображение из хранилища.

        ### Returns:
        - `PIL_Image`: Изображение.

        ### Raises:
        - ValueError: Если файл не найден или возникает ошибка при доступе к файлу.

        """
        try:
            response = client.get_object(Bucket=BUCKET_NAME, Key=self.key)
            return PIL_Image.open(io.BytesIO(response['Body'].read()))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ValueError("File not found")
            else:
                raise ValueError(f"Error while accessing a file: {e.response['Error']['Message']}")

    def create_full_set(self) -> Dict[str, Any]:
        """
        Создает полный набор изображений.

        ### Returns:
        - `Dict[str, Any]`: Словарь с информацией о созданных изображениях.

        ### Raises:
        - ValueError: Если возникает ошибка при обработке изображений в S3.

        """
        try:
            webp_bytes_io = self.process_image()
            webp_url = self.save_to_s3(webp_bytes_io, '/webp/')

            crop_bytes_io = self.process_image(thumbnail_size=(300, 300))
            crop_url = self.save_to_s3(crop_bytes_io, '/crop/')

            base64_bytes_io = self.process_image(thumbnail_size=(64, 64))
            image_base64 = 'data:image/webp;base64,' + base64.b64encode(base64_bytes_io.getvalue()).decode()

            Image.objects.create(
                image_id=self.img_id,
                image_webp=webp_url,
                image_crop=crop_url,
                image_base64=image_base64,
                is_created=True,
            )
            self.delete_from_s3()

            return f'Picture {self.img_id} in Minio and in the database were successfully created.'
        except Exception as e:
            raise ValueError(f"Error while processing images in S3: {e}")

    def process_image(self, thumbnail_size=None, format="WEBP"):
        """
        Обрабатывает изображение.

        ### Args:
        - thumbnail_size (`tuple`, optional): Размер миниатюры изображения.
        - format (`str`, optional): Формат сохраняемого изображения (по умолчанию "WEBP").

        ### Returns:
        - `io.BytesIO`: Объект BytesIO с обработанным изображением.

        """
        bytes_io = io.BytesIO()
        img = self.img.copy()
        if thumbnail_size:
            img.thumbnail(thumbnail_size)
        img.save(bytes_io, format=format)
        bytes_io.seek(0)
        return bytes_io

    def save_to_s3(self, webp_bytes_io: io.BytesIO, folder_key: str) -> str:
        """
        Сохраняет изображение в хранилище S3.

        ### Args:
        - webp_bytes_io (`io.BytesIO`): Объект BytesIO с данными изображения в формате WEBP.
        - folder_key (`str`): Ключ каталога для сохранения изображения.

        ### Returns:
        - `str`: Ключ сохраненного изображения.

        ### Raises:
        - ValueError: Если возникает ошибка при сохранении изображения в S3.

        """
        try:
            key = f'{self.key.replace("/raw/", folder_key)}.webp'
            client.put_object(
                Body=webp_bytes_io.getvalue(),
                Bucket=BUCKET_NAME,
                Key=key,
                ContentType='image/webp',
            )
            return key
        except Exception as e:
            raise ValueError(f"Error when saving an image on the S3: {e}")

    def delete_from_s3(self):
        """
        Удаляет изображение из хранилища S3.

        ### Raises:
        - ValueError: Если возникает ошибка при удалении изображения из S3.

        """
        try:
            client.delete_object(Bucket=BUCKET_NAME, Key=self.key)
        except Exception as e:
            raise ValueError(f"Error when deleting an image from S3: {e}")

    def __del__(self):
        """Уничтожение изображения при удалении объекта."""
        if hasattr(self, 'img') and self.img is not None:
            self.img.close()


class GetImagesLoadMeta(APIView):
    """
    Получение мета данных для загрузки картинки.
    """
    serializer_class = GetImageMetaSerializer

    def post(self, request: HttpRequest) -> JsonResponse:
        """Получение данных для загрузки на сервер с Minio для каждой картинки
        в списке images_meta.

        ## Args:
        - request (`HttpRequest`): запрос на получение дынных для загрузки картинки на сервер при помощи s3boto.

        ## Returns:
        - response (`JsonResponse`): словарь с данными
        """
        serializer = GetImageMetaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        object_id = serializer.validated_data['object_id']
        object_app = serializer.validated_data['object_app']
        images_meta = serializer.validated_data['images_meta']

        images_response = self.generate_upload_data_response(
            object_id,
            object_app,
            images_meta,
        )
        response = {
            'success': True,
            'images_response': images_response,
        }
        return Response(response)

    def presigned_url(self, key: str) -> Dict[str, Any]:
        """Возвращает объект, который представляет информацию о
        предварительно подписанной URL-форме для загрузки файла.

        ## Args:
        - key (`str`): Пусть и имя файла.

        ## Returns:
        - `Dict[str, Any]`: Информация о предварительно подписанной URL-форме.
        """
        return client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key
            },
            ExpiresIn=120
        )

    def generate_upload_data_response(self, object_id: int, object_app: str, images_meta: str) -> List:
        """Создание списка с словарей с данными для загрузки картинок.

        ## Args:
        - images_meta (`str`): _description_
        - shipping_app (`str`): Приложение из которого произошёл вызов.
        - shipping_obj_id (`int`): id вызова /может быть id товара или юзера/

        ## Returns:
        - `List[Dict[str, Any]]`: Список словарей с данными s3boto по картинкам для формирования запроса к серверу Minio.
        """
        images_upload_data = []
        post_data = {}
        for image in images_meta:
            django_id = uuid.uuid4()
            key = f'images/{object_app}/raw/{object_id}/{django_id}'
            post_data = {
                'url': self.presigned_url(key),
                'js_id': image['js_id'],
                'django_id': django_id
            }
            images_upload_data.append(post_data)
        return images_upload_data


class ImageAsUploaded(APIView):
    """
    Класс инициации обработки картинок после успешного добавления их через VUE.
    """
    serializer_class = ImageAsUploadedSerializer

    @extend_schema(responses={204: None, })
    def post(self, request: HttpRequest) -> HttpResponse:
        """Запуск процесса пересоздания картинок на сервере Minio и записи в БД.

        ## Args:
        - request (`HttpRequest`): Запрос с presigned_url s3boto.

        ## Returns:
        - `HttpResponse`: Ответ 204 в случае успешной проверки и отправки задания на пересоздание картинок или 400.
        """
        serializer = ImageAsUploadedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_full_set_images.delay(serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)
