import React, { useState, useEffect } from "react";
import { render } from "react-dom";
import styles from "./options.css";
import "regenerator-runtime/runtime.js";

const Options = () => {
  const [darkTheme, setDarkTheme] = useState(false);

  useEffect(async () => {
    chrome.storage.local.get({ darkTheme: false }, (result) => {
      if (result.darkTheme) {
        setDarkTheme(true);
        document.documentElement.setAttribute("data-theme", "dark");
      }
    });
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.darkTheme) {
        setDarkTheme(changes.darkTheme.newValue);
      }
    });
  }, []);
  return (
    <>
      <style type="text/css">{styles}</style>

      <div id="main-content">options</div>
    </>
  );
};

render(<Options />, document.getElementById("root"));
