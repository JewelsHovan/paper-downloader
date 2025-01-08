"""
PubMed paper downloader using NCBI E-utilities.
"""
import os
import time
import logging
import requests
import xmltodict
import re
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperDownloader:
    """Main class for downloading papers from PubMed."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    DOI_PATTERN = re.compile(r'^10\.\d{4,9}/[-._;()/:\w]+$')
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the downloader with optional API key."""
        self.api_key = api_key
        self.requests_per_second = 10 if api_key else 3
        self.last_request_time = 0
    
    def _throttle(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.0 / self.requests_per_second:
            time.sleep(1.0 / self.requests_per_second - time_since_last_request)
        self.last_request_time = time.time()
    
    def get_pmid_from_doi(self, doi: str) -> Optional[str]:
        """Convert a DOI to a PubMed ID (PMID)."""
        # Validate DOI format
        if not self.DOI_PATTERN.match(doi):
            logger.error(f"Invalid DOI format: {doi}")
            return None
            
        self._throttle()
        
        params = {
            "db": "pubmed",
            "term": f"\"{doi}\"[DOI]",  # Exact match with quotes
            "retmode": "json",
            "field": "DOI",  # Restrict to DOI field only
        }
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(f"{self.BASE_URL}/esearch.fcgi", params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return id_list[0] if id_list else None
            
        except (requests.RequestException, IndexError, KeyError) as e:
            logger.error(f"Error getting PMID for DOI {doi}: {str(e)}")
            return None
    
    def get_abstract_from_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Retrieve abstract and metadata for a given PMID."""
        self._throttle()
        
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(f"{self.BASE_URL}/efetch.fcgi", params=params, timeout=60)
            response.raise_for_status()
            
            data = xmltodict.parse(response.text)
            
            # Check if we have valid article data
            if ('PubmedArticleSet' not in data or
                not data['PubmedArticleSet'] or
                'PubmedArticle' not in data['PubmedArticleSet']):
                return None
            
            article = data['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']
            
            return {
                'pmid': pmid,
                'title': article.get('ArticleTitle', ''),
                'abstract': article.get('Abstract', {}).get('AbstractText', ''),
                'journal': article.get('Journal', {}).get('Title', ''),
                'publication_date': article.get('Journal', {}).get('PubDate', {}),
            }
            
        except (requests.RequestException, KeyError, xmltodict.expat.ExpatError) as e:
            logger.error(f"Error getting abstract for PMID {pmid}: {str(e)}")
            return None 
    
    def get_full_text(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Retrieve full paper data including abstract and full text if available."""
        self._throttle()
        
        # First get the basic article data
        article_data = self.get_abstract_from_pmid(pmid)
        if not article_data:
            return None
        
        # Try to get PMC ID for full text access
        params = {
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pmc",
            "retmode": "json"
        }
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(f"{self.BASE_URL}/elink.fcgi", params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Extract PMC ID if available
            link_set = data.get('linksets', [{}])[0]
            id_list = link_set.get('linksetdbs', [{}])[0].get('links', [])
            
            if id_list:
                pmc_id = f"PMC{id_list[0]}"
                article_data['pmc_id'] = pmc_id
                article_data['full_text_url'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}"
                
                # Get full text from PMC
                self._throttle()
                full_text_params = {
                    "db": "pmc",
                    "id": pmc_id,
                    "retmode": "xml",
                    "rettype": "full"
                }
                if self.api_key:
                    full_text_params["api_key"] = self.api_key
                
                full_text_response = requests.get(f"{self.BASE_URL}/efetch.fcgi", 
                                                params=full_text_params, timeout=60)
                full_text_response.raise_for_status()
                
                # Parse XML and extract full text
                data = xmltodict.parse(full_text_response.text)
                article_data['full_text'] = data.get('pmc-articleset', {}).get('article', {})
                
        except (requests.RequestException, KeyError, IndexError) as e:
            logger.warning(f"Could not retrieve full text for PMID {pmid}: {str(e)}")
            # Continue with abstract only
            pass
        
        return article_data 
