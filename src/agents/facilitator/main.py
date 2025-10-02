"""
Smoke test for Facilitator agent using Azure AI Foundry Agent Service.

This script creates a basic agent, sends a test message, and verifies the response.
"""
import os
import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run smoke test for facilitator agent."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
    
    if not project_endpoint:
        logger.error("PROJECT_ENDPOINT environment variable is not set")
        logger.info("Please copy .env.sample to .env and configure your Azure AI Foundry project endpoint")
        return
    
    if not model_deployment_name:
        logger.error("MODEL_DEPLOYMENT_NAME environment variable is not set")
        logger.info("Please set MODEL_DEPLOYMENT_NAME in your .env file (e.g., gpt-4o)")
        return
    
    logger.info("Starting facilitator agent smoke test...")
    logger.info(f"Project endpoint: {project_endpoint}")
    logger.info(f"Model deployment: {model_deployment_name}")
    
    try:
        # Create AIProjectClient with DefaultAzureCredential
        logger.info("Authenticating with Azure using DefaultAzureCredential...")
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        with project_client:
            logger.info("Creating facilitator agent...")
            
            # Create agent with basic instructions
            agent = project_client.agents.create_agent(
                model=model_deployment_name,
                name="facilitator-smoke-test",
                instructions="""You are a helpful facilitator agent for a product discovery system.
                Your role is to help users find the right products by understanding their needs.
                For this smoke test, simply acknowledge that you can help with product discovery.""",
            )
            logger.info(f"✓ Created agent with ID: {agent.id}")
            
            # Create a thread for communication
            logger.info("Creating conversation thread...")
            thread = project_client.agents.threads.create()
            logger.info(f"✓ Created thread with ID: {thread.id}")
            
            # Send a test message
            test_message = "Hello! Can you help me find products?"
            logger.info(f"Sending test message: '{test_message}'")
            
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=test_message,
            )
            logger.info(f"✓ Created message with ID: {message.id}")
            
            # Create and process agent run
            logger.info("Running agent and waiting for response...")
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            logger.info(f"✓ Run completed with status: {run.status}")
            
            # Check for failures
            if run.status == "failed":
                logger.error(f"✗ Run failed: {run.last_error}")
                return
            
            # Fetch and display messages
            logger.info("Fetching agent response...")
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            logger.info("\n" + "="*60)
            logger.info("CONVERSATION TRANSCRIPT")
            logger.info("="*60)
            
            for msg in reversed(list(messages)):
                role = msg.role.upper()
                if msg.text_messages:
                    for text_msg in msg.text_messages:
                        logger.info(f"\n{role}: {text_msg.text.value}")
            
            logger.info("\n" + "="*60)
            
            # Clean up - delete the agent
            logger.info(f"\nCleaning up - deleting agent {agent.id}...")
            project_client.agents.delete_agent(agent.id)
            logger.info("✓ Deleted agent")
            
            logger.info("\n" + "🎉 SMOKE TEST PASSED! 🎉")
            logger.info("The facilitator agent is working correctly.")
            
    except Exception as e:
        logger.error(f"\n✗ SMOKE TEST FAILED: {str(e)}")
        logger.exception("Full error details:")
        raise


if __name__ == "__main__":
    main()
