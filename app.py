# -*- coding: utf-8 -*-
# this a test comment
"""
Urdu Quranic Chatbot Web Application
Flask backend for the Quranic Q&A system
"""

from flask import Flask, render_template, request, jsonify
import random
import time

app = Flask(__name__)

# Load question-answer pairs
def load_qa_pairs():
    qa_pairs = {
        # Basic Quran Structure
        "قرآن کتنے پاروں پر مشتمل ہے": {
            "answer": "قرآن 30 پاروں پر مشتمل ہے۔",
            "keywords": ["پاروں", "سپارے", "30"],
        },
        "قرآن میں کتنی سورتیں ہیں": {
            "answer": "قرآن میں 114 سورتیں ہیں۔",
            "keywords": ["سورتیں", "114"],
        },
        "سب سے طویل سورۃ کون سی ہے": {
            "answer": "سب سے طویل سورۃ سورۃ البقرہ ہے۔",
            "keywords": ["طویل", "سورۃ", "بقرہ"],
        },
        "سب سے چھوٹی سورۃ کون سی ہے": {
            "answer": "سب سے چھوٹی سورۃ سورۃ الکوثر ہے۔",
            "keywords": ["چھوٹی", "سورۃ", "الکوثر"],
        },
        "قرآن میں کتنے رکوع ہیں": {
            "answer": "قرآن میں کل 558 رکوع ہیں۔",
            "keywords": ["رکوع", "558"],
        },
        "قرآن میں کتنے الفاظ ہیں": {
            "answer": "قرآن میں تقریباً 77,430 الفاظ ہیں۔",
            "keywords": ["الفاظ", "77430"],
        },
        "قرآن میں کتنے حروف ہیں": {
            "answer": "قرآن میں تقریباً 3,23,670 حروف ہیں۔",
            "keywords": ["حروف", "323670"],
        },
        "قرآن میں کتنی آیات ہیں": {
            "answer": "قرآن میں کل 6,236 آیات ہیں (بسم اللہ سمیت 6,349 آیات شمار کی جاتی ہیں)۔",
            "keywords": ["آیات", "6236", "6349"],
        },
        "قرآن میں کتنی مکی اور مدنی سورتیں ہیں": {
            "answer": "قرآن میں 86 مکی اور 28 مدنی سورتیں ہیں۔",
            "keywords": ["مکی", "مدنی", "86", "28"],
        },
        
        # Revelation Information
        "قرآن کس زبان میں نازل ہوا": {
            "answer": "قرآن عربی زبان میں نازل ہوا۔",
            "keywords": ["زبان", "عربی"],
        },
        "قرآن کس پیغمبر پر نازل ہوا": {
            "answer": "قرآن حضرت محمد ﷺ پر نازل ہوا۔",
            "keywords": ["پیغمبر", "محمد", "ﷺ"],
        },
        "قرآن میں سب سے پہلے نازل ہونے والی آیت کون سی ہے": {
            "answer": "سب سے پہلے نازل ہونے والی آیت سورۃ العلق کی پہلی پانچ آیات ہیں۔",
            "keywords": ["پہلے", "نازل", "علق"],
        },
        "سب سے پہلی وحی کون سی تھی": {
            "answer": "سب سے پہلی وحی سورۃ العلق کی پہلی پانچ آیات تھیں۔",
            "keywords": ["پہلی", "وحی", "علق"],
        },
        "سب سے پہلی وحی کہاں نازل ہوئی": {
            "answer": "سب سے پہلی وحی غارِ حرا میں نازل ہوئی۔",
            "keywords": ["پہلی", "وحی", "حرا"],
        },
        "قرآن کی آخری آیت کون سی ہے": {
            "answer": "قرآن کی آخری آیت سورۃ البقرہ کی آیت 281 ہے۔",
            "keywords": ["آخری", "281", "بقرہ"],
        },
        "قرآن کو مکمل ہونے میں کتنے سال لگے": {
            "answer": "قرآن کو مکمل نازل ہونے میں تقریباً 23 سال لگے۔",
            "keywords": ["مکمل", "23", "سال"],
        },
        "قرآن کا سب سے پہلا اور آخری نزول کہاں ہوا": {
            "answer": "قرآن کا سب سے پہلا نزول غارِ حرا میں اور آخری نزول حجۃ الوداع کے موقع پر میدانِ عرفات میں ہوا۔",
            "keywords": ["پہلا", "آخری", "نزول", "حرا", "عرفات"],
        },
        
        # Special Verses
        "قرآن کی سب سے بڑی آیت کون سی ہے": {
            "answer": "قرآن کی سب سے بڑی آیت آیتُ الدین (سورۃ البقرہ، آیت 282) ہے۔",
            "keywords": ["بڑی", "آیت", "الدین", "282"],
        },
        "قرآن کی سب سے زیادہ فضیلت والی آیت کون سی ہے": {
            "answer": "قرآن کی سب سے زیادہ فضیلت والی آیت آیتُ الکرسی (سورۃ البقرہ، آیت 255) ہے۔",
            "keywords": ["فضیلت", "آیت", "الکرسی", "255"],
        },
        "قرآن میں سب سے چھوٹی آیت کون سی ہے": {
            "answer": "قرآن میں سب سے چھوٹی آیت 'مدھامّتان' (سورۃ الرحمن، آیت 64) ہے۔",
            "keywords": ["چھوٹی", "آیت", "مدھامّتان"],
        },
        "قرآن میں سب سے بڑی سورت کون سی ہے": {
            "answer": "قرآن میں سب سے بڑی سورت سورۃ البقرہ ہے۔",
            "keywords": ["بڑی", "سورۃ", "بقرہ"],
        },
        
        # Mentions in Quran
        "قرآن میں سب سے زیادہ کس چیز کا ذکر ہے": {
            "answer": "قرآن میں سب سے زیادہ اللہ کا ذکر آیا ہے۔",
            "keywords": ["زیادہ", "ذکر", "اللہ"],
        },
        "قرآن میں سب سے زیادہ استعمال ہونے والا لفظ کون سا ہے": {
            "answer": "قرآن میں سب سے زیادہ استعمال ہونے والا لفظ 'اللہ' ہے۔",
            "keywords": ["زیادہ", "استعمال", "لفظ", "اللہ"],
        },
        "قرآن میں کتنے معجزات کا ذکر ہے": {
            "answer": "قرآن میں تقریباً 1000 معجزات کا ذکر ہے۔",
            "keywords": ["معجزات", "1000"],
        },
        
        # Prophets and People
        "قرآن میں سب سے زیادہ ذکر کس نبی کا آیا ہے": {
            "answer": "قرآن میں سب سے زیادہ ذکر حضرت موسیٰ علیہ السلام کا آیا ہے۔",
            "keywords": ["ذکر", "نبی", "موسیٰ"],
        },
        "قرآن میں کتنی بار محمد ﷺ کا ذکر آیا ہے": {
            "answer": "قرآن میں محمد ﷺ کا ذکر 4 بار آیا ہے۔",
            "keywords": ["محمد", "ذکر", "4"],
        },
        "قرآن میں کتنی بار حضرت عیسیٰ علیہ السلام کا ذکر آیا ہے": {
            "answer": "قرآن میں حضرت عیسیٰ علیہ السلام کا ذکر 25 بار آیا ہے۔",
            "keywords": ["عیسیٰ", "ذکر", "25"],
        },
        "قرآن میں کتنی بار حضرت ابراہیم علیہ السلام کا ذکر آیا ہے": {
            "answer": "قرآن میں حضرت ابراہیم علیہ السلام کا ذکر 69 بار آیا ہے۔",
            "keywords": ["ابراہیم", "ذکر", "69"],
        },
        "قرآن میں کتنے صحابہ کرام کے نام ذکر ہوئے ہیں": {
            "answer": "قرآن میں حضرت زید بن حارثہ رضی اللہ عنہ کا نام ذکر ہوا ہے، باقی صحابہ کے نام براہ راست مذکور نہیں ہیں۔",
            "keywords": ["صحابہ", "نام", "زید"],
        },
        "قرآن میں سب سے زیادہ ذکر ہونے والی عورت کون ہے": {
            "answer": "قرآن میں سب سے زیادہ ذکر حضرت مریم علیہا السلام کا آیا ہے۔",
            "keywords": ["ذکر", "عورت", "مریم"],
        },
        "قرآن میں فرعون کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں فرعون کا ذکر تقریباً 74 بار آیا ہے۔",
            "keywords": ["فرعون", "ذکر", "74"],
        },
        "قرآن میں سب سے زیادہ کس قوم کا ذکر آیا ہے": {
            "answer": "قرآن میں سب سے زیادہ بنی اسرائیل کا ذکر آیا ہے۔",
            "keywords": ["قوم", "ذکر", "بنی اسرائیل"],
        },
        
        # Islamic History
        "قرآن میں سب سے پہلے ایمان لانے والی خاتون کون تھیں": {
            "answer": "قرآن میں براہ راست ذکر تو نہیں، لیکن سب سے پہلے ایمان لانے والی خاتون حضرت خدیجہ رضی اللہ عنہا تھیں۔",
            "keywords": ["ایمان", "خاتون", "خدیجہ"],
        },
        "قرآن میں سب سے پہلے شہید ہونے والے صحابی کون تھے": {
            "answer": "سب سے پہلے شہید ہونے والے صحابی حضرت سمیہ رضی اللہ عنہا تھیں۔",
            "keywords": ["شہید", "صحابی", "سمیہ"],
        },
        "قرآن میں سب سے پہلے مسلمان ہونے والے مرد کون تھے": {
            "answer": "سب سے پہلے مسلمان ہونے والے مرد حضرت ابوبکر صدیق رضی اللہ عنہ تھے۔",
            "keywords": ["مسلمان", "مرد", "ابوبکر"],
        },
        "قرآن میں سب سے پہلے مسلمان ہونے والے بچہ کون تھے": {
            "answer": "سب سے پہلے اسلام قبول کرنے والے بچے حضرت علی رضی اللہ عنہ تھے۔",
            "keywords": ["مسلمان", "بچہ", "علی"],
        },
        "قرآن میں سب سے پہلے ایمان لانے والے غلام کون تھے": {
            "answer": "سب سے پہلے ایمان لانے والے غلام حضرت زید بن حارثہ رضی اللہ عنہ تھے۔",
            "keywords": ["ایمان", "غلام", "زید"],
        },
        
        # Pillars of Islam
        "قرآن میں نماز کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں نماز کا ذکر 700 سے زائد بار آیا ہے۔",
            "keywords": ["نماز", "ذکر", "700"],
        },
        "قرآن میں روزے کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں روزے کا ذکر 13 بار آیا ہے۔",
            "keywords": ["روزہ", "ذکر", "13"],
        },
        "قرآن میں حج کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں حج کا ذکر 12 بار آیا ہے۔",
            "keywords": ["حج", "ذکر", "12"],
        },
        "قرآن میں زکوٰۃ کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں زکوٰۃ کا ذکر 32 بار آیا ہے۔",
            "keywords": ["زکوٰۃ", "ذکر", "32"],
        },
        
        # Other Important Concepts
        "قرآن میں جنت کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں جنت کا ذکر 147 بار آیا ہے۔",
            "keywords": ["جنت", "147"],
        },
        "قرآن میں دوزخ کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں دوزخ کا ذکر 77 بار آیا ہے۔",
            "keywords": ["دوزخ", "77"],
        },
        "قرآن میں شیطان کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں شیطان کا ذکر 88 بار آیا ہے۔",
            "keywords": ["شیطان", "ذکر", "88"],
        },
        "قرآن میں دنیا اور آخرت کا ذکر کتنی بار آیا ہے": {
            "answer": "قرآن میں دنیا کا ذکر 115 بار اور آخرت کا ذکر بھی 115 بار آیا ہے۔",
            "keywords": ["دنیا", "آخرت", "115"],
        },
        "قرآن میں سب سے پہلے کس چیز کا حکم دیا گیا": {
            "answer": "قرآن میں سب سے پہلے 'اقرأ' (پڑھنے) کا حکم دیا گیا۔",
            "keywords": ["حکم", "پہلا", "اقرأ"],
        },
        "قرآن میں سب سے بڑی سزا کس چیز کے لیے ہے": {
            "answer": "قرآن میں سب سے بڑی سزا شرک کے لیے بیان کی گئی ہے۔",
            "keywords": ["سزا", "بڑی", "شرک"],
        },
        
        # Miscellaneous
        "قرآن میں کتنی زبانوں کے الفاظ استعمال ہوئے ہیں": {
            "answer": "قرآن میں زیادہ تر عربی زبان کے الفاظ ہیں، لیکن اس میں فارسی، رومی، حبشی اور عبرانی کے چند الفاظ بھی موجود ہیں۔",
            "keywords": ["زبان", "عربی", "فارسی", "رومی", "حبشی"],
        },
        "قرآن میں کتنے درختوں کا ذکر آیا ہے": {
            "answer": "قرآن میں کئی درختوں کا ذکر آیا ہے، جن میں زیتون، کھجور، انگور، اور بیری شامل ہیں۔",
            "keywords": ["درخت", "زیتون", "کھجور", "انگور"],
        },
        "قرآن میں کس جانور کا سب سے زیادہ ذکر ہے": {
            "answer": "قرآن میں سب سے زیادہ ذکر گائے (بقرہ) کا آیا ہے۔",
            "keywords": ["جانور", "ذکر", "گائے"],
        },
        "قرآن میں سب سے زیادہ ذکر کس دریا کا آیا ہے": {
            "answer": "قرآن میں سب سے زیادہ ذکر دریائے نیل کا آیا ہے۔",
            "keywords": ["ذکر", "دریا", "نیل"],
        },
    }
    return qa_pairs

# Text processing functions
def normalize(text):
    """Remove punctuation and extra spaces for better matching."""
    return text.replace("؟", "").strip()

def find_answer(user_input, qa_pairs):
    """Find an appropriate answer based on keywords."""
    best_match = None
    match_count = 0
    
    for question, details in qa_pairs.items():
        current_matches = 0
        for keyword in details["keywords"]:
            if keyword in user_input:
                current_matches += 1
        
        if current_matches > match_count:
            match_count = current_matches
            best_match = details
    
    return best_match

# Daily Quranic facts
def get_random_fact():
    facts = [
        "سورۃ الکوثر قرآن کی سب سے چھوٹی سورت ہے، اس میں صرف 3 آیات ہیں۔",
        "قرآن میں 'بسم اللہ الرحمن الرحیم' 114 بار آتا ہے (ہر سورت کے شروع میں، سوائے سورۃ التوبہ کے)۔",
        "قرآن کی آیت الکرسی (سورۃ البقرہ، آیت 255) کو قرآن کی سب سے عظیم آیت سمجھا جاتا ہے۔",
        "قرآن میں 30 پارے، 114 سورتیں، 558 رکوع اور 6236 آیات ہیں۔",
        "حضرت محمد ﷺ پر پہلی وحی غارِ حرا میں نازل ہوئی تھی۔",
        "قرآن میں سب سے زیادہ ذکر حضرت موسیٰ علیہ السلام کا آیا ہے۔"
    ]
    return random.choice(facts)

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Process the user's question and return an answer"""
    user_input = request.json.get('question', '')
    
    # Add slight delay to simulate thinking (optional)
    time.sleep(0.5)
    
    # Exit condition check
    if user_input == "اللہ حافظ ,ختم" or "اللہ حافظ" in user_input:
        return jsonify({
            'answer': "اللہ حافظ! دوبارہ بات کرنے کا شکریہ۔", 
            'farewell': True
        })
    
    # Handle greetings
    greetings = ["السلام علیکم", "سلام", "آداب", "ہیلو", "ہائے", "ہاے"]
    for greeting in greetings:
        if greeting in user_input.lower():
            return jsonify({
                'answer': "وعلیکم السلام! میں آپ کی قرآن سے متعلق سوالات کے جوابات دینے کے لیے حاضر ہوں۔ کیا آپ کوئی خاص سوال پوچھنا چاہتے ہیں؟",
                'suggestions': ["قرآن کتنے پاروں پر مشتمل ہے", "قرآن میں کتنی سورتیں ہیں"]
            })
    
    # Thank you responses
    thanks = ["شکریہ", "مہربانی", "احسان"]
    for thank in thanks:
        if thank in user_input.lower():
            return jsonify({
                'answer': "آپ کا شکریہ! میں آپ کی مدد کرکے خوش ہوں۔ کیا آپ کچھ اور پوچھنا چاہیں گے؟",
                'suggestions': ["ہاں", "نہیں، اللہ حافظ"]
            })
    
    # Normalize input and find answer
    normalized_input = normalize(user_input)
    qa_pairs = load_qa_pairs()
    match = find_answer(normalized_input, qa_pairs)
    
    if match:
        # Return answer with related questions as suggestions
        return jsonify({
            'answer': match["answer"],
            'suggestions': match.get("related", [])
        })
    else:
        # If no direct match found
        return jsonify({
            'answer': "معاف کیجیے، میں اس سوال کا جواب نہیں جانتا۔ برائے مہربانی قرآن سے متعلق کوئی اور سوال پوچھیں۔",
            'fact': get_random_fact(),
            'suggestions': ["قرآن کتنے پاروں پر مشتمل ہے", "قرآن میں کتنی سورتیں ہیں"]
        })


@app.route('/popular-questions')
def popular_questions():
    """Return a list of popular questions for suggestions"""
    popular = [
        "قرآن کتنے پاروں پر مشتمل ہے",
        "قرآن میں کتنی سورتیں ہیں",
        "سب سے طویل سورۃ کون سی ہے",
        "قرآن میں نماز کا ذکر کتنی بار آیا ہے",
        "قرآن میں سب سے زیادہ کس نبی کا ذکر آیا ہے"
    ]
    return jsonify({'questions': popular})

@app.route('/daily-fact')
def daily_fact():
    """Return a random Quranic fact"""
    return jsonify({'fact': get_random_fact()})

@app.route('/categories')
def get_categories():
    """Return categories and their questions"""
    categories = {
        "structure": {
            "title": "قرآن کی ساخت",
            "icon": "fa-book",
            "questions": [
                "قرآن کتنے پاروں پر مشتمل ہے",
                "قرآن میں کتنی سورتیں ہیں",
                "سب سے طویل سورۃ کون سی ہے",
                "سب سے چھوٹی سورۃ کون سی ہے"
            ]
        },
        "prophets": {
            "title": "انبیاء کرام",
            "icon": "fa-user",
            "questions": [
                "قرآن میں سب سے زیادہ ذکر کس نبی کا آیا ہے",
                "قرآن میں کتنی بار محمد ﷺ کا ذکر آیا ہے",
                "قرآن میں کتنی بار حضرت عیسیٰ علیہ السلام کا ذکر آیا ہے"
            ]
        },
        "pillars": {
            "title": "ارکان اسلام",
            "icon": "fa-mosque",
            "questions": [
                "قرآن میں نماز کا ذکر کتنی بار آیا ہے",
                "قرآن میں روزے کا ذکر کتنی بار آیا ہے",
                "قرآن میں حج کا ذکر کتنی بار آیا ہے",
                "قرآن میں زکوٰۃ کا ذکر کتنی بار آیا ہے"
            ]
        },
        "revelation": {
            "title": "وحی",
            "icon": "fa-scroll",
            "questions": [
                "قرآن میں سب سے پہلے نازل ہونے والی آیت کون سی ہے",
                "سب سے پہلی وحی کون سی تھی",
                "سب سے پہلی وحی کہاں نازل ہوئی"
            ]
        }
    }
    return jsonify(categories)


if __name__ == '__main__':
    app.run(debug=True)