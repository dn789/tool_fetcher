/*
Checks if tab is a PDF (first by URL, then by source of embeds/iFrames) or 
HTML web page.

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
if (PDF) {
    chrome.runtime.sendMessage({ type: 'checkType_send_tabType', tabType: 'PDF', url: url });
}
else {
    chrome.runtime.sendMessage({ type: 'checkType_send_tabType', tabType: 'HTML' });
}
