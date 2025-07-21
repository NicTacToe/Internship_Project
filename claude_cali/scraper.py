import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaliforniaCyberScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = []
        
        # Target websites and their specific cybersecurity sections
        self.target_sites = {
            'CalOES': {
                'base_url': 'https://www.caloes.ca.gov',
                'cybersecurity_paths': [
                    '/office-of-the-director/policy-administration/cyber-security-integration-center/',
                    '/cal-oes-divisions/law-enforcement/cybersecurity/',
                ]
            },
            'CDT': {
                'base_url': 'https://cdt.ca.gov',
                'cybersecurity_paths': [
                    '/services/cybersecurity/',
                    '/services/security/',
                    '/cybersecurity/'
                ]
            },
            'CA.gov': {
                'base_url': 'https://www.ca.gov',
                'cybersecurity_paths': [
                    '/government/cybersecurity/',
                ]
            },
            'CAL-CSIC': {
                'base_url': 'https://www.calcsic.org',
                'cybersecurity_paths': ['/']
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
        """Extract meaningful content from a webpage"""
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Extract main content areas
            content_selectors = [
                'main', '.main-content', '#main-content', '.content',
                '.entry-content', 'article', '.article-content'
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
            
            # Extract text content
            content_text = ""
            for element in content_elements:
                # Get headings and paragraphs
                for tag in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
                    text = tag.get_text().strip()
                    if text and len(text) > 20:  # Filter out very short texts
                        content_text += text + " "
            
            content_text = self.clean_text(content_text)
            
            if len(content_text) > 100:  # Only store meaningful content
                return {
                    'source': source_name,
                    'url': url,
                    'title': self.clean_text(title_text),
                    'content': content_text[:5000],  # Limit content length
                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
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