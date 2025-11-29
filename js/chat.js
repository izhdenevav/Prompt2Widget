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

    const adding_prompt = 'Представь, что ты программист, умеющий создавать виджеты в виде html-кода. Я хочу, чтобы css был написан внутри блока <style></> html-кода, а не отдельным файлом. То же самое с js-кодом. Создай виджет по следующему описанию:';
    const full_query = `${adding_prompt} ${text}`;

    const messageData = {
        session: SESSION_ID,
        text: full_query,
        timestamp: new Date().toISOString()
    };

    const jsonString = JSON.stringify(messageData);
    
    console.log('Отправляем на сервер JSON:', jsonString);

    addMessageToUI(text, 'sent');

    messageInput.value = '';
    messageInput.focus();

    fetch(`http://127.0.0.1:8000/gigachat?query=${encodeURIComponent(text)}&session_id=${SESSION_ID}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const botText = data.response || "Получил пустой ответ от сервера";

            addBotMessage(JSON.stringify({ text: botText }));
        })
        .catch(err => {
            console.error("Ошибка при запросе к серверу:", err);
            addBotMessage(JSON.stringify({ 
                text: "⚠️ Не могу связаться с сервером. Проверь, запущен ли FastAPI на порту 8000." 
            }));
        });
});

function markdownToHtml(text) {
    if (!text) return text;

    const codeBlocks = [];
    let id = 0;

    let processed = text.replace(/```(?:([a-zA-Z0-9+-]+)\n)?([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang ? lang.trim().toLowerCase() : 'plaintext';
        const cleanCode = code.trim();
        const placeholder = `%%%CODEBLOCK_${id++}%%%`;
        codeBlocks.push({ placeholder, language, cleanCode });
        return placeholder;
    });

    processed = processed.replace(/^#{1,6}\s+(.*$)/gm, (match, content) => {
        const level = match.trim().indexOf(' ');
        return `<h${level}>${content}</h${level}>`;
    });

    processed = processed.replace(/^\s*[\*+-]\s+(.*$)/gm, '<ul><li>$1</li></ul>');
    processed = processed.replace(/<\/ul>\s*<ul>/g, ''); 
    processed = processed.replace(/^\s*\d+\.\s+(.*$)/gm, '<ol><li>$1</li></ol>');
    processed = processed.replace(/<\/ol>\s*<ol>/g, ''); 

    processed = processed.replace(/(\*\*|__)(.*?)\1/g, '<strong>$2</strong>');
    processed = processed.replace(/(\*|_)(.*?)\1/g, '<em>$2</em>');

    processed = processed.replace(/`([^`]+)`/g, (match, code) => {
        return `<code class="inline">${escapeHtml(code)}</code>`;
    });

    processed = processed.split(/\n\n+/).map(block => {
        block = block.trim();
        if (!block) return '';
        if (block.match(/^(<h[1-6]|<ul|<ol|%%%CODEBLOCK_)/)) {
            return block;
        }
        return `<p>${block.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    codeBlocks.forEach(block => {
        const escapedCode = escapeHtml(block.cleanCode);
        let codeHtml;
        
        if (block.language !== 'plaintext') {
            codeHtml = `<pre><code class="language-${block.language} hljs">${escapedCode}</code><div class="code-lang-label">${block.language}</div></pre>`;
        } else {
            codeHtml = `<pre><code class="language-plaintext hljs">${escapedCode}</code></pre>`;
        }
        
        processed = processed.replace(block.placeholder, codeHtml);
    });

    return processed;
}

function escapeHtml(text) {
    if (!text) return text;
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
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