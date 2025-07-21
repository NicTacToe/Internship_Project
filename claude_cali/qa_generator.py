import csv
import re
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QAGenerator:
    def __init__(self, input_csv='california_cybersecurity_data.csv'):
        self.input_csv = input_csv
        self.qa_pairs = []
        
        # Question templates for different types of information
        self.question_templates = {
            'general': [
                "What is {topic}?",
                "Can you explain {topic}?",
                "Tell me about {topic}",
                "What should I know about {topic}?",
                "How does {topic} work in California?"
            ],
            'services': [
                "What cybersecurity services does {source} provide?",
                "How can {source} help with cybersecurity?",
                "What cybersecurity resources are available through {source}?",
                "What cybersecurity programs does California offer?"
            ],
            'incidents': [
                "How should I report a cybersecurity incident in California?",
                "What do I do if I experience a cyber attack?",
                "Who do I contact for cybersecurity incidents?",
                "How does California handle cybersecurity threats?"
            ],
            'protection': [
                "How can I protect my organization from cyber threats?",
                "What are California's cybersecurity best practices?",
                "How can businesses improve their cybersecurity in California?",
                "What cybersecurity measures does California recommend?"
            ],
            'compliance': [
                "What are California's cybersecurity requirements?",
                "What cybersecurity laws apply in California?",
                "How do I comply with California cybersecurity regulations?",
                "What are the cybersecurity compliance requirements for California businesses?"
            ]
        }
        
        # Keywords to identify content types
        self.content_keywords = {
            'incident': ['incident', 'breach', 'attack', 'threat', 'report', 'response'],
            'protection': ['protect', 'secure', 'defense', 'prevention', 'safeguard', 'best practice'],
            'service': ['service', 'program', 'resource', 'assistance', 'support', 'help'],
            'compliance': ['requirement', 'regulation', 'law', 'compliance', 'mandate', 'rule'],
            'general': ['overview', 'about', 'introduction', 'what is', 'definition']
        }
    
    def load_scraped_data(self):
        """Load the scraped data from CSV"""
        try:
            with open(self.input_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                return list(reader)
        except FileNotFoundError:
            logger.error(f"Could not find {self.input_csv}. Make sure to run the scraper first!")
            return []
    
    def extract_key_topics(self, text):
        """Extract key cybersecurity topics from text"""
        # Common cybersecurity topics
        topics = [
            'cybersecurity', 'data protection', 'incident response', 'threat assessment',
            'security awareness', 'risk management', 'vulnerability assessment',
            'security training', 'cyber threats', 'data breach', 'malware',
            'phishing', 'ransomware', 'network security', 'information security',
            'privacy protection', 'security compliance', 'cyber resilience'
        ]
        
        found_topics = []
        text_lower = text.lower()
        
        for topic in topics:
            if topic in text_lower:
                found_topics.append(topic)
        
        return found_topics
    
    def classify_content(self, content):
        """Classify content by type based on keywords"""
        content_lower = content.lower()
        scores = {}
        
        for category, keywords in self.content_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            scores[category] = score
        
        # Return the category with highest score, or 'general' if tied
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def create_answer_from_content(self, content, max_length=300):
        """Create a concise answer from content"""
        sentences = re.split(r'[.!?]+', content)
        
        # Filter out very short sentences
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first few sentences that fit within max_length
        answer = ""
        for sentence in meaningful_sentences[:5]:  # Limit to first 5 sentences
            if len(answer + sentence) < max_length:
                answer += sentence + ". "
            else:
                break
        
        return answer.strip()
    
    def generate_questions_for_content(self, data_row):
        """Generate multiple Q&A pairs for a single content piece"""
        content = data_row['content']
        title = data_row['title']
        source = data_row['source']
        
        if len(content) < 100:  # Skip very short content
            return []
        
        qa_pairs = []
        content_type = self.classify_content(content)
        topics = self.extract_key_topics(content)
        
        # Generate questions based on content type
        templates = self.question_templates.get(content_type, self.question_templates['general'])
        
        # Create Q&A pairs
        for i, template in enumerate(templates[:3]):  # Limit to 3 questions per content
            if '{topic}' in template and topics:
                topic = random.choice(topics)
                question = template.format(topic=topic, source=source)
            elif '{source}' in template:
                question = template.format(source=source, topic='cybersecurity')
            else:
                question = template
            
            # Create answer
            answer = self.create_answer_from_content(content)
            
            if answer:  # Only add if we have a meaningful answer
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'source': source,
                    'url': data_row['url'],
                    'category': content_type,
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Add a specific question based on title if it's informative
        if title and len(title) > 10 and 'No Title' not in title:
            title_question = f"What can you tell me about {title}?"
            title_answer = self.create_answer_from_content(content)
            
            if title_answer:
                qa_pairs.append({
                    'question': title_question,
                    'answer': title_answer,
                    'source': source,
                    'url': data_row['url'],
                    'category': 'general',
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return qa_pairs
    
    def generate_all_qa_pairs(self):
        """Generate Q&A pairs from all scraped data"""
        logger.info("Loading scraped data...")
        scraped_data = self.load_scraped_data()
        
        if not scraped_data:
            logger.error("No scraped data found!")
            return
        
        logger.info(f"Generating Q&A pairs from {len(scraped_data)} content pieces...")
        
        for data_row in scraped_data:
            qa_pairs = self.generate_questions_for_content(data_row)
            self.qa_pairs.extend(qa_pairs)
        
        logger.info(f"Generated {len(self.qa_pairs)} Q&A pairs")
    
    def add_general_california_questions(self):
        """Add some general California cybersecurity questions"""
        general_qa = [
            {
                'question': "What is Cal-CSIC?",
                'answer': "Cal-CSIC (California Cybersecurity Integration Center) is California's primary cybersecurity coordination center that helps protect the state's critical infrastructure and supports cybersecurity efforts across government and private sectors.",
                'source': 'General',
                'url': 'N/A',
                'category': 'general',
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'question': "How do I report a cybersecurity incident in California?",
                'answer': "You can report cybersecurity incidents to Cal-CSIC through their incident reporting system, or contact CalOES for critical infrastructure incidents. They provide 24/7 support for cybersecurity emergencies.",
                'source': 'General',
                'url': 'N/A',
                'category': 'incident',
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'question': "What cybersecurity resources does California provide for businesses?",
                'answer': "California provides various cybersecurity resources including threat intelligence, security assessments, training programs, and incident response support through agencies like CalOES and CDT.",
                'source': 'General',
                'url': 'N/A',
                'category': 'service',
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        self.qa_pairs.extend(general_qa)
    
    def save_qa_dataset(self, filename='california_cybersecurity_qa.csv'):
        """Save Q&A dataset to CSV"""
        if not self.qa_pairs:
            logger.warning("No Q&A pairs to save!")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['question', 'answer', 'source', 'url', 'category', 'generated_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for qa_pair in self.qa_pairs:
                writer.writerow(qa_pair)
        
        logger.info(f"Saved {len(self.qa_pairs)} Q&A pairs to {filename}")
    
    def print_sample_qa(self, num_samples=5):
        """Print sample Q&A pairs for review"""
        if not self.qa_pairs:
            print("No Q&A pairs available!")
            return
        
        print(f"\n=== Sample Q&A Pairs ({num_samples} of {len(self.qa_pairs)}) ===")
        sample_pairs = random.sample(self.qa_pairs, min(num_samples, len(self.qa_pairs)))
        
        for i, qa in enumerate(sample_pairs, 1):
            print(f"\n--- Q&A {i} ---")
            print(f"Q: {qa['question']}")
            print(f"A: {qa['answer'][:200]}..." if len(qa['answer']) > 200 else f"A: {qa['answer']}")
            print(f"Source: {qa['source']} | Category: {qa['category']}")

def main():
    generator = QAGenerator()
    generator.generate_all_qa_pairs()
    generator.add_general_california_questions()
    generator.save_qa_dataset()
    generator.print_sample_qa()
    
    print(f"\n✅ Q&A generation completed!")
    print(f"Generated {len(generator.qa_pairs)} question-answer pairs")
    print("Dataset saved to 'california_cybersecurity_qa.csv'")

if __name__ == "__main__":
    main()