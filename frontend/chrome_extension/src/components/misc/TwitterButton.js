import React from "react";

const TwitterFollowButton = ({ username }) => {

    return (
        <a
            className="twitter-button"
            title={`@${username}`}
            target="_blank"
            href={`https://twitter.com/${username}`}>
            <img src={chrome.runtime.getURL('./images/twitter_logo.svg')} />
        </a>
    )
}

export default TwitterFollowButton;