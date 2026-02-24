from django.db import models

from django.db import models
from core.models import TenantAwareModel

class Document(TenantAwareModel):
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name 