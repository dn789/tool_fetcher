import React from 'react';
import { useState } from "react";
import TermResultsTable from '../tables/TermResultsTable';
import Loading from '../misc/Loading';
import { serverRequest } from '../../utils/utils';

const TermResultsPanel = ({ show, source, status, termResults, authorWatchlist }) => {

    const [selectedGood, setSelectedGood] = useState([]);

    function sendRatingsToServer() {
        let resultsforServer = { source: source, resultsRatings: {} };
        termResults.forEach((result, index) => {
            resultsforServer.resultsRatings[result.term] = selectedGood[index];
        })
        serverRequest('rateResults', 'POST', resultsforServer);
    }

    const loadingMessage = (
        <div className='flex-column-med-gap'>
            <span>Finding terms in</span>
            <span>{source}...</span>
        </div>
    )

    return (
        <div className='panel attached-left' style={{ display: !show && 'none' }} >
            <div className='panel-header'>
                <span>Term Results</span>
            </div>
            {status.loading ?
                <Loading message={loadingMessage} />
                :
                <TermResultsTable
                    status={status}
                    termResults={termResults}
                    authorWatchlist={authorWatchlist}
                    source={source}
                />
            }
        </div >
    )
}
export default TermResultsPanel;
