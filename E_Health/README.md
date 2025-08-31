# E-Health: Electronic Health Records System

This README.md provides:
Complete project overview with problem statement and objectives
Technical details including architecture and API endpoints
Installation instructions for easy setup
Testing examples to verify functionality
Security features highlighting data protection


## 🏥 Project Overview

E-Health is a comprehensive Electronic Health Records (EHR) system designed to address the healthcare challenges faced by facilities in Africa. This capstone project provides a secure, digital platform for patient registration, appointment management, and medical record storage.

## 🎯 Problem Statement

Many healthcare facilities in Africa rely on manual record-keeping (brown files, registers), which leads to:
- Misplaced or duplicated patient records
- Long wait times and inefficient appointment management
- No centralized system for accessing patient history
- Inability of policymakers to analyze national health trends effectively

## 🚀 Objectives

- Provide a secure digital platform for patient registration, appointments, and medical records
- Improve healthcare efficiency with appointment scheduling and reminders
- Ensure data integrity and continuity of care across clinics
- Provide reporting dashboards for administrators and government bodies

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2.5
- **API**: Django REST Framework 3.16.1
- **Database**: SQLite (Development) / MySQL (Production)
- **Authentication**: Custom User Model with Role-Based Access Control
- **Language**: Python 3.12



## 📋 Features

### 🔐 Authentication & Authorization
- Role-based access control (Patient, Doctor, Admin)
- Secure login and session management
- Custom user model with email-based authentication

### 👥 Patient Management
- Patient registration with basic demographics and contact info
- Patient profile management with medical history
- Emergency contact information storage

### 📅 Appointment Management
- Appointment booking based on doctor availability
- Appointment status tracking (Pending, Confirmed, Completed, Cancelled)
- Doctor approval and rescheduling capabilities
- Double-booking prevention

### 📋 Medical Records
- Comprehensive visit details (symptoms, diagnosis, treatment)
- Chronological history of visits per patient
- Vital signs tracking (blood pressure, temperature, weight)
- Prescription and treatment notes

### 📊 Admin Dashboard
- Patient count and visit statistics
- Common diagnoses analysis
- System activity monitoring
- Report generation capabilities

## 🏗️ System Architecture

### Database Schema
Users
├── id (Primary Key)
├── email (Unique)
├── name
├── role (patient/doctor/admin)
├── contact_info (JSON)
├── is_active
├── date_joined
Appointments
├── id (Primary Key)
├── patient_id (Foreign Key → Users)
├── doctor_id (Foreign Key → Users)
├── date_time
├── status (pending/confirmed/completed/cancelled)
├── reason
├── notes
Medical_Records
├── id (Primary Key)
├── patient_id (Foreign Key → Users)
├── doctor_id (Foreign Key → Users)
├── appointment_id (Foreign Key → Appointments)
├── symptoms
├── diagnosis
├── prescription
├── vital_signs
├── created_at
Patient_Profiles
├── id (Primary Key)
├── user_id (One-to-One → Users)
├── date_of_birth
├── gender
├── blood_type
├── allergies
├── medical_history
├── emergency_contact_info

## API Endpoints

Authentication
POST /api/auth/login/ # User login


### User Management
GET /api/users/ # List users (admin only)
POST /api/users/ # Register new user
GET /api/users/{id}/ # Get user profile
PUT /api/users/{id}/ # Update user profile
DELETE /api/users/{id}/ # Delete user (admin only)


### Patient Profiles
GET /api/patient-profiles/ # List profiles (role-filtered)
POST /api/patient-profiles/ # Create patient profile
GET /api/patient-profiles/{id}/ # Get specific profile
PUT /api/patient-profiles/{id}/ # Update profile
DELETE /api/patient-profiles/{id}/ # Delete profile


### Appointments
GET /api/appointments/ # List appointments (role-filtered)
POST /api/appointments/ # Book new appointment
GET /api/appointments/{id}/ # Get appointment details
PUT /api/appointments/{id}/ # Update appointment
DELETE /api/appointments/{id}/ # Cancel appointment


### Custom Actions
POST /api/appointments/{id}/confirm/ # Doctor confirms appointment
POST /api/appointments/{id}/complete/ # Doctor marks as completed
POST /api/appointments/{id}/cancel/ # Cancel appointment
GET /api/appointments/upcoming/ # Get upcoming appointments
GET /api/appointments/today/ # Get today's appointments


### Medical Records
GET /api/medical-records/ # List records (role-filtered)
POST /api/medical-records/ # Create new record
GET /api/medical-records/{id}/ # Get record details
PUT /api/medical-records/{id}/ # Update record
DELETE /api/medical-records/{id}/ # Delete record

## Custom Actions
GET /api/medical-records/patient-history/?patient_id=123 # Get patient history

## Admin Dashboard
GET /api/dashboard/stats/ # Get system statistics
GET /api/dashboard/recent-activity/ # Get recent activity


## Health Check
GET /api/health-check/ # API health status

### Project Requirements 

Django==5.2.5
djangorestframework==3.16.1
asgiref==3.9.1
sqlparse==0.5.3





