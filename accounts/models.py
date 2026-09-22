from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


class UserProfile(models.Model):
    """Extended user profile with avatar, bio, and preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')],
        default='system'
    )
    language = models.CharField(max_length=10, default='en')
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def documents_count(self):
        return self.user.documents.count()

    @property
    def questions_count(self):
        return self.user.chat_messages.filter(role='user').count()


class PasswordResetOTP(models.Model):
    """Model to store OTP codes sent for password resets."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_resets')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username} ({self.otp_code})"

    def is_valid(self, expiration_minutes=10):
        """Check if OTP is valid (un-used and within validity window)."""
        if self.is_used:
            return False
        now = timezone.now()
        expiration_time = self.created_at + datetime.timedelta(minutes=expiration_minutes)
        return now <= expiration_time

