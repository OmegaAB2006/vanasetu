-- Smart Urban Tree & Green Cover Management Platform
-- MySQL Schema

CREATE DATABASE IF NOT EXISTS smart_urban_tree;
USE smart_urban_tree;

-- Core tree registry
CREATE TABLE IF NOT EXISTS trees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    species VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    ward INT NOT NULL,
    age_years INT DEFAULT 0,
    health_score INT DEFAULT 100 CHECK (health_score BETWEEN 0 AND 100),
    last_checked DATE DEFAULT NULL,
    status ENUM('healthy','stressed','diseased','critical','removed') DEFAULT 'healthy',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance log per tree
CREATE TABLE IF NOT EXISTS maintenance_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tree_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    officer_name VARCHAR(100),
    notes TEXT,
    approved_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tree_id) REFERENCES trees(id)
);

-- Immutable audit log (append-only enforced by trigger)
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INT,
    old_val JSON,
    new_val JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trigger: prevent UPDATE/DELETE on audit_log (append-only)
DROP TRIGGER IF EXISTS audit_log_no_update;
DELIMITER $$
CREATE TRIGGER audit_log_no_update
BEFORE UPDATE ON audit_log
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_log is append-only: UPDATE not allowed';
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS audit_log_no_delete;
DELIMITER $$
CREATE TRIGGER audit_log_no_delete
BEFORE DELETE ON audit_log
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_log is append-only: DELETE not allowed';
END$$
DELIMITER ;

-- Live weather per city fetch
CREATE TABLE IF NOT EXISTS live_weather (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(100) DEFAULT 'Bengaluru',
    temperature DECIMAL(5,2),
    rainfall DECIMAL(6,2),
    humidity INT,
    wind_speed DECIMAL(5,2),
    condition_text VARCHAR(100),
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- NDVI values per ward
CREATE TABLE IF NOT EXISTS ward_ndvi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT NOT NULL,
    ndvi_value DECIMAL(5,4),
    source VARCHAR(50) DEFAULT 'MODIS',
    recorded_date DATE,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- OSM green space area per ward
CREATE TABLE IF NOT EXISTS osm_green_spaces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT NOT NULL,
    green_area_sqm DECIMAL(14,2),
    total_area_sqm DECIMAL(14,2),
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Composite green cover per ward (recalculated every 30 min)
CREATE TABLE IF NOT EXISTS ward_green_cover (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT NOT NULL UNIQUE,
    green_cover_pct DECIMAL(5,2),
    ndvi_normalized DECIMAL(5,4),
    osm_ratio DECIMAL(5,4),
    rainfall_bonus DECIMAL(5,4),
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API token usage tracking
CREATE TABLE IF NOT EXISTS api_usage_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(50),
    endpoint VARCHAR(200),
    tokens_in INT,
    tokens_out INT,
    latency_ms INT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Agent-to-agent communication log
CREATE TABLE IF NOT EXISTS agent_comm_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(36),
    source_agent VARCHAR(50),
    dest_agent VARCHAR(50),
    payload_hash VARCHAR(64),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Pending HITL approvals
CREATE TABLE IF NOT EXISTS pending_approvals (
    id VARCHAR(36) PRIMARY KEY,
    action_type VARCHAR(100),
    payload JSON,
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME DEFAULT NULL,
    resolved_by VARCHAR(100) DEFAULT NULL
);
