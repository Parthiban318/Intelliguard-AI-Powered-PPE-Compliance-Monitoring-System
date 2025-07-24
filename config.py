import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    AWS_RDS_HOST = os.getenv('AWS_RDS_HOST')
    AWS_RDS_DB = os.getenv('AWS_RDS_DB')
    AWS_RDS_USER = os.getenv('AWS_RDS_USER')
    AWS_RDS_PASSWORD = os.getenv('AWS_RDS_PASSWORD')
    AWS_RDS_PORT = os.getenv('AWS_RDS_PORT', '5432')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # Application Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'intelliguard-secret-key')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # PPE Classes
    PPE_CLASSES = [
        'glove', 'goggles', 'helmet', 'mask', 'no-suit', 'no_glove',
        'no_goggles', 'no_helmet', 'no_mask', 'no_shoes', 'shoes', 'suit'
    ]
    
    # Violation Classes
    VIOLATION_CLASSES = ['no_glove', 'no_goggles', 'no_helmet', 'no_mask', 'no_shoes', 'no-suit']
    
    # Database URL
    @property
    def DATABASE_URL(self):
        if all([self.AWS_RDS_HOST, self.AWS_RDS_USER, self.AWS_RDS_PASSWORD, self.AWS_RDS_DB]):
            return f"postgresql://{self.AWS_RDS_USER}:{self.AWS_RDS_PASSWORD}@{self.AWS_RDS_HOST}:{self.AWS_RDS_PORT}/{self.AWS_RDS_DB}"
        return "sqlite:///intelliguard.db"  # Fallback to SQLite for local development

config = Config()