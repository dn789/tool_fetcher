import React from "react";
import { useState, useEffect, useContext, useRef } from "react";
import { TermsAndAuthorSelectContext } from "../SideBarContent";
import { SidebarRefContext } from "../SideBar";
import RepoAuthor from "../misc/RepoAuthor";
import { listenForOutsideClicks } from "../utils/utils";
import Loading from "../misc/Loading";

const AuthorPanel = ({ show, authorWatchlist, lastUpdated }) => {
  const select = useContext(TermsAndAuthorSelectContext);
  const sidebarRef = useContext(SidebarRefContext).ref;
  const [loading, setLoading] = useState([]);
  const [loadingMain, setLoadingMain] = useState(false);
  const [showConfirmBox, setShowConfirmBox] = useState(false);

  const confirmRef = useRef();
  useEffect(() => {
    if (showConfirmBox) {
      listenForOutsideClicks(sidebarRef, confirmRef, setShowConfirmBox);
    }
  }, [showConfirmBox]);

  return (
    <div className="panel" style={{ display: !show && "none" }}>
      <div
        ref={confirmRef}
        className={`confirm-box ${showConfirmBox ? "" : "display-none"}`}
      >
        <div>Clear watchlist?</div>
        <button
          className="reg-button"
          onClick={() => {
            select(null, "updateWatchlist", "remove");
            setShowConfirmBox(false);
          }}
        >
          Confirm
        </button>
        <button
          className="reg-button"
          onClick={() => {
            setShowConfirmBox(false);
          }}
        >
          Cancel
        </button>
      </div>
      {Object.keys(authorWatchlist).length && !loadingMain ? (
        <div className="table-wrapper">
          <table className="table">
            <colgroup>
              <col className="width-25-pct" />
              <col className="width-37-pct" />
              <col className="width-37-pct" />
            </colgroup>
            <thead>
              <tr>
                <th>
                  <div className="watchlist-icons">
                    <div
                      className="body-icon small-icon"
                      title="Clear watchlist"
                      onClick={() => setShowConfirmBox(true)}
                    >
                      <img
                        src={chrome.runtime.getURL("./images/close_icon.svg")}
                      />
                    </div>
                    <div className="action-element">
                      <div
                        className={
                          loadingMain
                            ? "loading-spinner"
                            : "body-icon small-icon"
                        }
                        title={
                          loadingMain
                            ? "Updating"
                            : `Update all (last updated: ${lastUpdated})`
                        }
                        onClick={async () => {
                          setLoadingMain(true);
                          await select(null, "updateWatchlist", "update_all");
                          setLoadingMain(false);
                        }}
                      >
                        {!loadingMain && (
                          <img
                            src={chrome.runtime.getURL("./images/refresh.svg")}
                          />
                        )}
                      </div>
                    </div>
                  </div>

                  <div>User</div>
                </th>
                <th>
                  <div>Latest posts</div>
                </th>

                <th>
                  <div>Latest repos</div>
                </th>
              </tr>
            </thead>
            <tbody style={{ overflowY: "scroll" }}>
              {Object.entries(authorWatchlist).map(
                ([authorName, author], index) => (
                  <tr className="author-watchlist-row" key={index}>
                    <td className="pos-relative width-28-percent">
                      <div className="watchlist-icons">
                        <div
                          className="body-icon small-icon"
                          title="Remove from watchlist"
                          onClick={() =>
                            select(authorName, "updateWatchlist", "remove")
                          }
                        >
                          <img
                            src={chrome.runtime.getURL(
                              "./images/close_icon.svg"
                            )}
                          />
                        </div>
                        <div className="action-element">
                          <div
                            className={
                              loading.includes(index)
                                ? "loading-spinner"
                                : "body-icon small-icon"
                            }
                            title={
                              loading.includes(index)
                                ? "Updating"
                                : "Update user info"
                            }
                            onClick={async () => {
                              setLoading([index, ...loading]);
                              await select(
                                { name: authorName, ...author },
                                "updateWatchlist",
                                "add"
                              );
                              setLoading(
                                loading.filter((item) => item != index)
                              );
                            }}
                          >
                            {!loading.includes(index) && (
                              <img
                                src={chrome.runtime.getURL(
                                  "./images/refresh.svg"
                                )}
                              />
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="margin-1em-except-right">
                        <RepoAuthor
                          author={{ name: authorName, ...author }}
                          action={null}
                          showBio={true}
                        />
                      </div>
                    </td>
                    {author.recentBlog.error ? (
                      <td className="width-35-percent">
                        <div className="padding-left-1em">
                          <i>{author.recentBlog.error}</i>
                        </div>
                      </td>
                    ) : (
                      <td className="top-align width-35-percent">
                        <ul className="author-list-cell-wrapper list-bullet-blue">
                          {author.recentBlog.method == "main content" ? (
                            <div className="content-text-small">
                              {author.recentBlog.main_content.map(
                                (line, index) => (
                                  <span key={index}>
                                    {line}
                                    {index ==
                                    author.recentBlog.main_content.length -
                                      1 ? (
                                      <>&nbsp;&nbsp;...&nbsp;&nbsp;</>
                                    ) : (
                                      <span>&emsp;....&emsp;</span>
                                    )}
                                  </span>
                                )
                              )}
                            </div>
                          ) : (
                            <div className="author-list-cell">
                              {author.recentBlog.posts.map(
                                (postDict, index) => (
                                  <li key={index}>
                                    {postDict.title ? (
                                      <a
                                        className="link-no-color"
                                        href={postDict.url}
                                        target="_blank"
                                      >
                                        {postDict.title}
                                      </a>
                                    ) : (
                                      <a
                                        className="link-no-color"
                                        href={postDict.url}
                                        target="_blank"
                                      >
                                        {postDict.post.length
                                          ? postDict.post.map((line, index) => (
                                              <span key={index}>
                                                {line}
                                                {index ==
                                                postDict.post.length - 1 ? (
                                                  <>
                                                    &nbsp;&nbsp;...&nbsp;&nbsp;
                                                  </>
                                                ) : (
                                                  <span>&emsp;....&emsp;</span>
                                                )}
                                              </span>
                                            ))
                                          : postDict.url}
                                      </a>
                                    )}
                                  </li>
                                )
                              )}
                            </div>
                          )}
                        </ul>
                      </td>
                    )}
                    {author.recentRepos.error ? (
                      <td className="width-35-percent">
                        <div className="padding-left-1em">
                          <i>{author.recentRepos.error}</i>
                        </div>
                      </td>
                    ) : (
                      <td className="top-align width-35-percent padding-right-point-2em">
                        <ul className="author-list-cell-wrapper padding-right-point-2em list-style-none">
                          <div className="author-list-cell">
                            {author.recentRepos.map((repo, index) => (
                              <li
                                className="flex-column-gap-point-5-em"
                                key={index}
                              >
                                <div className="flex-row-align-down-small-gap pull-left-slight">
                                  <a href={repo.downloadLink}>
                                    <span
                                      className="body-icon med-icon"
                                      title="Download this repo"
                                    >
                                      <img
                                        src={chrome.runtime.getURL(
                                          "./images/download.svg"
                                        )}
                                      />
                                    </span>
                                  </a>
                                  <a
                                    title={repo.url}
                                    className="repo-link"
                                    target="_blank"
                                    href={repo.url}
                                  >
                                    {repo.name}
                                  </a>
                                </div>
                                {repo.description && (
                                  <span className="content-text-small">
                                    {repo.description}
                                  </span>
                                )}
                              </li>
                            ))}
                          </div>
                        </ul>
                      </td>
                    )}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      ) : !loadingMain ? (
        <div className="empty-panel">
          <div>Not following any users.</div>
        </div>
      ) : (
        <Loading message={"Updating follower info..."} />
      )}
    </div>
  );
};

export default AuthorPanel;
