#!/usr/bin/env python3
"""
Simple runner script for Sales Management System
Run this to start the Streamlit application directly
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'psycopg2',
        'pandas', 
        'plotly',
        'pydantic',
        'faker',
        'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'psycopg2':
                import psycopg2
            elif package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def run_streamlit():
    """Run the Streamlit application"""
    try:
        print("Starting Sales Management System...")
        print("Application will open in your browser at: http://localhost:8501")
        print("Press Ctrl+C to stop the application")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error running application: {e}")

def main():
    print("=" * 50)
    print("Sales Management System - Master-Slave PostgreSQL")
    print("=" * 50)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        response = input("Would you like to install them? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            if not install_dependencies():
                print("Failed to install dependencies. Please install manually:")
                print("pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("Please install the required packages manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    print("All dependencies are installed!")
    print()
    
    # Check if we're in the src directory
    if not os.path.exists("main.py"):
        print("Please run this script from the src directory!")
        sys.exit(1)
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main()
