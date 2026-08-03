-- Database Schema for QR-Based Digital Prescription Management System

CREATE DATABASE IF NOT EXISTS qr_prescription_system;
USE qr_prescription_system;

-- Core Users Table (Handling Authentication and Roles)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role ENUM('admin', 'doctor', 'patient', 'pharmacist') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors specific details
CREATE TABLE doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    specialization VARCHAR(100),
    hospital VARCHAR(150),
    phone VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Patients specific details
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    blood_group VARCHAR(10),
    phone VARCHAR(20),
    address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Master list of medicines
CREATE TABLE medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(50),
    manufacturer VARCHAR(100)
);

-- Prescriptions header data
CREATE TABLE prescriptions (
    prescription_id VARCHAR(50) PRIMARY KEY,
    doctor_id INT NOT NULL,
    patient_id INT NOT NULL,
    diagnosis TEXT,
    symptoms TEXT,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qr_code_path VARCHAR(255),
    pdf_path VARCHAR(255),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- Prescription items (medicines prescribed)
CREATE TABLE prescription_medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id VARCHAR(50) NOT NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    duration VARCHAR(50),
    instructions TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE
);
