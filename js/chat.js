const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const chatWindow = document.getElementById('chat-window');

// функция для отрисовки сообщения пользователя в чате
function addMessageToUI(text, type = 'sent') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = text;

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-time');
    
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    timeDiv.textContent = currentTime;

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    chatWindow.appendChild(messageDiv);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// функция для создания json, в который оборачиваем сообщение пользователя
chatForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const text = messageInput.value.trim();

    if (!text) return;

    const messageData = {
        id: Date.now(),       
        text: text,          
        sender: 'user',       
        timestamp: new Date().toISOString()
    };

    const jsonString = JSON.stringify(messageData);
    
    console.log('Отправляем на сервер JSON:', jsonString);

    addMessageToUI(text, 'sent');

    messageInput.value = '';
    messageInput.focus();
});

