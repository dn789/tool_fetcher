import React from "react";
import { useState, useEffect, useContext } from "react";
import { TermsAndAuthorSelectContext } from "../SideBarContent";

const Term = ({ term, error, fromModel }) => {

    const select = useContext(TermsAndAuthorSelectContext);

    const [loading, setLoading] = useState(false);
    const [serverResponse, setServerResponse] = useState(null);

    async function getInfo() {
        setLoading(true);
        let response = await select([term], 'findResultsForTerms')
        setServerResponse(response)
    }

    useEffect(() => {
        if (serverResponse) {
            setLoading(false);
            setServerResponse(false);
        }
    }, [serverResponse])


    return <div className='cell-flex-row term'>
        {term}
        {error &&
            <div
                className={loading ? "loading-spinner" : 'body-icon small-icon'}
                title={loading ? 'Reloading' : 'Reload'}
                onClick={!loading ? getInfo : undefined}
            >
                {!loading && <img src={chrome.runtime.getURL('./images/refresh.svg')} />}
            </div>}
        {fromModel && <span className='from-model'>model</span>}
    </div>;
};

export default Term;
