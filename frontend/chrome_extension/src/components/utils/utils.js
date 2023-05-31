export function embedFile(fileURL) {
  return (
    <embed src={fileURL} style={{ height: "100%", width: "100%" }}></embed>
  );
}

export function getFileNameAndUrl(e) {
  let fileName = e.target.value.split("\\").pop();
  let fileURL = URL.createObjectURL(e.target.files[0]);
  if (fileName.endsWith(".pdf")) {
    return [fileName, fileURL];
  }
}

function replaceInText(element, pattern, replacement) {
  for (let node of element.childNodes) {
    switch (node.nodeType) {
      case Node.ELEMENT_NODE:
        replaceInText(node, pattern, replacement);
        break;
      case Node.TEXT_NODE:
        let oldText = node.textContent;
        let newText = oldText.replace(pattern, replacement);
        if (oldText != newText) {
          let newElement = document.createElement("span");
          newElement.innerHTML = newText;
          node.parentNode.insertBefore(newElement, node);
          node.parentNode.removeChild(node);
        }
        break;
    }
  }
}

export async function findTerms(fileURL, fileType, serializedFile, setError) {
  let contentType;
  let body;
  let paragraphs;
  let searchWholeBody;
  let termsHighlightColor;
  // Sets up server request.
  if (fileType == "HTML") {
    const readLocalStorage = async (keys) => {
      return new Promise((resolve, reject) => {
        chrome.storage.local.get(keys, function (result) {
          resolve(result);
        });
      });
    };
    let result = await readLocalStorage([
      "searchWholeBody",
      "termsHighlightColor",
    ]);
    searchWholeBody = result.searchWholeBody;
    termsHighlightColor = result.termsHighlightColor;
    if (searchWholeBody) {
      body = [document.body.innerText];
    } else {
      paragraphs = Array.from(document.getElementsByTagName("p"));
      let parasInner = [];
      paragraphs.forEach(function (item) {
        parasInner.push(item.innerHTML);
      });
      body = parasInner;
    }
    contentType = "application/json";
  } else if (fileType == "PDF") {
    if (!serializedFile) {
      let objectURL = await fetch(fileURL);
      let blob = await objectURL.blob();
      body = blob;
    } else {
      body = new Blob(deserializeBlob(serializedFile));
    }
    contentType = "application/pdf";
  }
  // Sends paragraph text, or PDF blob to server.
  let resultsObj = await serverRequest(
    fileType,
    "POST",
    body,
    contentType,
    setError
  );
  resultsObj["termResults"].forEach((result) => {
    result.key = result.term;
  });

  // For web pages, highlights terms on page.
  if (fileType == "HTML") {
    if (resultsObj["termResults"].length) {
      let pattern = [];
      resultsObj["termResults"].forEach((result) => {
        pattern.push(result.term);
      });
      pattern = pattern.join("|");
      let styleString = `<span style="font-weight:bold; background-color:${termsHighlightColor}; color:black">`;
      pattern = "\\b(" + pattern + ")\\b";
      let re = new RegExp(pattern, "gi");
      let elements;
      if (searchWholeBody) {
        elements = document.body.querySelectorAll(":not(:last-child)");
      } else {
        elements = paragraphs;
      }
      elements.forEach((element) => {
        replaceInText(element, re, styleString + `$&</span>`);
      });
    }
    return resultsObj["termResults"];
  }
  // For PDFs, displays tagged PDF in tab.
  else {
    // Converts base64 response to PDF object URL and embeds it into
    // <embed>.
    let binary = atob(resultsObj["encodedPDF"].replace(/\s/g, ""));
    let len = binary.length;
    let buffer = new ArrayBuffer(len);
    let view = new Uint8Array(buffer);
    for (let i = 0; i < len; i++) {
      view[i] = binary.charCodeAt(i);
    }
    let blob = new Blob([view], { type: "application/pdf" });
    let objectURL = URL.createObjectURL(blob);
    let embed = document.createElement("embed");
    embed.src = objectURL;
    embed.style.cssText =
      "position: absolute; top: 0; left: 0; height: 100%; width: 100%;";
    document.body.appendChild(embed);
    return resultsObj["termResults"];
  }
}

export async function serverRequest(type, method, body, contentType, setError) {
  if (!contentType) {
    contentType = "application/json";
  }
  if (body && contentType == "application/json") {
    body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch("http://127.0.0.1:5000/home", {
      headers: { "Content-Type": contentType, type: type },
      method: method,
      body: body,
    });
  } catch (error) {
    // TypeError: Failed to fetch
    setError("fetch");
  }
  let responseObj = JSON.parse(await response.text());
  return responseObj;
}

export function formatExtractedText(text, lineBreaks) {
  let replacePattern = new RegExp(`(\n{1,})|(\r{1,})`, "g");
  let segments = text.split(replacePattern);
  return segments.map((segment, index) => {
    if (replacePattern.test(segment)) {
      if (lineBreaks) {
        return (
          <span key={index}>
            {" "}
            <br />
            <br />
          </span>
        );
      } else {
        return (
          <span className="line-sep-icon" key={index}>
            &#9724;
          </span>
        );
      }
    } else {
      return segment;
    }
  });
}

export function listenForOutsideClicks(sideBarRef, menuRef, setIsOpen) {
  let sidebar = sideBarRef.current;
  if (!menuRef.current || !sideBarRef.current) return;
  const clickListener = (evt) => {
    if (!menuRef.current.contains(evt.target)) {
      setIsOpen(false);
      sidebar.removeEventListener("click", clickListener);
    }
  };
  sidebar.addEventListener("click", clickListener);
}

export async function serializeBlob(src) {
  const wasBlob = src instanceof Blob;
  const blob = wasBlob ? src : await new Response(src).blob();
  const reader = new FileReader();
  return new Promise((resolve) => {
    reader.onload = () => resolve([reader.result, blob.type, wasBlob]);
    reader.readAsDataURL(blob);
  });
}

export function deserializeBlob([base64, type, wasBlob]) {
  const str = atob(base64.slice(base64.indexOf(",") + 1));
  const len = str.length;
  const arr = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) arr[i] = str.charCodeAt(i);
  if (!wasBlob) {
    type = base64
      .match(/^data:(.+?);base64/)[1]
      .replace(
        /(boundary=)[^;]+/,
        (_, p1) => p1 + String.fromCharCode(...arr.slice(2, arr.indexOf(13)))
      );
  }
  return [arr, type];
}
