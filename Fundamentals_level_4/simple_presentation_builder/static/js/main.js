/**
 * Main JavaScript for AI Presentation Builder
 *
 * This file handles:
 * - File uploads (drag & drop, file selection)
 * - Chat message sending and receiving
 * - Server-Sent Events (SSE) for real-time streaming
 * - UI updates and animations
 */

// Global variable to track selected files
let selectedFiles = [];

/**
 * FILE UPLOAD FUNCTIONALITY
 * These functions handle image uploads for brand analysis
 */

/**
 * Handle file selection from the file input
 * @param {Event} event - The change event from file input
 */
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    selectedFiles = files;
    displayFileList();
}

/**
 * Display the list of selected files in the UI
 * Shows file names with remove buttons
 */
function displayFileList() {
    const fileList = document.getElementById('file-list');

    // If no files, hide the list
    if (selectedFiles.length === 0) {
        fileList.classList.add('hidden');
        return;
    }

    // Show file list with remove buttons
    fileList.classList.remove('hidden');
    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-gray-200">
            <span class="text-sm text-gray-700 flex items-center gap-2">
                <i data-lucide="file-image" class="w-4 h-4 text-gray-500"></i>
                <span>${file.name}</span>
                <span class="text-xs text-gray-500">(${(file.size / 1024).toFixed(1)} KB)</span>
            </span>
            <button
                type="button"
                onclick="removeFile(${index})"
                class="text-red-500 hover:text-red-700 transition-colors"
            >
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>
    `).join('');

    // Reinitialize Lucide icons for the new file list
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Remove a file from the selected files array
 * @param {number} index - Index of file to remove
 */
function removeFile(index) {
    selectedFiles.splice(index, 1);
    displayFileList();
}

/**
 * CHAT MESSAGE DISPLAY
 * Functions for adding messages to the chat interface
 */

/**
 * Add a message to the chat
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - The message text
 * @param {number} imageCount - Number of images attached (optional)
 */
function addMessage(role, content, imageCount = 0) {
    const messages = document.getElementById('messages');
    const welcome = document.getElementById('welcome');

    // Hide welcome message after first user message
    if (role === 'user' && welcome) {
        welcome.style.display = 'none';
    }

    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;

    // Style based on role (user vs assistant)
    const bgColor = role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200';
    const textColor = role === 'user' ? 'text-white' : 'text-gray-900';

    // Show image indicator if files were attached
    let imageIndicator = '';
    if (imageCount > 0) {
        imageIndicator = `
            <div class="flex items-center gap-1 text-xs opacity-75 mb-2">
                <i data-lucide="paperclip" class="w-3 h-3"></i>
                <span>${imageCount} image${imageCount > 1 ? 's' : ''} attached</span>
            </div>`;
    }

    messageDiv.innerHTML = `
        <div class="max-w-3xl px-4 py-3 rounded-2xl ${bgColor} shadow-sm">
            ${imageIndicator}
            <div class="${textColor} whitespace-pre-wrap">${escapeHtml(content)}</div>
        </div>
    `;

    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;

    // Reinitialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * PROGRESS INDICATOR
 * Functions for showing real-time progress during AI processing
 */

/**
 * Show the progress panel with animated loading dots
 * This appears while waiting for AI responses
 */
function showProgress() {
    const messages = document.getElementById('messages');
    const progressDiv = document.createElement('div');
    progressDiv.id = 'progress-indicator';
    progressDiv.className = 'chat-message flex justify-start';
    progressDiv.innerHTML = `
        <div class="max-w-4xl w-full px-6 py-4 rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 shadow-sm">
            <div class="flex items-center gap-3 mb-3">
                <div class="loading-dots flex gap-1">
                    <span class="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span class="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span class="w-2 h-2 bg-indigo-500 rounded-full"></span>
                </div>
                <span class="text-indigo-900 font-semibold">AI is working...</span>
            </div>
            <div id="progress-log" class="space-y-2 max-h-96 overflow-y-auto">
                <!-- Progress updates will appear here -->
            </div>
        </div>
    `;
    messages.appendChild(progressDiv);
    messages.scrollTop = messages.scrollHeight;

    // Reinitialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Add a progress update to the progress log
 * @param {string} message - The progress message
 * @param {string} icon - Emoji icon to display
 * @param {string} type - 'info', 'success', 'warning', or 'error'
 */
function addProgressUpdate(message, icon = '🔄', type = 'info') {
    const progressLog = document.getElementById('progress-log');
    if (!progressLog) return;

    // Color schemes for different update types
    const colors = {
        'info': 'bg-blue-100 text-blue-800 border-blue-200',
        'success': 'bg-green-100 text-green-800 border-green-200',
        'warning': 'bg-yellow-100 text-yellow-800 border-yellow-200',
        'error': 'bg-red-100 text-red-800 border-red-200'
    };

    const updateDiv = document.createElement('div');
    updateDiv.className = `p-2 rounded-lg border ${colors[type] || colors.info} text-sm fade-in`;
    updateDiv.innerHTML = `
        <div class="flex items-start gap-2">
            <span class="text-base">${icon}</span>
            <span class="flex-1">${escapeHtml(message)}</span>
        </div>
    `;

    progressLog.appendChild(updateDiv);

    // Auto-scroll to bottom
    progressLog.scrollTop = progressLog.scrollHeight;

    // Also scroll main messages container
    const messages = document.getElementById('messages');
    messages.scrollTop = messages.scrollHeight;
}

/**
 * Hide and remove the progress indicator
 */
function hideProgress() {
    const progress = document.getElementById('progress-indicator');
    if (progress) {
        progress.remove();
    }
}

/**
 * MESSAGE SENDING WITH SERVER-SENT EVENTS (SSE)
 * This is the core function that handles communication with the Flask backend
 */

/**
 * Send a message to the AI and stream the response
 * Uses Server-Sent Events for real-time updates
 * @param {Event} event - The form submit event
 */
async function sendMessage(event) {
    console.log('sendMessage called');
    event.preventDefault();

    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const fileInput = document.getElementById('file-input');
    const message = messageInput.value.trim();

    if (!message) {
        console.log('Empty message, returning');
        return;
    }

    console.log('Sending message:', message);

    // Disable form while processing
    messageInput.disabled = true;
    sendButton.disabled = true;

    // Add user message to chat
    console.log('Adding user message to chat');
    addMessage('user', message, selectedFiles.length);

    // Show progress panel
    console.log('Showing progress panel');
    showProgress();

    // Prepare form data (text + files)
    const formData = new FormData();
    formData.append('message', message);

    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });

    console.log('Files attached:', selectedFiles.length);

    try {
        // Send request to Flask backend
        console.log('Sending request to /api/chat/stream');
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            body: formData
        });

        console.log('Response received, status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Set up SSE reader
        // Server-Sent Events allow the server to push updates to the client
        console.log('Setting up SSE reader...');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // Read the stream
        while (true) {
            const {value, done} = await reader.read();

            if (done) {
                console.log('Stream reading complete');
                break;
            }

            // Decode the chunk
            buffer += decoder.decode(value, {stream: true});

            // Process complete lines (SSE format is line-based)
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                // SSE data lines start with "data: "
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        handleStreamEvent(data);
                    } catch (e) {
                        console.error('Error parsing SSE data:', e, line);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error in sendMessage:', error);
        hideProgress();
        addMessage('assistant', `Error: ${error.message}`);
    } finally {
        // Reset form
        messageInput.value = '';
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();

        // Clear files
        selectedFiles = [];
        if (fileInput) {
            fileInput.value = '';
        }
        displayFileList();
    }
}

/**
 * EVENT STREAM HANDLING
 * Process events received from the server via SSE
 */

/**
 * Handle a single stream event from the backend
 * Maps event types to user-friendly progress messages
 * @param {Object} event - Event object with {event, data}
 */
function handleStreamEvent(event) {
    const eventType = event.event;
    const data = event.data;

    console.log('Stream event:', eventType, data);

    // Map different event types to UI updates
    switch(eventType) {
        case 'generate_ppt_started':
            addProgressUpdate(data.message, '🚀', 'info');
            break;

        case 'agent_started':
            addProgressUpdate(data.message, '🤖', 'info');
            break;

        case 'iteration':
            addProgressUpdate(`Processing iteration ${data.iteration}...`, '🔄', 'info');
            break;

        case 'tool_use':
            // Show when the AI is using tools
            const toolIcons = {
                'create_file': '📄',
                'update_file': '✏️',
                'read_file': '📖',
                'list_files': '📋',
                'create_folder': '📁',
                'return_ppt_result': '✅'
            };
            const icon = toolIcons[data.tool] || '🔧';
            const toolName = data.tool.replace('_', ' ').toUpperCase();

            if (data.tool === 'create_file') {
                const fileName = data.input?.file_path?.split('/').pop() || 'file';
                addProgressUpdate(`Creating ${fileName}`, icon, 'info');
            } else {
                addProgressUpdate(`Using tool: ${toolName}`, icon, 'info');
            }
            break;

        case 'tool_result':
            // Only show results for important tools
            if (data.result && data.result.includes('Successfully created')) {
                addProgressUpdate(data.result.split('\n')[0], '✅', 'success');
            }
            break;

        case 'export_started':
            addProgressUpdate(data.message, '📤', 'info');
            break;

        case 'capturing_screenshots':
            addProgressUpdate(`${data.message} (${data.slide_count} slides)`, '📸', 'info');
            break;

        case 'screenshot_captured':
            addProgressUpdate(`Captured slide ${data.slide_number}/${data.total_slides}`, '✅', 'success');
            break;

        case 'creating_pptx':
            addProgressUpdate(data.message, '📊', 'info');
            break;

        case 'pptx_slide_added':
            addProgressUpdate(`Added slide ${data.slide_number}/${data.total_slides} to PPTX`, '➕', 'success');
            break;

        case 'export_complete':
            addProgressUpdate(data.message, '🎉', 'success');
            break;

        case 'complete':
            // AI has finished - hide progress and show response
            hideProgress();
            addMessage('assistant', data.response);

            // Show download section if PPTX is ready
            if (data.has_pptx) {
                const downloadSection = document.getElementById('download-section');
                const downloadFilename = document.getElementById('download-filename');
                downloadSection.classList.remove('hidden');
                if (data.pptx_filename) {
                    downloadFilename.textContent = `Download ${data.pptx_filename}`;
                }
            }
            break;

        case 'error':
            hideProgress();
            addMessage('assistant', `Error: ${data.message}`);
            break;
    }
}

/**
 * UTILITY FUNCTIONS
 */

/**
 * Reset the chat session
 * Clears all messages and starts fresh
 */
async function resetChat() {
    if (!confirm('Start a new conversation? This will clear the current chat.')) {
        return;
    }

    try {
        await fetch('/api/reset', { method: 'POST' });
        location.reload();
    } catch (error) {
        alert('Error resetting chat: ' + error.message);
    }
}

/**
 * Escape HTML to prevent XSS attacks
 * Converts special characters to HTML entities
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * INITIALIZATION
 * Set up drag and drop when DOM is ready
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing app...');

    // Get elements
    const uploadArea = document.getElementById('file-upload-area');
    const fileInput = document.getElementById('file-input');
    const messageInput = document.getElementById('message-input');
    const chatForm = document.getElementById('chat-form');

    // Set up drag and drop if elements exist
    if (uploadArea && fileInput) {
        // Prevent default drag behavior and highlight upload area
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        // Remove highlight when drag leaves the area
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        // Handle file drop
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');

            // Filter to only accept image files
            const files = Array.from(e.dataTransfer.files).filter(file =>
                file.type.startsWith('image/')
            );

            selectedFiles = files;
            displayFileList();
        });
    }

    // Add form submit handler
    if (chatForm) {
        chatForm.addEventListener('submit', sendMessage);
    }

    // Handle Enter key for sending (Shift+Enter for new line)
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                // Enter without Shift - send message
                e.preventDefault();
                if (chatForm) {
                    chatForm.requestSubmit(); // This triggers the form submit event properly
                }
            }
            // Shift+Enter will use default behavior (new line)
        });

        // Auto-resize textarea as user types
        messageInput.addEventListener('input', () => {
            // Reset height to auto to get the correct scrollHeight
            messageInput.style.height = 'auto';

            // Set height based on content, max 5 rows
            const maxHeight = parseInt(getComputedStyle(messageInput).lineHeight) * 5;
            const newHeight = Math.min(messageInput.scrollHeight, maxHeight);
            messageInput.style.height = newHeight + 'px';
        });

        // Focus on input field for better UX
        messageInput.focus();
    }

    console.log('App initialized successfully!');
});