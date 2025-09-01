"""
Comprehensive Test Script for Spotify App Agent Template

This script tests all major functionality to ensure everything works properly.

LEARNING OBJECTIVES:
- Understand comprehensive testing approaches
- Learn about system integration testing
- Practice error handling and validation
- Understand user experience testing
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_database_initialization():
    """Test database initialization."""
    print("🗄️  Testing database initialization...")
    
    try:
        # Run database initialization
        result = subprocess.run([sys.executable, 'tools/init_database.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialization successful")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def test_analytics_tool():
    """Test analytics tool functionality."""
    print("📊 Testing analytics tool...")
    
    try:
        # Test basic analytics
        result = subprocess.run([sys.executable, 'tools/analytics.py', '--performance'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and "Performance Metrics" in result.stdout:
            print("✅ Analytics tool working")
            return True
        else:
            print(f"❌ Analytics tool failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Analytics tool error: {e}")
        return False

def test_cli_tool():
    """Test CLI tool functionality."""
    print("🖥️  Testing CLI tool...")
    
    try:
        # Test CLI help
        result = subprocess.run([sys.executable, 'tools/cli.py', '--help'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and "Available commands" in result.stdout:
            print("✅ CLI tool working")
            return True
        else:
            print(f"❌ CLI tool failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI tool error: {e}")
        return False

def test_web_dashboard():
    """Test web dashboard functionality."""
    print("🌐 Testing web dashboard...")
    
    try:
        # Start dashboard in background
        process = subprocess.Popen([sys.executable, 'tools/web_dashboard.py'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(10)
        
        # Test different ports
        ports = [5000, 5001, 5002, 5003, 5004]
        dashboard_working = False
        
        for port in ports:
            try:
                response = requests.get(f'http://localhost:{port}', timeout=5)
                if response.status_code == 200:
                    print(f"✅ Web dashboard working on port {port}")
                    dashboard_working = True
                    break
            except requests.exceptions.RequestException:
                continue
        
        # Clean up
        process.terminate()
        process.wait()
        
        if dashboard_working:
            return True
        else:
            print("❌ Web dashboard not accessible on any port")
            return False
            
    except Exception as e:
        print(f"❌ Web dashboard error: {e}")
        return False

def test_makefile_commands():
    """Test Makefile commands."""
    print("🔧 Testing Makefile commands...")
    
    try:
        # Test help command
        result = subprocess.run(['make', 'help'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and "Available Commands" in result.stdout:
            print("✅ Makefile commands working")
            return True
        else:
            print(f"❌ Makefile commands failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Makefile commands error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("📁 Testing file structure...")
    
    required_files = [
        'requirements.txt',
        'Makefile',
        'README.md',
        'config/config.yaml',
        'tools/analytics.py',
        'tools/cli.py',
        'tools/web_dashboard.py',
        'tools/init_database.py',
        'templates/dashboard.html',
        'templates/config.html',
        'templates/analytics.html',
        'templates/logs.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_dependencies():
    """Test that all dependencies can be imported."""
    print("📦 Testing dependencies...")
    
    try:
        import flask
        import pandas
        import matplotlib
        import seaborn
        import yaml
        import sqlite3
        print("✅ All dependencies importable")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 COMPREHENSIVE TEMPLATE TESTING")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Database Initialization", test_database_initialization),
        ("Analytics Tool", test_analytics_tool),
        ("CLI Tool", test_cli_tool),
        ("Web Dashboard", test_web_dashboard),
        ("Makefile Commands", test_makefile_commands),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Template is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Template needs fixes.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
