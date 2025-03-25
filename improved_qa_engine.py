# -*- coding: utf-8 -*-
"""
Quranic QA Data Enrichment Utility
This script helps enrich the qa_data.json file with additional information
to improve response accuracy
"""

import json
import os
import re

# Path to the JSON data file
DATA_FILE = os.path.join(os.path.dirname(__file__), 'qa_data.json')

def load_data():
    """Load the existing QA data from JSON file"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading QA data: {e}")
        return None

def save_data(data):
    """Save the enriched data back to the JSON file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print("Data successfully saved to", DATA_FILE)
        return True
    except Exception as e:
        print(f"Error saving QA data: {e}")
        return False

def add_greetings(data):
    """Add more greeting responses to the data"""
    greetings = [
        "وعلیکم السلام! آپ کیسے ہیں؟",
        "السلام علیکم! میں آپ کی کیا مدد کر سکتا ہوں؟",
        "ہیلو! قرآن کے بارے میں کیا جاننا چاہتے ہیں؟",
        "جی ہاں، میں حاضر ہوں۔ کیا پوچھنا چاہتے ہیں؟",
        "آداب! آج میں آپ کی کیا خدمت کر سکتا ہوں؟"
    ]
    
    data["greetings"] = greetings
    return data

def add_thank_you_responses(data):
    """Add more thank you responses to the data"""
    thank_you_responses = [
        "آپ کا شکریہ!",
        "خوش آمدید!",
        "میری خدمت کا موقع دینے کا شکریہ۔",
        "آپ کا مسئلہ حل ہوگیا تو مجھے خوشی ہوئی۔",
        "قرآن کے بارے میں مزید معلومات کے لیے دوبارہ پوچھیں۔"
    ]
    
    data["thank_you_responses"] = thank_you_responses
    return data

def add_farewell_responses(data):
    """Add more farewell responses to the data"""
    farewell_responses = [
        "اللہ حافظ!",
        "خدا حافظ! دوبارہ تشریف لائیں۔",
        "الوداع! اللہ آپ کو اپنی امان میں رکھے۔",
        "فی امان اللہ!",
        "پھر ملیں گے، انشاء اللہ!"
    ]
    
    data["farewell_responses"] = farewell_responses
    return data

def add_not_found_responses(data):
    """Add more not found responses to the data"""
    not_found_responses = [
        "معاف کیجیے، میں اس سوال کا جواب نہیں جانتا۔",
        "اس سوال کا جواب میرے پاس نہیں ہے۔ کوئی اور سوال پوچھیں۔",
        "مجھے افسوس ہے، میں آپ کے سوال کا جواب دینے سے قاصر ہوں۔",
        "میں اس سوال کا مکمل جواب نہیں دے سکتا۔ قرآن کے بارے میں کوئی اور سوال پوچھیں۔",
        "یہ سوال میرے علم سے باہر ہے۔ براہ کرم دوسرا سوال پوچھیں۔"
    ]
    
    data["not_found_responses"] = not_found_responses
    return data

def add_quranic_facts(data):
    """Add interesting Quranic facts to the data"""
    facts = [
        "قرآن میں 114 سورتیں ہیں۔",
        "قرآن کو مکمل نازل ہونے میں 23 سال لگے۔",
        "قرآن میں سب سے چھوٹی سورت الکوثر ہے۔",
        "قرآن میں سب سے طویل آیت آیت الدین (سورۃ البقرہ، آیت 282) ہے۔",
        "قرآن میں سب سے زیادہ ذکر حضرت موسیٰ علیہ السلام کا آیا ہے۔",
        "قرآن میں 30 پارے ہیں۔",
        "قرآن کی سب سے زیادہ فضیلت والی آیت آیت الکرسی ہے۔",
        "قرآن میں تقریباً 6,236 آیات ہیں۔",
        "قرآن میں 86 مکی اور 28 مدنی سورتیں ہیں۔",
        "قرآن میں تقریباً 77,430 الفاظ ہیں۔"
    ]
    
    data["facts"] = facts
    return data

def enrich_questions(data):
    """Enrich existing questions with more keywords and alternatives"""
    for question in data["questions"]:
        # Ensure each question has these fields
        if "keywords" not in question:
            question["keywords"] = []
        if "alternative_phrasings" not in question:
            question["alternative_phrasings"] = []
        
        # Extract words from the question to use as keywords
        words = re.findall(r'\b\w+\b', question["question"])
        for word in words:
            if len(word) > 3 and word not in question["keywords"]:
                question["keywords"].append(word)
    
    return data

def add_related_questions(data):
    """Ensure all questions have related questions"""
    categories = {}
    
    # Group questions by category
    for question in data["questions"]:
        if "category" in question:
            cat = question["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(question["id"])
    
    # Add related questions by category if missing
    for question in data["questions"]:
        if "related_questions" not in question or not question["related_questions"]:
            question["related_questions"] = []
            
            if "category" in question and question["category"] in categories:
                # Get other questions from same category
                same_cat_questions = [q for q in categories[question["category"]] 
                                     if q != question["id"]]
                
                # Add up to 3 related questions
                for q_id in same_cat_questions[:3]:
                    if q_id not in question["related_questions"]:
                        question["related_questions"].append(q_id)
    
    return data

def add_categorical_keywords(data):
    """Add category-specific keywords to help with matching"""
    category_keywords = {
        "structure": ["ڈھانچا", "ترتیب", "تشکیل", "بناوٹ"],
        "revelation": ["وحی", "نازل", "نزول", "اتارا"],
        "prophets": ["انبیاء", "رسل", "پیغمبر", "نبی"],
        "special_verses": ["خاص", "مخصوص", "اہم", "خصوصی"],
        "mentions": ["ذکر", "نام", "اسم", "تذکرہ"],
        "islamic_history": ["تاریخ", "واقعہ", "حادثہ", "داستان"]
    }
    
    for question in data["questions"]:
        if "category" in question and question["category"] in category_keywords:
            for keyword in category_keywords[question["category"]]:
                if keyword not in question["keywords"]:
                    question["keywords"].append(keyword)
    
    return data

def main():
    """Main function to enrich the QA data"""
    data = load_data()
    if not data:
        print("Could not load data. Exiting.")
        return
    
    # Enrichment steps
    data = add_greetings(data)
    data = add_thank_you_responses(data)
    data = add_farewell_responses(data)
    data = add_not_found_responses(data)
    data = add_quranic_facts(data)
    data = enrich_questions(data)
    data = add_related_questions(data)
    data = add_categorical_keywords(data)
    
    # Save enriched data
    if save_data(data):
        print("Data enrichment completed successfully!")
    else:
        print("Failed to save enriched data.")

if __name__ == "__main__":
    main()