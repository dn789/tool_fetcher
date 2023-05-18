import React, { useState, useEffect } from "react";
import TermResultRow from "../misc/TermResultRow";


const TermResultsTable = ({ status, termResults, authorWatchlist }) => {


    const [expanded, setExpanded] = useState([]);

    useEffect(() => {
        if (termResults) {
            setExpanded(new Array(termResults.length).fill(false));
        }
    }, [termResults])

    function handleExpand(selected) {
        setExpanded(expanded.map((item, index) =>
            index === selected ? !item : item));
    }


    const emptyDisplay =
        <div className='empty-panel-container'>
            <div className='empty-panel'>
                {
                    termResults ?
                        'No terms found.'
                        :
                        'Click button in popup to find terms and repos on this page.'
                }

            </div>
        </div>

    // const emptyDisplay =
    //     <div className='empty-panel-container'>
    //         <div className='empty-panel'>

    //             {termResults ?
    //                 <>
    //                     <div>
    //                         <span>No terms found.</span>
    //                     </div>
    //                 </>
    //                 :
    //                 !termResults
    //                 &&
    //                 'Click button in popup to find terms and repos on this page.'
    //             }
    //         </div>
    //     </div>

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
                    {termResults && termResults.map((result, index) => (
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
    return (termResults && termResults.length) ? resultsDisplay : emptyDisplay;
};

export default TermResultsTable;
