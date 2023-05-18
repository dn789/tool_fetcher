/******/ (function() { // webpackBootstrap
var __webpack_exports__ = {};
/*!***************************!*\
  !*** ./src/getTabInfo.js ***!
  \***************************/
/*
Checks if tab is a PDF or web page.
*/
var PDF;
var url;
var tabURL = window.location.href.split('?')[0];

if (tabURL.endsWith('.pdf')) {
  PDF = true;
  url = tabURL;
} else {
  var elemTypes = ['iframe', 'embed'];

  for (var i = 0; i < elemTypes.length; i++) {
    var elemList = Array.from(document.getElementsByTagName(elemTypes[i]));

    for (var _i = 0; _i < elemList.length; _i++) {
      src_url = elemList[_i].src.split('?')[0];

      if (src_url.endsWith('pdf')) {
        PDF = true;
        url = src_url;
        break;
      }
    }

    ;
  }
}

var tabType = PDF ? 'PDF' : 'HTML';
var titleElement = document.querySelector('title');
var title = titleElement ? titleElement.textContent : url;
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
  if (message.type == 'getTabInfo') {
    sendResponse({
      type: tabType,
      url: url,
      title: title
    });
  }
});
/******/ })()
;
//# sourceMappingURL=getTabInfo.js.map