// генерирует уникальный идентификатор сессии через встроенный крипто-API браузера
function generateUUID() {
    return crypto.randomUUID();
}

// определяет или создаёт session_id для текущего пользователя
function getSessionId() {
    let sessionId = localStorage.getItem('chat_session_id');
   
    // если уже есть в localStorage — используем его
    if (sessionId) {
        return sessionId;
    }
    
    // проверяем, передан ли session в URL (?session=...)
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session');
    if (sessionId) {
        // сохраняем, чтобы не потерять при перезагрузке
        localStorage.setItem('chat_session_id', sessionId);
        return sessionId;
    }
    
    // если нигде нет — создаём новый UUID
    sessionId = generateUUID();
    // сохраняем в localStorage
    localStorage.setItem('chat_session_id', sessionId);     
    
    // добавляем session_id в URL без перезагрузки страницы (чтобы можно было делиться ссылкой)
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('session', sessionId);
    window.history.pushState({}, '', newUrl);
    
    return sessionId;
}

// экспортируем готовый ID сессии — он будет один на всю загрузку страницы
export const SESSION_ID = getSessionId();

// выводим в консоль для удобной отладки и шаринга сессии
console.log('Твоя сессия:', SESSION_ID);