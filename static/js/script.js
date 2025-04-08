document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const questionInput = document.getElementById('question-input');
    const sendButton = document.getElementById('send-button');
    const categoriesContainer = document.getElementById('categories-container');
    const chatContainer = document.getElementById('chat-container');
    const factContainer = document.getElementById('fact-container');
    const factText = factContainer.querySelector('.fact-text');
    
    // Track loading states
    let isProcessing = false;
    
    // Focus input field on load
    questionInput.focus();

    // Load daily fact
    loadDailyFact();
    
    // Load categories
    loadCategories();
    
    // Event listeners
    sendButton.addEventListener('click', function() {
        if (!isProcessing) sendQuestion();
    });
    
    questionInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !isProcessing) {
            event.preventDefault();
            sendQuestion();
        }
    });
    
    // Add tap to scroll to bottom on mobile
    chatContainer.addEventListener('click', function() {
        if (window.innerWidth < 768) {
            scrollToBottom();
        }
    });

    // Functions
    function loadDailyFact() {
        // Select the element where the fact will be displayed
        const factText = document.getElementById('fact-container'); // Assuming 'fact-container' is the correct ID
    
        // Fetch the daily fact from the backend
        fetch('/daily-fact')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // If you expect multiple facts and want to display them:
                const facts = data.facts; // Expecting `data.facts` to be an array
                if (facts && facts.length === 2) {
                    // Display two facts (you can adjust as needed)
                    factText.innerHTML = `<p class="text-base text-purple-800 fact-text leading-relaxed">${facts[0]}</p><p class="text-base text-purple-800 fact-text leading-relaxed mt-2">${facts[1]}</p>`;
                } else {
                    // Fallback for when the expected facts are missing or incomplete
                    factText.innerHTML = `<p class="text-base text-purple-800 fact-text leading-relaxed">کوئی معلومات دستیاب نہیں۔</p>`;
                }
    
                // Optionally, you can add a class to animate the fade-in effect
                factText.classList.add('fade-in');
            })
            .catch(error => {
                console.error('Error loading daily fact:', error);
                factText.innerHTML = `<p class="text-base text-purple-800 fact-text leading-relaxed">قرآن میں 114 سورتیں ہیں۔</p>`;  // Default fact
            });
    }
    
    

    function loadCategories() {
        fetch('/categories')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                categoriesContainer.innerHTML = '';
                
                // Check if we got any categories
                if (Object.keys(data).length === 0) {
                    console.log("No categories found, creating defaults");
                    createDefaultCategories();
                    return;
                }
                
                // Create and append category cards
                for (const [id, category] of Object.entries(data)) {
                    if (!category.questions || category.questions.length === 0) {
                        continue;
                    }
                    
                    const categoryCard = document.createElement('div');
                    categoryCard.className = 'category-card bg-white p-4 rounded-lg shadow-sm hover:shadow transition-all';
                    
                    categoryCard.innerHTML = `
                        <div class="flex items-center mb-3">
                            <div class="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0 ml-2">
                                <i class="fas ${category.icon || 'fa-book-open'}"></i>
                            </div>
                            <h3 class="text-lg font-bold text-emerald-700">${category.title}</h3>
                        </div>
                        <ul class="space-y-1">
                            ${category.questions.map(question => `
                                <li class="category-question cursor-pointer hover:text-emerald-700" onclick="setQuestion('${question.replace(/'/g, "\\'")}')">
                                    <i class="fas fa-angle-left text-emerald-600 ml-1"></i> ${question}
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    
                    categoriesContainer.appendChild(categoryCard);
                }
            })
            .catch(error => {
                console.error('Error loading categories:', error);
                createDefaultCategories();
            });
    }

    // Popular questions functionality removed

    function sendQuestion() {
        const question = questionInput.value.trim();
        
        // Don't send empty questions
        if (!question) {
            shakeBorder(questionInput.parentElement);
            return;
        }
        
        // Set processing state
        isProcessing = true;
        
        // Add user message to chat
        addMessage(question, 'user');
        
        // Clear input and disable during processing
        questionInput.value = '';
        questionInput.disabled = true;
        sendButton.disabled = true;
        sendButton.classList.add('opacity-50');
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send question to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add bot message to chat
            addMessage(data.answer, 'bot');
            
            
            // Reset processing state
            isProcessing = false;
            questionInput.disabled = false;
            sendButton.disabled = false;
            sendButton.classList.remove('opacity-50');
            questionInput.focus();
        })
        .catch(error => {
            console.error('Error sending question:', error);
            removeTypingIndicator();
            addMessage('معذرت، کوئی مسئلہ پیش آگیا ہے۔ براہ کرم دوبارہ کوشش کریں۔', 'bot', 'error');
            
            // Reset processing state
            isProcessing = false;
            questionInput.disabled = false;
            sendButton.disabled = false;
            sendButton.classList.remove('opacity-50');
            questionInput.focus();
        });
    }
    
    function addMessage(text, sender, type = 'normal') {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start mb-3 chat-message';
        
        if (sender === 'user') {
            messageDiv.classList.add('justify-end');
            messageDiv.innerHTML = `
                <div class="ml-2 py-2 px-3 bg-blue-100 user-message max-w-[75%] md:max-w-xs shadow-sm">
                    <p class="text-gray-800 text-sm">${text}</p>
                </div>
                <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            let backgroundColor;
            let icon;
            
            if (type === 'fact') {
                backgroundColor = 'bg-purple-100';
                icon = 'fa-lightbulb';
            } else if (type === 'error') {
                backgroundColor = 'bg-red-100';
                icon = 'fa-exclamation-circle';
            } else {
                backgroundColor = 'bg-emerald-100';
                icon = 'fa-robot';
            }
            
            messageDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white flex-shrink-0 ms-3">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="mr-2 py-2 px-3 ${backgroundColor} bot-message max-w-[75%] md:max-w-xs shadow-sm">
                    <p class="text-gray-800 text-sm">${text}</p>
                </div>
            `;
        }
        
        // Add message to chat
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom with a smooth animation
        scrollToBottom();
    }
    
    // Suggestions display functionality removed
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start mb-3 chat-message';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white flex-shrink-0 ms-3">
                <i class="fas fa-robot"></i>
            </div>
            <div class="mr-2 py-2 px-3 bg-gray-100 rounded-lg shadow-sm">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function scrollToBottom() {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    function shakeBorder(element) {
        element.classList.add('border-red-500');
        element.classList.add('shake');
        
        setTimeout(() => {
            element.classList.remove('border-red-500');
            element.classList.remove('shake');
        }, 820);
    }
    
    // Add shake animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0% { transform: translateX(0); }
            25% { transform: translateX(5px); }
            50% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
            100% { transform: translateX(0); }
        }
        .shake {
            animation: shake 0.4s ease-in-out 2;
        }
        .typing-indicator {
            display: flex;
            align-items: center;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            margin: 0 1px;
            background-color: #9CA3AF;
            border-radius: 50%;
            display: inline-block;
            opacity: 0.4;
        }
        
        .typing-indicator span:nth-of-type(1) {
            animation: 1s blink infinite 0.3333s;
        }
        .typing-indicator span:nth-of-type(2) {
            animation: 1s blink infinite 0.6666s;
        }
        .typing-indicator span:nth-of-type(3) {
            animation: 1s blink infinite 0.9999s;
        }
        
        @keyframes blink {
            50% {
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Make setQuestion available globally
    window.setQuestion = function(question) {
        if (isProcessing) return;
        
        questionInput.value = question;
        sendQuestion();
        
        // On mobile, scroll to chat area
        if (window.innerWidth < 768) {
            document.getElementById('chat-container').scrollIntoView({ 
                behavior: 'smooth' 
            });
        }
    };
    
    // Create default categories function
    function createDefaultCategories() {
        // Default categories
        const defaultCategories = {
            "structure": {
                "title": "قرآن کا ڈھانچہ",
                "icon": "fa-book-open",
                "questions": ["قرآن کتنے پاروں پر مشتمل ہے", "قرآن میں کتنی سورتیں ہیں", "سب سے طویل سورۃ کون سی ہے", "سب سے چھوٹی سورۃ کون سی ہے"]
            },
            "revelation": {
                "title": "قرآن کا نزول",
                "icon": "fa-moon",
                "questions": ["قرآن کس زبان میں نازل ہوا", "قرآن کس پیغمبر پر نازل ہوا", "سب سے پہلی وحی کون سی تھی", "قرآن کو مکمل ہونے میں کتنے سال لگے"]
            },
            "prophets": {
                "title": "انبیاء کرام",
                "icon": "fa-user",
                "questions": ["قرآن میں کتنی بار محمد ﷺ کا ذکر آیا ہے", "قرآن میں سب سے زیادہ ذکر کس نبی کا آیا ہے"]
            }
        };
        
        categoriesContainer.innerHTML = '';
        
        for (const [id, category] of Object.entries(defaultCategories)) {
            const categoryCard = document.createElement('div');
            categoryCard.className = 'category-card bg-white p-4 rounded-lg shadow-sm hover:shadow transition-all';
            
            categoryCard.innerHTML = `
                <div class="flex items-center mb-3">
                    <div class="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0 ml-2">
                        <i class="fas ${category.icon}"></i>
                    </div>
                    <h3 class="text-lg font-bold text-emerald-700">${category.title}</h3>
                </div>
                <ul class="space-y-1">
                    ${category.questions.map(question => `
                        <li class="category-question cursor-pointer hover:text-emerald-700" onclick="setQuestion('${question.replace(/'/g, "\\'")}')">
                            <i class="fas fa-angle-left text-emerald-600 ml-1"></i> ${question}
                        </li>
                    `).join('')}
                </ul>
            `;
            
            categoriesContainer.appendChild(categoryCard);
        }
    };
    
    // Make createDefaultCategories available globally
    window.createDefaultCategories = createDefaultCategories;
    
    // Resize handler for suggestions removed
    
    // Add offline detection
    window.addEventListener('online', function() {
        document.body.classList.remove('offline');
        // Refresh data if we were offline
        if (document.body.hasAttribute('data-was-offline')) {
            document.body.removeAttribute('data-was-offline');
            loadDailyFact();
            loadCategories();
            loadPopularQuestions();
            addMessage('آپ کا انٹرنیٹ کنکشن بحال ہو گیا ہے۔', 'bot', 'normal');
        }
    });
    
    window.addEventListener('offline', function() {
        document.body.classList.add('offline');
        document.body.setAttribute('data-was-offline', 'true');
        addMessage('آپ آف لائن ہیں۔ انٹرنیٹ کنکشن چیک کریں۔', 'bot', 'error');
    });
    
    // Add accessibility improvements
    questionInput.setAttribute('aria-label', 'اپنا سوال یہاں لکھیں');
    sendButton.setAttribute('aria-label', 'سوال بھیجیں');
    
    // Double tap prevention for mobile
    let lastTapTime = 0;
    document.addEventListener('click', function(e) {
        const el = e.target.closest('.category-question');
        if (el && e.type === 'touchend') {
            const currentTime = new Date().getTime();
            const tapInterval = currentTime - lastTapTime;
            
            if (tapInterval < 300 && tapInterval > 0) {
                e.preventDefault();
                return false;
            }
            
            lastTapTime = currentTime;
        }
    }, {passive: false});
    
    function formatVerseText(text) {
        // Check if this contains Quranic references
        if (!text.includes('📖')) {
            return text; // Return as is if no references
        }
        
        // Split by multiple verses if they exist
        if (text.includes('**مزید متعلقہ نتائج:**')) {
            const parts = text.split('**مزید متعلقہ نتائج:**');
            const mainVerse = formatSingleVerse(parts[0].trim());
            
            // Format additional verses if they exist
            let additionalVerses = '';
            if (parts.length > 1 && parts[1].trim()) {
                // Split additional results by numbered items
                const additionalParts = parts[1].trim().split(/\d+\.\s+/);
                additionalVerses = '<div class="mt-4 pt-2 border-t border-emerald-200">' +
                                   '<p class="text-emerald-700 font-semibold mb-2">**مزید متعلقہ نتائج:**</p>';
                
                // Process each additional verse (skip the first empty split)
                for (let i = 1; i < additionalParts.length; i++) {
                    if (additionalParts[i].trim()) {
                        additionalVerses += `<div class="mt-2 mb-3">${formatSingleVerse(additionalParts[i].trim())}</div>`;
                    }
                }
                additionalVerses += '</div>';
            }
            
            return mainVerse + additionalVerses;
        } else {
            // Single verse reference
            return formatSingleVerse(text);
        }
    }
    
    function formatSingleVerse(text) {
        // Split the verse from the reference
        const parts = text.split('📖');
        
        if (parts.length < 2) {
            return text; // Not a reference format we recognize
        }
        
        const verseText = parts[0].trim();
        const reference = parts[1].trim();
        
        // Create formatted HTML
        return `<div class="verse-container">
                  <p class="verse-text text-gray-800 mb-3 leading-relaxed">${verseText}</p>
                  <p class="verse-reference text-emerald-700 font-semibold text-sm">📖 ${reference}</p>
                </div>`;
    }
    
    function addMessage(text, sender, type = 'normal') {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start mb-3 chat-message';
        
        if (sender === 'user') {
            messageDiv.classList.add('justify-end');
            messageDiv.innerHTML = `
                <div class="ml-2 py-2 px-3 bg-blue-100 user-message max-w-[75%] md:max-w-xs shadow-sm">
                    <p class="text-gray-800 text-sm">${text}</p>
                </div>
                <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            let backgroundColor;
            let icon;
            
            if (type === 'fact') {
                backgroundColor = 'bg-purple-100';
                icon = 'fa-lightbulb';
            } else if (type === 'error') {
                backgroundColor = 'bg-red-100';
                icon = 'fa-exclamation-circle';
            } else {
                backgroundColor = 'bg-emerald-100';
                icon = 'fa-robot';
            }
            
            // Format Quranic references if needed
            let formattedText = text;
            if (type !== 'fact' && type !== 'error') {
                formattedText = formatVerseText(text);
            }
            
            messageDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white flex-shrink-0 ms-3">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="mr-2 py-2 px-3 ${backgroundColor} bot-message max-w-[75%] md:max-w-xs shadow-sm">
                    <div class="text-gray-800 text-sm">${formattedText}</div>
                </div>
            `;
        }
        
        // Add message to chat
        chatMessages.appendChild(messageDiv);
        
        // Ensure the chat container scrolls to the bottom after each new message
        scrollToBottom();
    }
});