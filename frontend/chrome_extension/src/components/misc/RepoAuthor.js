import React from "react";
import { useState, useEffect, useContext } from "react";
import { TermsAndAuthorSelectContext } from "../MainContent";
import TwitterFollowButton from "./TwitterButton";

const RepoAuthor = ({ author, action, authorWatchlist, showBio }) => {

    const select = useContext(TermsAndAuthorSelectContext);

    const [loading, setLoading] = useState(false);
    const [serverResponse, setServerResponse] = useState(null);

    async function addToWatchlistOrRefresh() {
        setLoading(true);
        let response = await select(author, 'updateWatchlist', 'add');
        setServerResponse(response);
    }

    useEffect(() => {
        if (serverResponse) {
            setLoading(false);
            setServerResponse(false);
        }
    }, [serverResponse])


    useEffect(() => {
        if (author.name) {
            setLoading(false);
        }
    }, [author])

    const actionElement = (loading, action) => {

        let className = loading ? 'loading-spinner' : author.name in authorWatchlist ? 'body-icon no-pointer' : 'body-icon'
        let onClick;
        let title;
        let imgSrc;

        if (action == 'add') {
            if (loading) {
                title = 'Adding to watch list';
            }
            else {
                title = author.name in authorWatchlist ? 'Added to watchlist' : 'Add to watchlist';
                imgSrc = author.name in authorWatchlist ? './images/check.svg' : './images/plus.svg';
                onClick = !(author.name in authorWatchlist) ? addToWatchlistOrRefresh : undefined;
            }
        }
        else {
            if (loading) {
                title = 'Reloading';
            }
            else {
                title = 'Reload author info';
                imgSrc = './images/refresh.svg';
                onClick = addToWatchlistOrRefresh;
            }
        }
        return (
            <div
                className={className}
                title={title}
                onClick={onClick}
            >
                {imgSrc && <img src={chrome.runtime.getURL(imgSrc)} />}
            </div>)
    }

    return <div className='heading-text-small-gap-div' >
        <div className={`cell-flex-row repo-author flex-wrap ${action ? ` indent-left` : ''}`}>

            {action && actionElement(loading, action)}
            <a className='author-link' title={author.url} target='_blank' href={author.url}>{author.name}</a>

            <div className="flex-row-no-gap">
                {author.blogURL && <a title={author.blogURL} target='_blank' href={author.blogURL}>
                    <div className="body-icon-white">
                        <img src={chrome.runtime.getURL('./images/globe.svg')} />
                    </div>
                </a>}
                {author.twitter && <TwitterFollowButton username={author.twitter} />}
            </div>

        </div>
        {showBio && <div className="small-text">{author.bio}</div>}
    </div>;
};

export default RepoAuthor;
