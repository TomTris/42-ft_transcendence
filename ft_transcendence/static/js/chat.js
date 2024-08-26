document.addEventListener('DOMContentLoaded', function() {
    const chatWrapper = document.getElementById('chat-wrapper');
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const toggleButton = document.getElementById('toggle-button');
    const hideButton = document.getElementById('hide-button');

    // Create a WebSocket connection
    const socket = new WebSocket('ws://' + window.location.host + '/wss/chat/');

    // Handle incoming messages
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        chatBox.innerHTML = '';

        if (Array.isArray(data)) {
            data.forEach(function(message) {
                displayMessage(message);
            });
        } else {
            console.error('Unexpected data format:', data);
        }
    };

    // Handle sending a new message
    sendButton.addEventListener('click', function() {
        const messageContent = messageInput.value.trim();
        if (messageContent) {
            socket.send(JSON.stringify({
                'type': 'message',
                'content': messageContent
            }));
            messageInput.value = '';
        }
    });

    // Function to display a message in the chat box
    function displayMessage(message) {
        const messageElement = document.createElement('div');
        const imageElement = document.createElement('img');
        imageElement.src = message.sender.avatar;
        imageElement.style.width = '20px'; // Set desired width
        imageElement.style.height = '20px';

        const contentElement = document.createElement('div');
        contentElement.textContent = `${message.sender.username}: ${message.content}`;

        messageElement.appendChild(imageElement);
        messageElement.appendChild(contentElement);

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }

    // Toggle chat box visibility
    toggleButton.addEventListener('click', function() {
        if (chatWrapper.style.display === 'none') {
            chatWrapper.style.display = 'flex';
            toggleButton.style.display = 'none';
        } else {
            chatWrapper.style.display = 'none';
            toggleButton.style.display = 'block';
        }
    });

    // Hide chat container
    hideButton.addEventListener('click', function() {
        chatWrapper.style.display = 'none';
        toggleButton.style.display = 'block'; // Show the toggle button when chat is hidden
    });
});