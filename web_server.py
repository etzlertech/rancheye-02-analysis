#!/usr/bin/env python3
"""
RanchEye Web Server
Runs the FastAPI web interface and API
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


def main():
    port = int(os.getenv("PORT", 8080))
    
    print(f"""
    🌐 RanchEye Web Server Starting...
    ================================
    
    Dashboard URL: http://localhost:{port}
    API Docs: http://localhost:{port}/docs
    
    Press Ctrl+C to stop
    """)
    
    # In production, disable reload
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        log_level="info"
    )


if __name__ == "__main__":
    main()