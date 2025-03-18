#!/usr/bin/env python
import sys
import warnings
import os
import logging
from dotenv import load_dotenv
import agentops
from datetime import datetime
from supplier.crew import Supplier
from supplier.config import SupplierConfig, DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supplier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables are set"""
    required_vars = [
        "AGENTOPS_API_KEY",
        "SERPER_API_KEY",
        "APIVOID_API_KEY",
        "SCRAPFLY_API_KEY"
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Load and validate environment variables
try:
    load_dotenv()
    validate_environment()
    logger.info("Environment variables loaded and validated successfully")
except Exception as e:
    logger.error(f"Failed to load environment variables: {str(e)}")
    raise

# Initialize agentops
agentops.init(
    api_key=os.getenv("AGENTOPS_API_KEY"),
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Ubiquiti',
        'country': "USA"
    }
    
    try:
        config = SupplierConfig.validate_inputs(inputs or DEFAULT_CONFIG)
        logger.info(f"Starting crew run with config: {config}")
        Supplier().crew().kickoff(inputs=vars(config))
        logger.info("Crew run completed successfully")
    except ValueError as e:
        logger.error(f"Invalid configuration: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An error occurred while running the crew: {str(e)}", exc_info=True)
        raise

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'topic': 'Garmin',
        'country': "USA"
    }
    try:
        if len(sys.argv) < 3:
            raise ValueError("Please provide number of iterations and filename")
        
        config = SupplierConfig.validate_inputs(DEFAULT_CONFIG)
        n_iterations = int(sys.argv[1])
        filename = sys.argv[2]
        
        logger.info(f"Starting crew training with {n_iterations} iterations")
        Supplier().crew().train(n_iterations=n_iterations, filename=filename, inputs=vars(config))
        logger.info("Crew training completed successfully")
    except (IndexError, ValueError) as e:
        logger.error("Invalid arguments provided for training", exc_info=True)
        raise ValueError(str(e))
    except Exception as e:
        logger.error(f"An error occurred while training the crew: {str(e)}", exc_info=True)
        raise

def replay():
    """Replay the crew execution from a specific task."""
    try:
        if len(sys.argv) < 2:
            raise ValueError("Please provide a task_id for replay")
            
        task_id = sys.argv[1]
        logger.info(f"Starting crew replay for task_id: {task_id}")
        Supplier().crew().replay(task_id=task_id)
        logger.info("Crew replay completed successfully")
    except ValueError as e:
        logger.error(str(e), exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An error occurred while replaying the crew: {str(e)}", exc_info=True)
        raise

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'topic': 'Garmin',
        'country': "USA"
    }
    try:
        if len(sys.argv) < 3:
            raise ValueError("Please provide number of iterations and OpenAI model name")
            
        config = SupplierConfig.validate_inputs(DEFAULT_CONFIG)
        n_iterations = int(sys.argv[1])
        model_name = sys.argv[2]
        
        logger.info(f"Starting crew test with {n_iterations} iterations")
        Supplier().crew().test(n_iterations=n_iterations, openai_model_name=model_name, inputs=vars(config))
        logger.info("Crew test completed successfully")
    except (IndexError, ValueError) as e:
        logger.error("Invalid arguments provided for testing", exc_info=True)
        raise ValueError(str(e))
    except Exception as e:
        logger.error(f"An error occurred while testing the crew: {str(e)}", exc_info=True)
        raise
