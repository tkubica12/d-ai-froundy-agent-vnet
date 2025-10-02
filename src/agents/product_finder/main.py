"""
Smoke test for Product Finder agent using Azure AI Foundry Agent Service.

This script creates a basic agent, sends a test message, and verifies the response.
"""
import os
import logging
import time
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, RunStatus
from azure.core.exceptions import DecodeError, HttpResponseError
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of Azure SDK loggers
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_step(emoji: str, text: str):
    """Print a step with emoji and color."""
    print(f"{Colors.BLUE}{emoji}  {text}{Colors.RESET}")


def print_success(emoji: str, text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}{emoji}  {text}{Colors.RESET}")


def print_error(emoji: str, text: str):
    """Print an error message."""
    print(f"{Colors.RED}{emoji}  {text}{Colors.RESET}")


def print_info(text: str, dim: bool = False):
    """Print informational text."""
    color = Colors.DIM if dim else Colors.RESET
    print(f"{color}{text}{Colors.RESET}")


def print_conversation_msg(role: str, content: str):
    """Print a conversation message with role styling."""
    if role == "USER":
        print(f"{Colors.BOLD}{Colors.MAGENTA}👤 {role}:{Colors.RESET} {content}")
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}🤖 {role}:{Colors.RESET} {content}")


def load_system_prompt() -> str:
    """Load and render the system prompt from Jinja2 template.
    
    Returns:
        str: The rendered system prompt.
    """
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('system_prompt.jinja2')
    return template.render()


def main():
    """Run smoke test for product finder agent."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
    
    if not project_endpoint:
        print_error("❌", "PROJECT_ENDPOINT environment variable is not set")
        print_info("Please copy .env.sample to .env and configure your Azure AI Foundry project endpoint", dim=True)
        return
    
    if not model_deployment_name:
        print_error("❌", "MODEL_DEPLOYMENT_NAME environment variable is not set")
        print_info("Please set MODEL_DEPLOYMENT_NAME in your .env file (e.g., gpt-4o)", dim=True)
        return
    
    print_header("🧪 PRODUCT FINDER AGENT SMOKE TEST")
    print_info(f"📍 Endpoint: {project_endpoint}", dim=True)
    print_info(f"🤖 Model: {model_deployment_name}", dim=True)
    print()
    
    try:
        # Create AIProjectClient with DefaultAzureCredential
        print_step("🔐", "Authenticating with Azure...")
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        with project_client:
            print_step("🏗️", "Creating product finder agent...")
            
            # Load system prompt from template
            system_prompt = load_system_prompt()
            
            # Create agent with basic instructions
            agent = project_client.agents.create_agent(
                model=model_deployment_name,
                name="product-finder-smoke-test",
                instructions=system_prompt,
            )
            print_success("✅", f"Created agent with ID: {Colors.DIM}{agent.id}{Colors.RESET}")
            
            # Create a thread for communication
            print_step("💬", "Creating conversation thread...")
            thread = project_client.agents.threads.create()
            print_success("✅", f"Created thread with ID: {Colors.DIM}{thread.id}{Colors.RESET}")
            
            # Send a test message
            test_message = "Can you help me find products for someone with a nut allergy who likes organic food?"
            print_step("📤", f"Sending test message: {Colors.YELLOW}'{test_message}'{Colors.RESET}")
            
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=test_message,
            )
            print_success("✅", f"Created message with ID: {Colors.DIM}{message.id}{Colors.RESET}")
            
            # Create and process agent run with retry logic
            print_step("⚙️", "Running agent and waiting for response...")
            max_retries = 3
            retry_delay = 5
            run = None
            
            for attempt in range(max_retries):
                try:
                    run = project_client.agents.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=agent.id,
                        timeout=90  # 90 second timeout
                    )
                    # Success - exit retry loop
                    break
                    
                except (DecodeError, HttpResponseError, Exception) as e:
                    error_msg = str(e).lower()
                    if "timed out" in error_msg or "timeout" in error_msg or "json is invalid" in error_msg:
                        print_error("⏱️", f"Request timed out (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            print_info(f"Retrying in {retry_delay}s...", dim=True)
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            print_error("❌", f"Max retries reached. Service may be slow or unavailable.")
                            print_info(f"Error details: {str(e)[:200]}", dim=True)
                            return
                    else:
                        # Different error, don't retry
                        raise
            
            if run is None:
                print_error("❌", "Failed to create run after all retries")
                return
                
            print_success("✅", f"Run completed with status: {Colors.GREEN}{Colors.BOLD}{run.status}{Colors.RESET}")
            
            # Check for failures
            if run.status == RunStatus.FAILED:
                print_error("❌", f"Run failed: {run.last_error}")
                return
            
            # Fetch and display messages
            print_step("📥", "Fetching agent response...")
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            print_header("💬 CONVERSATION TRANSCRIPT")
            
            for msg in reversed(list(messages)):
                role = msg.role.upper()
                if msg.text_messages:
                    for text_msg in msg.text_messages:
                        print_conversation_msg(role, text_msg.text.value)
                        print()
            
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}\n")
            
            # Clean up - delete the agent
            print_step("🧹", f"Cleaning up - deleting agent...")
            project_client.agents.delete_agent(agent.id)
            print_success("✅", "Agent deleted")
            
            print(f"\n{Colors.BG_GREEN}{Colors.BOLD} 🎉 SMOKE TEST PASSED! 🎉 {Colors.RESET}")
            print(f"{Colors.GREEN}The product finder agent is working correctly.{Colors.RESET}\n")
            
    except Exception as e:
        print(f"\n{Colors.BG_RED}{Colors.BOLD} ❌ SMOKE TEST FAILED ❌ {Colors.RESET}")
        print_error("💥", f"Error: {str(e)}")
        logger.exception("Full error details:")
        raise


if __name__ == "__main__":
    main()
