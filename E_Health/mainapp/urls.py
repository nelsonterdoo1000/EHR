from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'patient-profiles', views.PatientProfileViewSet, basename='patient-profile')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medical-record')
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Custom URL patterns (if needed)
    path('health-check/', views.health_check, name='health-check'),
]

# Add custom actions to the router
# These will be available as:
# POST /api/appointments/{id}/confirm/
# POST /api/appointments/{id}/complete/
# POST /api/appointments/{id}/cancel/
# GET /api/appointments/upcoming/
# GET /api/appointments/today/
# GET /api/medical-records/patient-history/?patient_id=123
# GET /api/dashboard/stats/
# GET /api/dashboard/recent-activity/
