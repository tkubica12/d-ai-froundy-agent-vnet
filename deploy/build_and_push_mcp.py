#!/usr/bin/env python3
"""
Build and push Products MCP server using Azure Container Registry remote build.
This script uses ACR's remote build capability to build the Docker image in Azure.
"""

import json
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


def trigger_acr_build(acr_name: str, image_name: str, image_tag: str, context_path: Path) -> str:
    """Trigger Azure Container Registry remote build.
    
    Returns:
        Full image reference (registry.azurecr.io/image:tag)
    """
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
        
        image_ref = f"{acr_name}.azurecr.io/{image_name}:{image_tag}"
        
        if result.returncode == 0:
            print()
            print_color("═" * 63, Colors.GREEN)
            print_color("✓ Build completed successfully!", Colors.GREEN)
            print_color("═" * 63, Colors.GREEN)
            print_color(f"Image: {image_ref}", Colors.YELLOW)
            print()
            return image_ref
        else:
            print_color(f"✗ ACR build failed with exit code {result.returncode}", Colors.RED)
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print_color(f"✗ Failed to execute ACR build: {e}", Colors.RED)
        sys.exit(1)


def update_container_app(resource_group: str, container_app_name: str, image_ref: str) -> None:
    """Update Container App with new image.
    
    Args:
        resource_group: Azure resource group name
        container_app_name: Container App name
        image_ref: Full image reference (registry.azurecr.io/image:tag)
    """
    print_color("\nUpdating Container App...", Colors.CYAN)
    print_color(f"Container App: {container_app_name}", Colors.YELLOW)
    print_color(f"Resource Group: {resource_group}", Colors.YELLOW)
    print_color(f"New Image: {image_ref}", Colors.YELLOW)
    print()
    
    cmd = [
        'az', 'containerapp', 'update',
        '--name', container_app_name,
        '--resource-group', resource_group,
        '--image', image_ref,
        '--output', 'json'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        update_info = json.loads(result.stdout)
        latest_revision = update_info.get('properties', {}).get('latestRevisionName', 'unknown')
        
        print()
        print_color("═" * 63, Colors.GREEN)
        print_color("✓ Container App updated successfully!", Colors.GREEN)
        print_color("═" * 63, Colors.GREEN)
        print_color(f"Latest Revision: {latest_revision}", Colors.YELLOW)
        print_color(f"Container App: {container_app_name}", Colors.YELLOW)
        print()
        
    except subprocess.CalledProcessError as e:
        print_color(f"✗ Failed to update Container App: {e}", Colors.RED)
        if e.stderr:
            print_color(f"Error details: {e.stderr}", Colors.RED)
        print_color("\nNote: The image was built successfully and is available in ACR.", Colors.YELLOW)
        print_color("You can manually update the Container App using:", Colors.YELLOW)
        print_color(f"  az containerapp update --name {container_app_name} \\", Colors.CYAN)
        print_color(f"    --resource-group {resource_group} \\", Colors.CYAN)
        print_color(f"    --image {image_ref}", Colors.CYAN)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_color(f"✗ Failed to parse Container App update response: {e}", Colors.RED)
        print_color("The Container App may have been updated, but response parsing failed.", Colors.YELLOW)
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
    resource_group = env_vars.get('RESOURCE_GROUP')
    base_name = env_vars.get('BASE_NAME')
    
    if not acr_name:
        print_color("✗ ACR_NAME is not set in .env file", Colors.RED)
        sys.exit(1)
    
    if not resource_group:
        print_color("✗ RESOURCE_GROUP is not set in .env file", Colors.RED)
        sys.exit(1)
    
    if not base_name:
        print_color("✗ BASE_NAME is not set in .env file", Colors.RED)
        sys.exit(1)
    
    # Construct container app name
    container_app_name = f"aca-mcp-{base_name}"
    
    # Print banner
    print()
    print_color("═" * 63, Colors.GREEN)
    print_color("Azure Container Registry Build & Deploy", Colors.GREEN)
    print_color("═" * 63, Colors.GREEN)
    print_color(f"Registry:       {acr_name}.azurecr.io", Colors.YELLOW)
    print_color(f"Image:          {image_name}:{image_tag}", Colors.YELLOW)
    print_color(f"Context:        {context_path}", Colors.YELLOW)
    print_color(f"Container App:  {container_app_name}", Colors.YELLOW)
    print_color(f"Resource Group: {resource_group}", Colors.YELLOW)
    print_color("═" * 63, Colors.GREEN)
    print()
    
    # Verify prerequisites
    check_azure_cli()
    check_azure_login()
    
    # Trigger the build
    image_ref = trigger_acr_build(acr_name, image_name, image_tag, context_path)
    
    # Update the Container App with the new image
    update_container_app(resource_group, container_app_name, image_ref)


if __name__ == "__main__":
    main()
