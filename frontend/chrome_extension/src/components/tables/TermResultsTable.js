import React, { useState, useEffect } from "react";
import TermResultRow from "../misc/TermResultRow";

const TermResultsTable = ({ status, termResults, authorWatchlist }) => {
  const [expanded, setExpanded] = useState([]);

  useEffect(() => {
    if (termResults) {
      setExpanded(new Array(termResults.length).fill(false));
    }
  }, [termResults]);

  function handleExpand(selected) {
    setExpanded(
      expanded.map((item, index) => (index === selected ? !item : item))
    );
  }

  const emptyDisplay = (
    <div className="empty-panel-container">
      <div className="empty-panel">
        {termResults && termResults.error
          ? termResults.error
          : termResults
          ? "No terms found."
          : "Click button in popup to find terms and repos on this page."}
      </div>
    </div>
  );

  const resultsDisplay = (
    <div className="table-wrapper">
      <table className="table">
        <colgroup>
          <col />
          <col className="width-37-pct" />
          <col className="width-37-pct" />
        </colgroup>
        <thead>
          <tr>
            <th>
              <div>Term</div>
            </th>
            <th>
              <div>Repo</div>
            </th>
            <th>
              <div>User</div>
            </th>
          </tr>
        </thead>
        <tbody>
          {Array.isArray(termResults) &&
            termResults.map((result, index) => (
              <React.Fragment key={index}>
                <TermResultRow
                  index={index}
                  showAll={expanded[index]}
                  handleExpand={handleExpand}
                  topResult={true}
                  term={result.term}
                  fromModel={result.from_model}
                  error={result.error}
                  bad={result.bad}
                  repo={!result.error ? result.repos[0] : {}}
                  authorWatchlist={authorWatchlist}
                />
                {expanded[index] && (
                  <>
                    {result.repos.slice(1).map((repo, index) => (
                      <TermResultRow
                        key={index}
                        topResult={false}
                        term={result.term}
                        fromModel={result.from_model}
                        error={result.error}
                        repo={repo}
                        bad={result.bad}
                        authorWatchlist={authorWatchlist}
                      />
                    ))}
                  </>
                )}
              </React.Fragment>
            ))}
        </tbody>
      </table>
    </div>
  );
  return termResults && termResults.length && !termResults.error
    ? resultsDisplay
    : emptyDisplay;
};

export default TermResultsTable;
