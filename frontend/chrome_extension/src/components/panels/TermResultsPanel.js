import React from 'react';
import TermResultsTable from '../tables/TermResultsTable';
import Loading from '../misc/Loading';

const TermResultsPanel = ({ show, status, termResults, authorWatchlist }) => {



    return (
        <div className='panel' style={{ display: !show && 'none' }} >
            {termResults == 'loading' ?
                <Loading message={'Finding terms and repos...'} />
                :
                <TermResultsTable
                    status={status}
                    termResults={termResults}
                    authorWatchlist={authorWatchlist}
                />
            }
        </div >
    )
}
export default TermResultsPanel;
