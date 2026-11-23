import mimetypes
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseMediaStorage(FileSystemStorage):
    """
    Storage hybrid:
    - Di komputer lokal / filesystem yang bisa ditulisi: menyimpan file ke disk lokal (MEDIA_ROOT).
    - Di environment serverless seperti Vercel (di mana /var/task adalah read-only):
      otomatis menyimpan file ke database (model MediaFile),
      sehingga unggahan banner, foto, artikel, dan produk tidak crash karena OSError [Errno 30].
    """

    def _save(self, name, content):
        clean_name = str(name).replace("\\", "/").lstrip("/")

        # Jika dijalankan di Vercel atau jika filesystem read-only, langsung simpan ke database
        if os.getenv("VERCEL"):
            return self._save_to_database(clean_name, content)

        # Coba simpan ke disk lokal terlebih dahulu
        try:
            return super()._save(clean_name, content)
        except (OSError, PermissionError):
            return self._save_to_database(clean_name, content)

    def _save_to_database(self, clean_name, content):
        from app.models import MediaFile

        content.seek(0)
        data = content.read()
        mime_type, _ = mimetypes.guess_type(clean_name)
        mime_type = mime_type or "application/octet-stream"

        MediaFile.objects.update_or_create(
            name=clean_name,
            defaults={
                "data": data,
                "content_type": mime_type,
                "size": len(data),
            },
        )
        return clean_name

    def exists(self, name):
        clean_name = str(name).replace("\\", "/").lstrip("/")
        if super().exists(clean_name):
            return True
        try:
            from app.models import MediaFile
            return MediaFile.objects.filter(name=clean_name).exists()
        except Exception:
            return False

    def _open(self, name, mode="rb"):
        clean_name = str(name).replace("\\", "/").lstrip("/")
        if super().exists(clean_name):
            try:
                return super()._open(clean_name, mode)
            except (OSError, PermissionError):
                pass
        from app.models import MediaFile
        media_obj = MediaFile.objects.filter(name=clean_name).first()
        if media_obj:
            return ContentFile(bytes(media_obj.data), name=clean_name)
        return super()._open(clean_name, mode)

    def size(self, name):
        clean_name = str(name).replace("\\", "/").lstrip("/")
        if super().exists(clean_name):
            try:
                return super().size(clean_name)
            except (OSError, PermissionError):
                pass
        from app.models import MediaFile
        media_obj = MediaFile.objects.filter(name=clean_name).first()
        if media_obj:
            return media_obj.size
        return 0

    def delete(self, name):
        clean_name = str(name).replace("\\", "/").lstrip("/")
        try:
            super().delete(clean_name)
        except (OSError, PermissionError):
            pass
        try:
            from app.models import MediaFile
            MediaFile.objects.filter(name=clean_name).delete()
        except Exception:
            pass

    def url(self, name):
        clean_name = str(name).replace("\\", "/").lstrip("/")
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        if not media_url.endswith("/"):
            media_url += "/"
        return f"{media_url}{clean_name}"
