/*
Checks if tab is a PDF or web page.
*/

let PDF;
let url;
let tabURL = window.location.href.split('?')[0];


if (tabURL.endsWith('.pdf')) {
    PDF = true;
    url = tabURL;
}
else {
    let elemTypes = ['iframe', 'embed']
    for (let i = 0; i < elemTypes.length; i++) {
        let elemList = Array.from(document.getElementsByTagName(elemTypes[i]));
        for (let i = 0; i < elemList.length; i++) {
            src_url = elemList[i].src.split('?')[0];
            if (src_url.endsWith('pdf')) {
                PDF = true;
                url = src_url;
                break
            }
        };
    }
}
let tabType = PDF ? 'PDF' : 'HTML';
let titleElement = document.querySelector('title');
let title = titleElement ? titleElement.textContent : url;


chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type == 'getTabInfo') {
        sendResponse({ type: tabType, url: url, title: title })
    }
})
