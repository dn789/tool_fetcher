import React from "react";
import { useState, useEffect, createContext } from "react";
import { createRef } from "react";
import SidebarResizer from "./SidebarResizer";
import SideBarContent from "./SideBarContent";

const SideBar = ({ termResults, tabType, error, setError }) => {
  const [sideBarOpen, setSideBarOpen] = useState(true);
  const [sideBarLeft, setSideBarLeft] = useState(true);
  const [sideBarWidth, setSideBarWidth] = useState(undefined);
  const [darkTheme, setDarkTheme] = useState(false);
  const [showError, setShowError] = useState(false);

  const sideBarRef = createRef();
  function changeWidth(newWidth) {
    if (newWidth >= 300) {
      setSideBarWidth(newWidth);
      return true;
    } else {
      setSideBarOpen(false);
      return false;
    }
  }

  useEffect(() => {
    if (error) {
      setShowError(true);
    }
  }, [error]);

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
      setSideBarWidth("");
    }
  }, [sideBarOpen]);

  useEffect(() => {
    chrome.storage.local.get(
      { darkTheme: false, defaultSideBarLeft: true },
      (result) => {
        if (!result.defaultSideBarLeft) {
          setSideBarLeft(false);
        }
        if (result.darkTheme) {
          setDarkTheme(true);
        }
      }
    );
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.darkTheme) {
        setDarkTheme(changes.darkTheme.newValue);
      }
    });
  }, []);

  function darkThemeHandle() {
    let newValue = !darkTheme;
    setDarkTheme(newValue);
    chrome.storage.local.set({ darkTheme: newValue });
  }

  const logoImage = darkTheme
    ? "images/logo_white_text.svg"
    : "images/logo.svg";
  const hidePanelImage = sideBarLeft
    ? "images/sidebar_hide_left.svg"
    : "images/sidebar_hide_right.svg";
  const toggleButtonImage = sideBarOpen
    ? hidePanelImage
    : "images/menu_icon.svg";
  const sideBarLocationImage = sideBarLeft
    ? "images/panel_right_icon.svg"
    : "images/panel_left_icon.svg";
  const toggleButtonTitle = sideBarOpen ? "Hide panel" : "Show panel";

  return (
    <div id="sidebar-container">
      <div
        id="sidebar"
        className={!sideBarOpen ? "closed-sidebar" : ""}
        ref={sideBarRef}
        style={{
          left: sideBarLeft && 0,
          right: !sideBarLeft && 0,
          width: !sideBarOpen && "3em",
        }}
        data-theme={darkTheme ? "dark" : ""}
      >
        <SidebarRefContext.Provider
          value={{
            ref: sideBarRef,
            setError: setError,
          }}
        >
          <div>
            <div
              className="body-icon med-icon"
              style={{ display: sideBarOpen && "none" }}
              onClick={() => setSideBarOpen(!sideBarOpen)}
              title={toggleButtonTitle}
            >
              <img src={chrome.runtime.getURL(toggleButtonImage)}></img>
            </div>
          </div>
          <div id="sidebar-content">
            {sideBarOpen && (
              <SidebarResizer
                parentWidth={sideBarWidth}
                parentLeft={sideBarLeft}
                handle={changeWidth}
                tabType={tabType}
              />
            )}
            <div id="main-icons">
              {error && (
                <div
                  id="error-div-small"
                  style={{ display: !sideBarOpen && "none" }}
                  title={error}
                >
                  ERROR
                </div>
              )}

              <div
                style={{ display: !sideBarOpen && "none" }}
                className="body-icon med-icon"
                onClick={darkThemeHandle}
                title="Toggle dark mode"
              >
                <img src={chrome.runtime.getURL("images/theme_icon.svg")}></img>
              </div>
              <div
                id="sidebar-location-toggle"
                className="body-icon med-icon"
                style={{ display: !sideBarOpen && "none" }}
                onClick={() => setSideBarLeft(!sideBarLeft)}
                title={sideBarLeft ? "Move panel right" : "Move panel left"}
              >
                <img src={chrome.runtime.getURL(sideBarLocationImage)}></img>
              </div>
              <div
                id="sidebar-toggle"
                className="body-icon med-icon"
                style={{ display: !sideBarOpen && "none" }}
                onClick={() => setSideBarOpen(!sideBarOpen)}
                title={toggleButtonTitle}
              >
                <img src={chrome.runtime.getURL(toggleButtonImage)}></img>
              </div>
            </div>
            <div style={{ display: !sideBarOpen && "none" }}>
              <div id="logo">
                <img src={chrome.runtime.getURL(logoImage)}></img>
              </div>
              <div id="main-content-container">
                {error && showError && (
                  <div className="error-container">
                    <div id="error-div" className="confirm-box">
                      {error}
                      <div
                        className="body-icon med-icon upper-right"
                        onClick={() => setShowError(false)}
                      >
                        <img
                          src={chrome.runtime.getURL("./images/close_icon.svg")}
                        />
                      </div>
                    </div>
                  </div>
                )}
                <SideBarContent termResultsFromServer={termResults} />
              </div>
            </div>
          </div>
        </SidebarRefContext.Provider>
      </div>
    </div>
  );
};

export default SideBar;
export const SidebarRefContext = createContext();
