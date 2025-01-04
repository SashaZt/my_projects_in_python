chrome.runtime.onInstalled.addListener(() => {
  getAndLogCookieValue();
  
  // Устанавливаем интервал для выполнения функции каждые 30 секунд
  setInterval(getAndLogCookieValue, 30000);
});

// Функция для копирования текста в буфер обмена
function copyToClipboard(text) {
  const inputElement = document.createElement('input');
  inputElement.value = text;
  document.body.appendChild(inputElement);
  inputElement.select();
  document.execCommand('copy');
  document.body.removeChild(inputElement);
  console.log("Value copied to clipboard:", text);
}

// Функция для получения значения куки и копирования его в буфер
function getAndLogCookieValue() {
  chrome.cookies.get({ url: "https://www.govets.com/", name: "cf_clearance" }, function(cookie) {
    if (cookie) {
      copyToClipboard(cookie.value);
    } else {
      console.log("Cookie not found or permission denied.");
    }
  });
}
