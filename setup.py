#!/usr/bin/env python3
"""
Setup script for AI Observability Platform.
Handles dependency installation and initial configuration.
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up AI Observability Platform...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("\n💡 Tip: You may need to use pip3 or ensure you have internet access")
        sys.exit(1)
    
    # Setup database
    print("\n🗄️  Setting up database...")
    if run_command("python scripts/seed_database.py --setup-all", "Setting up database"):
        print("✅ Database setup completed")
    else:
        print("⚠️  Database setup had issues (this is OK if PostgreSQL isn't running)")
        print("   You can set it up later with: python scripts/seed_database.py --setup-all")
    
    # Run verification
    print("\n🧪 Running verification...")
    if run_command("python verify_setup.py", "Verifying installation"):
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Start services: docker compose up -d")
        print("   2. Or run locally: uvicorn app.main:app --reload")
        print("   3. Access API at: http://localhost:8000")
        print("   4. See README.md for detailed instructions")
    else:
        print("⚠️  Verification had issues, but dependencies are installed")
        print("   You may need to configure your environment or start required services")
    
    print("\n" + "=" * 50)
    print("Setup process finished!")

if __name__ == "__main__":
    main()
