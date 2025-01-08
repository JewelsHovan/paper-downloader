"""
Tests for the PaperDownloader class.
"""
import pytest
from paper_downloader import PaperDownloader

@pytest.fixture
def downloader():
    """Create a PaperDownloader instance for testing."""
    return PaperDownloader()

def test_get_pmid_from_doi(downloader):
    """Test DOI to PMID conversion with a known paper."""
    # Using a known PubMed paper: "Lithocholic acid phenocopies anti-ageing effects of calorie restriction"
    doi = "10.1038/s41586-024-07095-8"
    pmid = downloader.get_pmid_from_doi(doi)
    assert pmid is not None
    assert pmid.isdigit()
    assert pmid == "38418917"  # Known PMID for this paper

def test_get_abstract_from_pmid(downloader):
    """Test abstract retrieval with a known PMID."""
    # Using PMID of a well-known paper
    pmid = "19197451"  # This is a real PubMed ID
    result = downloader.get_abstract_from_pmid(pmid)
    
    assert result is not None
    assert isinstance(result, dict)
    assert 'pmid' in result
    assert 'title' in result
    assert 'abstract' in result
    assert 'journal' in result
    
def test_invalid_doi(downloader):
    """Test behavior with invalid DOI."""
    doi = "invalid.doi/123456"
    pmid = downloader.get_pmid_from_doi(doi)
    assert pmid is None

def test_invalid_pmid(downloader):
    """Test behavior with invalid PMID."""
    pmid = "99999999999999"  # Invalid PMID
    result = downloader.get_abstract_from_pmid(pmid)
    assert result is None 