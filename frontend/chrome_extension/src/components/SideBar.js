import React from 'react';
import { useState, useEffect } from 'react';
import TermResultsPanel from '../components/panels/TermResultsPanel';
import { createRef } from 'react';
import SidebarResizer from './SidebarResizer';
import MainContent from './MainContent';

const SideBar = ({ results, serverResponse, tabType }) => {
    const [sideBarOpen, setSideBarOpen] = useState(true);
    const [sideBarLeft, setSideBarLeft] = useState(true);
    const [sideBarWidth, setSideBarWidth] = useState(undefined);
    const [darkTheme, setDarkTheme] = useState(false);

    const sideBarRef = createRef();
    function changeWidth(newWidth) {
        if (newWidth >= 300) {
            setSideBarWidth(newWidth);
            return true;
        }
        else {
            setSideBarOpen(false);
            return false;
        }
    }

    useEffect(() => {
        if (sideBarRef.current) {
            if (!sideBarWidth) {
                setSideBarWidth(sideBarRef.current?.clientWidth);
                return;
            }
            sideBarRef.current.style.width = `${sideBarWidth}px`;
        }
    }, [sideBarWidth]);

    useEffect(() => {
        if (sideBarOpen) {
            setSideBarWidth(400);
        }
    }, [sideBarOpen]);

    useEffect(() => {
        chrome.storage.local.get({ 'darkTheme': false, 'defaultSideBarLeft': true }, (result) => {
            if (!result.defaultSideBarLeft) {
                setSideBarLeft(false);
            }
            if (result.darkTheme) {
                setDarkTheme(true);
            }
        });
        chrome.storage.onChanged.addListener(changes => {
            if (changes.darkTheme) {
                setDarkTheme(changes.darkTheme.newValue);
            }
        });
    }, [])

    function darkThemeHandle() {
        let newValue = !darkTheme;
        setDarkTheme(newValue);
        chrome.storage.local.set({ darkTheme: newValue });
    }

    const logoImage = darkTheme ? "images/logo_white_text.svg" : "images/logo.svg";
    const toggleButtonImage = sideBarOpen ? "images/close_icon.svg" : "images/menu_icon.svg";
    const sideBarLocationImage = sideBarLeft ? "images/panel_right_icon.svg" : "images/panel_left_icon.svg"
    const toggleButtonTitle = sideBarOpen ? "Hide panel" : "Show panel";

    return (
        <div id="sidebar-container">
            <div id="sidebar"
                ref={sideBarRef}
                style={{
                    left: sideBarLeft && 0,
                    right: !sideBarLeft && 0,
                    width: !sideBarOpen && '50px'
                }}
                data-theme={darkTheme ? 'dark' : ''}>
                <div id='sidebar-content'>
                    {sideBarOpen && <SidebarResizer parentWidth={sideBarWidth} parentLeft={sideBarLeft} handle={changeWidth} tabType={tabType} />}
                    <div id="icons">
                        <div id="theme-toggle"
                            className="sidebar-icon"
                            onClick={darkThemeHandle}
                            style={{ display: !sideBarOpen && 'none' }}
                            title="Toggle dark mode">
                            <img src={chrome.runtime.getURL('images/theme_icon.svg')}></img>
                        </div>
                        <div id="sidebar-location-toggle"
                            className="sidebar-icon"
                            onClick={() => setSideBarLeft(!sideBarLeft)}
                            style={{ display: !sideBarOpen && 'none' }}
                            title={sideBarLeft ? "Move panel right" : "Move panel left"}>
                            <img src={chrome.runtime.getURL(sideBarLocationImage)}></img>
                        </div>
                        <div id="sidebar-toggle"
                            className="sidebar-icon"
                            onClick={() => setSideBarOpen(!sideBarOpen)}
                            title={toggleButtonTitle}>
                            <img src={chrome.runtime.getURL(toggleButtonImage)}></img>
                        </div>
                    </div>
                    <div style={{ display: !sideBarOpen && 'none' }}>
                        <div id="logo" >
                            <img src={chrome.runtime.getURL(logoImage)}></img>
                        </div>
                        < div className='status-div' style={{ display: (results.length && serverResponse) && 'none' }} >
                            <div id='loading-div' style={{ display: serverResponse && 'none' }} >
                                <img src={chrome.runtime.getURL("images/loading.gif")}></img>
                                Working...
                            </div>
                            <div style={{ display: (results.length || !serverResponse) && 'none' }}>
                                No results.
                            </div>
                        </div>
                        <div id='results-panel-container' style={{ display: (!results.length || !serverResponse) && 'none' }}>
                            <MainContent termResults={results ? results : []} />
                        </div>
                    </div>
                </div>
            </div >
        </div >

    )
}

export default SideBar
