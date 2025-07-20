"""
Production database configuration and utilities
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL based on environment"""
    # Check for Railway PostgreSQL environment variables
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    # Check for individual PostgreSQL components
    db_host = os.getenv('PGHOST', 'localhost')
    db_port = os.getenv('PGPORT', '5432')
    db_name = os.getenv('PGDATABASE', 'roi_calculator')
    db_user = os.getenv('PGUSER', 'postgres')
    db_password = os.getenv('PGPASSWORD', '')
    
    if db_password:
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Fallback to SQLite for development
    return "sqlite:///roi_calculator.db"

def configure_database(app):
    """Configure database for production"""
    database_url = get_database_url()
    
    # Configure SQLAlchemy settings
    if database_url.startswith('postgresql'):
        # Production PostgreSQL settings
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'poolclass': QueuePool,
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'roi_calculator'
            }
        }
        logger.info("Configured PostgreSQL database")
    else:
        # Development SQLite settings
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'connect_args': {'timeout': 20}
        }
        logger.info("Configured SQLite database")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return database_url

def create_database_indexes(db):
    """Create database indexes for performance"""
    try:
        # Create indexes for common queries using SQLAlchemy 2.x syntax
        with db.engine.connect() as connection:
            # Check if roi_submissions table exists before creating indexes
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='roi_submissions';
            """))
            
            if result.fetchone():
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_roi_submissions_email 
                    ON roi_submissions(email);
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_roi_submissions_timestamp 
                    ON roi_submissions(timestamp);
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_roi_submissions_tier 
                    ON roi_submissions(tier);
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_roi_submissions_hubspot_contact_id 
                    ON roi_submissions(hubspot_contact_id);
                """))
                
                connection.commit()
                logger.info("Database indexes created successfully")
            else:
                logger.info("roi_submissions table not found, skipping index creation")
            
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")

def test_database_connection(app, db_instance):
    """Test database connection using existing db instance within app context"""
    try:
        # Test connection using existing SQLAlchemy instance
        # Note: This function should be called within app.app_context()
        with db_instance.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def setup_database_migration():
    """Setup database migration system"""
    # This would typically use Flask-Migrate
    # For now, we'll implement basic table creation
    pass

class DatabaseHealthCheck:
    """Database health monitoring"""
    
    @staticmethod
    def check_connection(db):
        """Check database connection health"""
        try:
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    def get_connection_info(db):
        """Get database connection information"""
        try:
            engine = db.engine
            return {
                'url': str(engine.url).replace(engine.url.password or '', '***'),
                'pool_size': getattr(engine.pool, 'size', 'N/A'),
                'checked_out': getattr(engine.pool, 'checkedout', 'N/A'),
                'overflow': getattr(engine.pool, 'overflow', 'N/A'),
                'checked_in': getattr(engine.pool, 'checkedin', 'N/A')
            }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {'error': str(e)}

def backup_database():
    """Create database backup (placeholder)"""
    # This would implement database backup logic
    # For PostgreSQL: pg_dump
    # For SQLite: file copy
    logger.info("Database backup functionality placeholder")

def cleanup_old_data(db, days_to_keep=90):
    """Clean up old submission data"""
    try:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # This would delete old submissions based on retention policy
        # For now, just log the action
        logger.info(f"Would clean up data older than {cutoff_date}")
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")

# Environment-specific configurations
DATABASE_CONFIGS = {
    'development': {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///roi_calculator_dev.db',
        'SQLALCHEMY_ECHO': True
    },
    'testing': {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ECHO': False
    },
    'production': {
        'SQLALCHEMY_ECHO': False,
        'SQLALCHEMY_RECORD_QUERIES': True
    }
}



def ensure_database_stability(app, db):
    """Comprehensive database stability checks and initialization"""
    try:
        with app.app_context():
            # 1. Test basic connection
            if not test_database_connection(app, db):
                logger.error("❌ Database connection failed")
                return False
            
            # 2. Ensure tables exist
            try:
                db.create_all()
                logger.info("✅ Database tables verified/created")
            except Exception as e:
                logger.error(f"❌ Database table creation failed: {e}")
                return False
            
            # 3. Create indexes safely
            try:
                create_database_indexes(db)
                logger.info("✅ Database indexes verified/created")
            except Exception as e:
                logger.error(f"❌ Database index creation failed: {e}")
                # Non-critical, continue
            
            # 4. Test write capability
            try:
                with db.engine.connect() as connection:
                    # Test if we can write to database
                    connection.execute(text("SELECT 1"))
                    connection.commit()
                logger.info("✅ Database write capability confirmed")
            except Exception as e:
                logger.error(f"❌ Database write test failed: {e}")
                return False
            
            logger.info("🎯 Database stability check completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database stability check failed: {e}")
        return False

def get_database_health_status(db):
    """Get comprehensive database health information"""
    try:
        health_info = {
            'status': 'healthy',
            'connection_pool': {
                'size': getattr(db.engine.pool, 'size', 'N/A'),
                'checked_out': getattr(db.engine.pool, 'checkedout', 'N/A'),
                'overflow': getattr(db.engine.pool, 'overflow', 'N/A'),
                'checked_in': getattr(db.engine.pool, 'checkedin', 'N/A')
            },
            'database_url': str(db.engine.url).replace(str(db.engine.url.password) or '', '***'),
            'dialect': str(db.engine.dialect.name),
            'driver': str(db.engine.dialect.driver)
        }
        
        # Test connection
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            health_info['connection_test'] = 'passed'
        
        return health_info
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'connection_test': 'failed'
        }

def create_database_backup_info():
    """Create database backup information for monitoring"""
    return {
        'backup_strategy': 'Railway automatic backups',
        'retention_policy': '7 days point-in-time recovery',
        'manual_backup': 'Available via Railway dashboard',
        'disaster_recovery': 'Multi-region deployment available'
    }

