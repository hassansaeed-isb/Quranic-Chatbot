# -*- coding: utf-8 -*-
"""
Urdu Quranic Chatbot Web Application
Flask backend for the Quranic Q&A system with improved accuracy
and integration with a pre-created search model
"""

from flask import Flask, render_template, request, jsonify
import json
import random
import time
import re
import os
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import string
import logging
from pathlib import Path

# Import the model wrapper
from local_model_loader import QuranModelWrapper

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('QuranChatbot')

# Path to the JSON data file
DATA_FILE = os.path.join(os.path.dirname(__file__), 'qa_data.json')

# Initialize the model wrapper
model_path = Path("./models/processed_quran.pkl")
model_wrapper = QuranModelWrapper(model_path)

# Global cache for QA data
qa_data_cache = None

# Category mappings for reuse
CATEGORY_TITLES = {
    "structure": "قرآن کا تعارف",
    "revelation": "قرآن کا نزول",
    "prophets": "انبیاء کرام",
    "special_verses": "خاص آیات",
    "mentions": "مختلف ذکر",
    "islamic_history": "اسلامی تاریخ"
}

CATEGORY_ICONS = {
    "structure": "fa-book-open",
    "revelation": "fa-moon",
    "prophets": "fa-user",
    "special_verses": "fa-star",
    "mentions": "fa-list",
    "islamic_history": "fa-history"
}

CATEGORY_KEYWORDS = {
    "structure": ["پارہ", "سورت", "آیت", "رکوع", "حروف", "الفاظ"],
    "revelation": ["نزول", "وحی", "نازل", "مکہ", "مدینہ"],
    "prophets": ["نبی", "پیغمبر", "رسول", "محمد", "عیسیٰ", "موسیٰ"],
    "special_verses": ["خاص", "فضیلت", "مشہور", "بڑی", "چھوٹی"],
    "mentions": ["ذکر", "کتنی بار", "نام", "کتنی دفعہ"],
    "islamic_history": ["پہلا", "سب سے پہلے", "اسلام کا آغاز", "شہید", "خاتون"]
}

# Dictionary of prophet-related patterns and their answers
PROPHET_QUESTIONS = {
    "most_mentioned_prophet": {
        "patterns": [
            "سب سے زیادہ ذکر کس نبی کا",
            "کس نبی کا سب سے زیادہ ذکر",
            "کس پیغمبر کا سب سے زیادہ ذکر",
            "سب سے زیادہ کس نبی کا ذکر",
            "کونسے نبی کا سب سے زیادہ ذکر"
        ],
        "answer": """قرآن میں سب سے زیادہ حضرت موسیٰ علیہ السلام کا ذکر آیا ہے۔ ان کا نام یا ان سے متعلق واقعات تقریباً 136 مرتبہ قرآن میں بیان ہوئے ہیں۔ دوسرے نمبر پر حضرت ابراہیم علیہ السلام (69 مرتبہ) اور پھر حضرت نوح علیہ السلام (43 مرتبہ) کا ذکر ہے۔ حضرت محمد ﷺ کا نام قرآن میں صرف 4 مرتبہ آیا ہے لیکن آپ کو مختلف القاب سے بہت زیادہ خطاب کیا گیا ہے۔"""
    },
    "prophet_jesus_mentions": {
        "patterns": [
            "کتنی بار حضرت عیسیٰ",
            "عیسیٰ علیہ السلام کا ذکر",
            "حضرت عیسیٰ کا کتنا ذکر",
            "عیسیٰ کا نام کتنی بار"
        ],
        "answer": """قرآن میں حضرت عیسیٰ علیہ السلام کا ذکر 25 مرتبہ آیا ہے۔ ان کا نام 'عیسیٰ' کے طور پر 25 بار آیا ہے، اور 'ابن مریم' (مریم کے بیٹے) کے طور پر بھی کئی بار ذکر کیا گیا ہے۔ حضرت عیسیٰ علیہ السلام کا ذکر 11 مختلف سورتوں میں آیا ہے، بشمول سورۃ البقرہ، آل عمران، النساء، المائدہ، الأنعام، مریم، الأحزاب، الشوریٰ، الزخرف، الحدید اور الصف۔"""
    },
    "prophet_ibrahim_mentions": {
        "patterns": [
            "کتنی بار حضرت ابراہیم",
            "ابراہیم علیہ السلام کا ذکر",
            "حضرت ابراہیم کا کتنا ذکر",
            "ابراہیم کا نام کتنی بار"
        ],
        "answer": """قرآن میں حضرت ابراہیم علیہ السلام کا ذکر 69 مرتبہ آیا ہے۔ ان کا تذکرہ 25 سورتوں میں ملتا ہے، جس میں سورۃ البقرہ، آل عمران، النساء، الانعام، ہود، ابراہیم، الحجر، مریم، الانبیاء، الحج، الشعراء، العنکبوت، الصافات، ص، الشوریٰ، الزخرف، الذاریات، النجم، الحدید، الممتحنہ، اور الاعلی شامل ہیں۔"""
    },
    "prophet_muhammad_mentions": {
        "patterns": [
            "کتنی بار حضرت محمد",
            "محمد صلی اللہ علیہ وسلم کا ذکر",
            "حضرت محمد کا کتنا ذکر",
            "محمد کا نام کتنی بار"
        ],
        "answer": """قرآن میں حضرت محمد ﷺ کا نام براہ راست صرف 4 مرتبہ آیا ہے۔ یہ ذکر سورۃ آل عمران (آیت 144)، سورۃ الأحزاب (آیت 40)، سورۃ محمد (آیت 2) اور سورۃ الفتح (آیت 29) میں ملتا ہے۔ تاہم، آپ کا ذکر مختلف القاب جیسے 'رسول'، 'نبی'، 'بشیر'، 'نذیر'، اور 'مزمل' وغیرہ کے ساتھ بہت زیادہ بار آیا ہے۔ اگر ان تمام اشاروں کو شمار کیا جائے تو یہ تعداد 70 سے زیادہ ہے۔"""
    },
    "prophet_noah_mentions": {
        "patterns": [
            "کتنی بار حضرت نوح",
            "نوح علیہ السلام کا ذکر",
            "حضرت نوح کا کتنا ذکر",
            "نوح کا نام کتنی بار"
        ],
        "answer": """قرآن میں حضرت نوح علیہ السلام کا ذکر تقریباً 43 مرتبہ آیا ہے۔ حضرت نوح علیہ السلام قرآن میں تیسرے سب سے زیادہ ذکر کیے جانے والے نبی ہیں، حضرت موسیٰ علیہ السلام (136 بار) اور حضرت ابراہیم علیہ السلام (69 بار) کے بعد۔ قرآن میں ایک پوری سورت 'سورۃ نوح' بھی نازل ہوئی ہے جو کہ قرآن کی 71ویں سورت ہے۔"""
    },
    "total_prophets_quran": {
        "patterns": [
            "قرآن میں کتنے انبیاء",
            "قرآن میں کتنے نبیوں",
            "کتنے پیغمبروں کے نام",
            "کتنے انبیاء کا تذکرہ"
        ],
        "answer": """قرآن میں کل 25 انبیاء کرام کا نام لے کر ذکر کیا گیا ہے۔ یہ انبیاء کرام ہیں: آدم، ادریس، نوح، ہود، صالح، ابراہیم، لوط، اسماعیل، اسحاق، یعقوب، یوسف، ایوب، شعیب، موسی، ہارون، ذوالکفل، داؤد، سلیمان، الیاس، الیسع، یونس، زکریا، یحییٰ، عیسیٰ اور محمد (علیہم السلام)۔ قرآن میں ان کے علاوہ بھی کچھ انبیاء کا ذکر ہے، لیکن ان کے نام نہیں بتائے گئے ہیں۔"""
    }
}

# Intent detection patterns
GREETING_PATTERNS = [
    "السلام علیکم", "سلام", "آداب", "ہیلو", "ہائے", "اسلام علیکم", "جی ", 
    "hello", "hi ", "hey", "assalam", "salam"
]

THANKS_WORDS = ["شکریہ", "مہربانی", "احسان", "ممنون", "تھینکس", "thanks", "thank you", "thanks a lot"]
FAREWELL_WORDS = ["اللہ حافظ", "خدا حافظ", "فی امان اللہ", "الوداع", "بائے", "bye", "goodbye", "see you"]
HELP_WORDS = ["مدد", "help", "کیسے", "how to", "guide", "explain"]
HISTORY_KEYWORDS = ["پہلا", "سب سے پہلے", "اسلام کا آغاز", "شہید", "خاتون"]

# Try to pre-load the model at startup
if model_path.exists():
    model_wrapper.load()
    logger.info(f"Pre-loaded model from {model_path}")
else:
    logger.warning(f"Model not found at {model_path}. Will try to create fallback database.")

def load_qa_data(force_reload=False):
    """Load the question-answer data from JSON file with optional caching"""
    global qa_data_cache
    
    # Return cached data if available and not forcing reload
    if qa_data_cache is not None and not force_reload:
        return qa_data_cache
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            qa_data_cache = json.load(file)
            logger.info(f"Loaded QA data from {DATA_FILE}")
            return qa_data_cache
    except Exception as e:
        logger.error(f"Error loading QA data: {e}")
        # Return minimal data structure in case of error
        return {"questions": [], "categories": {}, "facts": [], 
                "greetings": [], "thank_you_responses": [], 
                "farewell_responses": [], "not_found_responses": []}

def get_question_by_id(question_id, data):
    """Get question by ID with O(1) complexity using dictionary lookup"""
    # Create a lookup dictionary if it doesn't exist
    if not hasattr(get_question_by_id, "lookup_dict"):
        get_question_by_id.lookup_dict = {}
        
    # Rebuild lookup if data has changed
    if id(data) not in get_question_by_id.lookup_dict:
        lookup = {}
        for question in data.get("questions", []):
            if "id" in question:
                lookup[question["id"]] = question
        get_question_by_id.lookup_dict[id(data)] = lookup
    
    # Return the question or None
    return get_question_by_id.lookup_dict[id(data)].get(question_id)

def preprocess_text(text, is_urdu=True):
    """Clean and normalize text for better matching"""
    if not text:
        return ""
        
    # For Urdu text
    if is_urdu:
        # Remove Urdu punctuation
        text = re.sub(r'[۔،؟!؛:\(\)]', ' ', text)
    else:
        # For English parts
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Convert to lowercase
        text = text.lower()
        
    # Normalize whitespace for both
    return re.sub(r'\s+', ' ', text).strip()

def tokenize_urdu(text):
    """Tokenize Urdu text into words"""
    # Basic tokenization by whitespace
    tokens = text.split()
    # Further clean tokens
    return [token.strip() for token in tokens if token.strip()]

def advanced_similarity_score(query, reference, is_urdu=True):
    """Calculate advanced similarity between query and reference texts"""
    # Preprocess both texts
    query_processed = preprocess_text(query, is_urdu)
    reference_processed = preprocess_text(reference, is_urdu)
    
    # Method 1: String Sequence Matching
    sequence_similarity = SequenceMatcher(None, query_processed, reference_processed).ratio()
    
    # Method 2: Word Overlap
    if is_urdu:
        query_tokens = tokenize_urdu(query_processed)
        reference_tokens = tokenize_urdu(reference_processed)
    else:
        # For English, use more advanced NLP
        query_tokens = word_tokenize(query_processed)
        reference_tokens = word_tokenize(reference_processed)
        
        # Remove stopwords for English
        stop_words = set(stopwords.words('english'))
        query_tokens = [w for w in query_tokens if w not in stop_words]
        reference_tokens = [w for w in reference_tokens if w not in stop_words]
        
        # Stem words for English
        stemmer = PorterStemmer()
        query_tokens = [stemmer.stem(w) for w in query_tokens]
        reference_tokens = [stemmer.stem(w) for w in reference_tokens]
    
    # Count matching words
    matching_words = sum(1 for word in query_tokens if word in reference_tokens)
    
    # Calculate word overlap ratio
    total_words = len(set(query_tokens + reference_tokens))
    word_overlap = matching_words / total_words if total_words > 0 else 0
    
    # Combined similarity (weighted average)
    return (0.6 * sequence_similarity) + (0.4 * word_overlap)

def find_matching_question(user_input, qa_data):
    """Find the best matching question using advanced methods"""
    processed_input = preprocess_text(user_input)
    
    # Direct match check with higher threshold for short queries
    for question in qa_data.get("questions", []):
        question_text = question.get("question", "")
        if advanced_similarity_score(processed_input, question_text) > 0.8:
            return question
        
        # Check alternative phrasings
        for alt in question.get("alternative_phrasings", []):
            if advanced_similarity_score(processed_input, alt) > 0.8:
                return question
    
    # Keyword matching with improved weighting
    best_match = None
    highest_score = 0
    
    # Lower threshold for short queries
    threshold = 2 if len(processed_input.split()) <= 3 else 3
    
    for question in qa_data.get("questions", []):
        score = 0
        
        # Check for keywords
        for keyword in question.get("keywords", []):
            if keyword.lower() in processed_input.lower():
                # Weight longer keywords more (improved algorithm)
                score += (len(keyword) ** 1.5) * 0.1
        
        # Add category weighting
        if "category" in question and question["category"] in CATEGORY_KEYWORDS:
            for cat_keyword in CATEGORY_KEYWORDS[question["category"]]:
                if cat_keyword in processed_input.lower():
                    score += 2  # Boost category relevance
        
        if score > highest_score:
            highest_score = score
            best_match = question
    
    # Return keyword match if score is above threshold
    if highest_score >= threshold:
        return best_match
    
    # Fuzzy matching as a fallback
    best_match = None
    highest_similarity = 0
    
    for question in qa_data.get("questions", []):
        similarity = advanced_similarity_score(processed_input, question.get("question", ""))
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = question
    
    if highest_similarity > 0.5:
        return best_match
    
    return None

def get_related_questions(question, qa_data):
    """Get related questions with smart fallback"""
    related = []
    
    if not question or "related_questions" not in question:
        # Determine category from user input if possible
        matched_category = None
        
        if question and isinstance(question, dict) and "category" in question:
            matched_category = question["category"]
        elif isinstance(question, str):
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(kw in question for kw in keywords):
                    matched_category = cat
                    break
        
        # Get questions from the matched category or popular questions
        if matched_category:
            cat_questions = [q for q in qa_data.get("questions", []) if q.get("category") == matched_category]
            related = cat_questions[:3]
        else:
            # Popular questions as fallback
            popular_ids = ["quran_paras", "quran_surahs", "longest_surah", "shortest_surah"]
            for qid in popular_ids:
                q = get_question_by_id(qid, qa_data)
                if q:
                    related.append(q)
    else:
        # Get explicitly related questions
        for q_id in question.get("related_questions", []):
            q = get_question_by_id(q_id, qa_data)
            if q:
                related.append(q)
    
    return related[:3]  # Limit to 3 related questions

def detect_intent(text):
    """Detect the intent of the user's message"""
    if not text:
        return "question"  # Default
        
    text_lower = text.lower()
    
    # Historical intent detection
    if any(word in text_lower for word in HISTORY_KEYWORDS):
        return "history"
    
    # Greeting detection
    if any(greeting in text_lower for greeting in GREETING_PATTERNS):
        return "greeting"
    
    # Thanks
    if any(word in text_lower for word in THANKS_WORDS):
        return "thanks"
    
    # Farewell
    if any(farewell in text_lower for farewell in FAREWELL_WORDS):
        return "farewell"
    
    # Help
    if any(word in text_lower for word in HELP_WORDS):
        return "help"
    
    # Default to question
    return "question"

def detect_specific_questions(user_input):
    """Detect specific high-priority questions that need direct answers"""
    if not user_input:
        return None
        
    # Normalize user input for matching
    normalized_input = preprocess_text(user_input).lower()
    
    # Check each question pattern
    for q_type, data in PROPHET_QUESTIONS.items():
        for pattern in data["patterns"]:
            if pattern in normalized_input:
                return {
                    "type": q_type,
                    "answer": data["answer"]
                }
    
    return None

def search_quran(query):
    """Search Quran using the loaded model and include all relevant matches"""
    if not query or not model_wrapper.loaded:
        return None
        
    try:
        # Get search results
        results = model_wrapper.search(query)
        
        if "error" in results:
            logger.warning(f"Search error: {results['error']}")
            return None
            
        if results["primary_match"]:
            primary = results["primary_match"]
            # Format the answer with the verse and reference (improved spacing)
            answer = f"{primary['verse']}\n\n📖 {primary['reference']}"
            
            # Include all matches in the answer if available
            other_matches = results.get("other_matches", [])
            if other_matches:
                answer += "\n\n**مزید متعلقہ نتائج:**\n"
                for i, match in enumerate(other_matches, 1):
                    other_match_text = f"{i}. {match['verse']}\n📖 {match['reference']}"
                    answer += other_match_text + "\n\n"
            
            # Create related suggestions from other matches
            suggestions = []
            related_queries = []
            
            for match in other_matches:
                # Extract a potential follow-up question from the verse
                verse_parts = match['verse'].split('،')
                if len(verse_parts) > 1:
                    q = verse_parts[0] + "؟"
                    if len(q) > 10 and len(q) < 60:  # Reasonable question length
                        related_queries.append(q)
                        
            # If we have related queries, add them to suggestions
            if related_queries:
                suggestions.extend(related_queries[:2])
            
            # Add some general follow-up questions
            suggestions.append(f"مزید معلومات {query} کے بارے میں")
            
            return {
                "answer": answer,
                "suggestions": suggestions
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error in search_quran: {e}")
        return None

def process_question(user_input, qa_data):
    """Process user input and return appropriate response"""
    if not user_input:
        return {
            'answer': "کوئی سوال نہیں ملا۔ براہ کرم دوبارہ کوشش کریں۔",
            'confidence': 'none',
            'intent': 'unknown'
        }
    
    # First check for specific high-priority questions
    specific_question = detect_specific_questions(user_input)
    if specific_question:
        related = []
        if specific_question["type"].startswith("prophet_") or specific_question["type"] == "most_mentioned_prophet":
            # Get related questions for prophets
            for q in qa_data.get("questions", []):
                if q.get("category") == "prophets" and q.get("id", "") != specific_question["type"]:
                    related.append(q)
                    if len(related) >= 3:
                        break
        
        return {
            'answer': specific_question["answer"],
            'confidence': 'high',
            'suggestions': [q["question"] for q in related] if related else ["قرآن میں کتنی بار حضرت ابراہیم کا ذکر آیا ہے"],
            'intent': 'question',
            'source': 'specific_answers'
        }
    
    # Detect intent
    intent = detect_intent(user_input)
    
    if intent == "greeting":
        return {
            'answer': random.choice(qa_data.get("greetings", ["وعلیکم السلام!"])),
            'suggestions': [q["question"] for q in get_related_questions(None, qa_data)],
            'confidence': 'high',
            'intent': 'greeting'
        }
    
    if intent == "thanks":
        return {
            'answer': random.choice(qa_data.get("thank_you_responses", ["آپ کا شکریہ!"])),
            'suggestions': ["مزید سوالات", "اللہ حافظ"],
            'confidence': 'high',
            'intent': 'thanks'
        }
    
    if intent == "farewell":
        return {
            'answer': random.choice(qa_data.get("farewell_responses", ["اللہ حافظ!"])),
            'farewell': True,
            'confidence': 'high',
            'intent': 'farewell'
        }
    
    if intent == "help":
        help_text = """آپ قرآن کے بارے میں کوئی بھی سوال پوچھ سکتے ہیں، جیسے:
- قرآن کتنے پاروں پر مشتمل ہے؟
- سب سے طویل سورۃ کون سی ہے؟
- قرآن میں کتنی سورتیں ہیں؟
- قرآن میں کس پیغمبر کا سب سے زیادہ ذکر ہے؟"""
        return {
            'answer': help_text,
            'suggestions': [q["question"] for q in get_related_questions(None, qa_data)[:4]],
            'confidence': 'high',
            'intent': 'help'
        }
    
    # Process as a question
    match = find_matching_question(user_input, qa_data)
    
    if match:
        # Direct match from QA database
        related = get_related_questions(match, qa_data)
        return {
            'answer': match["answer"],
            'confidence': 'high',
            'suggestions': [q["question"] for q in related],
            'intent': 'question',
            'source': 'qa_database'
        }
    else:
        # Try using the search model if no match found
        search_result = None
        if model_wrapper.loaded:
            search_result = search_quran(user_input)
        
        if search_result:
            # Match from search model
            return {
                'answer': search_result["answer"],
                'confidence': 'medium',
                'suggestions': search_result["suggestions"],
                'intent': 'question',
                'source': 'search_model'
            }
        else:
            # No match found
            not_found = random.choice(qa_data.get("not_found_responses", 
                              ["معاف کیجیے، میں اس سوال کا جواب نہیں جانتا۔"]))
            return {
                'answer': not_found,
                'confidence': 'none',
                'suggestions': [q["question"] for q in get_related_questions(None, qa_data)],
                'intent': 'unknown'
            }

# Routes
@app.route('/')
def home():
    """Render the home page"""
    # Ensure model is loaded
    if not model_wrapper.loaded and model_path.exists():
        model_wrapper.load()
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Process the user's question and return an answer"""
    user_input = request.json.get('question', '')
    qa_data = load_qa_data()
    
    # Add slight delay to simulate thinking
    time.sleep(0.2)
    
    # Process the question using our improved engine
    result = process_question(user_input, qa_data)
    
    return jsonify(result)

@app.route('/check-model', methods=['GET'])
def check_model():
    """API endpoint to check if the model is loaded"""
    try:
        is_loaded = model_wrapper.loaded
        model_exists = model_path.exists()
        
        if is_loaded:
            status = "Model is loaded and ready"
            model_type = model_wrapper.model_type if hasattr(model_wrapper, 'model_type') else "unknown"
        elif model_exists:
            status = "Model file exists but is not loaded yet"
            model_type = "unknown"
        else:
            status = "Model file not found"
            model_type = "none"
            
        return jsonify({
            'success': is_loaded,
            'model_exists': model_exists,
            'model_type': model_type,
            'status': status,
            'model_path': str(model_path)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/popular-questions')
def popular_questions():
    """Return a list of popular questions for suggestions"""
    qa_data = load_qa_data()
    popular_ids = ["quran_paras", "quran_surahs", "longest_surah", "shortest_surah"]
    popular = []
    
    for q_id in popular_ids:
        q = get_question_by_id(q_id, qa_data)
        if q:
            popular.append(q["question"])
    
    return jsonify({'questions': popular})

@app.route('/daily-fact')
def daily_fact():
    """Return two random Quranic facts"""
    qa_data = load_qa_data()
    facts = random.sample(qa_data.get("facts", ["قرآن میں 114 سورتیں ہیں۔"]), 
                        min(2, len(qa_data.get("facts", ["قرآن میں 114 سورتیں ہیں۔"]))))
    return jsonify({'facts': facts})

@app.route('/categories')
def get_categories():
    """Return categories and their questions"""
    qa_data = load_qa_data()
    result = {}
    
    # Group questions by category
    category_questions = {}
    for question in qa_data.get("questions", []):
        if "category" in question:
            category = question["category"]
            if category not in category_questions:
                category_questions[category] = []
            category_questions[category].append(question["question"])
    
    # Create result object
    for category, questions in category_questions.items():
        result[category] = {
            "title": CATEGORY_TITLES.get(category, category),
            "icon": CATEGORY_ICONS.get(category, "fa-question"),
            "questions": questions[:4]  # Limit to 4 questions per category
        }
    
    return jsonify(result)

@app.route('/search', methods=['POST'])
def search():
    """Search for questions matching a query"""
    query = request.json.get('query', '')
    qa_data = load_qa_data()
    
    if len(query) < 2:
        return jsonify({'results': []})
    
    results = []
    for q in qa_data.get("questions", []):
        # Check main question
        if query.lower() in q["question"].lower():
            results.append({
                'question': q["question"],
                'preview': q["answer"][:50] + "..." if len(q["answer"]) > 50 else q["answer"]
            })
            continue
        
        # Check alternative phrasings
        for alt in q.get("alternative_phrasings", []):
            if query.lower() in alt.lower():
                results.append({
                    'question': q["question"],
                    'preview': q["answer"][:50] + "..." if len(q["answer"]) > 50 else q["answer"]
                })
                break
    
    return jsonify({'results': results[:5]})  # Limit to 5 results

@app.route('/load-model', methods=['POST'])
def load_model():
    """API endpoint to explicitly load the model"""
    try:
        if model_wrapper.loaded:
            return jsonify({
                'success': True,
                'message': 'Model is already loaded',
                'model_type': model_wrapper.model_type if hasattr(model_wrapper, 'model_type') else "unknown"
            })
        
        if not model_path.exists():
            return jsonify({
                'success': False,
                'message': f'Model file not found at {model_path}'
            }), 404
            
        success = model_wrapper.load()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Model loaded successfully',
                'model_type': model_wrapper.model_type if hasattr(model_wrapper, 'model_type') else "unknown"
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to load model'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reload-qa-data', methods=['POST'])
def reload_qa_data():
    """API endpoint to reload the QA data"""
    try:
        # Store the current data for comparison
        old_data = None
        qa_file = Path(DATA_FILE)
        if qa_file.exists():
            try:
                with open(qa_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load existing QA data: {e}")
        
        # Force reload from file
        global qa_data_cache
        qa_data_cache = None  # Clear cache
        new_data = load_qa_data(force_reload=True)
        
        # Check if data was successfully loaded
        if not new_data:
            return jsonify({
                'success': False,
                'message': 'Failed to load new QA data'
            }), 500
        
        # Compare data sizes to give feedback
        old_count = len(old_data.get("questions", [])) if old_data else 0
        new_count = len(new_data.get("questions", [])) if new_data else 0
        
        # Reset the lookup dictionary in get_question_by_id
        if hasattr(get_question_by_id, "lookup_dict"):
            get_question_by_id.lookup_dict = {}
        
        return jsonify({
            'success': True,
            'message': f'QA data reloaded successfully. {old_count} -> {new_count} questions',
            'old_count': old_count,
            'new_count': new_count
        })
    except Exception as e:
        logger.error(f"Error reloading QA data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Try to pre-load the model when starting the server
    if model_path.exists() and not model_wrapper.loaded:
        try:
            model_wrapper.load()
            logger.info(f"Pre-loaded model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to pre-load model: {e}")
    
    app.run(debug=True)