import { useState, useEffect, useContext } from "react";
import { TermsAndAuthorSelectContext } from "../../App";

const Term = ({ index, term, error, bad, fromModel }) => {

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


    return <div className='cell-flex-row min-wdt-18'>
        <div
            className={`body-icon scale-point-8  ${bad ? 'red' : 'red-on-hover'}`}
            title={bad ? 'Undo mark as bad' : 'Mark bad term result'}
            onClick={() => {
                select(index, bad ? 'unMarkBadTermResult' : 'markBadTermResult')
            }}
        >
            <img src='./images/close_icon.svg' />
        </div>
        {term}
        {error &&
            <div
                className={loading ? "loading-spinner" : 'body-icon'}
                title={loading ? 'Reloading' : 'Reload'}
                onClick={!loading ? getInfo : undefined}
            >
                {!loading && <img src='./images/refresh.svg' />}
            </div>}
        {fromModel && <span className='from-model'>model</span>}
    </div>;
};

export default Term;
