#!/usr/bin/env python
"""
Quick Setup Script for Power Monitoring System
Run this after creating your Django project to set everything up
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a shell command and print status"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   Power Monitoring System - Quick Setup Script           ║
    ║   This will set up your Django backend with sample data  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if we're in a Django project
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found!")
        print("Please run this script from your Django project root directory.")
        sys.exit(1)
    
    print("\n📋 Setup Steps:")
    print("  1. Create database migrations")
    print("  2. Apply migrations")
    print("  3. Create superuser (optional)")
    print("  4. Generate sample data")
    print("  5. Start development server")
    
    input("\nPress Enter to continue...")
    
    # Step 1: Make migrations
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        sys.exit(1)
    
    # Step 2: Apply migrations
    if not run_command("python manage.py migrate", "Applying migrations"):
        sys.exit(1)
    
    # Step 3: Create superuser (optional)
    print("\n" + "="*60)
    print("🔐 Create Superuser")
    print("="*60)
    create_superuser = input("Would you like to create a superuser? (y/n): ").lower()
    
    if create_superuser == 'y':
        print("\nCreating superuser...")
        print("(You'll be prompted for username, email, and password)")
        os.system("python manage.py createsuperuser")
    
    # Step 4: Generate sample data
    print("\n" + "="*60)
    print("📊 Generate Sample Data")
    print("="*60)
    
    days = input("How many days of historical data? (default: 7): ").strip()
    if not days:
        days = "7"
    
    clear = input("Clear existing data first? (y/n, default: n): ").lower()
    clear_flag = "--clear" if clear == 'y' else ""
    
    command = f"python manage.py generate_sample_data --days={days} {clear_flag}"
    if not run_command(command, f"Generating {days} days of sample data"):
        print("⚠️  Sample data generation failed, but you can continue without it")
    
    # Step 5: Summary
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("\n1. Start the development server:")
    print("   python manage.py runserver 0.0.0.0:8000")
    print("\n2. Access the Django admin panel:")
    print("   http://localhost:8000/admin/")
    print("\n3. API Endpoints are available at:")
    print("   http://localhost:8000/api/")
    print("\n4. Open your React app to see the dashboard!")
    print("\n5. (Optional) Access the API documentation:")
    print("   http://localhost:8000/api/ (browsable API)")
    
    print("\n" + "="*60)
    print("🚀 Quick Test:")
    print("="*60)
    print("curl http://localhost:8000/api/readings/latest/")
    print("curl http://localhost:8000/api/devices/")
    print("curl http://localhost:8000/api/alerts/active/")
    
    print("\n" + "="*60)
    start_server = input("\nWould you like to start the development server now? (y/n): ").lower()
    
    if start_server == 'y':
        print("\n🚀 Starting Django development server...")
        print("Press Ctrl+C to stop the server")
        print("="*60 + "\n")
        os.system("python manage.py runserver 0.0.0.0:8000")
    else:
        print("\n👋 Setup complete! Run 'python manage.py runserver' when ready.")

if __name__ == "__main__":
    main()


# Alternative: Simple bash script for Linux/Mac
# setup.sh
"""
#!/bin/bash

echo "=========================================="
echo "Power Monitoring System - Quick Setup"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found!${NC}"
    echo "Please run this script from your Django project root."
    exit 1
fi

# Make migrations
echo -e "\n${YELLOW}Creating migrations...${NC}"
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create migrations${NC}"
    exit 1
fi

# Apply migrations
echo -e "\n${YELLOW}Applying migrations...${NC}"
python manage.py migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to apply migrations${NC}"
    exit 1
fi

# Create superuser
echo -e "\n${YELLOW}Create superuser (optional)${NC}"
read -p "Would you like to create a superuser? (y/n): " create_super
if [ "$create_super" = "y" ]; then
    python manage.py createsuperuser
fi

# Generate sample data
echo -e "\n${YELLOW}Generate sample data${NC}"
read -p "How many days of historical data? (default: 7): " days
days=${days:-7}

read -p "Clear existing data first? (y/n): " clear
if [ "$clear" = "y" ]; then
    python manage.py generate_sample_data --days=$days --clear
else
    python manage.py generate_sample_data --days=$days
fi

# Summary
echo -e "\n${GREEN}=========================================="
echo "✓ Setup Complete!"
echo "==========================================${NC}"

echo -e "\nNext steps:"
echo "1. Start the server: python manage.py runserver 0.0.0.0:8000"
echo "2. Access admin: http://localhost:8000/admin/"
echo "3. Access API: http://localhost:8000/api/"

read -p $'\nStart development server now? (y/n): ' start_server
if [ "$start_server" = "y" ]; then
    echo -e "\n${GREEN}Starting server...${NC}"
    python manage.py runserver 0.0.0.0:8000
fi
"""