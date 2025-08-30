from django.contrib.auth.models import AbstractBaseUser, UserManager,PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(UserManager):
    def _create_user(self,email,password,**extra_fields):
        if not email:
            raise ValueError("You have not provided a valid e-mail address")
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_user(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',False)
        extra_fields.setdefault('is_superuser',False)
        
        return self._create_user(email,password,**extra_fields)
    
    def create_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        
        return self._create_user(email,password,**extra_fields)
    
    
class User(AbstractBaseUser,PermissionsMixin):
    # Role choices for the system
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Administrator'),
    ]
    
    # Basic user fields
    email = models.EmailField(blank=True, default='', unique=True)
    name = models.CharField(max_length=255, blank=True, default='')
    
    # Role-based access control
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='patient',
        help_text='User role in the system'
    )
    
    # Contact information
    contact_info = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional contact information (phone, address, etc.)'
    )
    
    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Custom manager
    objects = CustomUserManager()
    
    # Authentication fields
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.get_role_display()}"
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name or self.email.split('@')[0]
    
    # Role-based helper methods
    def is_patient(self):
        return self.role == 'patient'
    
    def is_doctor(self):
        return self.role == 'doctor'
    
    def is_admin(self):
        return self.role == 'admin'
    
    
    
    
    
