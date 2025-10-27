"""
Setup script for the AI Application
"""
import os
import subprocess
import sys


def setup_backend():
    """Setup backend dependencies"""
    print("Setting up backend...")
    os.chdir("backend")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Install dependencies
    pip_cmd = "venv/bin/pip" if sys.platform != "win32" else "venv\\Scripts\\pip"
    subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])
    
    print("Backend setup complete!")
    os.chdir("..")


def setup_frontend():
    """Setup frontend dependencies"""
    print("Setting up frontend...")
    os.chdir("frontend")
    
    # Install dependencies
    subprocess.run(["npm", "install"])
    
    print("Frontend setup complete!")
    os.chdir("..")


def setup_docker():
    """Setup Docker containers"""
    print("Setting up Docker containers...")
    subprocess.run(["docker-compose", "up", "-d"])
    print("Docker containers started!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI Application")
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Setup backend only"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Setup frontend only"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Setup Docker containers"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Setup everything"
    )
    
    args = parser.parse_args()
    
    if args.all:
        setup_backend()
        setup_frontend()
        print("\nSetup complete! Next steps:")
        print("1. Add your OpenAI API key to backend/.env")
        print("2. Start MongoDB: docker-compose up -d mongodb")
        print("3. Start backend: cd backend && python main.py")
        print("4. Start frontend: cd frontend && npm run dev")
    elif args.backend:
        setup_backend()
    elif args.frontend:
        setup_frontend()
    elif args.docker:
        setup_docker()
    else:
        print("Usage: python setup.py --all")


