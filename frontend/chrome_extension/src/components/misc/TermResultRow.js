import React from "react";
import { useContext } from "react";
import RepoAuthor from "./RepoAuthor";
import Term from "./Term";
import { TermsAndAuthorSelectContext } from "../SideBarContent";

const TermResultRow = ({
  index,
  showAll,
  topResult,
  term,
  fromModel,
  error,
  bad,
  repo,
  authorWatchlist,
  handleExpand,
}) => {
  const select = useContext(TermsAndAuthorSelectContext);

  return (
    <tr>
      {topResult ? (
        <td
          className="top-align top-term-result padding-top-point-2em"
          title={term}
        >
          <div
            className={`body-icon small-icon margin-left-point-2em ${
              bad ? "red" : "red-on-hover"
            }`}
            title={bad ? "Undo mark as bad" : "Mark bad term result"}
            onClick={() => {
              select(index, bad ? "unMarkBadTermResult" : "markBadTermResult");
            }}
          >
            <img src={chrome.runtime.getURL("./images/close_icon.svg")} />
          </div>

          <Term term={term} error={error} fromModel={fromModel} />
        </td>
      ) : (
        <td className="top-align padding-top-1em"></td>
      )}
      <td
        className={`top-align width-35-percent padding-top-point-2em ${
          !topResult ? "padding-top-1em" : ""
        }`}
      >
        <div className="flex-column">
          {topResult && !error && (
            <div
              className="body-icon small-icon expand-icon width-point-9em-img"
              onClick={() => handleExpand(index)}
              title={
                showAll
                  ? "Show fewer repos for " + term
                  : "Show more repos for " + term
              }
            >
              <img
                src={chrome.runtime.getURL(
                  showAll
                    ? "./images/expand_icon_down.svg"
                    : "./images/expand_icon_right.svg"
                )}
              />
            </div>
          )}
          {!error ? (
            <div className="flex-column-gap-point-5-em margin-left-1-5em">
              <div className="flex-row-align-down-small-gap pull-left-slight">
                <a href={repo.downloadLink}>
                  <div
                    className="body-icon med-icon"
                    title="Download this repo"
                  >
                    <img src={chrome.runtime.getURL("./images/download.svg")} />
                  </div>
                </a>
                <a
                  className="repo-link"
                  target="_blank"
                  href={repo.url}
                  title={repo.url}
                >
                  {repo.name}
                </a>
              </div>
              {repo.description && (
                <div className="content-text-small">{repo.description}</div>
              )}
            </div>
          ) : (
            <>
              <div className="body-icon small-icon expand-icon width-point-9em-img invisible">
                <img
                  src={chrome.runtime.getURL(
                    showAll
                      ? "./images/expand_icon_down.svg"
                      : "./images/expand_icon_right.svg"
                  )}
                />
              </div>
              <div className="margin-top-point-2em margin-left-1-5em">
                {error}
              </div>
            </>
          )}
        </div>
      </td>

      <td
        className={`top-align width-35-percent  ${
          !topResult ? "padding-top-1em" : "padding-top-point-2em"
        }`}
      >
        {topResult && (
          <div className="body-icon small-icon expand-icon width-1em-img invisible">
            <img
              src={chrome.runtime.getURL(
                showAll
                  ? "./images/expand_icon_down.svg"
                  : "./images/expand_icon_right.svg"
              )}
            />
          </div>
        )}
        {repo.author && (
          <RepoAuthor
            author={repo.author}
            action={"add"}
            authorWatchlist={authorWatchlist}
            showBio={true}
          />
        )}
      </td>
    </tr>
  );
};

export default TermResultRow;
