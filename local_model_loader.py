# local_model_loader.py
"""
Utility to load the existing Quran model and provide search functionality
specifically designed for a pandas DataFrame model with improved searching
"""
import pickle
import os
import logging
from pathlib import Path
import re
import difflib
import json
import random
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LocalModelLoader')

# Full Surah names mapping
SURAH_NAMES = {
    1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة", 6: "الأنعام", 7: "الأعراف", 8: "الأنفال",
    9: "التوبة", 10: "یونس", 11: "ھود", 12: "یوسف", 13: "الرعد", 14: "ابراھیم", 15: "الحجر", 16: "النحل",
    17: "الإسراء", 18: "الکهف", 19: "مریم", 20: "طه", 21: "الأنبیاء", 22: "الحج", 23: "المؤمنون", 24: "النور",
    25: "الفرقان", 26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم", 31: "لقمان", 32: "السجدة",
    33: "الأحزاب", 34: "سبأ", 35: "فاطر", 36: "یٰس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
    41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية", 46: "الأحقاف", 47: "محمد", 48: "الفتح",
    49: "الحجرات", 50: "ق", 51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن", 56: "الواقعہ",
    57: "الحدید", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة", 61: "الصف", 62: "الجمعة", 63: "المنافقون",
    64: "التغابن", 65: "الطلاق", 66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
    71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة", 76: "الإنسان", 77: "المرسلات",
    78: "النبأ", 79: "النازعات", 80: "عبس", 81: "التكوير", 82: "الانفطار", 83: "المطففين", 84: "الانشقاق",
    85: "البروج", 86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد", 91: "الشمس",
    92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين", 96: "العلق", 97: "القدر", 98: "البينة",
    99: "الزلزلة", 100: "العاديات", 101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة",
    105: "الفيل", 106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
    111: "اللهب", 112: "الإخلاص", 113: "الفلق", 114: "الناس"
}

class QuranModelWrapper:
    def __init__(self, model_path="./models/processed_quran.pkl"):
        self.model_path = Path(model_path)
        self.engine = None
        self.loaded = False

    def load(self):
        if not self.model_path.exists():
            logger.error(f"Model not found: {self.model_path}")
            return False
        try:
            with open(self.model_path, 'rb') as f:
                self.engine = pickle.load(f)
            self.loaded = True
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def normalize_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        return re.sub(r'[۔،؟!؛:\(\)]', ' ', text).strip()

    def get_reference(self, surah, ayah):
        """Generate formatted reference with Surah name and Ayah number only."""
        try:
            surah = int(surah)
            # Get Surah name from the SURAH_NAMES mapping
            surah_name = SURAH_NAMES.get(surah, f"Surah {surah}")
            
            # Return the reference, using only the name and Ayah number
            return f"{surah_name} ، آیت {ayah}"
        except Exception as e:
            # Fallback in case of error
            logger.error(f"Error generating reference: {e}")
            return f"{surah_name} ، آیت {ayah}"

        
    def search(self, query):
        if not self.loaded:
            if not self.load():
                return {"error": "Model not loaded"}

        query = self.normalize_text(query)
        query_words = query.split()

        results = []

        for record in self.engine.to_dict('records'):
            verse_text = record.get('Translation', '')
            normalized_verse = self.normalize_text(verse_text)
            surah = record.get('Surah', '?')
            ayah = record.get('Ayah', '?')

            score = 0
            methods = []

            if query.lower() == verse_text.lower():
                score = 1.0
                methods.append("exact_match")
            elif query.lower() in verse_text.lower():
                score = 0.9
                methods.append("contains_match")
            else:
                matching_words = sum(1 for word in query_words if word in normalized_verse)
                if matching_words > 0:
                    score = max(score, matching_words / len(query_words) * 0.8)
                    methods.append("word_match")
                fuzzy_score = difflib.SequenceMatcher(None, query, normalized_verse).ratio()
                if fuzzy_score > 0.5:
                    score = max(score, fuzzy_score * 0.7)
                    methods.append("fuzzy_match")

            if score > 0:
                results.append({
                    "verse": verse_text,
                    "reference": self.get_reference(surah, ayah),
                    "score": score,
                    "methods": methods
                })

        # Sort all results (no top_k limitation now)
        results = sorted(results, key=lambda x: x['score'], reverse=True)

        return {
            "primary_match": results[0] if results else None,
            "other_matches": results[1:] if len(results) > 1 else [],
            "total_matches": len(results)
        }
            
    
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