from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Appointment(models.Model):
    """
    Appointment model for managing patient-doctor meetings
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        limit_choices_to={'role': 'patient'},
        help_text='Patient who booked the appointment'
    )
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'},
        help_text='Doctor assigned to the appointment'
    )
    
    # Appointment details
    date_time = models.DateTimeField(
        help_text='Date and time of the appointment'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the appointment'
    )
    
    # Additional information
    reason = models.TextField(
        blank=True,
        help_text='Reason for the appointment'
    )
    
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the appointment'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_time']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        # Ensure no double-booking for the same doctor at the same time
        unique_together = ['doctor', 'date_time']
    
    def __str__(self):
        return f"{self.patient.name} with Dr. {self.doctor.name} on {self.date_time.strftime('%B %d, %Y at %I:%M %p')}"
    
    def is_upcoming(self):
        """Check if appointment is in the future"""
        return self.date_time > timezone.now()
    
    def can_be_cancelled(self):
        """Check if appointment can still be cancelled"""
        return self.status in ['pending', 'confirmed'] and self.is_upcoming()


class MedicalRecord(models.Model):
    """
    Medical record for storing consultation details
    """
    # Relationships
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_records',
        limit_choices_to={'role': 'patient'},
        help_text='Patient this record belongs to'
    )
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_given',
        limit_choices_to={'role': 'doctor'},
        help_text='Doctor who conducted the consultation'
    )
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='medical_records',
        help_text='Appointment this record is associated with'
    )
    
    # Medical information
    symptoms = models.TextField(
        help_text='Patient symptoms and complaints'
    )
    
    diagnosis = models.TextField(
        help_text='Doctor\'s diagnosis'
    )
    
    prescription = models.TextField(
        blank=True,
        help_text='Prescribed medications and treatments'
    )
    
    notes = models.TextField(
        blank=True,
        help_text='Additional medical notes'
    )
    
    # Vital signs (optional)
    blood_pressure = models.CharField(
        max_length=20,
        blank=True,
        help_text='Blood pressure reading (e.g., 120/80)'
    )
    
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Body temperature in Celsius'
    )
    
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Patient weight in kg'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
    
    def __str__(self):
        return f"Medical record for {self.patient.name} by Dr. {self.doctor.name} on {self.created_at.strftime('%B %d, %Y')}"


class PatientProfile(models.Model):
    """
    Extended profile information for patients
    """
    # One-to-one relationship with User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        limit_choices_to={'role': 'patient'}
    )
    
    # Personal information
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text='Patient\'s date of birth'
    )
    
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ],
        blank=True,
        help_text='Patient\'s gender'
    )
    
    # Medical information
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True,
        help_text='Patient\'s blood type'
    )
    
    allergies = models.TextField(
        blank=True,
        help_text='Known allergies (medications, foods, etc.)'
    )
    
    medical_history = models.TextField(
        blank=True,
        help_text='Previous medical conditions and surgeries'
    )
    
    # Emergency contact
    emergency_contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name of emergency contact person'
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Phone number of emergency contact'
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text='Relationship to patient (e.g., spouse, parent)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.name}"
    
    def get_age(self):
        """Calculate patient's age"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

