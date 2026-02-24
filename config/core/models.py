from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class User(AbstractUser):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

class TenantAwareModel(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True