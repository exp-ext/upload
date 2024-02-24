from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticStorage(S3StaticStorage):
    bucket_name = settings.STATIC_BUCKET_NAME
    default_acl = 'public-read'
    file_overwrite = False


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.MEDIA_BUCKET_NAME
    default_acl = 'public-read'
    file_overwrite = False


class DataBaseStorage(S3Boto3Storage):
    bucket_name = settings.DATABASE_BUCKET_NAME
    default_acl = 'private'
    file_overwrite = False
