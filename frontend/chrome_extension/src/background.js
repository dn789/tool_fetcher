/*
Background script
*/
import "regenerator-runtime/runtime.js";
import { findTerms } from "./components/utils/utils";
// import { findTerms } from "./components/utils/utils";


function executeContentScript(tabId, tabInfo, findTerms) {
    if (tabInfo.type == 'HTML' || !tabInfo.type || !findTerms) {
        chrome.scripting.executeScript(
            {
                target: { tabId: tabId },
                files: ['content.js']
            }, function () {
                chrome.tabs.sendMessage(tabId, { type: 'run', tabInfo: tabInfo, findTerms: findTerms })
            });
    }
    else if (tabInfo.type == 'PDF') {
        chrome.tabs.create({ url: 'pdf.html' }, function (tab) {
            chrome.tabs.onUpdated.addListener(function checkPDFTab(tabId, changeInfo) {
                if (tabId === tab.id && changeInfo.status === 'complete') {
                    chrome.tabs.sendMessage(tabId, { type: 'run', tabInfo: tabInfo, findTerms: findTerms });
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
            else {
                chrome.tabs.sendMessage(tabs[0].id, { type: 'checkContentScript' }, function (response) {
                    if (response) {
                        sendResponse({ tabType: response.type, errorMessage: response.errorMessage })
                    }
                    chrome.runtime.lastError;
                })
            }
        })
    }
    // If popup requests to find terms in current tab, run script to determine
    // if tab is a web page or PDF.
    else if (message.type == 'popup_request_run_in_tab') {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            chrome.tabs.sendMessage(tabs[0].id, { type: 'checkContentScript' }, function (response) {
                if (response) {
                    if (response.type != 'content_active') {
                        sendResponse({ tabType: response.type, errorMessage: response.errorMessage })
                    }
                    else if (response.type == 'content_active') {
                        chrome.tabs.sendMessage(tabs[0].id, { type: 'getTabInfo' }, (response) => {
                            let tabInfo = response;
                            if (tabInfo.type == 'HTML') {
                                chrome.tabs.sendMessage(tabs[0].id, { type: 'run', tabInfo: tabInfo, findTerms: true })
                            }
                            else if (tabInfo.type == 'PDF') {
                                executeContentScript(tabs[0].id, tabInfo, true)
                            }
                        })
                    }
                }
                else {
                    chrome.scripting.executeScript(
                        {
                            target: { tabId: tabs[0].id },
                            files: ['getTabInfo.js']
                        },
                        () => {
                            chrome.tabs.sendMessage(tabs[0].id, { type: 'getTabInfo' }, (response) => {
                                let tabInfo = response;
                                executeContentScript(tabs[0].id, tabInfo, message.findTerms)
                            })
                        }
                    );
                }
                chrome.runtime.lastError;
            })
        })
    }
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
            executeContentScript(null, tabInfo, true)
        }
    }
    return true;
});

