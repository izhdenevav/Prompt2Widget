// получаем элементы: поле для ввода кода и iframe для предпросмотра
const textarea = document.getElementById('html-code');
const iframe = document.getElementById('preview-frame');

let timeoutId;  // идентификатор таймера для дебаунса

// обновляет содержимое iframe на основе текста из textarea
function updatePreview() {
    const code = textarea.value;
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    
    doc.open();
    doc.write(code);
    doc.close();
}

// реагируем на любое изменение в поле ввода
textarea.addEventListener('input', () => {
    clearTimeout(timeoutId);  // сбрасываем предыдущий таймер

    // ждём 500 мс после последнего ввода, чтобы не обновлять слишком часто
    timeoutId = setTimeout(() => {
        updatePreview();
    }, 500);
});

// дефолтный код, который показывается при загрузке страницы
const defaultCode = `<!DOCTYPE html>
<style>
  body { 
      font-family: sans-serif; 
     32      padding: 20px; 
      color: #333; 
      display: flex; 
      flex-direction: column; 
      align-items: center; 
      justify-content: center; 
      height: 100vh;
      background-color: #f9f9f9; /* Светлый фон чтобы не было белых вспышек */
  }
  h1 { color: #0b57d0; margin-bottom: 10px; }
  p { margin-bottom: 20px; }
  button { 
      padding: 10px 20px; 
      background: #0b57d0; 
      color: white; 
      border: none; 
      border-radius: 20px; 
      cursor: pointer; 
      font-size: 16px;
  }
  button:hover { opacity: 0.9; }
</style>

<h1>Привет!</h1>
<p>Введи код, который Я тебе отправил.</p>
<button onclick="alert('JS тоже работает!')">Нажми меня</button>`;

// вставляем дефолтный код в поле ввода
textarea.value = defaultCode;

// сразу показываем предпросмотр при загрузке страницы
updatePreview();