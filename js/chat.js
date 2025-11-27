import { SESSION_ID } from '../utils/session.js';

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

function addBotMessage(jsonString) {
    let data;
    try {
        data = JSON.parse(jsonString);
    } catch (e) {
        console.error("Не удалось распарсить JSON:", e);
        return;
    }

    const text = data.text?.trim();
    if (!text) return;

    const messageRow = document.createElement('div');
    messageRow.classList.add('message-row');

    const botIcon = document.createElement('img');
    botIcon.src = 'favicon.png';
    botIcon.alt = 'Bot';
    botIcon.classList.add('msg-icon');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'received');

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = text;

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-time');
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    timeDiv.textContent = currentTime;

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    messageRow.appendChild(botIcon);
    messageRow.appendChild(messageDiv);

    chatWindow.appendChild(messageRow);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// функция для создания json, в который оборачиваем сообщение пользователя
chatForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const text = messageInput.value.trim();

    if (!text) return;

    const messageData = {
        session: SESSION_ID,
        text: text,
        timestamp: new Date().toISOString()
    };

    const jsonString = JSON.stringify(messageData);
    
    console.log('Отправляем на сервер JSON:', jsonString);

    addMessageToUI(text, 'sent');

    messageInput.value = '';
    messageInput.focus();

    // тут будем кидать запрос на сервер, получать ответ в json и парсить
    const botResponseText = {
        text: "вот твой ответ"
    };

    addBotMessage(JSON.stringify(botResponseText));
});

