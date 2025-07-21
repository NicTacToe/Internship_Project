#!/usr/bin/env python3
"""
Complete automation script for California Cybersecurity Chatbot
Runs scraper, Q&A generator, and chatbot in sequence
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def install_requirements():
    """Install required packages"""
    required_packages = [
        'requests',
        'beautifulsoup4',
        'scikit-learn',
        'numpy',
        'lxml'
    ]
    
    print("📦 Installing required packages...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    return True

def run_scraper():
    """Run the web scraper"""
    print("\n🕷️  Starting web scraper...")
    print("This will scrape California government cybersecurity websites...")
    
    try:
        # Import and run scraper
        from scraper import CaliforniaCyberScraper
        
        scraper = CaliforniaCyberScraper()
        scraper.scrape_all_sites()
        scraper.save_to_csv()
        
        if len(scraper.scraped_data) > 0:
            print(f"✅ Scraping completed! Found {len(scraper.scraped_data)} pages")
            return True
        else:
            print("⚠️  No data scraped. Check internet connection or website availability.")
            return False
            
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        return False

def run_qa_generator():
    """Run the Q&A generator"""
    print("\n🧠 Generating Q&A dataset...")
    
    if not os.path.exists('california_cybersecurity_data.csv'):
        print("❌ No scraped data found. Run scraper first.")
        return False
    
    try:
        from qa_generator import QAGenerator
        
        generator = QAGenerator()
        generator.generate_all_qa_pairs()
        generator.add_general_california_questions()
        generator.save_qa_dataset()
        
        if len(generator.qa_pairs) > 0:
            print(f"✅ Generated {len(generator.qa_pairs)} Q&A pairs")
            return True
        else:
            print("⚠️  No Q&A pairs generated from scraped data.")
            return False
            
    except Exception as e:
        print(f"❌ Error during Q&A generation: {str(e)}")
        return False

def run_chatbot():
    """Initialize and test the chatbot"""
    print("\n🤖 Initializing chatbot...")
    
    if not os.path.exists('california_cybersecurity_qa.csv'):
        print("❌ No Q&A dataset found. Run Q&A generator first.")
        return False
    
    try:
        from chatbot import CaliforniaCybersecurityChatbot
        
        chatbot = CaliforniaCybersecurityChatbot()
        
        if not chatbot.load_qa_data():
            print("❌ Failed to load Q&A data")
            return False
        
        if not chatbot.train_model():
            print("❌ Failed to train chatbot model")
            return False
        
        print("✅ Chatbot initialized successfully!")
        return chatbot
        
    except Exception as e:
        print(f"❌ Error initializing chatbot: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("🏛️  CALIFORNIA CYBERSECURITY CHATBOT SETUP")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Install requirements
    if not install_requirements():
        print("\n❌ Failed to install requirements. Please install manually.")
        return
    
    # Step 2: Run scraper
    if not run_scraper():
        print("\n❌ Scraping failed. Cannot proceed.")
        return
    
    # Step 3: Generate Q&A dataset
    if not run_qa_generator():
        print("\n❌ Q&A generation failed. Cannot proceed.")
        return
    
    # Step 4: Initialize chatbot
    chatbot = run_chatbot()
    if not chatbot:
        print("\n❌ Chatbot initialization failed.")
        return
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    
    # Show files created
    files_created = []
    if os.path.exists('california_cybersecurity_data.csv'):
        size = os.path.getsize('california_cybersecurity_data.csv')
        files_created.append(f"📄 california_cybersecurity_data.csv ({size:,} bytes)")
    
    if os.path.exists('california_cybersecurity_qa.csv'):
        size = os.path.getsize('california_cybersecurity_qa.csv')
        files_created.append(f"📄 california_cybersecurity_qa.csv ({size:,} bytes)")
    
    print("Files created:")
    for file_info in files_created:
        print(f"  {file_info}")
    
    # Test the chatbot
    print(f"\n🧪 Running quick test...")
    test_query = "What is Cal-CSIC?"
    result = chatbot.generate_response(test_query)
    print(f"Test Query: {test_query}")
    print(f"Response: {result['response'][:100]}...")
    print(f"Confidence: {result['confidence']}")
    
    # Ask user what to do next
    print("\n" + "=" * 60)
    print("WHAT'S NEXT?")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Start interactive chat with the bot")
        print("2. Run comprehensive test queries")
        print("3. Show sample Q&A pairs")
        print("4. Exit")
        
        choice = input("\nWhat would you like to do? (1-4): ").strip()
        
        if choice == '1':
            chatbot.chat_session()
        elif choice == '2':
            chatbot.test_queries()
        elif choice == '3':
            from qa_generator import QAGenerator
            generator = QAGenerator()
            generator.load_qa_data = lambda: generator.__dict__.update({'qa_pairs': chatbot.qa_data}) or chatbot.qa_data
            generator.qa_pairs = chatbot.qa_data
            generator.print_sample_qa(10)
        elif choice == '4':
            print("👋 Thanks for using the California Cybersecurity Chatbot!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()