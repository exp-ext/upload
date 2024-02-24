from typing import List
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.apps import apps
from django.conf import settings
from rest_framework import serializers

from upload.models import Image

client = settings.S3_CLIENT
BUCKET_NAME = settings.MEDIA_BUCKET_NAME


class InImageMetaSerializer(serializers.Serializer):
    """
    Сериализатор ImageMeta входящих данных для Minio.
    """
    js_id = serializers.CharField()
    file_name = serializers.CharField()


class OutImageMetaSerializer(serializers.Serializer):
    """
    Сериализатор ImageMeta полученных данных от Minio.
    """
    key = serializers.CharField()
    AWSAccessKeyId = serializers.CharField()
    policy = serializers.CharField()
    signature = serializers.CharField()
    js_id = serializers.CharField()
    django_id = serializers.UUIDField()
    url = serializers.FileField()


class GetImageMetaSerializer(serializers.Serializer):
    """
    Сериализатор для проверки данных по картинкам на получение ссылки в S3.
    """
    object_id = serializers.IntegerField()
    object_app = serializers.CharField()
    images_meta = InImageMetaSerializer(many=True)
    images_meta_response = OutImageMetaSerializer(many=True, read_only=True)

    def validate(self, data):
        object_id = data.get('object_id')
        object_app = data.get('object_app')
        images_meta = data.get('images_meta')

        if not (object_id and object_app and images_meta):
            raise serializers.ValidationError(
                {'field error': ['Missing required fields.']}
            )

        if not isinstance(images_meta, list):
            raise serializers.ValidationError(
                {'variable error': ['Images_meta should be List.']}
            )

        if len(images_meta) == 0:
            raise serializers.ValidationError(
                {'variable error': ['Count of Images must be greater than 0.']}
            )

        if not self.check_list_contains_only_dicts(images_meta):
            raise serializers.ValidationError(
                {'variable error': ['Images_meta should contain only dictionaries.']}
            )

        if not self.check_object_app_exist(object_app):
            raise serializers.ValidationError(
                {'value error': ['The application does not exist in the Object_app variable.']}
            )
        return data

    @classmethod
    def check_list_contains_only_dicts(cls, my_list: List) -> bool:
        """Проверка что все объекты в списке являются словарями.

        ## Args:
        - object_app (`str`): Имя приложения.

        ## Returns:
        - bool: True, если проверку прошли, False в противном случае.
        """
        return all(isinstance(item, dict) for item in my_list)

    @classmethod
    def check_object_app_exist(cls, object_app: str) -> bool:
        """Проверка что приложение существует в проекте.

        ## Args:
        - object_app (`str`): Имя приложения.

        ## Returns:
        - bool: True, если оно есть, False в противном случае.
        """
        all_apps = [app_config.name for app_config in apps.get_app_configs()]
        return object_app in all_apps


class ImageAsUploadedSerializer(serializers.Serializer):
    """
    Сериализатор для проверки входных данных по загруженной картинке,
    существования файла на сервере Minio и совпадении имени в БД.
    """
    presigned_url = serializers.CharField()
    django_id = serializers.UUIDField()

    def validate(self, data):
        presigned_url = data.pop('presigned_url')
        django_id = data.get('django_id')

        # Проверяем, что оба поля присутствуют
        if not presigned_url or not django_id:
            raise serializers.ValidationError({'field error': ['Missing required fields.']})

        # Проверяем существование записи в базе данных
        if self.check_file_in_db(django_id):
            raise serializers.ValidationError({'object error': ['Object already exists.']})

        url_parsed = urlparse(presigned_url)
        full_path = url_parsed.path.lstrip('/')
        key = '/'.join(full_path.split('/')[1:])

        # Проверяем существование файла в Minio
        if not self.check_file_in_minio(key):
            raise serializers.ValidationError({'object error': ['Object not uploaded to the server Minio.']})

        data['key'] = key
        return data

    @staticmethod
    def check_file_in_db(django_id) -> bool:
        """Проверка существования записи в базе данных."""
        return Image.objects.filter(image_id=django_id).exists()

    @staticmethod
    def check_file_in_minio(key) -> bool:
        """Проверка существования файла в Minio."""
        try:
            client.head_object(Bucket=BUCKET_NAME, Key=key)
            return True
        except ClientError:
            return False


class ImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для класса `Image`.
    """

    class Meta:
        model = Image
        fields = '__all__'
