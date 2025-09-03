"""Monitoring, health check, and metrics endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from app.database import get_db
from app.schemas.common import create_success_response, HealthStatus, MetricsResponse
from app.core.exceptions import BRSException
from app.config import settings


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health/detailed",
           summary="Detailed Health Check",
           description="Comprehensive health check including database connectivity and system resources",
           response_model=Dict[str, Any])
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint for monitoring systems.
    
    Checks:
    - Database connectivity and response time
    - System resource usage (CPU, Memory)
    - Application status
    
    Returns detailed status information for each component.
    """
    start_time = time.time()
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": getattr(settings, 'environment', 'development'),
        "services": {},
        "system": {},
        "response_time_ms": 0
    }
    
    overall_healthy = True
    
    # Test database connectivity
    db_start = time.time()
    try:
        # Simple query to test database
        result = db.execute(text("SELECT 1 as test"))
        db_result = result.fetchone()
        db_response_time = round((time.time() - db_start) * 1000, 2)
        
        if db_result and db_result[0] == 1:
            health_data["services"]["database"] = {
                "status": "healthy",
                "response_time_ms": db_response_time,
                "message": "Database connection successful"
            }
        else:
            raise Exception("Database query returned unexpected result")
            
    except Exception as e:
        overall_healthy = False
        health_data["services"]["database"] = {
            "status": "unhealthy",
            "response_time_ms": None,
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Test database pool status
    try:
        pool_info = db.get_bind().pool
        health_data["services"]["database_pool"] = {
            "status": "healthy",
            "pool_size": pool_info.size(),
            "checked_in": pool_info.checkedin(),
            "checked_out": pool_info.checkedout(),
            "overflow": pool_info.overflow(),
            "invalidated": pool_info.invalidated()
        }
    except Exception as e:
        health_data["services"]["database_pool"] = {
            "status": "warning",
            "message": f"Could not retrieve pool info: {str(e)}"
        }
    
    # System resource monitoring
    try:
        if PSUTIL_AVAILABLE and psutil:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = round(memory.available / (1024**3), 2)
            
            # Disk usage for current directory
            disk = psutil.disk_usage('/')
            disk_percent = round((disk.used / disk.total) * 100, 2)
            disk_free_gb = round(disk.free / (1024**3), 2)
            
            # Process info
            process = psutil.Process(os.getpid())
            process_memory_mb = round(process.memory_info().rss / (1024**2), 2)
            process_cpu_percent = process.cpu_percent()
            
            health_data["system"] = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "memory_available_gb": memory_available_gb,
                "disk_usage_percent": disk_percent,
                "disk_free_gb": disk_free_gb,
                "process_memory_mb": process_memory_mb,
                "process_cpu_percent": process_cpu_percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            # Health thresholds
            if cpu_percent > 90:
                overall_healthy = False
                health_data["system"]["cpu_warning"] = "High CPU usage detected"
            
            if memory_percent > 90:
                overall_healthy = False
                health_data["system"]["memory_warning"] = "High memory usage detected"
                
            if disk_percent > 90:
                overall_healthy = False
                health_data["system"]["disk_warning"] = "High disk usage detected"
        else:
            health_data["system"] = {
                "status": "monitoring_unavailable",
                "message": "System monitoring requires psutil package",
                "cpu_usage_percent": "N/A",
                "memory_usage_percent": "N/A"
            }
            
    except Exception as e:
        health_data["system"]["error"] = f"Could not retrieve system metrics: {str(e)}"
    
    # Calculate total response time
    total_response_time = round((time.time() - start_time) * 1000, 2)
    health_data["response_time_ms"] = total_response_time
    
    # Set overall status
    if not overall_healthy:
        health_data["status"] = "unhealthy"
    elif total_response_time > 5000:  # 5 seconds
        health_data["status"] = "degraded"
        health_data["warning"] = "Slow response time detected"
    
    return create_success_response(
        data=health_data,
        message=f"Health check completed - Status: {health_data['status']}"
    )


@router.get("/health/readiness",
           summary="Readiness Check",
           description="Kubernetes-style readiness probe to determine if the service is ready to receive traffic")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for container orchestration.
    
    Performs minimal checks to determine if the service is ready to handle requests.
    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Quick database connectivity check
        db.execute(text("SELECT 1"))
        
        return create_success_response(
            data={"ready": True, "timestamp": datetime.utcnow().isoformat()},
            message="Service is ready to receive traffic"
        )
    except Exception as e:
        raise BRSException(
            message="Service is not ready to receive traffic",
            status_code=503,
            details={"error": str(e), "component": "database"}
        )


@router.get("/health/liveness",
           summary="Liveness Check", 
           description="Kubernetes-style liveness probe to determine if the service is alive")
async def liveness_check():
    """
    Liveness probe for container orchestration.
    
    Performs minimal checks to determine if the service is alive.
    Returns 200 if alive, 503 if not alive.
    """
    try:
        # Basic application liveness check
        current_time = datetime.utcnow()
        
        return create_success_response(
            data={
                "alive": True,
                "timestamp": current_time.isoformat(),
                "uptime_check": "passed"
            },
            message="Service is alive and responding"
        )
    except Exception as e:
        raise BRSException(
            message="Service liveness check failed",
            status_code=503,
            details={"error": str(e)}
        )


@router.get("/metrics",
           summary="Application Metrics",
           description="Retrieve application performance metrics and statistics")
async def get_application_metrics(request: Request, db: Session = Depends(get_db)):
    """
    Get application metrics and statistics.
    
    Provides insights into application performance, usage patterns,
    and operational metrics for monitoring and observability.
    """
    try:
        metrics_data = {}
        
        # Application uptime (simulated - in production this would be tracked)
        metrics_data["uptime"] = "N/A"  # Would be calculated from app start time
        
        # Database metrics
        try:
            # Get approximate table counts (for PostgreSQL)
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            book_count = db.execute(text("SELECT COUNT(*) FROM books")).fetchone()[0] 
            review_count = db.execute(text("SELECT COUNT(*) FROM reviews")).fetchone()[0]
            genre_count = db.execute(text("SELECT COUNT(*) FROM genres")).fetchone()[0]
            
            metrics_data["database"] = {
                "total_users": user_count,
                "total_books": book_count,
                "total_reviews": review_count,
                "total_genres": genre_count,
                "database_size_mb": "N/A"  # Would require specific queries
            }
        except Exception as e:
            metrics_data["database"] = {
                "error": f"Could not retrieve database metrics: {str(e)}"
            }
        
        # Request metrics (simulated - in production use metrics collection)
        metrics_data["requests"] = {
            "total_requests": "N/A",  # Would be tracked by middleware
            "requests_per_minute": "N/A",
            "average_response_time_ms": "N/A",
            "error_rate_percent": "N/A"
        }
        
        # Performance metrics
        try:
            if PSUTIL_AVAILABLE and psutil:
                # CPU and memory from system
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                metrics_data["performance"] = {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "active_connections": "N/A",  # Would track database connections
                    "cache_hit_rate": "N/A"  # If using caching
                }
            else:
                metrics_data["performance"] = {
                    "cpu_usage_percent": "N/A (psutil not available)",
                    "memory_usage_percent": "N/A (psutil not available)",
                    "active_connections": "N/A",
                    "cache_hit_rate": "N/A"
                }
        except Exception:
            metrics_data["performance"] = {
                "error": "Could not retrieve performance metrics"
            }
        
        # API endpoint usage (simulated)
        metrics_data["api_usage"] = {
            "most_used_endpoints": [
                {"endpoint": "/api/v1/books", "requests": "N/A"},
                {"endpoint": "/api/v1/auth/login", "requests": "N/A"},
                {"endpoint": "/api/v1/reviews", "requests": "N/A"}
            ],
            "authentication_success_rate": "N/A",
            "average_requests_per_user": "N/A"
        }
        
        # Add timestamp and metadata
        metrics_data["timestamp"] = datetime.utcnow().isoformat()
        metrics_data["collection_time_ms"] = "N/A"
        metrics_data["version"] = settings.app_version
        
        return create_success_response(
            data=metrics_data,
            message="Application metrics retrieved successfully"
        )
        
    except Exception as e:
        raise BRSException(
            message="Failed to retrieve application metrics",
            status_code=500,
            details={"error": str(e)}
        )


@router.get("/version",
           summary="Application Version",
           description="Get application version and build information")
async def get_version_info():
    """
    Get application version and build information.
    
    Returns version, build details, and deployment information.
    """
    version_data = {
        "version": settings.app_version,
        "name": settings.app_name,
        "environment": getattr(settings, 'environment', 'development'),
        "build_time": "N/A",  # Would be set during build process
        "git_commit": "N/A",  # Would be set during CI/CD
        "python_version": "3.11+",
        "fastapi_version": "0.104+",
        "api_version": "v1",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/api/v1/openapi.json"
        }
    }
    
    return create_success_response(
        data=version_data,
        message="Version information retrieved successfully"
    )


@router.get("/status",
           summary="Service Status",
           description="Get overall service status and key indicators")
async def get_service_status(db: Session = Depends(get_db)):
    """
    Get overall service status and key health indicators.
    
    Provides a quick overview of service health without detailed metrics.
    """
    try:
        # Quick health checks
        start_time = time.time()
        
        # Database quick check
        db.execute(text("SELECT 1"))
        db_response_time = round((time.time() - start_time) * 1000, 2)
        
        # Basic system check
        if PSUTIL_AVAILABLE and psutil:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
        else:
            cpu_percent = 0  # Default when psutil not available
            memory_percent = 0
        
        # Determine overall status
        status = "healthy"
        if cpu_percent > 90 or memory_percent > 90:
            status = "degraded"
        if db_response_time > 1000:  # 1 second
            status = "degraded"
        
        status_data = {
            "overall_status": status,
            "database_status": "healthy" if db_response_time < 1000 else "slow",
            "database_response_time_ms": db_response_time,
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_percent,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version
        }
        
        return create_success_response(
            data=status_data,
            message=f"Service status: {status}"
        )
        
    except Exception as e:
        raise BRSException(
            message="Failed to retrieve service status",
            status_code=500,
            details={"error": str(e)}
        )
