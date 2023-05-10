import React from 'react';
import ReactDOM from "react-dom";
import { useState, useEffect } from 'react';
import "regenerator-runtime/runtime.js";
import root from 'react-shadow';
import SideBar from './components/SideBar';
import { findTerms } from './components/utils/utils';
import styles from './sidebar.css'

function InjectSideBar() {
    const [tabInfo, setTabInfo] = useState({ type: null, title: null, url: null });
    const [results, setResults] = useState(null);
    const [serverResponse, setServerResponse] = useState(false);

    useEffect(() => {
        chrome.runtime.onMessage.addListener(
            async function fromBackground(message) {
                if (message.type == 'run') {
                    setTabInfo(message.tabInfo);
                    setResults(await findTerms(message.tabInfo.url, message.tabInfo.type, message.tabInfo.serializedFile));
                    chrome.runtime.onMessage.removeListener(fromBackground);
                }
            }
        );
    }, [])


    useEffect(() => {
        if (results) {
            setServerResponse(true);
            if (tabInfo.type == 'PDF') {
                document.title = tabInfo.title || 'ToolFetcher - PDF';
            }
        }
    }, [results])

    return (
        <root.div>
            <style type="text/css">{styles}</style>
            <SideBar results={results ? results : []} serverResponse={serverResponse} tabType={tabInfo.type} />
        </root.div>
    );
}

ReactDOM.render(
    <React.StrictMode>
        <InjectSideBar />
    </React.StrictMode>,
    document.body.appendChild(document.createElement("DIV"))
);





