"""
Test script for semantic search functionality.

Usage:
    python test_semantic_search.py <project_id> "<search_query>"

Example:
    python test_semantic_search.py 8161ddec-10d6-40f3-95e3-876ef549eedd "What is machine learning?"
"""
import sys
from pathlib import Path

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config import Config
from app.services.embedding_workflow_service import embedding_workflow_service


def test_semantic_search(project_id: str, query: str, top_k: int = 5):
    """
    Test semantic search for a project.

    Args:
        project_id: The project UUID
        query: Search query text
        top_k: Number of results to return
    """
    print(f"\n{'='*60}")
    print(f"Semantic Search Test")
    print(f"{'='*60}")
    print(f"Project ID: {project_id}")
    print(f"Query: {query}")
    print(f"Top K: {top_k}")
    print(f"{'='*60}\n")

    # Get chunks directory for the project
    chunks_dir = Config.PROJECTS_DIR / project_id / "sources" / "chunks"

    if not chunks_dir.exists():
        print(f"Error: Chunks directory not found: {chunks_dir}")
        print("Make sure the project has embedded sources.")
        return

    # Perform search
    print("Searching...")
    results = embedding_workflow_service.search_similar(
        project_id=project_id,
        query_text=query,
        chunks_dir=chunks_dir,
        top_k=top_k
    )

    if not results:
        print("\nNo results found.")
        print("Possible reasons:")
        print("  - No embedded sources in this project")
        print("  - Pinecone not configured")
        print("  - OpenAI API key not set")
        return

    print(f"\nFound {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"Score: {result.get('score', 'N/A'):.4f}")
        print(f"Source: {result.get('source_name', 'Unknown')}")
        print(f"Page: {result.get('page_number', 'N/A')}")
        print(f"Chunk ID: {result.get('chunk_id', 'N/A')}")
        print(f"Text preview: {result.get('text', '')[:200]}...")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nAvailable projects:")
        projects_dir = Config.PROJECTS_DIR
        if projects_dir.exists():
            for p in projects_dir.iterdir():
                if p.is_dir() and (p / "sources" / "chunks").exists():
                    print(f"  - {p.name}")
        sys.exit(1)

    project_id = sys.argv[1]
    query = sys.argv[2]
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    test_semantic_search(project_id, query, top_k)
