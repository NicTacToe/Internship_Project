import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaliforniaCyberScraper:
    def __init__(self):
        self.session = requests.Session()
        # Enhanced headers to bypass 403 errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Add retry strategy
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            backoff_factor=2
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.scraped_data = []
        
        # Target websites with updated URLs and more sources
        self.target_sites = {
            'CalOES': {
                'base_url': 'https://www.caloes.ca.gov',
                'cybersecurity_paths': [
                    '/cal-oes-divisions/law-enforcement/cybersecurity/',
                    '/office-of-the-director/operations/recovery-preparedness/cybersecurity/',
                ]
            },
            'CDT': {
                'base_url': 'https://cdt.ca.gov',
                'cybersecurity_paths': [
                    '/services/cybersecurity/',
                    '/services/security/',
                    '/technology-services/information-security/'
                ]
            },
            'CA.gov': {
                'base_url': 'https://www.ca.gov',
                'cybersecurity_paths': [
                    '/service/report-cyber-crime/',
                    '/government/'
                ]
            },
            'CAL-CSIC': {
                'base_url': 'https://calcsic.org',
                'cybersecurity_paths': ['/']
            },
            'Department of Justice': {
                'base_url': 'https://oag.ca.gov',
                'cybersecurity_paths': [
                    '/cybersecurity',
                    '/privacy',
                    '/data-breaches'
                ]
            },
            'CISA California': {
                'base_url': 'https://www.cisa.gov',
                'cybersecurity_paths': [
                    '/state-local-tribal-territorial',
                    '/cybersecurity-best-practices'
                ]
            }
        }
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might cause CSV issues
        text = re.sub(r'[^\w\s\-.,!?:;()"]', '', text)
        return text
    
    def extract_content_from_page(self, url, source_name):
        """Extract meaningful content from a webpage with enhanced error handling"""
        try:
            logger.info(f"Scraping: {url}")
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=15, allow_redirects=True)
            
            # Handle different response codes
            if response.status_code == 403:
                logger.warning(f"403 Forbidden for {url} - trying alternative approach")
                # Try with different headers
                alt_headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
                    'Referer': 'https://www.google.com/',
                    'Accept': '*/*'
                }
                response = self.session.get(url, headers=alt_headers, timeout=15)
            
            if response.status_code == 404:
                logger.warning(f"404 Not Found for {url} - skipping")
                return None
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Enhanced content extraction with multiple fallbacks
            content_selectors = [
                'main', '.main-content', '#main-content', '.content', '.page-content',
                '.entry-content', 'article', '.article-content', '.post-content',
                '#content', '.body-content', '.site-content'
            ]
            
            content_elements = []
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_elements.extend(elements)
                    break
            
            # If no main content found, use body
            if not content_elements:
                content_elements = [soup.body] if soup.body else [soup]
            
            # Extract text content with better filtering
            content_text = ""
            for element in content_elements:
                # Get headings and paragraphs
                for tag in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
                    text = tag.get_text().strip()
                    # Better filtering for meaningful content
                    if (text and len(text) > 30 and 
                        not text.lower().startswith(('cookie', 'javascript', 'skip to', 'menu')) and
                        'cyber' in text.lower() or 'security' in text.lower() or len(text) > 100):
                        content_text += text + " "
            
            content_text = self.clean_text(content_text)
            
            if len(content_text) > 200:  # Only store meaningful content
                return {
                    'source': source_name,
                    'url': url,
                    'title': self.clean_text(title_text),
                    'content': content_text[:8000],  # Increased limit
                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error scraping {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def find_cybersecurity_links(self, base_url, source_name):
        """Find additional cybersecurity-related links on a site"""
        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            cyber_links = []
            
            # Look for links containing cybersecurity keywords
            keywords = ['cyber', 'security', 'threat', 'incident', 'breach', 'protection', 'privacy']
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text().lower()
                
                if any(keyword in link_text or keyword in href.lower() for keyword in keywords):
                    full_url = urljoin(base_url, href)
                    if base_url in full_url:  # Only internal links
                        cyber_links.append(full_url)
            
            return list(set(cyber_links))[:5]  # Limit to 5 additional links
        
        except Exception as e:
            logger.error(f"Error finding links on {base_url}: {str(e)}")
            return []
    
    def scrape_all_sites(self):
        """Scrape all target sites for cybersecurity information"""
        logger.info("Starting California cybersecurity data scraping...")
        
        for source_name, site_info in self.target_sites.items():
            base_url = site_info['base_url']
            logger.info(f"Scraping {source_name}...")
            
            # Scrape predefined paths
            for path in site_info['cybersecurity_paths']:
                url = urljoin(base_url, path)
                content = self.extract_content_from_page(url, source_name)
                if content:
                    self.scraped_data.append(content)
            
            # Find and scrape additional cybersecurity links
            additional_links = self.find_cybersecurity_links(base_url, source_name)
            for link in additional_links:
                content = self.extract_content_from_page(link, source_name)
                if content:
                    self.scraped_data.append(content)
            
            # Be respectful with requests
            time.sleep(2)
    
    def save_to_csv(self, filename='california_cybersecurity_data.csv'):
        """Save scraped data to CSV file"""
        if not self.scraped_data:
            logger.warning("No data to save!")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['source', 'url', 'title', 'content', 'scraped_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.scraped_data:
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.scraped_data)} records to {filename}")

def main():
    scraper = CaliforniaCyberScraper()
    scraper.scrape_all_sites()
    scraper.save_to_csv()
    
    print(f"Scraping completed! Found {len(scraper.scraped_data)} cybersecurity-related pages.")
    print("Data saved to 'california_cybersecurity_data.csv'")

if __name__ == "__main__":
    main()