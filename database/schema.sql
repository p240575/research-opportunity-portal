-- ====================================================================
-- University Research Opportunity Portal Database Schema
-- Assignment No. 1 - Computer Networks (Fall 2026)
-- FAST-NUCES Peshawar Campus
-- Updated: Three-role RBAC (Visitor | Faculty | Admin)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS research_portal
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE research_portal;

-- ====================================================================
-- TABLE: admins
-- Stores the single portal administrator account.
-- ====================================================================
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) DEFAULT 'Portal Administrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed Default Administrator (password: AdminPassword123!)
INSERT INTO admins (username, password_hash, full_name)
SELECT 'admin', 'scrypt:32768:8:1$yN3k4GH55j6UpdAr$22319e165fd9620b7663c3b4806e782ce5653be89a2d01cef3f18c1a429cd7a7150ec534713bd7a02bc7350b82ec9097f50ab70e94e406150acb3a1a237cc092', 'Portal Administrator'
WHERE NOT EXISTS (SELECT 1 FROM admins WHERE username = 'admin');

-- ====================================================================
-- TABLE: faculty
-- Stores registered faculty member accounts.
-- Faculty can self-register; passwords stored as secure hashes only.
-- ====================================================================
CREATE TABLE IF NOT EXISTS faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- TABLE: research_opportunities
-- faculty_id links each post to its owning faculty member.
-- NULL faculty_id means the post was created by the admin.
-- ====================================================================
CREATE TABLE IF NOT EXISTS research_opportunities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    research_area VARCHAR(150) NOT NULL,
    faculty_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    required_skills TEXT NOT NULL,
    available_positions INT NOT NULL DEFAULT 1,
    deadline DATE NOT NULL,
    status ENUM('Open', 'Closed') NOT NULL DEFAULT 'Open',
    faculty_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_department (department),
    INDEX idx_area (research_area),
    INDEX idx_faculty_id (faculty_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- SEED DATA: Sample research opportunities (admin-created, faculty_id NULL)
-- ====================================================================
INSERT INTO research_opportunities
(title, description, research_area, faculty_name, department, required_skills, available_positions, deadline, status, faculty_id)
SELECT * FROM (SELECT
    'AI-Driven Traffic Optimization for Software Defined Networks',
    'Investigating deep reinforcement learning algorithms to dynamically route packet flows and minimize latency in enterprise SDN topologies.',
    'Computer Networks & AI',
    'Dr. Tariq Khan',
    'Computer Science',
    'Python, Mininet, PyTorch, SDN / OpenFlow',
    2,
    DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY),
    'Open',
    NULL
) AS tmp WHERE NOT EXISTS (SELECT 1 FROM research_opportunities LIMIT 1);

INSERT INTO research_opportunities
(title, description, research_area, faculty_name, department, required_skills, available_positions, deadline, status, faculty_id)
SELECT * FROM (SELECT
    'Zero-Trust Security Architectures for Edge IoT Devices',
    'Designing lightweight mutual authentication and continuous verification protocols for resource-constrained IoT gateways in smart campus deployments.',
    'Cybersecurity',
    'Dr. Ayesha Siddiqa',
    'Computer Science',
    'C/C++, Cryptography basics, Network Security, Wireshark',
    3,
    DATE_ADD(CURRENT_DATE, INTERVAL 45 DAY),
    'Open',
    NULL
) AS tmp WHERE (SELECT COUNT(*) FROM research_opportunities) < 2;

INSERT INTO research_opportunities
(title, description, research_area, faculty_name, department, required_skills, available_positions, deadline, status, faculty_id)
SELECT * FROM (SELECT
    'Federated Learning for Privacy-Preserving Medical Telemetry',
    'Developing decentralized model training frameworks across hospital edge nodes while ensuring zero patient biometric data leakage.',
    'Machine Learning',
    'Dr. Usman Farooq',
    'Data Science',
    'Python, TensorFlow Federated, Differential Privacy',
    1,
    DATE_ADD(CURRENT_DATE, INTERVAL 14 DAY),
    'Closed',
    NULL
) AS tmp WHERE (SELECT COUNT(*) FROM research_opportunities) < 3;
