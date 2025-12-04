// Flask app JavaScript

// Tab switching
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active', 'border-emerald-500', 'text-emerald-500');
        button.classList.add('border-transparent', 'text-slate-400');
    });
    
    // Show selected tab content
    const content = document.getElementById(`content-${tabName}`);
    if (content) {
        content.classList.remove('hidden');
    }
    
    // Activate selected tab button
    const button = document.getElementById(`tab-${tabName}`);
    if (button) {
        button.classList.add('active', 'border-emerald-500', 'text-emerald-500');
        button.classList.remove('border-transparent', 'text-slate-400');
    }
}

// Chat sidebar toggle
function toggleChat() {
    const sidebar = document.getElementById('chatSidebar');
    const toggle = document.getElementById('chatToggle');
    
    if (sidebar.classList.contains('hidden')) {
        sidebar.classList.remove('hidden');
        toggle.classList.add('bg-emerald-600', 'text-white');
        toggle.classList.remove('bg-slate-800', 'text-slate-400');
    } else {
        sidebar.classList.add('hidden');
        toggle.classList.remove('bg-emerald-600', 'text-white');
        toggle.classList.add('bg-slate-800', 'text-slate-400');
    }
}

// Reset app
function resetApp() {
    fetch('/reset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error resetting app');
    });
}

// Input form submission
const inputForm = document.getElementById('inputForm');
if (inputForm) {
    inputForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitButton = inputForm.querySelector('button[type="submit"]');
        const submitText = document.getElementById('submitText');
        const submitLoading = document.getElementById('submitLoading');
        const errorMessage = document.getElementById('errorMessage');
        
        // Disable form
        submitButton.disabled = true;
        submitText.classList.add('hidden');
        submitLoading.classList.remove('hidden');
        errorMessage.classList.add('hidden');
        
        // Get form data
        const formData = {
            trading_date: inputForm.trading_date.value,
            tickers: inputForm.tickers.value,
            market_json: inputForm.market_json.value,
            news_json: inputForm.news_json.value,
            macro_context: inputForm.macro_context.value,
            constraints: inputForm.constraints.value
        };
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = data.redirect || '/';
            } else {
                errorMessage.textContent = data.error || 'An error occurred';
                errorMessage.classList.remove('hidden');
                submitButton.disabled = false;
                submitText.classList.remove('hidden');
                submitLoading.classList.add('hidden');
            }
        } catch (error) {
            errorMessage.textContent = 'Network error: ' + error.message;
            errorMessage.classList.remove('hidden');
            submitButton.disabled = false;
            submitText.classList.remove('hidden');
            submitLoading.classList.add('hidden');
        }
    });
}

// Chat form submission
const chatForm = document.getElementById('chatForm');
if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const chatInput = document.getElementById('chatInput');
        const chatMessages = document.getElementById('chatMessages');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Add user message to UI
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'flex justify-end';
        userMsgDiv.innerHTML = `
            <div class="bg-emerald-600 text-white rounded-lg px-4 py-2 max-w-xs">
                <p class="text-sm">${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(userMsgDiv);
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Show loading
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'flex justify-start';
        loadingDiv.innerHTML = `
            <div class="bg-slate-800 text-slate-200 rounded-lg px-4 py-2 max-w-xs">
                <div class="spinner"></div>
                <span class="text-sm">Thinking...</span>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // Remove loading
            loadingDiv.remove();
            
            if (data.success) {
                // Add bot response
                const botMsgDiv = document.createElement('div');
                botMsgDiv.className = 'flex justify-start';
                botMsgDiv.innerHTML = `
                    <div class="bg-slate-800 text-slate-200 rounded-lg px-4 py-2 max-w-xs">
                        <p class="text-sm whitespace-pre-wrap">${escapeHtml(data.response)}</p>
                    </div>
                `;
                chatMessages.appendChild(botMsgDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'flex justify-start';
                errorDiv.innerHTML = `
                    <div class="bg-red-900/20 border border-red-800 text-red-200 rounded-lg px-4 py-2 max-w-xs">
                        <p class="text-sm">Error: ${escapeHtml(data.error)}</p>
                    </div>
                `;
                chatMessages.appendChild(errorDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } catch (error) {
            loadingDiv.remove();
            const errorDiv = document.createElement('div');
            errorDiv.className = 'flex justify-start';
            errorDiv.innerHTML = `
                <div class="bg-red-900/20 border border-red-800 text-red-200 rounded-lg px-4 py-2 max-w-xs">
                    <p class="text-sm">Network error: ${escapeHtml(error.message)}</p>
                </div>
            `;
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Markdown rendering (simple version)
function renderMarkdown(markdown) {
    // Simple markdown to HTML conversion
    return markdown
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

