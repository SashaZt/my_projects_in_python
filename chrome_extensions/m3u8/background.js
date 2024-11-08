chrome.runtime.onInstalled.addListener(() => {
    console.log('M3U8 Request Downloader extension installed.');
});

// Слушатель для всех запросов, чтобы обнаружить файлы с расширением .m3u8
chrome.webRequest.onBeforeRequest.addListener(
    function (details) {
        if (details.url.includes('.m3u8')) {
            console.log('Detected .m3u8 request:', details.url);

            // Инициировать загрузку обнаруженного файла .m3u8
            chrome.downloads.download({
                url: details.url,
                filename: 'playlist.m3u8', // Установить желаемое имя файла
                conflictAction: 'uniquify' // Создать уникальное имя, если такой файл уже существует
            }, (downloadId) => {
                if (chrome.runtime.lastError) {
                    console.error('Error downloading .m3u8 file:', chrome.runtime.lastError);
                } else {
                    console.log('Download started for .m3u8 file, ID:', downloadId);
                }
            });
        }
    },
    { urls: ["<all_urls>"] }
);
