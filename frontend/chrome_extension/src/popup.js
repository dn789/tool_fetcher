/*
Popup script
*/
import React from 'react';
import { useState, useEffect } from 'react'
import { render } from "react-dom";
import { serializeBlob } from './components/utils/utils';
import './popup.css';
import "regenerator-runtime/runtime.js";

function Popup() {
    const [darkTheme, setDarkTheme] = useState(false);
    const [logoOnly, setLogoOnly] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [defaultSideBarLeft, setDefaultSideBarLeft] = useState(true);


    useEffect(async () => {
        chrome.storage.local.get({ 'darkTheme': false, 'defaultSideBarLeft': true }, (result) => {
            if (result.darkTheme) {
                setDarkTheme(true);
                document.documentElement.setAttribute('data-theme', 'dark');
            }
            if (!result.defaultSideBarLeft) {
                setDefaultSideBarLeft(false);
            }
        });
        chrome.storage.onChanged.addListener(changes => {
            if (changes.darkTheme) {
                setDarkTheme(changes.darkTheme.newValue);
            }
        });
        chrome.runtime.sendMessage({ type: 'popup_request_tabType' }, function (response) {
            if (response.tabType == 'chrome') {
                setLogoOnly(true);
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



    function runInTab() {
        chrome.tabs.query({ active: true, currentWindow: true }, function () {
            chrome.runtime.sendMessage({ type: 'popup_request_run_in_tab' });
        });
        // Closing popup stops extension from running in Linux. 
        // window.close();
    }

    // async function serialize(src) {
    //     const wasBlob = src instanceof Blob;
    //     const blob = wasBlob ? src : await new Response(src).blob();
    //     const reader = new FileReader();
    //     return new Promise(resolve => {
    //         reader.onload = () => resolve([
    //             reader.result,
    //             blob.type,
    //             wasBlob,
    //         ]);
    //         reader.readAsDataURL(blob);
    //     });
    // }
    async function handleUpload(e) {
        let fileName = e.target.value.split("\\").pop();
        let serialized = await serializeBlob(e.target.files[0]);

        if (fileName.endsWith('.pdf')) {
            setSelectedFile({ name: fileName, serialized: serialized });
        }
    }

    function submitFile() {
        chrome.runtime.sendMessage({ type: 'popup_request_run_on_file', fileType: 'PDF', fileName: selectedFile.name, serializedFile: selectedFile.serialized });
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
                    className="body-icon"
                    onClick={darkThemeHandle}
                    title="Toggle dark mode">
                    <img src={themeToggleImage}></img>
                </div>
                <div
                    className="body-icon"
                    onClick={() => { setDefaultSideBarLeft(!defaultSideBarLeft) }}
                    title="Toggle default side panel position">
                    <img src={sideBarLeftImage}></img>
                </div>
            </div>
            <div
                id="content"
                style={{ display: logoOnly ? 'none' : '' }}>
                <button
                    className="reg-button"
                    onClick={runInTab}
                >
                    Find on page
                </button>
                <label
                    htmlFor="upload-button"
                    className={'input-label' + (selectedFile ? ' file-selected' : ' no-file-selected')}
                >
                    {!selectedFile ? "Upload file" : selectedFile.name}
                    <form
                        encType="multipart/form-data"
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