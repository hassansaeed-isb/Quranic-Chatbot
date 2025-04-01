# local_model_loader.py
"""
Utility to load the existing Quran model and provide search functionality
specifically designed for a pandas DataFrame model with improved searching
"""
import pickle
import os
import sys
import logging
from pathlib import Path
import re
import difflib
import json
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("model_usage.log", encoding="utf-8")  # Use UTF-8 encoding
    ]
)
logger = logging.getLogger('LocalModelLoader')

class QuranModelWrapper:
    """
    A wrapper around the pandas DataFrame model to provide search functionality
    """
    def __init__(self, model_path="./models/processed_quran.pkl"):
        self.model_path = Path(model_path)
        self.engine = None
        self.loaded = False
        self.model_type = None
        
        # Default QA data in case we need it
        self.qa_data = {
            "questions": [],
            "facts": [
                "قرآن میں 114 سورتیں ہیں۔",
                "قرآن 30 پاروں پر مشتمل ہے۔",
                "سب سے طویل سورۃ سورۃ البقرہ ہے۔"
            ],
            "greetings": [
                "وعلیکم السلام! میں آپ کی قرآن سے متعلق سوالات کے جوابات دینے کے لیے حاضر ہوں۔"
            ],
            "thank_you_responses": [
                "آپ کا شکریہ! میں آپ کی مدد کرکے خوش ہوں۔"
            ],
            "farewell_responses": [
                "اللہ حافظ! دوبارہ بات کرنے کا شکریہ۔"
            ],
            "not_found_responses": [
                "معاف کیجیے، میں اس سوال کا جواب نہیں جانتا۔ برائے مہربانی قرآن سے متعلق کوئی اور سوال پوچھیں۔"
            ]
        }
        
        # Try to load QA data from file if it exists
        qa_file = Path("qa_data.json")
        if qa_file.exists():
            try:
                with open(qa_file, "r", encoding="utf-8") as f:
                    self.qa_data = json.load(f)
                logger.info(f"Loaded QA data from {qa_file}")
            except Exception as e:
                logger.error(f"Failed to load QA data: {e}")
    
    def load(self):
        """Load the pre-created model from disk"""
        if not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                self.engine = pickle.load(f)
            
            # Check if it's a pandas DataFrame
            if hasattr(self.engine, 'to_dict') and hasattr(self.engine, 'iloc'):
                self.model_type = "dataframe"
                # Check available columns
                self.columns = list(self.engine.columns)
                logger.info(f"Model loaded successfully from {self.model_path} (type: {self.model_type})")
                logger.info(f"DataFrame has columns: {self.columns}")
                logger.info(f"DataFrame shape: {self.engine.shape}")
                self.loaded = True
                return True
            else:
                logger.error("Model is not a pandas DataFrame")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def normalize_text(self, text):
        """Normalize text for better matching"""
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
            
        # Basic normalization
        text = re.sub(r'[۔،؟!؛:\(\)]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def search(self, query, top_k=5):
        """
        Search using the DataFrame model with multiple search strategies:
        1. Exact matches
        2. Contains matches
        3. Word-level matches
        4. Fuzzy matches
        """
        if not self.loaded:
            success = self.load()
            if not success:
                return {"error": "Failed to load model", "primary_match": None, "other_matches": [], "total_matches": 0}
        
        try:
            # Normalize query for better matching
            normalized_query = self.normalize_text(query)
            query_words = normalized_query.split()
            
            # List to store all potential matches with their scores
            all_matches = []
            
            # Get records for easier processing
            if hasattr(self.engine, 'to_dict'):
                records = self.engine.to_dict('records')
            else:
                records = self.engine  # Assume it's already in a list-like format
            
            # Multiple search strategies
            for record in records:
                # Extract verse text and reference
                verse_text = record.get('Translation', '')
                normalized_verse = self.normalize_text(verse_text)
                verse_words = normalized_verse.split()
                
                surah = record.get('Surah', '?')
                ayah = record.get('Ayah', '?')
                reference = record.get('Reference', f"Surah {surah}:{ayah}")
                
                # Calculate match score
                score = 0
                methods = []
                
                # Strategy 1: Exact match (highest priority)
                if query.lower() == verse_text.lower():
                    score = 1.0
                    methods.append("exact_match")
                
                # Strategy 2: Contains match
                elif query.lower() in verse_text.lower():
                    score = 0.9
                    methods.append("contains_match")
                
                # Strategy 3: Word-level match
                else:
                    # Count matching words
                    matching_words = sum(1 for word in query_words if word in verse_words)
                    if matching_words > 0:
                        word_match_score = matching_words / len(query_words)
                        score = max(score, word_match_score * 0.8)  # Up to 0.8 score for word matches
                        methods.append("word_match")
                    
                    # Strategy 4: Fuzzy matching as fallback
                    fuzzy_score = difflib.SequenceMatcher(None, normalized_query, normalized_verse).ratio()
                    if fuzzy_score > 0.5:  # Reasonable threshold
                        score = max(score, fuzzy_score * 0.7)  # Up to 0.7 score for fuzzy matches
                        methods.append("fuzzy_match")
                
                # Add to results if there's any match
                if score > 0:
                    all_matches.append({
                        "verse": verse_text,
                        "reference": reference,
                        "score": score,
                        "methods": methods
                    })
            
            # Sort by score and limit to top_k
            all_matches = sorted(all_matches, key=lambda x: x["score"], reverse=True)[:top_k]
            
            # If no matches, try a more lenient approach
            if not all_matches:
                logger.info(f"No matches found for '{query}', trying more lenient matching")
                
                for record in records:
                    verse_text = record.get('Translation', '')
                    normalized_verse = self.normalize_text(verse_text)
                    surah = record.get('Surah', '?')
                    ayah = record.get('Ayah', '?')
                    reference = record.get('Reference', f"Surah {surah}:{ayah}")
                    
                    # Try character-level matching
                    for word in query_words:
                        if len(word) > 2 and word in normalized_verse:
                            score = 0.5  # Lower score for partial matches
                            all_matches.append({
                                "verse": verse_text,
                                "reference": reference,
                                "score": score,
                                "methods": ["partial_match"]
                            })
                            break
                
                # Sort and limit again
                all_matches = sorted(all_matches, key=lambda x: x["score"], reverse=True)[:top_k]
            
            # Format results
            return {
                "primary_match": all_matches[0] if all_matches else None,
                "other_matches": all_matches[1:] if len(all_matches) > 1 else [],
                "total_matches": len(all_matches)
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": str(e), "primary_match": None, "other_matches": [], "total_matches": 0}
    
    def get_random_fact(self):
        """Get a random fact from QA data"""
        return random.choice(self.qa_data.get("facts", ["قرآن میں 114 سورتیں ہیں۔"]))
    
    def get_greeting(self):
        """Get a random greeting response"""
        return random.choice(self.qa_data.get("greetings", ["وعلیکم السلام!"]))
    
    def get_thank_you_response(self):
        """Get a random thank you response"""
        return random.choice(self.qa_data.get("thank_you_responses", ["آپ کا شکریہ!"]))
    
    def get_farewell_response(self):
        """Get a random farewell response"""
        return random.choice(self.qa_data.get("farewell_responses", ["اللہ حافظ!"]))
    
    def get_not_found_response(self):
        """Get a random not found response"""
        return random.choice(self.qa_data.get("not_found_responses", ["معاف کیجیے، میں اس سوال کا جواب نہیں جانتا۔"]))
    
    def formatted_search_results(self, query, top_k=5):
        """Get formatted search results"""
        results = self.search(query, top_k=top_k)
        
        if "error" in results:
            return f"Error: {results['error']}"
        
        output = [f"Search results for: '{query}'"]
        output.append("=" * 50)
        
        if results["primary_match"]:
            primary = results["primary_match"]
            output.append("Primary Match:")
            output.append(f"📖 {primary.get('reference', 'Unknown')}")
            output.append(f"📝 {primary.get('verse', 'No verse found')}")
            if 'methods' in primary:
                output.append(f"✓ Match score: {primary.get('score', 0):.2f} using {', '.join(primary['methods'])}")
            output.append("-" * 50)
        else:
            output.append("No primary match found.")
            output.append("-" * 50)
        
        if results["other_matches"]:
            output.append("Other Relevant Matches:")
            for i, match in enumerate(results["other_matches"], 1):
                output.append(f"{i}. 📖 {match.get('reference', 'Unknown')}")
                output.append(f"   📝 {match.get('verse', 'No verse found')}")
                if 'methods' in match:
                    output.append(f"   ✓ Match score: {match.get('score', 0):.2f} using {', '.join(match['methods'])}")
                output.append("   " + "-" * 40)
        else:
            output.append("No other relevant matches found.")
        
        if "total_matches" in results:
            output.append(f"\nTotal matches: {results['total_matches']}")
        
        return "\n".join(output)

# Simple test function
def test_model():
    """Test the model loading and searching"""
    model_path = Path("./models/processed_quran.pkl")
    
    if not model_path.exists():
        print(f"Model not found at {model_path}")
        print("Please ensure you've placed the model in the models directory")
        return False
    
    print(f"Testing model at {model_path}")
    wrapper = QuranModelWrapper(model_path)
    
    if not wrapper.load():
        print("Failed to load model. See logs for details.")
        return False
    
    # Test with a simple query
    test_query = "رحمن"
    print(f"\nTesting search with query: '{test_query}'")
    
    try:
        results = wrapper.formatted_search_results(test_query)
        print(results)
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    test_model()