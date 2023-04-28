const TwitterFollowButton = ({ username }) => {

    return (
        <a
            className="twitter-button"
            title={`@${username}`}
            target="_blank"
            href={`https://twitter.com/${username}`}>
            <img src='./images/twitter_logo.svg' />
        </a>
    )
}

export default TwitterFollowButton;