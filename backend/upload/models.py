from django.db import models
from django.utils.translation import gettext_lazy as _


class Image(models.Model):
    """
    Модель для хранения информации о изображениях.

    ### Args:
    - created_at (`DateTimeField`): Дата и время создания изображения (автоматически добавляется при создании).
    - image_id (`UUIDField`): Уникальный идентификатор изображения.
    - image_webp (`ImageField`): Ссылка на изображение в формате webp.
    - image_crop (`ImageField`): Ссылка на сжатое изображение размером до 300x300 пикселей в формате webp.
    - image_base64 (`TextField`, необязательный): Изображение в формате base64 (может быть пустым).
    - is_created (`BooleanField`): Флаг, указывающий, было ли изображение создано на сервере.

    """
    created_at = models.DateTimeField(_('дата и время создания'), auto_now_add=True)
    image_id = models.UUIDField(_('ID картинки'), db_index=True)
    image_webp = models.ImageField(_('ссылка на картинку в формате webp'))
    image_crop = models.ImageField(_('ссылка на сжатую до 300*300px картинку в формате webp'))
    image_base64 = models.TextField(_('картинка в base64'), null=True, blank=True)
    is_created = models.BooleanField(_('фото на сервере созданы'), default=False)

    class Meta:
        verbose_name = 'картинка'
        verbose_name_plural = 'картинки'

    def __str__(self):
        return f'{self.image_id}'
