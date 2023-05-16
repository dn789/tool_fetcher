import React from 'react';
import ReactDOM from "react-dom";
import { useState, useEffect, useRef } from 'react';
import "regenerator-runtime/runtime.js";
import root from 'react-shadow';
import SideBar from './components/SideBar';
import { findTerms } from './components/utils/utils';
import styles from './sidebar.css'

function InjectSideBar() {
    const [tabInfo, setTabInfo] = useState({ type: null, title: null, url: null });
    const [termResults, setTermResults] = useState(null);
    const [error, setError] = useState(false);
    const savedTermResults = useRef(termResults);
    const savedError = useRef(error);


    useEffect(() => {
        chrome.runtime.onMessage.addListener(
            async function fromBackground(message, sender, sendResponse) {
                if (message.type == 'run') {
                    if (message.tabInfo) {
                        setTabInfo(message.tabInfo);
                    }
                    if (message.findTerms) {
                        setTermResults('loading')
                        setTermResults(await findTerms(message.tabInfo.url, message.tabInfo.type, message.tabInfo.serializedFile, setErrorWrapper));
                    }
                }
                if (message.type == 'checkContentScript') {
                    if (savedError.current) {
                        sendResponse({ type: 'error', errorMessage: savedError.current })
                    }
                    else if (savedTermResults.current) {
                        sendResponse({ type: 'already_run' });
                    }
                    else {
                        sendResponse({ type: 'content_active' });
                    }
                }
            }
        );
    }, [])

    useEffect(() => {
        if (tabInfo.type == 'PDF') {
            let div = document.createElement('DIV');
            div.id = 'blank-fill'
            document.body.append(div);
        }
    }, [tabInfo])

    useEffect(() => {
        savedTermResults.current = termResults;
        if (termResults) {
            if (tabInfo.type == 'PDF') {
                document.title = tabInfo.title || 'ToolFetcher - PDF';
            }
        }
    }, [termResults])

    useEffect(() => {
        savedError.current = error;
    }, [error])

    const setErrorWrapper = (type) => {
        let message;
        if (type == 'fetch') {
            message = 'ERROR: Can\'t connect to server. Ensure server is running and refresh this page.'
        }
        setError(message);
    }


    return (
        <root.div>
            <style type="text/css">{styles}</style>
            <SideBar termResults={termResults} tabType={tabInfo.type} error={error} setError={setErrorWrapper} />
        </root.div>
    );
}

ReactDOM.render(
    <React.StrictMode>
        <InjectSideBar />
    </React.StrictMode>,
    document.body.appendChild(document.createElement("DIV"))
);

