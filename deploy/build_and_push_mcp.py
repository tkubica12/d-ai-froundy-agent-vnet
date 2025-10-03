#!/usr/bin/env python3
"""
Build and push Products MCP server using Azure Container Registry remote build.
This script uses ACR's remote build capability to build the Docker image in Azure.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_color(message: str, color: str = Colors.RESET) -> None:
    """Print colored message to console."""
    print(f"{color}{message}{Colors.RESET}")


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    
    if not env_path.exists():
        print_color(f"✗ .env file not found at {env_path}", Colors.RED)
        print_color("  Please create it based on .env.sample", Colors.RED)
        sys.exit(1)
    
    print_color("Loading environment variables from .env...", Colors.CYAN)
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def check_azure_cli() -> dict:
    """Check if Azure CLI is installed and return version info."""
    print_color("Checking Azure CLI installation...", Colors.CYAN)
    
    try:
        result = subprocess.run(
            ['az', 'version', '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        version_info = json.loads(result.stdout)
        print_color(f"✓ Azure CLI version: {version_info.get('azure-cli', 'unknown')}", Colors.GREEN)
        return version_info
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        print_color("✗ Azure CLI is not installed or not working properly", Colors.RED)
        print_color("  Please install it from https://docs.microsoft.com/cli/azure/install-azure-cli", Colors.RED)
        sys.exit(1)


def check_azure_login() -> dict:
    """Check if logged in to Azure and return account info."""
    print_color("Checking Azure login status...", Colors.CYAN)
    
    try:
        result = subprocess.run(
            ['az', 'account', 'show', '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        account_info = json.loads(result.stdout)
        print_color(f"✓ Logged in as: {account_info['user']['name']}", Colors.GREEN)
        print_color(f"✓ Subscription: {account_info['name']}", Colors.GREEN)
        return account_info
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print_color("✗ Not logged in to Azure", Colors.RED)
        print_color("  Please run 'az login' first", Colors.RED)
        sys.exit(1)


def trigger_acr_build(acr_name: str, image_name: str, image_tag: str, context_path: Path) -> None:
    """Trigger Azure Container Registry remote build."""
    print_color("\nStarting ACR remote build...", Colors.CYAN)
    print_color("This will upload the build context to Azure and build the image in ACR.", Colors.YELLOW)
    print()
    
    # Verify Dockerfile exists in context path
    dockerfile_path = context_path / "Dockerfile"
    if not dockerfile_path.exists():
        print_color(f"✗ Dockerfile not found at {dockerfile_path}", Colors.RED)
        sys.exit(1)
    
    cmd = [
        'az', 'acr', 'build',
        '--registry', acr_name,
        '--image', f"{image_name}:{image_tag}",
        '--platform', 'linux/amd64',
        str(context_path)
    ]
    
    try:
        # Run the build command with live output
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print()
            print_color("═" * 63, Colors.GREEN)
            print_color("✓ Build completed successfully!", Colors.GREEN)
            print_color("═" * 63, Colors.GREEN)
            print_color(f"Image: {acr_name}.azurecr.io/{image_name}:{image_tag}", Colors.YELLOW)
            print()
        else:
            print_color(f"✗ ACR build failed with exit code {result.returncode}", Colors.RED)
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print_color(f"✗ Failed to execute ACR build: {e}", Colors.RED)
        sys.exit(1)


def main() -> None:
    """Main execution function."""
    # Determine script directory and paths
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    context_path = script_dir.parent / "src" / "tools" / "products_mcp"
    
    # Configuration
    image_name = "products-mcp"
    image_tag = "latest"
    
    # Load environment variables
    env_vars = load_env_file(env_file)
    
    # Validate required environment variables
    acr_name = env_vars.get('ACR_NAME')
    if not acr_name:
        print_color("✗ ACR_NAME is not set in .env file", Colors.RED)
        sys.exit(1)
    
    # Print banner
    print()
    print_color("═" * 63, Colors.GREEN)
    print_color("Azure Container Registry Remote Build", Colors.GREEN)
    print_color("═" * 63, Colors.GREEN)
    print_color(f"Registry:  {acr_name}.azurecr.io", Colors.YELLOW)
    print_color(f"Image:     {image_name}:{image_tag}", Colors.YELLOW)
    print_color(f"Context:   {context_path}", Colors.YELLOW)
    print_color("═" * 63, Colors.GREEN)
    print()
    
    # Verify prerequisites
    check_azure_cli()
    check_azure_login()
    
    # Trigger the build
    trigger_acr_build(acr_name, image_name, image_tag, context_path)


if __name__ == "__main__":
    main()
