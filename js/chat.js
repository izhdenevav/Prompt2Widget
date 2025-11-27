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
    botIcon.style.marginTop = '7px';

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'received');

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    // Вот здесь происходит волшебство — превращаем markdown в красивый HTML
    contentDiv.innerHTML = markdownToHtml(text);

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-time');
    timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    messageRow.appendChild(botIcon);
    messageRow.appendChild(messageDiv);

    chatWindow.appendChild(messageRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Подсвечиваем код после вставки
    contentDiv.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
        addCopyButton(block);
    });
}

addBotMessage(JSON.stringify({text: "Привет! Чем могу помочь?"}))

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
        "text": "Привет! Вот пример кода на Python:\n\n```html\n<button>Нажми меня</button>\n```\n\nКрасиво?"
    };

    addBotMessage(JSON.stringify(botResponseText));
});

function markdownToHtml(text) {
    const codeBlocks = [];
    let id = 0;

    const processed = text.replace(/```(?:([a-zA-Z0-9+-]+)\n)?([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang ? lang.trim().toLowerCase() : 'plaintext';
        const cleanCode = code.trim();
        const placeholder = `__CODEBLOCK_${id++}__`;
        codeBlocks.push({ placeholder, language, cleanCode });
        return placeholder;
    });

    let html = processed
        .replace(/\n\n+/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code class="inline">$1</code>');

    codeBlocks.forEach(block => {
        let codeHtml = `<pre><code class="language-${block.language} hljs">${escapeHtml(block.cleanCode)}</code></pre>`;
        if (block.language !== 'plaintext') {
            codeHtml = `<pre><code class="language-${block.language} hljs">${escapeHtml(block.cleanCode)}</code><div class="code-lang-label">${block.language}</div></pre>`;
        }
        html = html.replace(block.placeholder, codeHtml);
    });

    if (!html.startsWith('<pre>')) html = '<p>' + html + '</p>';
    html = html.replace(/<p><\/p>/g, '');

    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addCopyButton(codeBlock) {
    if (codeBlock.parentElement.querySelector('.code-copy-btn')) return;

    const button = document.createElement('button');
    button.className = 'code-copy-btn';
    button.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
    `;

    button.onclick = async () => {
        try {
            await navigator.clipboard.writeText(codeBlock.textContent);
            button.classList.add('copied');
            setTimeout(() => button.classList.remove('copied'), 2000);
        } catch (err) {
            console.error('Не удалось скопировать');
        }
    };

    codeBlock.parentElement.style.position = 'relative';
    codeBlock.parentElement.appendChild(button);
}