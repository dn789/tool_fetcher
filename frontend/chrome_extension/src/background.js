/*
Background script
*/

function executeContentScript(tabId, tabType, url) {
    if (tabType == 'HTML') {
        chrome.scripting.executeScript(
            {
                target: { tabId: tabId },
                files: ['content.js']
            }, function () {
                chrome.tabs.sendMessage(tabId, { type: 'run', tabType: 'HTML', url: null })
            });
    }
    else if (tabType == 'PDF') {
        chrome.tabs.create({ url: 'pdf.html' }, function (tab) {
            chrome.tabs.onUpdated.addListener(function checkPDFTab(tabId, changeInfo) {
                if (tabId === tab.id && changeInfo.status === 'complete') {
                    chrome.tabs.sendMessage(tabId, { type: 'run', tabType: 'PDF', url: url });
                    chrome.tabs.onUpdated.removeListener(checkPDFTab);
                };
            });
        })
    }
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    // Checks tab status for popup.
    if (message.type == 'popup_request_tabType') {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            // Responds directly if tab is a chrome browser URL...
            if (tabs[0].url.startsWith('chrome://')) {
                sendResponse('chrome');
            }
            // Otherwise, sends message to tab requesting status. If tab is 
            // (1) a web page that's already had the extension run on it or
            // (2) a PDF highlighted by the extension, a content script 
            // present in the tab will send a message to the popup.
            else {
                chrome.tabs.sendMessage(tabs[0].id, { type: 'background_request_tabType', tabId: tabs[0].id });
            }
        })
    }
    // Message from popup to find terms in current tab. If refresh is true 
    // (tab has already had extension run on it), tab will be refreshed before
    // content.js is injected. 
    else if (message.type == 'popup_request_run_in_tab') {
        if (message.refresh) {
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                chrome.tabs.reload(tabs[0].id);
                chrome.tabs.onUpdated.addListener(function checkReload(tabId, changeInfo) {
                    if (tabId === tabs[0].id && changeInfo.status === 'complete') {
                        executeContentScript(tabs[0].id, 'HTML', null);
                        chrome.tabs.onUpdated.removeListener(checkReload);
                    };
                });
            });
        }
        // If refresh is false, checkType.js is injected to determine whether 
        // the tab is a web page or PDF. 
        else {
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                chrome.scripting.executeScript(
                    {
                        target: { tabId: tabs[0].id },
                        files: ['checkType.js']
                    });
            })
        }
    }
    // Injects content.js if the tab is a web page or runs in a new tab if it's a PDF.
    else if (message.type == 'checkType_send_tabType') {
        if (message.tabType == 'HTML') {
            executeContentScript(sender.tab.id, 'HTML', null);
        }
        else if (message.tabType == 'PDF') {
            executeContentScript(null, 'PDF', message.url);

        }
    }
    // Handles request from popup to run file (opens new tab).
    else if (message.type == 'popup_request_run_on_file') {
        if (message.fileType == 'PDF') {
            executeContentScript(null, 'PDF', message.url)
        }
    }
    return true;
});

