from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from authuser.models import User
from .models import Appointment, MedicalRecord, PatientProfile
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'contact_info', 'password', 'password2', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        """Create user with validated data"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for PatientProfile model"""
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_age(self, obj):
        """Get calculated age"""
        return obj.get_age()


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model"""
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    is_upcoming = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_upcoming(self, obj):
        """Get whether appointment is in the future"""
        return obj.is_upcoming()
    
    def get_can_be_cancelled(self, obj):
        """Get whether appointment can be cancelled"""
        return obj.can_be_cancelled()
    
    def validate(self, attrs):
        """Validate appointment data"""
        # Check if patient and doctor exist and have correct roles
        try:
            patient = User.objects.get(id=attrs['patient_id'], role='patient')
            doctor = User.objects.get(id=attrs['doctor_id'], role='doctor')
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid patient or doctor ID')
        
        # Check if appointment time is in the future
        if attrs['date_time'] <= timezone.now():
            raise serializers.ValidationError('Appointment must be scheduled for the future')
        
        # Check for double-booking
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            date_time=attrs['date_time'],
            status__in=['pending', 'confirmed']
        ).first()
        
        if existing_appointment:
            raise serializers.ValidationError('Doctor is already booked at this time')
        
        return attrs


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model"""
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    appointment_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate medical record data"""
        # Check if patient, doctor, and appointment exist and have correct roles
        try:
            patient = User.objects.get(id=attrs['patient_id'], role='patient')
            doctor = User.objects.get(id=attrs['doctor_id'], role='doctor')
            appointment = Appointment.objects.get(id=attrs['appointment_id'])
        except (User.DoesNotExist, Appointment.DoesNotExist):
            raise serializers.ValidationError('Invalid patient, doctor, or appointment ID')
        
        # Verify the appointment belongs to the patient and doctor
        if appointment.patient != patient or appointment.doctor != doctor:
            raise serializers.ValidationError('Appointment does not match patient and doctor')
        
        return attrs


class AppointmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for appointment lists"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient_name', 'doctor_name', 'date_time', 'status', 'reason', 'is_upcoming']
    
    def get_is_upcoming(self, obj):
        return obj.is_upcoming()


class MedicalRecordListSerializer(serializers.ModelSerializer):
    """Simplified serializer for medical record lists"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    appointment_date = serializers.DateTimeField(source='appointment.date_time', read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = ['id', 'patient_name', 'doctor_name', 'appointment_date', 'diagnosis', 'created_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for admin dashboard statistics"""
    total_patients = serializers.IntegerField()
    total_doctors = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    pending_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    total_medical_records = serializers.IntegerField()
    common_diagnoses = serializers.ListField(child=serializers.DictField())
