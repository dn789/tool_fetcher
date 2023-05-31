/*
Popup script
*/
import React from "react";
import { useState, useEffect, useCallback } from "react";
import { render } from "react-dom";
import { serializeBlob } from "./components/utils/utils";
import { debounce } from "lodash";
import "./popup.css";
import "regenerator-runtime/runtime.js";

function Popup() {
  const [darkTheme, setDarkTheme] = useState(false);
  const [logoOnly, setLogoOnly] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [defaultSideBarLeft, setDefaultSideBarLeft] = useState(true);
  const [alreadyRun, setAlreadyRun] = useState(false);
  const [contentActive, setContentActive] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [error, setError] = useState(false);
  const [options, setOptions] = useState({});

  useEffect(async () => {
    chrome.storage.local.get(
      {
        darkTheme: false,
        defaultSideBarLeft: true,
        searchWholeBody: false,
        termsHighlightColor: "#f58142",
      },
      (result) => {
        if (result.darkTheme) {
          setDarkTheme(true);
          document.documentElement.setAttribute("data-theme", "dark");
        }
        if (!result.defaultSideBarLeft) {
          setDefaultSideBarLeft(false);
        }
        setOptions(result);
      }
    );
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.darkTheme) {
        setDarkTheme(changes.darkTheme.newValue);
      }
    });
    chrome.runtime.sendMessage(
      { type: "popup_request_tabType" },
      function (response) {
        if (response.tabType == "error") {
          setError(response.errorMessage);
        } else if (response.tabType == "chrome") {
          setLogoOnly(true);
        } else if (response.tabType == "already_run") {
          setAlreadyRun(true);
        } else if (response.tabType == "content_active") {
          setContentActive(true);
        }
      }
    );
  }, []);

  useEffect(() => {
    chrome.storage.local.set({ defaultSideBarLeft: defaultSideBarLeft });
  }, [defaultSideBarLeft]);

  useEffect(() => {});

  function darkThemeHandle() {
    let newValue = !darkTheme;
    setDarkTheme(newValue);
    chrome.storage.local.set({ darkTheme: newValue });
    document.documentElement.setAttribute("data-theme", newValue ? "dark" : "");
  }

  function runInTab(findTerms) {
    chrome.tabs.query({ active: true, currentWindow: true }, function () {
      chrome.runtime.sendMessage(
        { type: "popup_request_run_in_tab", findTerms: findTerms },
        function (response) {
          if (response.type == "already_run") {
            setAlreadyRun(true);
          }
        }
      );
    });
    // Closing popup stops extension from running in Linux.
    // window.close();
  }

  async function handleUpload(e) {
    let fileName = e.target.value.split("\\").pop();
    let serialized = await serializeBlob(e.target.files[0]);

    if (fileName.endsWith(".pdf")) {
      setSelectedFile({ name: fileName, serialized: serialized });
    }
  }

  function submitFile() {
    chrome.runtime.sendMessage({
      type: "popup_request_run_on_file",
      fileType: "PDF",
      fileName: selectedFile.name,
      serializedFile: selectedFile.serialized,
    });
    document.write("");
  }

  const storeColor = debounce((option, value) => {
    chrome.storage.local.set({ [option]: value });
  }, 300);

  const debounceStore = useCallback(
    (option, value) => storeColor(option, value),
    []
  );

  function setOptionsWrapper(e) {
    let ele = e.target;
    let option = ele.id;
    let value = ele.type == "checkbox" ? ele.checked : ele.value;
    setOptions((options) => ({
      ...options,
      [option]: value,
    }));
    if (option == "termsHighlightColor") {
      debounceStore(option, value);
      return;
    }
    chrome.storage.local.set({ [option]: value });
  }

  const logoImage = darkTheme
    ? "images/logo_white_text.svg"
    : "images/logo.svg";
  const themeToggleImage = "images/theme_icon.svg";
  const sideBarLeftImage = defaultSideBarLeft
    ? "images/panel_left_icon.svg"
    : "images/panel_right_icon.svg";
  const settingsImage = showOptions
    ? "images/sidebar_hide_left.svg"
    : "images/settings.svg";

  return (
    <div id="popup">
      <div id="logo">
        <img src={logoImage} />
      </div>
      <div id="icons">
        <div
          className="body-icon"
          onClick={darkThemeHandle}
          title="Toggle dark mode"
        >
          <img src={themeToggleImage}></img>
        </div>
        <div
          className="body-icon"
          onClick={() => {
            setDefaultSideBarLeft(!defaultSideBarLeft);
          }}
          title="Toggle default side panel position"
        >
          <img src={sideBarLeftImage}></img>
        </div>
        <div
          className="body-icon"
          onClick={() => setShowOptions(!showOptions)}
          title={showOptions ? "Back" : "More options"}
        >
          <img src={settingsImage}></img>
        </div>
      </div>
      <div
        id="main-content"
        style={{ display: logoOnly || error || showOptions ? "none" : "" }}
      >
        {alreadyRun ? (
          <div className="notification">Refresh page to run again.</div>
        ) : (
          <button
            className="reg-button"
            onClick={() => {
              runInTab(true);
            }}
          >
            Run on page
          </button>
        )}
        <div className="upload-div">
          <label
            htmlFor="upload-button"
            className={
              "input-label" +
              (selectedFile ? " file-selected" : " no-file-selected")
            }
          >
            {!selectedFile ? "Upload file" : selectedFile.name}
            <form
              encType="multipart/form-data"
              method="POST"
              id="upload-form"
              className="hidden"
            >
              <input
                type="file"
                id="upload-button"
                className="hidden"
                onChange={(e) => handleUpload(e)}
                accept=".pdf"
              />
            </form>
          </label>
          {selectedFile && (
            <div
              className="body-icon"
              onClick={submitFile}
              title={"Find terms in file"}
            >
              <img src="./images/find_file.svg" />
            </div>
          )}
        </div>
        {!contentActive && !alreadyRun && (
          <button
            type="button"
            className="reg-button"
            onClick={() => {
              runInTab(false);
            }}
          >
            Open app
          </button>
        )}
      </div>
      {error && (
        <div id="error-container">
          <div id="error-div-small">{error}</div>
        </div>
      )}
      {showOptions && (
        <div id="options-container">
          <div className="option">
            <div>
              Search whole body text (defaults to searching paragraph elements)
            </div>
            <input
              id="searchWholeBody"
              onChange={setOptionsWrapper}
              checked={options.searchWholeBody}
              type="checkbox"
            ></input>
          </div>
          <div className="option">
            <div>Term highlight color</div>
            <input
              id="termsHighlightColor"
              type="color"
              onChange={setOptionsWrapper}
              value={options.termsHighlightColor}
            ></input>
          </div>
        </div>
      )}
    </div>
  );
}

render(<Popup />, document.getElementById("root"));
