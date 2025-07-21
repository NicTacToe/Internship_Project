import csv
import re
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaliforniaCybersecurityChatbot:
    def __init__(self, qa_csv='california_cybersecurity_qa.csv'):
        self.qa_csv = qa_csv
        self.qa_data = []
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        self.question_vectors = None
        self.is_trained = False
        
        # Enhanced greeting responses
        self.greetings = [
            "Hello! I'm your California Cybersecurity Assistant. I can help you with information about California's cybersecurity initiatives, services, and best practices. What would you like to know?",
            "Hi there! I'm here to help with California cybersecurity information. Feel free to ask about cyber threats, incident reporting, or state cybersecurity services.",
            "Welcome! I can provide information about California's cybersecurity programs and resources. What cybersecurity topic can I help you with today?"
        ]
        
        # Fallback responses for when no good match is found
        self.fallback_responses = [
            "I don't have specific information about that topic in my California cybersecurity database. However, I'd recommend contacting Cal-CSIC (California Cybersecurity Integration Center) or CalOES for more specialized assistance.",
            "That's an interesting question, but I don't have detailed information about that specific topic. You might want to check the official California cybersecurity websites or contact the California Department of Technology (CDT) for more information.",
            "I'm not finding a good match for that question in my knowledge base. For the most current and specific information, I'd suggest visiting the official CalOES or CDT cybersecurity pages."
        ]
    
    def load_qa_data(self):
        """Load the Q&A dataset"""
        try:
            with open(self.qa_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.qa_data = list(reader)
            
            logger.info(f"Loaded {len(self.qa_data)} Q&A pairs")
            return True
        except FileNotFoundError:
            logger.error(f"Could not find {self.qa_csv}. Make sure to run the Q&A generator first!")
            return False
    
    def train_model(self):
        """Train the TF-IDF model on questions"""
        if not self.qa_data:
            logger.error("No Q&A data loaded!")
            return False
        
        questions = [qa['question'] for qa in self.qa_data]
        
        # Fit the vectorizer on all questions
        self.question_vectors = self.vectorizer.fit_transform(questions)
        self.is_trained = True
        
        logger.info("Model trained successfully!")
        return True
    
    def preprocess_query(self, query):
        """Clean and preprocess user query"""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Remove special characters except question marks
        query = re.sub(r'[^\w\s\?]', '', query)
        
        return query
    
    def is_greeting(self, query):
        """Check if the query is a greeting"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in query.lower() for greeting in greetings)
    
    def find_best_match(self, user_query, similarity_threshold=0.1):
        """Find the best matching Q&A pair for the user query"""
        if not self.is_trained:
            logger.error("Model not trained yet!")
            return None
        
        # Vectorize the user query
        query_vector = self.vectorizer.transform([user_query])
        
        # Calculate cosine similarity with all questions
        similarities = cosine_similarity(query_vector, self.question_vectors).flatten()
        
        # Find the best match
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        # Return match if similarity is above threshold
        if best_similarity >= similarity_threshold:
            return {
                'qa_pair': self.qa_data[best_match_idx],
                'similarity': best_similarity,
                'confidence': 'high' if best_similarity > 0.3 else 'medium' if best_similarity > 0.15 else 'low'
            }
        
        return None
    
    def generate_response(self, user_query):
        """Generate a response to the user query"""
        processed_query = self.preprocess_query(user_query)
        
        # Handle greetings
        if self.is_greeting(processed_query):
            return {
                'response': np.random.choice(self.greetings),
                'confidence': 'high',
                'source': 'System',
                'type': 'greeting'
            }
        
        # Find best match
        match = self.find_best_match(processed_query)
        
        if match:
            qa_pair = match['qa_pair']
            confidence = match['confidence']
            
            # Customize response based on confidence
            if confidence == 'high':
                response = qa_pair['answer']
            elif confidence == 'medium':
                response = f"Based on available information: {qa_pair['answer']}"
            else:  # low confidence
                response = f"This might be relevant: {qa_pair['answer']} \n\nFor more specific information, please contact the relevant California cybersecurity agencies."
            
            return {
                'response': response,
                'confidence': confidence,
                'source': qa_pair['source'],
                'category': qa_pair.get('category', 'general'),
                'similarity_score': match['similarity'],
                'type': 'answer'
            }
        
        # No good match found - return fallback response
        return {
            'response': np.random.choice(self.fallback_responses),
            'confidence': 'low',
            'source': 'System',
            'type': 'fallback'
        }
    
    def chat_session(self):
        """Start an interactive chat session"""
        print("=== California Cybersecurity Chatbot ===")
        print("Ask me anything about California's cybersecurity initiatives!")
        print("Type 'quit' or 'exit' to end the conversation.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("Chatbot: Thank you for using the California Cybersecurity Assistant. Stay safe online!")
                break
            
            if not user_input:
                print("Chatbot: Please ask a question about California cybersecurity.")
                continue
            
            # Generate response
            result = self.generate_response(user_input)
            
            # Display response with confidence indicator
            confidence_indicator = {
                'high': '✅',
                'medium': '⚠️',
                'low': '❓'
            }
            
            print(f"Chatbot {confidence_indicator[result['confidence']]}: {result['response']}")
            
            # Show source for non-system responses
            if result['source'] != 'System' and result['confidence'] in ['high', 'medium']:
                print(f"   📋 Source: {result['source']}")
            
            print()  # Add spacing
    
    def test_queries(self):
        """Test the chatbot with sample queries"""
        test_queries = [
            "Hello",
            "What is Cal-CSIC?",
            "How do I report a cyber attack?",
            "What cybersecurity services does California provide?",
            "How can I protect my business from cyber threats?",
            "What are California's data breach laws?",
            "Who should I contact for cybersecurity incidents?",
            "What is the California Department of Technology?",
            "How does California handle ransomware attacks?",
            "What cybersecurity training is available in California?"
        ]
        
        print("=== Testing Chatbot Responses ===\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test {i}: {query}")
            result = self.generate_response(query)
            print(f"Response ({result['confidence']}): {result['response'][:200]}...")
            print(f"Source: {result['source']}")
            print("-" * 50)

def main():
    # Initialize chatbot
    chatbot = CaliforniaCybersecurityChatbot()
    
    # Load data and train model
    if not chatbot.load_qa_data():
        print("Error: Could not load Q&A data. Please run the Q&A generator first.")
        return
    
    if not chatbot.train_model():
        print("Error: Could not train the model.")
        return
    
    print("✅ Chatbot initialized and ready!")
    
    # Ask user what they want to do
    while True:
        print("\nWhat would you like to do?")
        print("1. Start interactive chat")
        print("2. Run test queries")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            chatbot.chat_session()
        elif choice == '2':
            chatbot.test_queries()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()