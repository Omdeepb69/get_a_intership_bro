"""
Automated AI/ML Internship Application Script
This script:
1. Searches for AI/ML internships from multiple sources
2. Filters and ranks them based on relevance and requirements
3. Sends personalized application emails with your CV attached
4. Keeps track of sent applications to avoid duplicates
"""

import requests
import smtplib
import time
import os
import json
import random
import logging
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("internship_bot.log"),
        logging.StreamHandler()
    ]
)

# User Configuration
EMAIL = "omdeeborkar@gmail.com"
CV_PATH = "path/to/your/cv.pdf"  # Update this with your CV path
EMAIL_PASSWORD = ""  # Will prompt for this securely at runtime
APPLICATION_HISTORY_FILE = "application_history.json"

# Internship search parameters
SEARCH_KEYWORDS = [
    "AI internship", 
    "ML internship", 
    "machine learning internship", 
    "artificial intelligence internship",
    "data science internship",
    "deep learning internship"
]

# Company scoring/filtering criteria
DESIRED_SKILLS = [
    "python", "tensorflow", "pytorch", "keras", "scikit-learn", 
    "machine learning", "deep learning", "nlp", "computer vision", 
    "data analysis", "ai", "ml", "artificial intelligence"
]

# Internship job boards and their search endpoints
JOB_BOARDS = {
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords={}",
    "Indeed": "https://www.indeed.com/jobs?q={}",
    "Glassdoor": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={}",
    "Internships.com": "https://www.internships.com/search/{}",
    "Handshake": "https://app.joinhandshake.com/stu/postings?text={}"
}

# Email templates
EMAIL_SUBJECT_TEMPLATE = "Application for {position} at {company}"

EMAIL_BODY_TEMPLATE = """
Dear {company} Hiring Team,

I hope this email finds you well. I'm writing to express my strong interest in the {position} position at {company} that I found on {source}.

As an AI/ML enthusiast with experience in {skills}, I believe I would be a great addition to your team. I'm particularly excited about {company_focus} that your company is working on.

My GitHub profile (included in my CV) demonstrates my practical experience and projects in the AI/ML field. I am eager to apply my skills and learn in a real-world environment.

I have attached my CV for your consideration. I would welcome the opportunity to discuss how my background, technical skills, and enthusiasm could contribute to your team.

Thank you for considering my application. I look forward to the possibility of discussing this opportunity with you further.

Best regards,
Om Borkar
Email: omdeeborkar@gmail.com
"""

class InternshipBot:
    def __init__(self):
        self.driver = None
        self.results = []
        self.application_history = self.load_application_history()
        
    def load_application_history(self):
        """Load the history of already applied internships to avoid duplicates"""
        if os.path.exists(APPLICATION_HISTORY_FILE):
            with open(APPLICATION_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def save_application_history(self):
        """Save the updated application history"""
        with open(APPLICATION_HISTORY_FILE, 'w') as f:
            json.dump(self.application_history, f, indent=4)
    
    def setup_webdriver(self):
        """Set up the Selenium webdriver for web scraping"""
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("Webdriver setup complete")
    
    def close_webdriver(self):
        """Close the Selenium webdriver"""
        if self.driver:
            self.driver.quit()
            logging.info("Webdriver closed")
    
    def search_internships(self):
        """Search for internships across multiple job boards"""
        if not self.driver:
            self.setup_webdriver()
        
        for keyword in SEARCH_KEYWORDS:
            logging.info(f"Searching for: {keyword}")
            
            for board_name, url_template in JOB_BOARDS.items():
                try:
                    url = url_template.format(keyword.replace(" ", "+"))
                    logging.info(f"Searching {board_name} at {url}")
                    
                    self.driver.get(url)
                    time.sleep(random.uniform(2, 5))  # Random delay to avoid detection
                    
                    # Handle each job board differently as they have different HTML structures
                    if board_name == "LinkedIn":
                        self.scrape_linkedin()
                    elif board_name == "Indeed":
                        self.scrape_indeed()
                    elif board_name == "Glassdoor":
                        self.scrape_glassdoor()
                    elif board_name == "Internships.com":
                        self.scrape_internships_com()
                    elif board_name == "Handshake":
                        self.scrape_handshake()
                    
                    time.sleep(random.uniform(1, 3))  # Random delay between searches
                
                except Exception as e:
                    logging.error(f"Error searching {board_name}: {str(e)}")
        
        logging.info(f"Found {len(self.results)} total internship listings")
        return self.results
    
    def scrape_linkedin(self):
        """Scrape internship listings from LinkedIn"""
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")
            
            for card in job_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "base-search-card__title")
                    company_element = card.find_element(By.CLASS_NAME, "base-search-card__subtitle")
                    link_element = card.find_element(By.CLASS_NAME, "base-card__full-link")
                    
                    job = {
                        "title": title_element.text,
                        "company": company_element.text,
                        "url": link_element.get_attribute("href"),
                        "source": "LinkedIn",
                        "description": "",
                        "score": 0
                    }
                    
                    # Click on the job to get the description
                    link_element.click()
                    time.sleep(2)
                    
                    try:
                        description_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "description__text"))
                        )
                        job["description"] = description_element.text
                    except:
                        logging.warning("Could not get job description from LinkedIn")
                    
                    self.results.append(job)
                except Exception as e:
                    logging.error(f"Error processing LinkedIn job card: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error in LinkedIn scraping: {str(e)}")
    
    def scrape_indeed(self):
        """Scrape internship listings from Indeed"""
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
            
            for card in job_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "jobTitle")
                    company_element = card.find_element(By.CLASS_NAME, "companyName")
                    
                    job = {
                        "title": title_element.text,
                        "company": company_element.text,
                        "url": title_element.find_element(By.TAG_NAME, "a").get_attribute("href"),
                        "source": "Indeed",
                        "description": "",
                        "score": 0
                    }
                    
                    # Try to get the description from the card itself
                    try:
                        description_element = card.find_element(By.CLASS_NAME, "job-snippet")
                        job["description"] = description_element.text
                    except:
                        logging.warning("Could not get job snippet from Indeed card")
                    
                    self.results.append(job)
                except Exception as e:
                    logging.error(f"Error processing Indeed job card: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error in Indeed scraping: {str(e)}")
    
    def scrape_glassdoor(self):
        """Scrape internship listings from Glassdoor"""
        try:
            # Handle Glassdoor's initial popup if it appears
            try:
                continue_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "react-job-listing"))
                )
            except:
                logging.warning("No Glassdoor popup or timeout waiting for listings")
            
            job_cards = self.driver.find_elements(By.CLASS_NAME, "react-job-listing")
            
            for card in job_cards:
                try:
                    # Click on the card to load the job details
                    card.click()
                    time.sleep(2)
                    
                    # Now get the job details from the right panel
                    title_element = self.driver.find_element(By.CLASS_NAME, "jobTitle")
                    company_element = self.driver.find_element(By.CLASS_NAME, "employerName")
                    description_element = self.driver.find_element(By.CLASS_NAME, "jobDescriptionContent")
                    
                    job = {
                        "title": title_element.text,
                        "company": company_element.text,
                        "url": self.driver.current_url,
                        "source": "Glassdoor",
                        "description": description_element.text,
                        "score": 0
                    }
                    
                    self.results.append(job)
                except Exception as e:
                    logging.error(f"Error processing Glassdoor job card: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error in Glassdoor scraping: {str(e)}")
    
    def scrape_internships_com(self):
        """Scrape internship listings from Internships.com"""
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "internship-listing")
            
            for card in job_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "internship-title")
                    company_element = card.find_element(By.CLASS_NAME, "company-name")
                    
                    job = {
                        "title": title_element.text,
                        "company": company_element.text,
                        "url": title_element.find_element(By.TAG_NAME, "a").get_attribute("href"),
                        "source": "Internships.com",
                        "description": "",
                        "score": 0
                    }
                    
                    # Open the job page to get the description
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.get(job["url"])
                    time.sleep(2)
                    
                    try:
                        description_element = self.driver.find_element(By.CLASS_NAME, "internship-description")
                        job["description"] = description_element.text
                    except:
                        logging.warning("Could not get job description from Internships.com")
                    
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                    self.results.append(job)
                except Exception as e:
                    logging.error(f"Error processing Internships.com job card: {str(e)}")
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
        
        except Exception as e:
            logging.error(f"Error in Internships.com scraping: {str(e)}")
    
    def scrape_handshake(self):
        """Scrape internship listings from Handshake"""
        try:
            # Handshake requires login so we'll just log this
            logging.info("Handshake requires login - skipping automated scraping")
            # In a real implementation, you might use a saved session or API key
        except Exception as e:
            logging.error(f"Error in Handshake scraping: {str(e)}")
    
    def score_internships(self):
        """Score and rank internships based on relevance to AI/ML and other criteria"""
        for job in self.results:
            score = 0
            description = job["description"].lower()
            title = job["title"].lower()
            
            # Check if "intern" or "internship" is in the title
            if "intern" in title or "internship" in title:
                score += 10
            
            # Check if AI/ML keywords are in the title
            ai_ml_in_title = any(keyword in title for keyword in ["ai", "ml", "machine learning", "artificial intelligence", "deep learning"])
            if ai_ml_in_title:
                score += 15
            
            # Count the number of desired skills mentioned
            for skill in DESIRED_SKILLS:
                if skill in description:
                    score += 3
            
            # Consider the credibility of the source
            source_credibility = {
                "LinkedIn": 5,
                "Indeed": 4,
                "Glassdoor": 4,
                "Internships.com": 3,
                "Handshake": 5
            }
            score += source_credibility.get(job["source"], 0)
            
            # Check if the posting is recent (if we can extract a date)
            # This would require additional parsing for each source
            
            # Update the job score
            job["score"] = score
        
        # Sort by score (descending)
        self.results.sort(key=lambda x: x["score"], reverse=True)
        logging.info("Internships scored and ranked")
    
    def filter_top_internships(self, top_n=20):
        """Filter to only keep the top N internships based on score"""
        top_internships = self.results[:top_n]
        logging.info(f"Filtered to top {len(top_internships)} internships")
        return top_internships
    
    def get_company_focus(self, job):
        """Extract the main focus or technology of the company from the job description"""
        description = job["description"].lower()
        
        focus_areas = {
            "nlp": ["natural language processing", "nlp", "language model", "text analysis", "sentiment analysis"],
            "computer vision": ["computer vision", "image processing", "object detection", "facial recognition"],
            "robotics": ["robotics", "autonomous", "robot", "automation"],
            "healthcare AI": ["healthcare", "medical", "diagnosis", "patient"],
            "fintech": ["fintech", "financial", "banking", "trading", "investment"],
            "recommendation systems": ["recommendation", "personalization", "user experience"]
        }
        
        for area, keywords in focus_areas.items():
            if any(keyword in description for keyword in keywords):
                return area
        
        # Default if no specific focus is identified
        return "artificial intelligence and machine learning technologies"
    
    def get_required_skills(self, job):
        """Extract required skills from the job description"""
        description = job["description"].lower()
        matched_skills = [skill for skill in DESIRED_SKILLS if skill in description]
        
        if matched_skills:
            return ", ".join(matched_skills[:5])  # Return up to 5 skills
        return "Python, machine learning, and data analysis"  # Default
    
    def send_application_email(self, job, email_password):
        """Send application email with CV attached"""
        if any(j["url"] == job["url"] for j in self.application_history):
            logging.info(f"Already applied to {job['company']} - {job['title']}")
            return False
        
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg["From"] = EMAIL
            
            # Try to find HR email, otherwise use a generic format
            hr_email = self.find_hr_email(job["company"])
            msg["To"] = hr_email if hr_email else f"careers@{job['company'].lower().replace(' ', '')}.com"
            
            # Create email subject
            msg["Subject"] = EMAIL_SUBJECT_TEMPLATE.format(
                position=job["title"],
                company=job["company"]
            )
            
            # Create email body with personalization
            company_focus = self.get_company_focus(job)
            required_skills = self.get_required_skills(job)
            
            email_body = EMAIL_BODY_TEMPLATE.format(
                company=job["company"],
                position=job["title"],
                source=job["source"],
                skills=required_skills,
                company_focus=company_focus
            )
            
            msg.attach(MIMEText(email_body, "plain"))
            
            # Attach CV
            with open(CV_PATH, "rb") as file:
                attachment = MIMEApplication(file.read(), _subtype="pdf")
                attachment.add_header('Content-Disposition', 'attachment', filename="Om_Borkar_CV.pdf")
                msg.attach(attachment)
            
            # Send the email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(EMAIL, email_password)
                server.send_message(msg)
            
            # Log the application
            logging.info(f"Application sent to {job['company']} for {job['title']}")
            
            # Add to history
            application_record = {
                "company": job["company"],
                "title": job["title"],
                "url": job["url"],
                "date_applied": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.application_history.append(application_record)
            self.save_application_history()
            
            time.sleep(random.uniform(60, 180))  # Wait between 1-3 minutes between emails
            return True
            
        except Exception as e:
            logging.error(f"Failed to send application to {job['company']}: {str(e)}")
            return False
    
    def find_hr_email(self, company_name):
        """Try to find HR email for the company (simplified version)"""
        # In a real implementation, you would:
        # 1. Search the company website
        # 2. Use services like Hunter.io or Clearbit
        # 3. Check LinkedIn for contacts
        
        # This is just a placeholder
        return None
    
    def generate_stats_report(self, sent_count):
        """Generate a report of the application campaign"""
        report = f"""
        ===== Internship Application Bot Report =====
        Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        Total internships found: {len(self.results)}
        Top internships filtered: {len(self.results[:20])}
        Applications sent: {sent_count}
        
        Top companies applied to:
        {chr(10).join(f"- {job['company']} ({job['title']})" for job in self.application_history[-sent_count:])}
        
        Total applications sent to date: {len(self.application_history)}
        """
        
        logging.info(report)
        print(report)
        
        # Save the report to a file
        with open(f"application_report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
            f.write(report)

def main():
    bot = InternshipBot()
    
    try:
        # Get email password securely
        import getpass
        email_password = getpass.getpass("Enter your email password: ")
        
        # Check if CV exists
        if not os.path.exists(CV_PATH):
            raise FileNotFoundError(f"CV file not found at {CV_PATH}. Please update the CV_PATH variable.")
        
        # Search for internships
        bot.search_internships()
        
        # Score and filter internships
        bot.score_internships()
        top_internships = bot.filter_top_internships()
        
        if not top_internships:
            logging.warning("No suitable internships found")
            return
        
        # Send applications
        sent_count = 0
        for job in top_internships:
            success = bot.send_application_email(job, email_password)
            if success:
                sent_count += 1
        
        # Generate report
        bot.generate_stats_report(sent_count)
        
    except Exception as e:
        logging.error(f"An error occurred in the main process: {str(e)}")
    finally:
        bot.close_webdriver()
        logging.info("Internship application process completed")

if __name__ == "__main__":
    main()