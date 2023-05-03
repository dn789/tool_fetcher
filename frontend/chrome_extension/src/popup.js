import React from 'react';
import { useState, useEffect } from 'react'
import { render } from "react-dom";
import './popup.css';

function Popup() {
    const [darkTheme, setDarkTheme] = useState(false);
    const [logoOnly, setLogoOnly] = useState(false);
    const [refresh, setRefresh] = useState(false);
    const [tabIsProcessedPDF, setTabIsProcessedPDF] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [defaultSideBarLeft, setDefaultSideBarLeft] = useState(true);


    useEffect(() => {
        chrome.storage.local.get({ 'darkTheme': false, 'defaultSideBarLeft': true }, (result) => {
            if (result.darkTheme) {
                setDarkTheme(true);
                document.documentElement.setAttribute('data-theme', 'dark');
            }
            if (!result.defaultSideBarLeft) {
                setDefaultSideBarLeft(false);
            }
        });
        chrome.runtime.sendMessage({ type: 'popup_request_tabType' }, function (response) {
            response = response || {};
            if (response == 'chrome') {
                setLogoOnly(true);
            }
        });
        chrome.storage.onChanged.addListener(changes => {
            if (changes.darkTheme) {
                setDarkTheme(changes.darkTheme.newValue);
            }
        });
    }, [])

    useEffect(() => {
        chrome.storage.local.set({ 'defaultSideBarLeft': defaultSideBarLeft });
    }, [defaultSideBarLeft])

    function darkThemeHandle() {
        let newValue = !darkTheme;
        setDarkTheme(newValue);
        chrome.storage.local.set({ darkTheme: newValue });
        document.documentElement.setAttribute('data-theme', newValue ? 'dark' : '');

    }


    chrome.runtime.onMessage.addListener(function (message) {
        if (message.type == 'content_send_tabType') {
            if (message.tabType == 'HTML') {
                // If extension has already been run on tab, displays notification that tab 
                // will refresh if automatically if extension is run again. 
                setRefresh(true);
            }
            else if (message.tabType == 'PDF') {
                // If tab is a PDF highlighted by the extension, 'Find terms' 
                // button is removed. 
                setTabIsProcessedPDF(true);
            }
        }
    });


    function runInTab() {
        chrome.tabs.query({ active: true, currentWindow: true }, function () {
            chrome.runtime.sendMessage({ type: 'popup_request_run_in_tab', refresh: refresh });
        });
        // Closing popup stops extension from running in Linux. 
        // window.close();
    }

    function handleUpload(e) {
        let fileName = e.target.value.split("\\").pop();
        let fileURL = URL.createObjectURL(e.target.files[0]);
        if (fileName.endsWith('.pdf')) {
            setSelectedFile({ name: fileName, url: fileURL });
        }
    }

    function submitFile() {
        chrome.runtime.sendMessage({ type: 'popup_request_run_on_file', fileType: 'PDF', url: selectedFile.url });
        document.write('')
    }

    const logoImage = darkTheme ? "images/logo_white_text.svg" : "images/logo.svg";
    const themeToggleImage = "images/theme_icon.svg";
    const sideBarLeftImage = defaultSideBarLeft ? 'images/panel_left_icon.svg' : 'images/panel_right_icon.svg'



    return (
        <div>
            <div id="logo"><img src={logoImage} /></div>
            <div id='icons'>
                <div
                    className="svg-icon"
                    onClick={darkThemeHandle}
                    title="Toggle dark mode">
                    <img src={themeToggleImage}></img>
                </div>
                <div
                    className="svg-icon"
                    onClick={() => { setDefaultSideBarLeft(!defaultSideBarLeft) }}
                    title="Toggle default side panel position">
                    <img src={sideBarLeftImage}></img>
                </div>
            </div>
            <div
                id="content"
                style={{ display: logoOnly ? 'none' : '' }}>
                <div className='notification'
                    style={{ display: tabIsProcessedPDF ? '' : 'none' }}>
                    Select original PDF<br /> to run again.
                </div>
                <button
                    className="reg-button"
                    onClick={runInTab}
                    style={{ display: tabIsProcessedPDF ? 'none' : '' }}>
                    {!refresh ? 'Find on page' : 'Run again'}
                </button>
                <label
                    for="upload-button"
                    className={'input-label' + (selectedFile ? ' file-selected' : ' no-file-selected')} >
                    {!selectedFile ? "Upload file" : selectedFile.name}
                    <form
                        enctype="multipart/form-data"
                        method="POST"
                        id="upload-form"
                        className='hidden'>
                        <input
                            type="file"
                            id="upload-button"
                            className="hidden"
                            onChange={(e) => handleUpload(e)}
                            accept=".pdf" />
                    </form>
                </label>
                <button
                    type="button"
                    className="reg-button"
                    onClick={submitFile}
                    style={{ display: selectedFile ? "block" : "none" }}>
                    Find in file
                </button>
            </div>
        </div >
    );
}

render(<Popup />, document.getElementById('root'));