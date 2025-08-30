from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

from authuser.models import User
from .models import Appointment, MedicalRecord, PatientProfile
from .serializers import (
    UserSerializer, UserLoginSerializer, PatientProfileSerializer,
    AppointmentSerializer, MedicalRecordSerializer, AppointmentListSerializer,
    MedicalRecordListSerializer, DashboardStatsSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (registration, profile updates)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allow registration
    
    def get_permissions(self):
        """Customize permissions based on action"""
        if self.action in ['create']:
            return [permissions.AllowAny]  # Anyone can register
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated]  # Users can only edit their own profile
        else:
            return [IsAdminUser]  # Only admins can list/delete users
    
    def create(self, request, *args, **kwargs):
        """User registration"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get user profile - users can only see their own profile"""
        user = self.get_object()
        if request.user != user and not request.user.is_admin():
            return Response(
                {'error': 'You can only view your own profile'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user profile - users can only edit their own profile"""
        user = self.get_object()
        if request.user != user and not request.user.is_admin():
            return Response(
                {'error': 'You can only edit your own profile'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication (login, logout)
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """User login"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # In a real app, you'd generate JWT tokens here
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for patient profile management
    """
    queryset = PatientProfile.objects.all()
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        if self.request.user.is_admin():
            return PatientProfile.objects.all()  # Admins see all
        elif self.request.user.is_doctor():
            # Doctors see profiles of their patients
            patient_ids = Appointment.objects.filter(
                doctor=self.request.user
            ).values_list('patient_id', flat=True).distinct()
            return PatientProfile.objects.filter(user_id__in=patient_ids)
        else:
            # Patients only see their own profile
            return PatientProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Ensure profile is created for the authenticated user"""
        if self.request.user.is_patient():
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for appointment management
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        """Filter appointments based on user role"""
        user = self.request.user
        
        if user.is_admin():
            return Appointment.objects.all()  # Admins see all
        elif user.is_doctor():
            return Appointment.objects.filter(doctor=user)  # Doctor's appointments
        else:
            return Appointment.objects.filter(patient=user)  # Patient's appointments
    
    def perform_create(self, serializer):
        """Set patient automatically if user is a patient"""
        if self.request.user.is_patient():
            serializer.save(patient=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Doctor confirms an appointment"""
        appointment = self.get_object()
        
        if not request.user.is_doctor() or appointment.doctor != request.user:
            return Response(
                {'error': 'Only the assigned doctor can confirm appointments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.status != 'pending':
            return Response(
                {'error': 'Only pending appointments can be confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'confirmed'
        appointment.save()
        
        return Response({
            'message': 'Appointment confirmed successfully',
            'appointment': AppointmentSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Doctor marks appointment as completed"""
        appointment = self.get_object()
        
        if not request.user.is_doctor() or appointment.doctor != request.user:
            return Response(
                {'error': 'Only the assigned doctor can complete appointments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed appointments can be completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'completed'
        appointment.save()
        
        return Response({
            'message': 'Appointment completed successfully',
            'appointment': AppointmentSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        # Check if user can cancel this appointment
        if not (request.user == appointment.patient or 
                request.user == appointment.doctor or 
                request.user.is_admin()):
            return Response(
                {'error': 'You can only cancel your own appointments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not appointment.can_be_cancelled():
            return Response(
                {'error': 'This appointment cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'cancelled'
        appointment.save()
        
        return Response({
            'message': 'Appointment cancelled successfully',
            'appointment': AppointmentSerializer(appointment).data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        queryset = self.get_queryset().filter(
            date_time__gt=timezone.now(),
            status__in=['pending', 'confirmed']
        ).order_by('date_time')
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            date_time__date=today,
            status__in=['pending', 'confirmed']
        ).order_by('date_time')
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for medical record management
    """
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return MedicalRecordListSerializer
        return MedicalRecordSerializer
    
    def get_queryset(self):
        """Filter medical records based on user role"""
        user = self.request.user
        
        if user.is_admin():
            return MedicalRecord.objects.all()  # Admins see all
        elif user.is_doctor():
            return MedicalRecord.objects.filter(doctor=user)  # Doctor's records
        else:
            return MedicalRecord.objects.filter(patient=user)  # Patient's records
    
    def perform_create(self, serializer):
        """Set doctor automatically if user is a doctor"""
        if self.request.user.is_doctor():
            serializer.save(doctor=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def patient_history(self, request):
        """Get complete medical history for a patient"""
        patient_id = request.query_params.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if request.user.is_patient() and str(request.user.id) != patient_id:
            return Response(
                {'error': 'You can only view your own medical history'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.is_doctor():
            # Doctors can only see records of their patients
            patient_appointments = Appointment.objects.filter(
                doctor=request.user,
                patient_id=patient_id
            ).values_list('id', flat=True)
            
            queryset = MedicalRecord.objects.filter(
                patient_id=patient_id,
                appointment_id__in=patient_appointments
            )
        else:
            # Admins can see all records
            queryset = MedicalRecord.objects.filter(patient_id=patient_id)
        
        serializer = MedicalRecordSerializer(queryset, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for admin dashboard statistics
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        # Count users by role
        total_patients = User.objects.filter(role='patient').count()
        total_doctors = User.objects.filter(role='doctor').count()
        
        # Count appointments
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects.filter(status='pending').count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
        
        # Count medical records
        total_medical_records = MedicalRecord.objects.count()
        
        # Get common diagnoses (top 5)
        common_diagnoses = MedicalRecord.objects.values('diagnosis').annotate(
            count=Count('diagnosis')
        ).order_by('-count')[:5]
        
        stats = {
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'completed_appointments': completed_appointments,
            'total_medical_records': total_medical_records,
            'common_diagnoses': list(common_diagnoses)
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent system activity"""
        # Recent appointments
        recent_appointments = Appointment.objects.select_related(
            'patient', 'doctor'
        ).order_by('-created_at')[:10]
        
        # Recent medical records
        recent_records = MedicalRecord.objects.select_related(
            'patient', 'doctor'
        ).order_by('-created_at')[:10]
        
        return Response({
            'recent_appointments': AppointmentListSerializer(recent_appointments, many=True).data,
            'recent_records': MedicalRecordListSerializer(recent_records, many=True).data
        })


def health_check(request):
    """Simple health check endpoint for API testing"""
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    
    return Response({
        'status': 'healthy',
        'message': 'EHR API is running successfully',
        'timestamp': timezone.now().isoformat()
    })