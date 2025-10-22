from django.db import models
from django.contrib.auth.hashers import make_password

class UserProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=256)  # hashed password
    office_email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        # Hash password before saving
        self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username