import React from 'react';
import ReactDOM from "react-dom";
import { useState, useEffect } from 'react';
import "regenerator-runtime/runtime.js";
import root from 'react-shadow';
import SideBar from './components/SideBar';
import { findTerms } from './components/utils/utils';
import styles from './sidebar.css'

function InjectSideBar() {
    const [tabInfo, setTabInfo] = useState(null);
    const [results, setResults] = useState(null);
    const [serverResponse, setServerResponse] = useState(false);

    useEffect(() => {
        chrome.runtime.onMessage.addListener(
            function fromBackground(message) {
                if (message.type == 'run') {

                    setTabInfo({ type: message.tabType, url: message.url })
                    chrome.runtime.onMessage.removeListener(fromBackground);
                }
            }
        );
    }, [])

    useEffect(async () => {
        if (tabInfo) {
            chrome.runtime.onMessage.addListener(function sendTabInfo(message) {
                if (message.type == 'background_request_tabType') {
                    chrome.runtime.sendMessage({ type: 'content_send_tabType', tabType: tabInfo.type });
                }
            })
            setResults(await findTerms(tabInfo, 'HTML'));
        }
    }, [tabInfo])

    useEffect(() => {
        if (results) {
            setServerResponse(true);
        }
    }, [results])

    return (
        <root.div>
            <style type="text/css">{styles}</style>
            <SideBar results={results ? results : []} serverResponse={serverResponse} tabType={tabInfo ? tabInfo.type : null} />
        </root.div>
    );
}

ReactDOM.render(
    <React.StrictMode>
        <InjectSideBar />
    </React.StrictMode>,
    document.body.appendChild(document.createElement("DIV"))
);





