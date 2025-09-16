#!/usr/bin/env python3
"""
Simple KCB Buni Configuration Checker
Check if your environment is ready for KCB integration
"""

import os
from pathlib import Path

def check_environment_file():
    """Check if .env file exists and has KCB settings"""
    print("=== Environment Configuration Check ===")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Create .env file from .env.example")
        return False
    
    print("✅ .env file exists")
    
    # Read .env file and check KCB settings
    env_content = env_file.read_text()
    
    required_vars = [
        'KCB_BUNI_BASE_URL',
        'KCB_BUNI_CLIENT_ID', 
        'KCB_BUNI_CLIENT_SECRET',
        'KCB_BUNI_API_KEY'
    ]
    
    missing_vars = []
    configured_vars = []
    
    for var in required_vars:
        if var in env_content:
            # Check if it's actually configured (not just commented)
            lines = env_content.split('\n')
            configured = False
            for line in lines:
                if line.startswith(var + '=') and not line.startswith('#'):
                    value = line.split('=', 1)[1] if '=' in line else ''
                    if value and value not in ['your-kcb-client-id', 'your-kcb-client-secret', 'your-kcb-api-key']:
                        configured_vars.append(var)
                        configured = True
                        break
            
            if not configured:
                missing_vars.append(var)
        else:
            missing_vars.append(var)
    
    if configured_vars:
        print("✅ Configured KCB variables:")
        for var in configured_vars:
            print(f"   - {var}")
    
    if missing_vars:
        print("❌ Missing or unconfigured KCB variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("✅ All KCB environment variables are configured")
        return True

def check_payment_integration_files():
    """Check if payment integration files exist"""
    print("\n=== Payment Integration Files Check ===")
    
    required_files = [
        'payments/kcb_buni_service.py',
        'payments/kcb_webhooks.py',
        'payments/models.py',
        'payments/views.py',
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    if existing_files:
        print("✅ Found payment integration files:")
        for file in existing_files:
            print(f"   - {file}")
    
    if missing_files:
        print("❌ Missing payment integration files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ All payment integration files exist")
        return True

def check_database_requirements():
    """Check if database migration files exist"""
    print("\n=== Database Migration Check ===")
    
    migration_dirs = [
        'payments/migrations',
        'mikrotik_integration/migrations',
        'billing/migrations'
    ]
    
    all_good = True
    
    for migration_dir in migration_dirs:
        if Path(migration_dir).exists():
            migration_files = list(Path(migration_dir).glob('*.py'))
            migration_files = [f for f in migration_files if f.name != '__init__.py']
            
            if migration_files:
                print(f"✅ {migration_dir}: {len(migration_files)} migration files")
            else:
                print(f"⚠️  {migration_dir}: No migration files (may need to run makemigrations)")
        else:
            print(f"❌ {migration_dir}: Directory not found")
            all_good = False
    
    return all_good

def check_requirements():
    """Check if requirements.txt has necessary packages"""
    print("\n=== Requirements Check ===")
    
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
    
    requirements = Path('requirements.txt').read_text()
    
    required_packages = [
        'requests',
        'django',
        'psycopg2-binary',
        'gunicorn'
    ]
    
    missing_packages = []
    found_packages = []
    
    for package in required_packages:
        if package.lower() in requirements.lower():
            found_packages.append(package)
        else:
            missing_packages.append(package)
    
    if found_packages:
        print("✅ Found required packages:")
        for package in found_packages:
            print(f"   - {package}")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        return False
    else:
        print("✅ All required packages are in requirements.txt")
        return True

def main():
    """Run all configuration checks"""
    print("KCB Buni Integration Configuration Checker")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment_file),
        ("Integration Files", check_payment_integration_files), 
        ("Database Migrations", check_database_requirements),
        ("Python Requirements", check_requirements),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error running {check_name} check: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("CONFIGURATION CHECK SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 50)
    print(f"Total Checks: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All configuration checks passed!")
        print("\nNext steps:")
        print("1. Get KCB Buni API credentials from KCB Bank")
        print("2. Update your .env file with real credentials")
        print("3. Configure station payment details in Django admin")
        print("4. Test the integration with sandbox credentials first")
    else:
        print(f"\n⚠️  {failed} check(s) failed. Please fix the issues above.")
        print("\nRecommended actions:")
        if any("Environment" in name for name, result in results if not result):
            print("- Create and configure your .env file")
        if any("Integration" in name for name, result in results if not result):
            print("- Ensure all payment integration files are present")
        if any("Database" in name for name, result in results if not result):
            print("- Run: python manage.py makemigrations")
            print("- Run: python manage.py migrate")

if __name__ == "__main__":
    main()