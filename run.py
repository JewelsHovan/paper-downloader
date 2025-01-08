"""
Example script demonstrating the usage of PaperDownloader class.
"""
import os
import json
import logging
from pathlib import Path
from paper_downloader import PaperDownloader
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path='config.json'):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        raise

def format_text(text_data):
    """Helper function to format text data which might be a string, list, or dict."""
    if isinstance(text_data, str):
        return text_data
    elif isinstance(text_data, list):
        return ' '.join(str(item) for item in text_data)
    elif isinstance(text_data, dict):
        # Handle different possible dictionary structures
        if 'AbstractText' in text_data:
            return str(text_data.get('AbstractText', ''))
        return ' '.join(str(value) for value in text_data.values())
    return str(text_data)

def save_paper_data(paper_data, output_dir):
    """Save paper data to files in the specified directory."""
    # Create output directory if it doesn't exist
    paper_dir = Path(output_dir) / f"paper_{paper_data['pmid']}"
    paper_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata as JSON
    metadata = {
        'pmid': paper_data['pmid'],
        'title': paper_data['title'],
        'journal': paper_data['journal'],
        'doi': paper_data.get('doi', ''),
        'pmc_id': paper_data.get('pmc_id', ''),
        'full_text_url': paper_data.get('full_text_url', '')
    }
    with open(paper_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Save abstract
    abstract_text = format_text(paper_data['abstract'])
    with open(paper_dir / 'abstract.txt', 'w', encoding='utf-8') as f:
        f.write(abstract_text)

    # Save full text if available
    if 'full_text' in paper_data and paper_data['full_text']:
        full_text = format_text(paper_data['full_text'])
        with open(paper_dir / 'full_text.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)

def main():
    # Load configuration
    config = load_config()
    
    # Get API key from environment variable (recommended for security)
    api_key = os.getenv('NCBI_API_KEY')
    if not api_key:
        logger.warning("No API key found. Rate limits will be restricted.")
    
    # Set up output directory from config
    output_dir = Path(config.get('output_directory', 'downloaded_papers'))
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the downloader
    downloader = PaperDownloader(api_key=api_key)
    
    # Process each paper from config
    for entry in config['papers']:
        doi = entry['doi']
        description = entry.get('description', '')
        
        logger.info(f"Processing DOI: {doi} ({description})")
        
        try:
            # Step 1: Get PMID from DOI
            pmid = downloader.get_pmid_from_doi(doi)
            if not pmid:
                logger.error(f"Could not find PMID for DOI: {doi}")
                continue
                
            logger.info(f"Found PMID: {pmid}")
            
            # Step 2: Try to get full text using PMID
            paper_data = downloader.get_full_text(pmid)
            if not paper_data:
                logger.error(f"Could not retrieve paper data for PMID: {pmid}")
                continue
            
            # Add DOI and description to paper data
            paper_data['doi'] = doi
            paper_data['description'] = description
            
            # Save the paper data
            save_paper_data(paper_data, output_dir)
            logger.info(f"Successfully saved paper data for PMID: {pmid}")
            
            # Print summary
            print("\nPaper Details:")
            print(f"Title: {paper_data['title']}")
            print(f"Journal: {paper_data['journal']}")
            print(f"Description: {description}")
            print(f"Output directory: {output_dir}/paper_{pmid}/")
            
            if 'pmc_id' in paper_data:
                print(f"PMC ID: {paper_data['pmc_id']}")
                print(f"Full Text URL: {paper_data['full_text_url']}")
            
            print("-" * 80)

        except Exception as e:
            logger.error(f"Error processing DOI {doi}: {str(e)}")
            continue

        # Respect rate limits
        time.sleep(3)

if __name__ == "__main__":
    main()
