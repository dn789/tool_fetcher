import React, { useState, useEffect } from "react";
import TermResultRow from "../misc/TermResultRow";


const TermResultsTable = ({ status, termResults, authorWatchlist, source }) => {

    const [expanded, setExpanded] = useState([]);

    useEffect(() => {
        setExpanded(new Array(termResults.length).fill(false));
    }, [termResults])

    function handleExpand(selected) {
        setExpanded(expanded.map((item, index) =>
            index === selected ? !item : item));
    }

    const emptyDisplay =
        <div className='default-panel'>
            {(source && status.count != null) ?
                <>
                    <div className='flex-column-med-gap'>
                        <span>No terms found in</span>
                        <span>{source} .</span>
                    </div>
                </>
                :
                !source
                &&
                'Enter a URL or select a file to find terms.'
            }
        </div>

    const resultsDisplay =
        <div className='table-wrapper'>
            <table className='table'>
                <colgroup>
                    <col />
                    <col className='width-37-pct' />
                    <col className='width-37-pct' />
                </colgroup>
                <thead>
                    <tr>
                        <th>
                            <div>Term</div>
                        </th>
                        <th >
                            <div>Repos</div>
                        </th>
                        <th>
                            <div>Author</div>
                        </th>
                    </tr>
                </thead>
                <tbody >
                    {termResults.map((result, index) => (
                        <React.Fragment key={index}>
                            <TermResultRow
                                index={index}
                                showAll={expanded[index]}
                                multipleRepos={result.repos && result.repos.length > 1}
                                handleExpand={handleExpand}
                                topResult={true}
                                term={result.term}
                                fromModel={result.from_model}
                                error={result.error}
                                bad={result.bad}
                                repo={!result.error ? result.repos[0] : {}}
                                authorWatchlist={authorWatchlist}
                            />
                            {expanded[index] &&
                                <>
                                    {
                                        result.repos.slice(1).map((repo, index) => (
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
                                        ))
                                    }
                                </>}

                        </React.Fragment>
                    ))
                    }
                </tbody>
            </table>
        </div>
    return termResults.length ? resultsDisplay : emptyDisplay;
};

export default TermResultsTable;
