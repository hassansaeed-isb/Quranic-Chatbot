// File: static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const userMessageInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-button');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const categoryButtons = document.querySelectorAll('.category-btn');
    const categoryModal = document.getElementById('category-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalQuestions = document.getElementById('modal-questions');
    const closeModal = document.querySelector('.close-modal');
    
    // Categories and their questions
    const categories = {
        structure: {
            title: "قرآن کی ساخت",
            questions: [
                "قرآن کتنے پاروں پر مشتمل ہے",
                "قرآن میں کتنی سورتیں ہیں",
                "سب سے طویل سورۃ کون سی ہے",
                "سب سے چھوٹی سورۃ کون سی ہے",
                "قرآن میں کتنے رکوع ہیں",
                "قرآن میں کتنے الفاظ ہیں",
                "قرآن میں کتنے حروف ہیں",
                "قرآن میں کتنی آیات ہیں"
            ]
        },
        prophets: {
            title: "انبیاء کرام",
            questions: [
                "قرآن میں سب سے زیادہ ذکر کس نبی کا آیا ہے",
                "قرآن میں کتنی بار محمد ﷺ کا ذکر آیا ہے",
                "قرآن میں کتنی بار حضرت عیسیٰ علیہ السلام کا ذکر آیا ہے",
                "قرآن میں کتنی بار حضرت ابراہیم علیہ السلام کا ذکر آیا ہے"
            ]
        },
        pillars: {
            title: "ارکان اسلام",
            questions: [
                "قرآن میں نماز کا ذکر کتنی بار آیا ہے",
                "قرآن میں روزے کا ذکر کتنی بار آیا ہے",
                "قرآن میں حج کا ذکر کتنی بار آیا ہے",
                "قرآن میں زکوٰۃ کا ذکر کتنی بار آیا ہے"
            ]
        },
        revelation: {
            title: "وحی",
            questions: [
                "قرآن میں سب سے پہلے نازل ہونے والی آیت کون سی ہے",
                "سب سے پہلی وحی کون سی تھی",
                "سب سے پہلی وحی کہاں نازل ہوئی",
                "قرآن کی آخری آیت کون سی ہے",
                "قرآن کو مکمل ہونے میں کتنے سال لگے",
                "قرآن کا سب سے پہلا اور آخری نزول کہاں ہوا"
            ]
        },
        history: {
            title: "تاریخ",
            questions: [
                "قرآن میں سب سے پہلے ایمان لانے والی خاتون کون تھیں",
                "قرآن میں سب سے پہلے شہید ہونے والے صحابی کون تھے",
                "قرآن میں سب سے پہلے مسلمان ہونے والے مرد کون تھے",
                "قرآن میں سب سے پہلے مسلمان ہونے والے بچہ کون تھے",
                "قرآن میں سب سے پہلے ایمان لانے والے غلام کون تھے"
            ]
        }
    };
    
    // Function to add a message to the chat
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        messageContent.innerHTML = `<p>${text}</p>`;
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'typing';
        
        typingContent.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
        
        typingDiv.appendChild(typingContent);
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Function to send the user's message to the server and get a response
    async function sendMessage(message) {
        // Add user message to chat
        addMessage(message, true);
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message }),
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add bot response to chat
            addMessage(data.answer);
            
            // If this is a farewell message, disable input
            if (data.farewell) {
                userMessageInput.disabled = true;
                sendButton.disabled = true;
            }
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('عذر خواہ ہوں، کچھ غلطی ہوئی۔ براۓ مہربانی دوبارہ کوشش کریں۔');
        }
    }
    
    // Function to show the category modal
    function showCategoryModal(categoryKey) {
        const category = categories[categoryKey];
        if (!category) return;
        
        modalTitle.textContent = category.title;
        modalQuestions.innerHTML = '';
        
        category.questions.forEach(question => {
            const questionElement = document.createElement('div');
            questionElement.className = 'modal-question';
            questionElement.textContent = question;
            questionElement.addEventListener('click', function() {
                sendMessage(question);
                categoryModal.style.display = 'none';
            });
            
            modalQuestions.appendChild(questionElement);
        });
        
        categoryModal.style.display = 'flex';
    }
    
    // Button animation
    function animateButton(button) {
        button.classList.add('btn-press');
        setTimeout(() => {
            button.classList.remove('btn-press');
        }, 200);
    }
    
    // Event listener for send button
    sendButton.addEventListener('click', function() {
        const message = userMessageInput.value.trim();
        if (message !== '') {
            animateButton(sendButton);
            sendMessage(message);
            userMessageInput.value = '';
        }
    });
    
    // Event listener for Enter key
    userMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = userMessageInput.value.trim();
            if (message !== '') {
                sendMessage(message);
                userMessageInput.value = '';
            }
        }
    });
    
    // Event listeners for suggestion buttons
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.textContent;
            animateButton(this);
            sendMessage(message);
        });
    });
    
    // Event listeners for category buttons
    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            animateButton(this);
            showCategoryModal(category);
        });
    });
    
    // Close modal when clicking the close button
    closeModal.addEventListener('click', function() {
        categoryModal.style.display = 'none';
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === categoryModal) {
            categoryModal.style.display = 'none';
        }
    });
    
    // Focus on input field when page loads
    userMessageInput.focus();
    
    // Fetch and populate popular questions from the server
    async function fetchPopularQuestions() {
        try {
            const response = await fetch('/popular-questions');
            const data = await response.json();
            
            if (data.questions && data.questions.length > 0) {
                const suggestionsDiv = document.querySelector('.suggestion-buttons');
                suggestionsDiv.innerHTML = '';
                
                data.questions.forEach(question => {
                    const button = document.createElement('button');
                    button.className = 'suggestion-btn';
                    button.textContent = question;
                    button.addEventListener('click', function() {
                        animateButton(this);
                        sendMessage(question);
                    });
                    
                    suggestionsDiv.appendChild(button);
                });
            }
        } catch (error) {
            console.error('Error fetching popular questions:', error);
        }
    }
    
    // Call the function to fetch popular questions
    fetchPopularQuestions();
});