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
    const dailyFactContainer = document.getElementById('daily-fact');
    const scrollIndicator = document.getElementById('scroll-indicator');
    
    // Animation settings
    const typingSpeed = 15; // ms per character for typing animation (slightly faster)
    
    // Chat history (limiting to just what we need)
    let chatHistory = [];
    
    // Track last bot message element for scrolling purposes
    let lastBotMessageElement = null;
    
    // Track if user has scrolled up
    let userHasScrolledUp = false;
    
    // Add scroll to top button (simplified)
    const scrollTopButton = document.createElement('button');
    scrollTopButton.id = 'scroll-top-btn';
    scrollTopButton.className = 'scroll-top-btn';
    scrollTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollTopButton.title = 'اوپر جائیں';
    document.body.appendChild(scrollTopButton);
    
    // Function to add a message to the chat with typing animation
    function addMessage(text, isUser = false, withAnimation = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser || !withAnimation) {
            // User messages or messages without animation
            messageContent.innerHTML = `<p>${text}</p>`;
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            // Bot messages with typing animation
            messageContent.innerHTML = `<p></p>`;
            
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);
            
            // Save reference to the last bot message for scrolling
            lastBotMessageElement = messageDiv;
            
            const textElement = messageContent.querySelector('p');
            let index = 0;
            
            // Show scroll indicator if user has scrolled up
            if (chatMessages.scrollHeight > chatMessages.clientHeight && 
                chatMessages.scrollTop < chatMessages.scrollHeight - chatMessages.clientHeight - 100) {
                showScrollIndicator();
                userHasScrolledUp = true;
            }
            
            function typeText() {
                if (index < text.length) {
                    textElement.textContent += text.charAt(index);
                    index++;
                    
                    // Only auto-scroll if user hasn't scrolled up
                    if (!userHasScrolledUp) {
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                    
                    setTimeout(typeText, typingSpeed);
                } else {
                    // Add suggestions if available
                    if (currentSuggestions && currentSuggestions.length > 0) {
                        displaySuggestions(currentSuggestions, messageDiv);
                        currentSuggestions = null;
                    }
                    
                    // Add a visual indicator that this is the latest answer
                    messageDiv.setAttribute('id', 'latest-answer');
                }
            }
            
            typeText();
        }
        
        // Save to chat history (limited to last 10 messages)
        chatHistory.push({
            text: text,
            isUser: isUser
        });
        
        if (chatHistory.length > 10) {
            chatHistory.shift();
        }
        
        if (!userHasScrolledUp) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    HEAD

    // Function to copy message text to clipboard
    function copyMessageText(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Show success message
            const copySuccess = document.querySelector('.copy-success');
            if (copySuccess) {
                copySuccess.classList.add('show');
                setTimeout(() => {
                    copySuccess.classList.remove('show');
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    }
    
    // Function to add emoji reactions
    function addEmojiReactions(messageElement) {
        const reactions = document.createElement('div');
        reactions.className = 'emoji-reactions';
        
        // Add some emoji reactions
        const emojis = ['❤️',];
        
        emojis.forEach(emoji => {
            const emojiSpan = document.createElement('span');
            emojiSpan.className = 'emoji-reaction';
            emojiSpan.textContent = emoji;
            emojiSpan.addEventListener('click', function() {
                this.classList.toggle('selected');
            });
            reactions.appendChild(emojiSpan);
        });
        
        messageElement.appendChild(reactions);
    }
    

    // Variable to store current suggestions
    let currentSuggestions = null;
    
    // Function to display clickable suggestions
    function displaySuggestions(suggestions, parentElement) {
        if (!suggestions || suggestions.length === 0) return;
        
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'message-suggestions';
        
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'message-suggestion-btn';
            button.textContent = suggestion;
            button.addEventListener('click', function() {
                animateButton(this);
                sendMessage(suggestion);
                
                // Smooth scroll to top of chat messages first to give visual feedback
                smoothScrollToTop();
            });
            
            suggestionsDiv.appendChild(button);
        });
        
        parentElement.appendChild(suggestionsDiv);
    }
    
    // Function to smoothly scroll to the top of chat messages
    function smoothScrollToTop() {
        chatMessages.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    // Function to smoothly scroll to the latest answer
    function smoothScrollToLatestAnswer() {
        const latestAnswer = document.getElementById('latest-answer');
        if (latestAnswer) {
            latestAnswer.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            
            // Highlight effect after scrolling
            setTimeout(() => {
                if (latestAnswer.querySelector('.message-content')) {
                    latestAnswer.querySelector('.message-content').classList.add('highlight');
                    setTimeout(() => {
                        latestAnswer.querySelector('.message-content').classList.remove('highlight');
                    }, 1000);
                }
            }, 500);
        }
    }
    
    // Function to show scroll indicator
    function showScrollIndicator() {
        scrollIndicator.classList.add('show');
        setTimeout(() => {
            scrollIndicator.classList.remove('show');
        }, 3000);
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
    
    // Function to show a daily fact with animation
    function showDailyFact(fact) {
        if (dailyFactContainer && fact) {
            dailyFactContainer.innerHTML = `<i class="fas fa-lightbulb"></i> ${fact}`;
            dailyFactContainer.style.display = 'block';
            
            // Add animation
            dailyFactContainer.classList.add('fact-animate');
            setTimeout(() => {
                dailyFactContainer.classList.remove('fact-animate');
            }, 1000);
        }
    }
    
    // Function to show thinking animation before bot responses
    function showThinking() {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'thinking';
        thinkingDiv.id = 'thinking-indicator';
        thinkingDiv.innerHTML = `میں آپ کے سوال پر غور کر رہا ہوں <i class="fas fa-brain"></i>`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        messageDiv.appendChild(thinkingDiv);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv; // Return for later removal
    }
    
    // Function to remove thinking animation
    function removeThinking(thinkingElement) {
        if (thinkingElement && thinkingElement.parentNode) {
            thinkingElement.parentNode.removeChild(thinkingElement);
        }
    }
    
    // Function to send the user's message to the server and get a response
    async function sendMessage(message) {
        // Don't send empty messages
        if (!message.trim()) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input field
        userMessageInput.value = '';
        
        // Show thinking animation first
        const thinkingElement = showThinking();
        
        // After a short delay, replace with typing indicator
        setTimeout(() => {
            removeThinking(thinkingElement);
            showTypingIndicator();
        }, 800);
        
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
            
            // Reset user scroll tracking
            userHasScrolledUp = false;
            
            // Store suggestions to display after typing animation
            currentSuggestions = data.suggestions;
            
            // Add bot response to chat
            addMessage(data.answer);
            
            // After answer is displayed, scroll to it if necessary
            if (chatMessages.scrollHeight > chatMessages.clientHeight && 
                chatMessages.scrollTop < chatMessages.scrollHeight - chatMessages.clientHeight - 100) {
                
                setTimeout(() => {
                    smoothScrollToLatestAnswer();
                }, data.answer.length * typingSpeed + 300);
            }
            
            // Show daily fact if provided
            if (data.fact) {
                showDailyFact(data.fact);
            }
            
            // If this is a farewell message, disable input
            if (data.farewell) {
                userMessageInput.disabled = true;
                sendButton.disabled = true;
                
                // Show restart option after 2 seconds
                setTimeout(() => {
                    const restartDiv = document.createElement('div');
                    restartDiv.className = 'restart-container';
                    restartDiv.innerHTML = `
                        <button id="restart-chat" class="restart-btn">
                            <i class="fas fa-redo"></i> نئی گفتگو شروع کریں
                        </button>
                    `;
                    chatMessages.appendChild(restartDiv);
                    
                    // Add event listener to restart button
                    document.getElementById('restart-chat').addEventListener('click', function() {
                        // Show loading animation
                        const loadingOverlay = document.getElementById('loading-overlay');
                        loadingOverlay.classList.add('show');
                        
                        // Reload after a short delay for better UX
                        setTimeout(() => {
                            window.location.reload();
                        }, 500);
                    });
                }, 2000);
            }
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('عذر خواہ ہوں، کچھ غلطی ہوئی۔ براۓ مہربانی دوبارہ کوشش کریں۔');
        }
    }
    
    // Voice input functionality (simplified)
    let isListening = false;
    let recognition;
    
    // Check if browser supports speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'ur-PK'; // Set language to Urdu
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userMessageInput.value = transcript;
            toggleVoiceInput(); // Stop listening
            
            // Visual feedback - briefly highlight the input field
            userMessageInput.classList.add('voice-input-success');
            setTimeout(() => {
                userMessageInput.classList.remove('voice-input-success');
                sendMessage(transcript);
            }, 300);
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            toggleVoiceInput(); // Stop listening
            
            // Visual feedback for error
            const voiceButton = document.getElementById('voice-input-button');
            voiceButton.classList.add('voice-error');
            setTimeout(() => {
                voiceButton.classList.remove('voice-error');
            }, 500);
        };
        
        // Add voice input button
        const voiceButton = document.createElement('button');
        voiceButton.id = 'voice-input-button';
        voiceButton.className = 'voice-btn';
        voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceButton.title = 'بولنا شروع کریں';
        
        // Insert before send button
        const chatInput = document.querySelector('.chat-input');
        chatInput.insertBefore(voiceButton, sendButton);
        
        // Event listener for voice button
        voiceButton.addEventListener('click', toggleVoiceInput);
    }
    
    function toggleVoiceInput() {
        const voiceButton = document.getElementById('voice-input-button');
        
        if (isListening) {
            // Stop listening
            recognition.stop();
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceButton.classList.remove('listening');
            isListening = false;
        } else {
            // Start listening
            recognition.start();
            voiceButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            voiceButton.classList.add('listening');
            isListening = true;
        }
    }
    
    // Function to show the category modal
    function showCategoryModal(categoryKey) {
        fetch('/categories')
            .then(response => response.json())
            .then(categories => {
                const category = categories[categoryKey];
                if (!category) return;
                
                modalTitle.textContent = category.title;
                modalQuestions.innerHTML = '';
                
                category.questions.forEach(question => {
                    const questionElement = document.createElement('div');
                    questionElement.className = 'modal-question';
                    questionElement.innerHTML = `<i class="fas ${category.icon}"></i> ${question}`;
                    questionElement.addEventListener('click', function() {
                        sendMessage(question);
                        
                        // Animate modal closing
                        const modalContent = document.querySelector('.modal-content');
                        modalContent.style.animation = 'modalFadeOut 0.2s ease-in forwards';
                        
                        setTimeout(() => {
                            categoryModal.style.display = 'none';
                        }, 200);
                        
                        // Smooth scroll to top first to give visual feedback that something is happening
                        smoothScrollToTop();
                    });
                    
                    modalQuestions.appendChild(questionElement);
                });
                
                // Display and animate modal
                categoryModal.style.display = 'flex';
                setTimeout(() => {
                    categoryModal.classList.add('show');
                }, 10);
                
                // Add animation to modal opening
                const modalContent = document.querySelector('.modal-content');
                modalContent.style.animation = 'modalFadeIn 0.3s ease-out';
            })
            .catch(error => {
                console.error('Error fetching categories:', error);
            });
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
        } else {
            // Visual feedback for empty message
            userMessageInput.classList.add('empty-input-shake');
            setTimeout(() => {
                userMessageInput.classList.remove('empty-input-shake');
            }, 500);
        }
    });
    
    // Event listener for Enter key
    userMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = userMessageInput.value.trim();
            if (message !== '') {
                sendMessage(message);
            } else {
                // Visual feedback for empty message
                this.classList.add('empty-input-shake');
                setTimeout(() => {
                    this.classList.remove('empty-input-shake');
                }, 500);
            }
        }
    });
    
    // Add focus effect for input field
    userMessageInput.addEventListener('focus', function() {
        this.parentElement.parentElement.classList.add('input-focused');
    });
    
    userMessageInput.addEventListener('blur', function() {
        this.parentElement.parentElement.classList.remove('input-focused');
    });
    
    // Add keyup event to handle input changes
    userMessageInput.addEventListener('input', function() {
        // Enable/disable send button based on input
        sendButton.disabled = this.value.trim() === '';
        if (sendButton.disabled) {
            sendButton.classList.add('disabled');
        } else {
            sendButton.classList.remove('disabled');
        }
    });
    
    // Track chat scrolling
    chatMessages.addEventListener('scroll', function() {
        // Show/hide scroll button based on scroll position
        if (this.scrollTop > 200) {
            scrollTopButton.classList.add('show');
        } else {
            scrollTopButton.classList.remove('show');
        }
        
        // Track if user has scrolled up
        if (this.scrollHeight - this.scrollTop - this.clientHeight > 100) {
            userHasScrolledUp = true;
        } else {
            userHasScrolledUp = false;
        }
    });
    
    // Scroll indicator click event
    scrollIndicator.addEventListener('click', function() {
        smoothScrollToLatestAnswer();
    });
    
    // Event listeners for suggestion buttons
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.textContent;
            animateButton(this);
            sendMessage(message);
            
            // Smooth scroll to top first
            smoothScrollToTop();
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
        const modalContent = document.querySelector('.modal-content');
        modalContent.style.animation = 'modalFadeOut 0.2s ease-in forwards';
        
        setTimeout(() => {
            categoryModal.style.display = 'none';
            categoryModal.classList.remove('show');
        }, 200);
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === categoryModal) {
            const modalContent = document.querySelector('.modal-content');
            modalContent.style.animation = 'modalFadeOut 0.2s ease-in forwards';
            
            setTimeout(() => {
                categoryModal.style.display = 'none';
                categoryModal.classList.remove('show');
            }, 200);
        }
    });
    
    // Scroll to top when button is clicked
    scrollTopButton.addEventListener('click', function() {
        smoothScrollToTop();
    });
    
    // Show a daily fact when page loads with delay for better UX
    setTimeout(() => {
        fetch('/daily-fact')
            .then(response => response.json())
            .then(data => {
                showDailyFact(data.fact);
            })
            .catch(error => {
                console.error('Error fetching daily fact:', error);
            });
    }, 2000);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Focus on input field when pressing / key
        if (e.key === '/' && document.activeElement !== userMessageInput) {
            e.preventDefault();
            userMessageInput.focus();
        }
        
        // Escape key closes modal
        if (e.key === 'Escape' && categoryModal.style.display === 'flex') {
            closeModal.click();
        }
    });
    
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
                        
                        // Smooth scroll to top first
                        smoothScrollToTop();
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
    
    // Focus on input field when page loads
    userMessageInput.focus();
    
    // Send welcome message after a short delay
    setTimeout(() => {
        addMessage('السلام علیکم! میں آپ کی قرآن سے متعلق سوالات کے جوابات دینے کے لیے حاضر ہوں۔ آپ کیا جاننا چاہتے ہیں؟');
    }, 500);
    
    // Add dark mode toggle if supported
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        const darkModeToggle = document.createElement('button');
        darkModeToggle.id = 'dark-mode-toggle';
        darkModeToggle.className = 'dark-mode-btn';
        darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        darkModeToggle.title = 'ڈارک موڈ ٹوگل کریں';
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            if (document.body.classList.contains('dark-mode')) {
                this.innerHTML = '<i class="fas fa-sun"></i>';
                this.title = 'لائٹ موڈ ٹوگل کریں';
            } else {
                this.innerHTML = '<i class="fas fa-moon"></i>';
                this.title = 'ڈارک موڈ ٹوگل کریں';
            }
        });
        document.body.appendChild(darkModeToggle);
    }
});