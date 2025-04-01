import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import json
import pickle
from pathlib import Path
import difflib
from collections import defaultdict
import logging
import warnings
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('QuranSearchEngine')

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning)

class EnhancedQuranSearchEngine:
    """
    Enhanced Quran Search Engine with multi-technique search capabilities
    and comprehensive reference handling.
    """
    
    def __init__(self, cache_dir="/kaggle/working/quran_cache"):
        """Initialize the search engine with various search techniques"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.data = None
        self.surah_names = {}
        self.vectorizer = None
        self.tfidf_matrix = None
        self.sentence_transformer = None
        self.sentence_embeddings = None
        self.qa_model = None
        self.qa_tokenizer = None
        self.index_map = {}  # For mapping between different verse numbering systems
        
        logger.info("Initializing Enhanced Quran Search Engine")
        
    def normalize_arabic_text(self, text):
        """Normalize Arabic/Urdu text by removing diacritics and standardizing characters"""
        # Handle None or non-string inputs
        if not isinstance(text, str):
            return ""
            
        # Remove diacritics (harakat)
        text = ''.join(c for c in unicodedata.normalize('NFKD', text) 
                      if not unicodedata.combining(c))
        
        # Standardize certain characters
        text = text.replace('ی', 'ي')  # Standardize ya
        text = text.replace('ۃ', 'ة')  # Standardize ta marbutah
        text = text.replace('ك', 'ک')  # Standardize kaf
        
        return text
    
    def load_data_from_multiple_sources(self):
        """Load Quran data from multiple possible sources, with fallbacks"""
        # 1. Try to load from cache first
        cache_path = self.cache_dir / "processed_quran.pkl"
        if cache_path.exists():
            try:
                logger.info(f"Loading data from cache: {cache_path}")
                with open(cache_path, 'rb') as f:
                    self.data = pickle.load(f)
                return True
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # 2. Try multiple possible file locations
        possible_paths = [
            # Standard Kaggle paths
            '/kaggle/input/urdu-quran-dataset/Urdu.csv',
            '/kaggle/input/urdu-quran/Urdu.csv',
            '/kaggle/input/urdu-csv/Urdu.csv',
            '/kaggle/input/quran-urdu-translation/quran-urdu.csv',
            '/kaggle/input/urdu-quran-translation/Urdu.csv',
            '/kaggle/working/Urdu.csv',
            # Common local paths
            'data/quran-urdu.csv',
            'quran-data/Urdu.csv',
            # Plain text file possibilities
            '/kaggle/input/urdu-quran-dataset/quran.txt',
            '/kaggle/input/urdu-quran/quran.txt'
        ]
        
        for path in possible_paths:
            try:
                # Try to determine the file type and read appropriately
                if path.endswith('.csv'):
                    logger.info(f"Attempting to read CSV file: {path}")
                    # First try with standard CSV format
                    try:
                        df = pd.read_csv(path)
                        if all(col in df.columns for col in ['Surah', 'Ayah', 'Translation']):
                            self.data = df
                            logger.info(f"Successfully loaded standard CSV: {path}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to read as standard CSV: {e}")
                    
                    # Try with delimiters
                    for delimiter in [',', '|', '\t']:
                        try:
                            df = pd.read_csv(path, delimiter=delimiter, header=None)
                            if df.shape[1] >= 3:
                                # Assume first 3 columns are Surah, Ayah, Translation
                                df.columns = ['Surah', 'Ayah', 'Translation'] + [f'Extra{i}' for i in range(df.shape[1]-3)]
                                self.data = df
                                logger.info(f"Successfully loaded delimited file: {path} with delimiter: {delimiter}")
                                break
                        except Exception as e:
                            logger.debug(f"Failed to read with delimiter {delimiter}: {e}")
                    
                    # Try as plain text with no header
                    if self.data is None:
                        try:
                            df = pd.read_csv(path, header=None, names=['Text'], encoding='utf-8')
                            verses = []
                            for i, row in df.iterrows():
                                if not isinstance(row['Text'], str):
                                    continue
                                parts = row['Text'].split('|')
                                if len(parts) >= 3:
                                    try:
                                        surah, ayah = int(parts[0]), int(parts[1])
                                        translation = parts[2]
                                        verses.append({"Surah": surah, "Ayah": ayah, "Translation": translation})
                                    except (ValueError, TypeError):
                                        continue
                            
                            if verses:
                                self.data = pd.DataFrame(verses)
                                logger.info(f"Successfully parsed plain text CSV: {path}")
                                break
                        except Exception as e:
                            logger.debug(f"Failed to read as plain text: {e}")
                
                # Try as plain text file
                elif path.endswith('.txt'):
                    logger.info(f"Attempting to read text file: {path}")
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        verses = []
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if not line:
                                continue
                                
                            # Check if line has a format like "1:1 - Translation"
                            match = re.match(r'(\d+):(\d+)\s*[-–]\s*(.*)', line)
                            if match:
                                surah, ayah, translation = match.groups()
                                verses.append({
                                    "Surah": int(surah),
                                    "Ayah": int(ayah),
                                    "Translation": translation.strip()
                                })
                            else:
                                # Assign artificial numbers
                                verses.append({
                                    "Surah": (i // 10) + 1, 
                                    "Ayah": (i % 10) + 1,
                                    "Translation": line
                                })
                        
                        if verses:
                            self.data = pd.DataFrame(verses)
                            logger.info(f"Successfully parsed text file: {path}")
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read text file {path}: {e}")
            
            except Exception as e:
                logger.warning(f"Error processing {path}: {e}")
                continue
        
        # 3. Try to extract from error messages if needed
        if self.data is None:
            logger.info("Attempting to extract data from error messages")
            try:
                error_files = [
                    '/kaggle/working/error_log.txt',
                    'error_log.txt'
                ]
                
                for error_file in error_files:
                    if os.path.exists(error_file):
                        with open(error_file, 'r', encoding='utf-8') as f:
                            error_text = f.read()
                        
                        pattern = r"Error processing row: (.*?), Error:"
                        matches = re.findall(pattern, error_text)
                        
                        if matches:
                            verses = []
                            for i, verse in enumerate(matches):
                                verses.append({
                                    "Surah": (i // 10) + 1,
                                    "Ayah": (i % 10) + 1,
                                    "Translation": verse.strip()
                                })
                            
                            self.data = pd.DataFrame(verses)
                            logger.info(f"Created dataset from error log: {error_file}")
                            break
            except Exception as e:
                logger.warning(f"Failed to extract from error log: {e}")
        
        # 4. Create dataset from direct text input
        if self.data is None and 'paste.txt' in possible_paths:
            logger.info("Attempting to create dataset from paste.txt content")
            try:
                with open('paste.txt', 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Extract error messages containing verses
                pattern = r"Error processing row: (.*?), Error: invalid literal for int\(\)"
                matches = re.findall(pattern, text)
                
                if matches:
                    verses = []
                    for i, verse in enumerate(matches):
                        verses.append({
                            "Surah": (i // 10) + 1,
                            "Ayah": (i % 10) + 1,
                            "Translation": verse.strip()
                        })
                    
                    self.data = pd.DataFrame(verses)
                    logger.info(f"Created dataset from paste.txt content with {len(verses)} verses")
            except Exception as e:
                logger.warning(f"Failed to extract from paste.txt: {e}")
        
        # 5. Use hard-coded fallback data if all else fails
        if self.data is None:
            logger.warning("All data loading methods failed. Using fallback dataset.")
            self.data = pd.DataFrame([
                {"Surah": 1, "Ayah": 1, "Translation": "بسم اللہ الرحمن الرحیم"},
                {"Surah": 1, "Ayah": 2, "Translation": "الحمد للہ رب العالمین"},
                {"Surah": 1, "Ayah": 3, "Translation": "الرحمن الرحیم"},
                {"Surah": 1, "Ayah": 4, "Translation": "مالک یوم الدین"},
                {"Surah": 1, "Ayah": 5, "Translation": "ایاک نعبد و ایاک نستعین"},
                {"Surah": 1, "Ayah": 6, "Translation": "اھدنا الصراط المستقیم"},
                {"Surah": 1, "Ayah": 7, "Translation": "صراط الذین انعمت علیھم غیر المغضوب علیھم و لا الضالین"},
                {"Surah": 2, "Ayah": 1, "Translation": "الم"},
                {"Surah": 2, "Ayah": 2, "Translation": "ذٰلِکَ الْکِتٰبُ لَا رَیْبَ ۚ فِیْہِ ۚ ہُدًی لِّلْمُتَّقِیْنَ"},
                {"Surah": 112, "Ayah": 1, "Translation": "قل هو الله احد"},
                {"Surah": 112, "Ayah": 2, "Translation": "الله الصمد"},
                {"Surah": 112, "Ayah": 3, "Translation": "لم يلد ولم يولد"},
                {"Surah": 112, "Ayah": 4, "Translation": "ولم يكن له كفوا احد"}
            ])
        
        # Load surah names
        self.load_surah_names()
        
        # Cache the processed data
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(self.data, f)
            logger.info(f"Cached processed data to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")
        
        # Add normalized text column for improved matching
        if 'Translation' in self.data.columns:
            self.data['NormalizedText'] = self.data['Translation'].apply(self.normalize_arabic_text)
            
            # Add combined reference string for convenience
            self.data['Reference'] = self.data.apply(
                lambda x: f"Surah {x['Surah']}:{x['Ayah']}" + 
                        (f" ({self.surah_names.get(x['Surah'], '')})" if x['Surah'] in self.surah_names else ""), 
                axis=1
            )
        else:
            logger.error("Data loaded but 'Translation' column not found. Check data format.")
            return False
        
        return True
    
    def load_surah_names(self):
        """Load Surah names from various possible sources"""
        # First try to load from cache
        cache_path = self.cache_dir / "surah_names.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self.surah_names = json.load(f)
                return
            except:
                pass
        
        # Hardcoded names as fallback
        self.surah_names = {
            1: "الفاتحة (Al-Fatiha)",
            2: "البقرة (Al-Baqara)",
            3: "آل عمران (Aal-Imran)",
            4: "النساء (An-Nisa)",
            5: "المائدة (Al-Ma'ida)",
            6: "الأنعام (Al-An'am)",
            112: "الإخلاص (Al-Ikhlas)",
            113: "الفلق (Al-Falaq)",
            114: "الناس (An-Nas)"
        }
        
        # Try to find a surah names file
        possible_paths = [
            '/kaggle/input/quran-metadata/surah_names.json',
            '/kaggle/input/quran-urdu-translation/surah_names.json',
            'data/surah_names.json'
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.surah_names = json.load(f)
                logger.info(f"Loaded surah names from {path}")
                break
            except:
                continue
        
        # Cache the names
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.surah_names, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def initialize_search_methods(self):
        """Initialize multiple search methods for robust text retrieval"""
        if self.data is None or len(self.data) == 0:
            logger.error("No data available. Please load data first.")
            return False
        
        # 1. Initialize TF-IDF vectorizer
        logger.info("Initializing TF-IDF vectorizer...")
        try:
            self.vectorizer = TfidfVectorizer(
                min_df=1, 
                max_df=0.9,
                ngram_range=(1, 3),
                sublinear_tf=True
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.data['NormalizedText'])
            logger.info(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        except Exception as e:
            logger.warning(f"Failed to initialize TF-IDF: {e}")
        
        # 2. Try to initialize sentence transformer (if available)
        try:
            from sentence_transformers import SentenceTransformer
            
            # Try loading cached embeddings first
            embeddings_path = self.cache_dir / "sentence_embeddings.npy"
            if embeddings_path.exists():
                try:
                    self.sentence_embeddings = np.load(embeddings_path)
                    logger.info(f"Loaded sentence embeddings from cache: {embeddings_path}")
                    self.sentence_transformer = True  # Just a flag that we have embeddings
                except Exception as e:
                    logger.warning(f"Failed to load cached embeddings: {e}")
            
            # If not loaded from cache, try to generate them
            if self.sentence_embeddings is None:
                try:
                    # Try multilingual model first
                    model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
                    self.sentence_transformer = SentenceTransformer(model_name)
                    
                    # Compute embeddings (may take time for large datasets)
                    logger.info(f"Computing sentence embeddings using {model_name}...")
                    self.sentence_embeddings = self.sentence_transformer.encode(
                        self.data['Translation'].tolist(), 
                        show_progress_bar=True,
                        batch_size=32
                    )
                    
                    # Cache the embeddings
                    try:
                        np.save(embeddings_path, self.sentence_embeddings)
                        logger.info(f"Cached sentence embeddings to {embeddings_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cache embeddings: {e}")
                        
                except Exception as e:
                    logger.warning(f"Failed to initialize sentence transformer: {e}")
                    self.sentence_transformer = None
        except ImportError:
            logger.info("SentenceTransformer not available. Skipping semantic search capabilities.")
            self.sentence_transformer = None
        
        # 3. Initialize QA model if transformers is available
        try:
            from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
            
            # Only initialize if data is large enough to be useful
            if len(self.data) > 10:
                logger.info("Initializing QA model...")
                try:
                    model_name = "bert-base-multilingual-cased"
                    self.qa_tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.qa_model = AutoModelForQuestionAnswering.from_pretrained(model_name)
                    logger.info("QA model initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize QA model: {e}")
        except ImportError:
            logger.info("Transformers not available. Skipping QA capabilities.")
        
        logger.info("Search methods initialization complete")
        return True
    
    def search(self, query, top_k=5, include_partial=True, include_similar=True, threshold=0.1):
        """
        Search for verses matching the query using multiple techniques
        
        Args:
            query: The search query text
            top_k: Number of results to return
            include_partial: Whether to include partial matches
            include_similar: Whether to include semantically similar results
            threshold: Similarity threshold for including results
            
        Returns:
            Dictionary with primary match and other matches
        """
        if self.data is None or len(self.data) == 0:
            return {"error": "No data available. Please load data first."}
        
        # Handle empty query
        if not query or not isinstance(query, str):
            return {"error": "Empty or invalid query", "primary_match": None, "other_matches": [], "total_matches": 0}
        
        # Normalize the query
        normalized_query = self.normalize_arabic_text(query)
        
        # Dictionary to store all matches with their scores and methods
        all_matches = defaultdict(lambda: {"score": 0, "methods": []})
        
        # 1. Look for exact matches first (highest priority)
        exact_indices = []
        for idx, row in self.data.iterrows():
            if query in row['Translation'] or normalized_query in row['NormalizedText']:
                match_key = f"{row['Surah']}:{row['Ayah']}"
                all_matches[match_key]["verse"] = row['Translation']
                all_matches[match_key]["reference"] = row['Reference']
                all_matches[match_key]["score"] += 10  # High score for exact match
                all_matches[match_key]["methods"].append("exact")
                exact_indices.append(idx)
        
        # 2. Use TF-IDF for partial keyword matching
        if self.vectorizer is not None and (include_partial or len(all_matches) < top_k):
            try:
                query_vec = self.vectorizer.transform([normalized_query])
                similarity_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                
                # Get indices of top matches
                top_indices = similarity_scores.argsort()[-top_k*2:][::-1]
                
                for idx in top_indices:
                    if similarity_scores[idx] > threshold:
                        row = self.data.iloc[idx]
                        match_key = f"{row['Surah']}:{row['Ayah']}"
                        
                        # Only add if not already an exact match or update score if better
                        if match_key not in all_matches or all_matches[match_key]["score"] < similarity_scores[idx] * 5:
                            all_matches[match_key]["verse"] = row['Translation']
                            all_matches[match_key]["reference"] = row['Reference']
                            all_matches[match_key]["score"] = max(all_matches[match_key]["score"], similarity_scores[idx] * 5)
                            all_matches[match_key]["methods"].append("tfidf")
            except Exception as e:
                logger.warning(f"TF-IDF search failed: {e}")
        
        # 3. Use semantic search with sentence embeddings
        if self.sentence_transformer is not None and self.sentence_embeddings is not None and include_similar:
            try:
                # If it's just a flag, we only have cached embeddings
                if isinstance(self.sentence_transformer, bool):
                    # Use a simpler approach with dot product
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                    query_embedding = model.encode([query])[0]
                    
                    # Calculate similarities
                    similarities = np.dot(self.sentence_embeddings, query_embedding)
                    top_indices = similarities.argsort()[-top_k*2:][::-1]
                    
                    for idx in top_indices:
                        if similarities[idx] > threshold:
                            row = self.data.iloc[idx]
                            match_key = f"{row['Surah']}:{row['Ayah']}"
                            
                            all_matches[match_key]["verse"] = row['Translation']
                            all_matches[match_key]["reference"] = row['Reference']
                            all_matches[match_key]["score"] = max(all_matches[match_key]["score"], similarities[idx] * 3)
                            all_matches[match_key]["methods"].append("semantic")
                else:
                    # Use the model directly
                    query_embedding = self.sentence_transformer.encode([query])[0]
                    
                    # Calculate similarities
                    similarities = np.dot(self.sentence_embeddings, query_embedding)
                    top_indices = similarities.argsort()[-top_k*2:][::-1]
                    
                    for idx in top_indices:
                        if similarities[idx] > threshold:
                            row = self.data.iloc[idx]
                            match_key = f"{row['Surah']}:{row['Ayah']}"
                            
                            all_matches[match_key]["verse"] = row['Translation']
                            all_matches[match_key]["reference"] = row['Reference']
                            all_matches[match_key]["score"] = max(all_matches[match_key]["score"], similarities[idx] * 3)
                            all_matches[match_key]["methods"].append("semantic")
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")
        
        # 4. Use fuzzy matching for query with typos
        if include_partial and len(all_matches) < top_k:
            for idx, row in self.data.iterrows():
                # Skip already matched verses
                match_key = f"{row['Surah']}:{row['Ayah']}"
                if match_key in all_matches:
                    continue
                
                # Calculate fuzzy match ratio
                ratio = difflib.SequenceMatcher(None, normalized_query, row['NormalizedText']).ratio()
                
                if ratio > max(0.6, threshold * 2):  # Higher threshold for fuzzy matching
                    all_matches[match_key]["verse"] = row['Translation']
                    all_matches[match_key]["reference"] = row['Reference']
                    all_matches[match_key]["score"] = max(all_matches[match_key]["score"], ratio * 2)
                    all_matches[match_key]["methods"].append("fuzzy")
        
        # Sort matches by score
        sorted_matches = sorted(all_matches.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # Prepare results
        results = {
            "primary_match": None,
            "other_matches": [],
            "total_matches": len(sorted_matches)
        }
        
        # Set primary match (the one with highest score)
        if sorted_matches:
            primary = sorted_matches[0][1]
            results["primary_match"] = {
                "verse": primary["verse"],
                "reference": primary["reference"],
                "score": primary["score"],
                "methods": primary["methods"]
            }
            
            # Add other matches
            other_matches = []
            for _, match in sorted_matches[1:top_k]:
                other_matches.append({
                    "verse": match["verse"],
                    "reference": match["reference"],
                    "score": match["score"],
                    "methods": match["methods"]
                })
            
            results["other_matches"] = other_matches
        
        return results
    
    def answer_question(self, question, context=None, max_length=512):
        """
        Answer a question using the QA model.
        
        Args:
            question: The question to answer
            context: Optional context to use, otherwise will search for relevant verses
            
        Returns:
            Dictionary with answer and reference
        """
        if self.qa_model is None or self.qa_tokenizer is None:
            return {"error": "QA model not available"}
        
        try:
            from transformers import pipeline
            qa_pipeline = pipeline("question-answering", model=self.qa_model, tokenizer=self.qa_tokenizer)
            
            # Get context if not provided
            if context is None:
                search_results = self.search(question, top_k=3)
                
                if search_results["primary_match"]:
                    context = search_results["primary_match"]["verse"]
                    
                    # Add some additional context if available
                    for match in search_results["other_matches"][:2]:
                        context += " " + match["verse"]
                else:
                    return {"error": "No relevant context found for the question"}
            
            # Use the QA pipeline to get an answer
            result = qa_pipeline(question=question, context=context, max_length=max_length)
            
            return {
                "answer": result["answer"],
                "score": result["score"],
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return {"error": f"Failed to answer question: {str(e)}"}

    def formatted_search_results(self, query, top_k=5):
        """
        Return search results in a nicely formatted string.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            Formatted string with search results
        """
        results = self.search(query, top_k=top_k)
        
        if "error" in results:
            return f"Error: {results['error']}"
        
        output = [f"Search results for: '{query}'"]
        output.append("=" * 50)
        
        if results["primary_match"]:
            primary = results["primary_match"]
            output.append("Primary Match:")
            output.append(f"📖 {primary['reference']}")
            output.append(f"📝 {primary['verse']}")
            output.append(f"✓ Match score: {primary['score']:.2f} using {', '.join(primary['methods'])}")
            output.append("-" * 50)
        else:
            output.append("No primary match found.")
            output.append("-" * 50)
        
        if results["other_matches"]:
            output.append("Other Relevant Matches:")
            for i, match in enumerate(results["other_matches"], 1):
                output.append(f"{i}. 📖 {match['reference']}")
                output.append(f"   📝 {match['verse']}")
                output.append(f"   ✓ Match score: {match['score']:.2f} using {', '.join(match['methods'])}")
                output.append("   " + "-" * 40)
        else:
            output.append("No other matches found.")
        
        output.append(f"\nTotal matches: {results['total_matches']}")
        
        return "\n".join(output)

def initialize_search_engine():
    """Helper function to initialize the search engine"""
    engine = EnhancedQuranSearchEngine()
    success = engine.load_data_from_multiple_sources()
    
    if success:
        engine.initialize_search_methods()
        logger.info(f"Engine initialized with {len(engine.data)} verses")
        return engine
    else:
        logger.error("Failed to initialize search engine")
        return None

def main():
    """Main function to demonstrate search capabilities"""
    logger.info("Starting Quran Search Engine")
    
    # Initialize engine
    engine = initialize_search_engine()
    
    if not engine:
        logger.error("Engine initialization failed. Exiting.")
        return
    
    # Example search
    test_queries = [
        "رحمن",
        "نماز",
        "جنت",
        "توبه",
        "صبر"
    ]
    
    for query in test_queries:
        logger.info(f"\nTesting search for: '{query}'")
        results = engine.formatted_search_results(query)
        print(results)
    
    # Interactive mode
    print("\n" + "=" * 60)
    print("Interactive Quran Search Engine")
    print("=" * 60)
    print("Enter your search query (or 'exit' to quit):")
    
    while True:
        query = input("\nSearch: ")
        if query.lower() in ['exit', 'quit', 'q']:
            break
        
        if not query.strip():
            continue
            
        results = engine.formatted_search_results(query)
        print(results)

if __name__ == "__main__":
    main()