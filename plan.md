# plan.md

## 1. Overview

This document outlines the plan for implementing a PubMed paper download workflow based on NCBI's Entrez Programming Utilities (E-utilities). The primary goal is to retrieve the abstracts (or full text, when permissible) for a large number of research articles, prioritizing DOIs but allowing fallback to PubMed IDs (PMIDs) or text-based queries.

## 2. Objectives

1. **DOI-based Retrieval**  
   - Given a list of DOIs, efficiently map each DOI to a PMID (where available), then retrieve the relevant paper data (abstracts, metadata).

2. **Fallback Mechanism**  
   - If the DOI -> PMID lookup fails, attempt secondary strategies, such as text-based queries with the article title, keywords, or authors.

3. **Scalability**  
   - Handle large volumes of queries without violating NCBI rate limits.  
   - Utilize the Entrez History server for batch operations.

4. **Robustness**  
   - Incorporate error handling, logging, and retry logic for network issues or invalid queries.

5. **Maintainability**  
   - Code should be modular, well-documented, and easily extensible for new features or evolving NCBI policies.

## 3. Technical Approach

### 3.1 Data Flow

1. **Input**  
   - A list of DOIs in a file or database.  
   - (Optional) Additional metadata such as article title, authors, or year if needed for fallback searches.

2. **ESearch (with DOI)**  
   - For each DOI, call `ESearch` with `db=pubmed` and `term=<DOI>`.  
   - Retrieve the JSON/XML response, parse out the PMIDs.

3. **EFetch (by PMID)**  
   - Once a valid PMID is found, call `EFetch` with the desired format (`retmode=xml` or `rettype=abstract`).  
   - Parse the returned XML to extract abstract text and relevant metadata.

4. **Storage**  
   - Store the retrieved abstracts, PMIDs, DOIs, and any additional metadata in a structured format (e.g., JSON, CSV, or a relational database).  
   - Log any errors (no results, malformed requests, etc.).

5. **Rate Limit Handling**  
   - Include a short delay between requests if not using an API key (3 requests/second max).  
   - If using an API key (10 requests/second max), still implement throttling to handle spikes and avoid timeouts.

### 3.2 Batch Operations with History Server (Optional)

- When processing thousands of queries:  
  1. **EPost**: Upload a list of PMIDs to the Entrez History server.  
  2. **EFetch**: Use `WebEnv` and `query_key` to batch-retrieve results, which is more efficient than many individual calls.

### 3.3 Error and Logging Strategy

- **Logging**:  
  - Timestamp each request to E-utilities.  
  - Record the request parameters, status code, and any error messages.  
  - Maintain an error log for failed lookups or malformed responses.

- **Retries**:  
  - For HTTP 429 (Too Many Requests) or other transient errors, implement exponential backoff.  
  - Possibly queue failed DOIs for a second pass after a cooldown period.

## 4. Implementation Steps

1. **Set Up Project Structure**  
   - Create a Python package or script directory (e.g., `scraper/`).  
   - Add a `requirements.txt` listing dependencies: `requests`, possibly `xmltodict` or an XML parsing library.

2. **Write a Configuration File**  
   - Store NCBI API key (if available) in environment variables for security.  
   - Include rate limit settings, log file paths, etc.

3. **Build the Core Functions**  
   - **`get_pmid_from_doi(doi, api_key=None)`**  
     - Sends an `ESearch` request to NCBI.  
     - Parses JSON response for PMIDs.  
     - Returns the first PMID if present.
   - **`get_abstract_from_pmid(pmid, api_key=None)`**  
     - Sends an `EFetch` request.  
     - Parses the XML for the `<AbstractText>` node.  
     - Returns the abstract text (or `None` if not found).

4. **Assemble the Main Script / Pipeline**  
   - Read DOIs from an input file or database.  
   - For each DOI:  
     1. Retrieve PMID (via `get_pmid_from_doi`).  
     2. If DOI -> PMID fails, optionally attempt a fallback search with article title/keywords.  
     3. Retrieve abstract using `get_abstract_from_pmid`.  
     4. Write results (PMID, abstract, etc.) to your storage (database or JSON lines file).

5. **Implement Logging and Error Handling**  
   - Wrap API calls in try/except blocks.  
   - If a request fails, record the error and possibly retry.

6. **Testing and Validation**  
   - Use a small set of known DOIs to ensure the workflow is correct.  
   - Validate that retrieved abstracts match expected content.  
   - Confirm the logic for fallback queries if DOI is not recognized.

7. **Performance Tuning (Optional)**  
   - If dealing with tens of thousands of DOIs, integrate the Entrez History server to reduce overhead.  
   - Monitor performance metrics, memory usage, and response times.

## 5. Timeline

| Phase             | Task                                   | Duration         |
|-------------------|----------------------------------------|------------------|
| **Phase 1**       | Project setup & initial environment    | 1-2 days         |
| **Phase 2**       | Core functions (ESearch, EFetch)       | 2-3 days         |
| **Phase 3**       | Logging & error handling               | 2 days           |
| **Phase 4**       | Testing & fallback queries             | 1-2 days         |
| **Phase 5**       | Performance tuning & batch downloads   | 1-2 weeks (ongoing) |

## 6. References

- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25500/)  
- [PubMed MEDLINE FTP](https://www.nlm.nih.gov/databases/download/pubmed_medline.html)

---

=> Libraries to use: requests, xmltodict, tqdm (progress bar), time (sleep)
