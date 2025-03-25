# -*- coding: utf-8 -*-
"""
Test Script for Quranic QA Engine
This script helps test the accuracy of the QA engine with various test cases
"""

import sys
import json
import os

# Add current directory to path to import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from app.py
try:
    from app import load_qa_data, process_question
except ImportError:
    print("Could not import functions from app.py. Make sure the file exists in the current directory.")
    sys.exit(1)

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_colored(text, color):
    """Print text with color"""
    print(f"{color}{text}{Colors.ENDC}")

def run_accuracy_test():
    """Run accuracy tests on the QA engine"""
    qa_data = load_qa_data()
    
    # If no data was loaded, exit
    if not qa_data or not qa_data.get("questions"):
        print_colored("ERROR: Could not load QA data or no questions found.", Colors.RED)
        return {"total": 0, "passed": 0, "failed": 0, "details": []}
    
    # Various test cases to evaluate accuracy
    test_cases = [
        # Direct matches
        {"query": "قرآن میں کتنی سورتیں ہیں؟", "expected_id": "quran_surahs"},
        {"query": "سب سے طویل سورۃ کون سی ہے", "expected_id": "longest_surah"},
        
        # Paraphrased questions
        {"query": "قرآن کی سورتوں کی کل تعداد کتنی ہے", "expected_id": "quran_surahs"},
        {"query": "قرآن مجید میں کل کتنی سورتیں موجود ہیں", "expected_id": "quran_surahs"},
        
        # Questions with typos
        {"query": "قرآن مین کتنی سورتین ہیں", "expected_id": "quran_surahs"},
        {"query": "سب سے لمبی سورت کونسی ہے", "expected_id": "longest_surah"},
        
        # Keyword-based matches
        {"query": "قرآن کے پارے", "expected_id": "quran_paras"},
        {"query": "سب سے چھوٹی سورت", "expected_id": "shortest_surah"},
        
        # Intent detection
        {"query": "السلام علیکم", "expected_intent": "greeting"},
        {"query": "شکریہ", "expected_intent": "thanks"},
        {"query": "اللہ حافظ", "expected_intent": "farewell"},
        
        # Different phrasing
        {"query": "قرآن میں محمد ﷺ کا نام کتنی بار آیا", "expected_id": "muhammad_mentions"},
        {"query": "پاروں کی تعداد", "expected_id": "quran_paras"}
    ]
    
    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    print_colored("\n===== URDU QURANIC CHATBOT ACCURACY TEST =====\n", Colors.BLUE)
    
    for idx, test in enumerate(test_cases):
        query = test["query"]
        print(f"Test #{idx+1}: \"{query}\"")
        
        # Process the question
        result = process_question(query, qa_data)
        
        # Check if expected ID exists in test
        test_passed = False
        failure_reason = None
        
        if "expected_id" in test:
            # Find the question in the result to check its ID
            expected_id = test["expected_id"]
            
            # Direct check for intent-based responses
            if "intent" in result and result["intent"] in ["greeting", "thanks", "farewell"]:
                if "expected_intent" in test and test["expected_intent"] == result["intent"]:
                    test_passed = True
                else:
                    test_passed = False
                    failure_reason = f"Got intent '{result['intent']}' but expected question id '{expected_id}'"
            else:
                # For question responses, find the matching question
                matched_question = None
                for question in qa_data["questions"]:
                    if result.get("answer") == question["answer"]:
                        matched_question = question
                        break
                
                if matched_question and matched_question["id"] == expected_id:
                    test_passed = True
                elif matched_question:
                    test_passed = False
                    failure_reason = f"Got '{matched_question['id']}' but expected '{expected_id}'"
                else:
                    test_passed = False
                    failure_reason = f"No matching question found, expected '{expected_id}'"
        
        elif "expected_intent" in test:
            expected_intent = test["expected_intent"]
            if "intent" in result and result["intent"] == expected_intent:
                test_passed = True
            else:
                test_passed = False
                failure_reason = f"Got intent '{result.get('intent')}' but expected '{expected_intent}'"
        
        # Log the test result
        if test_passed:
            print_colored("  ✓ PASSED", Colors.GREEN)
            results["passed"] += 1
        else:
            print_colored(f"  ✗ FAILED: {failure_reason}", Colors.RED)
            print(f"    Answer: {result.get('answer')}")
            print(f"    Confidence: {result.get('confidence')}")
            results["failed"] += 1
        
        # Store test details
        results["details"].append({
            "query": query,
            "passed": test_passed,
            "failure_reason": failure_reason,
            "response": result
        })
        
        print("")  # Add a blank line between tests
    
    # Print summary
    print_colored("\n===== TEST SUMMARY =====", Colors.BLUE)
    print(f"Total tests: {results['total']}")
    print_colored(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)", Colors.GREEN)
    
    if results["failed"] > 0:
        print_colored(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)", Colors.RED)
    
    return results

# Make sure this runs when the script is executed directly
if __name__ == "__main__":
    run_accuracy_test()