/*
Background script
*/
import "regenerator-runtime/runtime.js";

function executeContentScript(tabId, tabInfo) {
    if (tabInfo.type == 'HTML') {
        chrome.scripting.executeScript(
            {
                target: { tabId: tabId },
                files: ['content.js']
            }, function () {
                chrome.tabs.sendMessage(tabId, { type: 'run', tabInfo: tabInfo })
            });
    }
    else if (tabInfo.type == 'PDF') {
        chrome.tabs.create({ url: 'pdf.html' }, function (tab) {
            chrome.tabs.onUpdated.addListener(function checkPDFTab(tabId, changeInfo) {
                if (tabId === tab.id && changeInfo.status === 'complete') {
                    chrome.tabs.sendMessage(tabId, { type: 'run', tabInfo: tabInfo });
                    chrome.tabs.onUpdated.removeListener(checkPDFTab);
                };
            });
        })
    }
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    // Tells popup if tab is a chrome tab.
    if (message.type == 'popup_request_tabType') {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs[0].url.startsWith('chrome://')) {
                sendResponse({ tabType: 'chrome' });
            }
        })
    }
    // If popup requests to find terms in current tab, run script to determine
    // if tab is a web page or PDF.
    else if (message.type == 'popup_request_run_in_tab') {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            chrome.scripting.executeScript(
                {
                    target: { tabId: tabs[0].id },
                    files: ['getTabInfo.js']
                });
        })
    }
    // Injects content.js if the tab is a web page or runs in a new tab if it's
    // a PDF.
    else if (message.type == 'getTabInfo_send_tabInfo') {
        executeContentScript(sender.tab.id, message.tabInfo);
    }
    // Handles watchlist updates.
    else if (message.type == 'updateWatchlist_to_background') {
        chrome.tabs.query({}, function (tabs) {
            tabs.forEach(tab => {
                if (sender.tab.id != tab.id) {
                    message.type = 'updateWatchlist_to_content'
                    chrome.tabs.sendMessage(tab.id, message);
                }
            });
        });
    }
    // Handles request from popup to run uploaded PDF (runs in new tab).
    else if (message.type == 'popup_request_run_on_file') {
        if (message.fileType == 'PDF') {
            let tabInfo = { type: 'PDF', url: null, title: message.fileName, serializedFile: message.serializedFile }
            executeContentScript(null, tabInfo)
        }
    }
    return true;
});

