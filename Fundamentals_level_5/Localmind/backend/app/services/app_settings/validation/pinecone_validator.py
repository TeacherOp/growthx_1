"""
Pinecone API key validator.

Educational Note: Validates Pinecone API keys and auto-creates the
"growthxlearn" index if it doesn't exist.
"""
from typing import Tuple, Dict, Optional
from pinecone import Pinecone
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import time


def validate_pinecone_key(api_key: str) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """
    Validate Pinecone API key and auto-create/check index.

    Educational Note: This validator does more than just test the API key.
    It also ensures a "growthxlearn" index exists for the application to use.
    If the index doesn't exist, it creates it automatically.

    Args:
        api_key: The Pinecone API key to validate

    Returns:
        Tuple of (is_valid, message, index_details)
        index_details contains: {'index_name': 'growthxlearn', 'region': 'us-east-1'}
    """
    if not api_key or api_key == '':
        return False, "API key is empty", None

    # Standard index configuration for the application
    INDEX_NAME = "growthxlearn"
    REGION = "us-east-1"
    CLOUD = "aws"

    try:
        # Create Pinecone client with the provided API key
        print(f"Creating Pinecone client...")
        pc = Pinecone(api_key=api_key)

        # Check if the index already exists
        print(f"Checking if index '{INDEX_NAME}' exists...")
        if pc.has_index(INDEX_NAME):
            print(f"Index '{INDEX_NAME}' already exists, using existing index")
            # Index exists, just return success
            index_details = {
                'index_name': INDEX_NAME,
                'region': REGION
            }
            return True, f"Valid Pinecone API key (using existing index '{INDEX_NAME}')", index_details
        else:
            # Index doesn't exist, create it
            print(f"Index '{INDEX_NAME}' not found, creating new index...")
            pc.create_index(
                name=INDEX_NAME,
                vector_type="dense",
                dimension=1536,  # Standard for OpenAI embeddings
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=CLOUD,
                    region=REGION
                ),
                deletion_protection="disabled",
                tags={
                    "environment": "development",
                    "created_by": "localmind"
                }
            )

            # Wait for the index to be ready (with timeout)
            print(f"Waiting for index '{INDEX_NAME}' to be ready...")
            max_wait_time = 60  # seconds
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                try:
                    # Check index status
                    index_list = pc.list_indexes()
                    for idx in index_list:
                        if idx['name'] == INDEX_NAME and idx.get('status', {}).get('ready', False):
                            print(f"Index '{INDEX_NAME}' is ready!")
                            index_details = {
                                'index_name': INDEX_NAME,
                                'region': REGION
                            }
                            return True, f"Valid Pinecone API key (created index '{INDEX_NAME}')", index_details

                    # Wait a bit before checking again
                    time.sleep(2)
                except Exception as e:
                    print(f"Error checking index status: {e}")
                    time.sleep(2)

            # If we get here, index creation timed out but might still succeed
            # Return success anyway since the API key is valid
            index_details = {
                'index_name': INDEX_NAME,
                'region': REGION
            }
            return True, f"Valid Pinecone API key (index '{INDEX_NAME}' is being created)", index_details

    except Exception as e:
        error_message = str(e).lower()

        # Check for common error types
        if 'invalid' in error_message or 'unauthorized' in error_message or 'api key' in error_message:
            return False, "Invalid API key", None
        elif 'quota' in error_message or 'limit' in error_message:
            return False, "API key valid but quota/limit exceeded", None
        elif 'rate' in error_message:
            return True, "Valid API key (rate limited)", {'index_name': INDEX_NAME, 'region': REGION}
        else:
            print(f"Pinecone validation error: {type(e).__name__}: {str(e)}")
            return False, f"Validation failed: {str(e)[:100]}", None
