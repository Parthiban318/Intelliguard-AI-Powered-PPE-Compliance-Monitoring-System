from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pandas as pd
from config import config
import logging

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    department = Column(String(50), nullable=False)
    role = Column(String(20), default='user')  # admin, user
    face_encoding = Column(Text)  # JSON string of face encoding
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with violations
    violations = relationship("Violation", back_populates="employee")

class PPEDetection(Base):
    __tablename__ = 'ppe_detections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    image_path = Column(String(255), nullable=False)
    detection_timestamp = Column(DateTime, default=datetime.utcnow)
    total_detections = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    compliance_status = Column(String(20))  # COMPLIANT, VIOLATION, PARTIAL
    confidence_score = Column(Float)
    processed_by = Column(String(50))
    notes = Column(Text)
    
    # Relationship with violations
    violations = relationship("Violation", back_populates="detection")
    employee = relationship("Employee")

class Violation(Base):
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey('ppe_detections.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    violation_type = Column(String(50), nullable=False)  # no_helmet, no_mask, etc.
    severity = Column(String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH, CRITICAL
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime)
    
    # Relationships
    detection = relationship("PPEDetection", back_populates="violations")
    employee = relationship("Employee", back_populates="violations")

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('employees.id'))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("Employee")

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.create_tables()
        
    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def add_employee(self, employee_data):
        """Add new employee"""
        session = self.get_session()
        try:
            employee = Employee(**employee_data)
            session.add(employee)
            session.commit()
            return employee.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding employee: {e}")
            return None
        finally:
            session.close()
    
    def get_employee_by_username(self, username):
        """Get employee by username"""
        session = self.get_session()
        try:
            employee = session.query(Employee).filter(Employee.username == username).first()
            return employee
        finally:
            session.close()
    
    def get_all_employees(self):
        """Get all employees"""
        session = self.get_session()
        try:
            employees = session.query(Employee).all()
            return employees
        finally:
            session.close()
    
    def add_detection(self, detection_data):
        """Add PPE detection record"""
        session = self.get_session()
        try:
            detection = PPEDetection(**detection_data)
            session.add(detection)
            session.commit()
            return detection.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding detection: {e}")
            return None
        finally:
            session.close()
    
    def add_violation(self, violation_data):
        """Add violation record"""
        session = self.get_session()
        try:
            violation = Violation(**violation_data)
            session.add(violation)
            session.commit()
            return violation.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding violation: {e}")
            return None
        finally:
            session.close()
    
    def get_violations_summary(self):
        """Get violations summary for dashboard"""
        session = self.get_session()
        try:
            query = """
            SELECT 
                v.violation_type,
                COUNT(*) as count,
                AVG(v.confidence) as avg_confidence,
                DATE(v.timestamp) as date
            FROM violations v
            WHERE v.timestamp >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY v.violation_type, DATE(v.timestamp)
            ORDER BY v.timestamp DESC
            """
            result = pd.read_sql(query, session.bind)
            return result
        except Exception as e:
            logging.error(f"Error getting violations summary: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_compliance_stats(self):
        """Get compliance statistics"""
        session = self.get_session()
        try:
            total_detections = session.query(PPEDetection).count()
            violation_detections = session.query(PPEDetection).filter(
                PPEDetection.compliance_status == 'VIOLATION'
            ).count()
            
            compliance_rate = ((total_detections - violation_detections) / total_detections * 100) if total_detections > 0 else 0
            
            return {
                'total_detections': total_detections,
                'violation_count': violation_detections,
                'compliance_rate': round(compliance_rate, 2)
            }
        except Exception as e:
            logging.error(f"Error getting compliance stats: {e}")
            return {'total_detections': 0, 'violation_count': 0, 'compliance_rate': 0}
        finally:
            session.close()
    
    def export_violations_csv(self, start_date=None, end_date=None):
        """Export violations to CSV"""
        session = self.get_session()
        try:
            query = """
            SELECT 
                v.id,
                e.first_name || ' ' || e.last_name as employee_name,
                e.department,
                v.violation_type,
                v.severity,
                v.confidence,
                v.timestamp,
                v.resolved,
                v.resolved_by,
                v.resolved_at
            FROM violations v
            JOIN employees e ON v.employee_id = e.id
            """
            
            if start_date and end_date:
                query += f" WHERE v.timestamp BETWEEN '{start_date}' AND '{end_date}'"
            
            query += " ORDER BY v.timestamp DESC"
            
            df = pd.read_sql(query, session.bind)
            return df
        except Exception as e:
            logging.error(f"Error exporting violations: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def log_audit_action(self, user_id, action, details=None, ip_address=None):
        """Log audit action"""
        session = self.get_session()
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                details=details,
                ip_address=ip_address
            )
            session.add(audit_log)
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error logging audit action: {e}")
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager()