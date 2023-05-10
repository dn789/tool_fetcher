import React from 'react';
import { useState, useEffect, useContext, useRef } from "react";
import { TermsAndAuthorSelectContext } from '../MainContent';
import { SidebarRefContext } from '../SideBar';
import RepoAuthor from '../misc/RepoAuthor';
import { listenForOutsideClicks } from '../utils/utils';
// import { formatExtractedText } from '../utils/utils';


const AuthorPanel = ({ show, authorWatchlist }) => {

    const select = useContext(TermsAndAuthorSelectContext);
    const sidebarRef = useContext(SidebarRefContext);
    const [loading, setLoading] = useState([]);
    const [showConfirmBox, setShowConfirmBox] = useState(false);

    const confirmRef = useRef();
    useEffect(() => {
        if (showConfirmBox) {
            listenForOutsideClicks(
                sidebarRef,
                confirmRef,
                setShowConfirmBox
            )
        }
    }, [showConfirmBox]);

    return (
        <div className='panel attached-left' style={{ display: !show && 'none' }} >
            <div ref={confirmRef} className={`confirm-box ${showConfirmBox ? '' : 'display-none'}`}>
                <div>Clear watchlist?</div>
                <button
                    className="reg-button"
                    onClick={() => {
                        select(null, 'updateWatchlist', 'remove');
                        setShowConfirmBox(false);
                    }}
                >
                    Confirm
                </button>
                <button
                    className="reg-button"
                    onClick={() => { setShowConfirmBox(false); }}>
                    Cancel
                </button>
            </div>
            {
                Object.keys(authorWatchlist).length ?
                    <div className='table-wrapper'>
                        <table className='table'>
                            <colgroup>
                                <col className='width-25-pct' />
                                <col className='width-37-pct' />
                                <col className='width-37-pct' />
                            </colgroup>
                            <thead>
                                <tr>

                                    <th>
                                        <div
                                            className="body-icon body-icon clear-watchlist"
                                            title='Clear watchlist'
                                            onClick={() => setShowConfirmBox(true)}
                                        >
                                            <img src={chrome.runtime.getURL('./images/close_icon.svg')} />
                                        </div>

                                        <div>User</div>
                                    </th>
                                    <th>
                                        <div>Recent posts</div>
                                    </th>

                                    <th>
                                        <div>Recent repos</div>
                                    </th>
                                </tr>
                            </thead>
                            <tbody style={{ overflowY: 'scroll' }}>
                                {Object.entries(authorWatchlist).map(([authorName, author], index) => (
                                    <tr className='author-watchlist-row' key={index}>

                                        <td className="relative width-28-percent">
                                            <div className="watchlist-icons">
                                                <div
                                                    className="body-icon"
                                                    title='Remove from watchlist'
                                                    onClick={() => select(authorName, 'updateWatchlist', 'remove')}
                                                >
                                                    <img src={chrome.runtime.getURL('./images/close_icon.svg')} />
                                                </div>
                                                <div
                                                    className={loading.includes(index) ? 'loading-spinner' : 'body-icon'}
                                                    title={loading.includes(index) ? 'Refreshing' : 'Refresh author info'}
                                                    onClick={async () => {
                                                        setLoading([index, ...loading]);
                                                        await select({ name: authorName, ...author }, 'updateWatchlist', 'add');
                                                        setLoading(loading.filter(item => item != index));
                                                    }}
                                                >
                                                    {!loading.includes(index) && <img src={chrome.runtime.getURL('./images/refresh.svg')} />}
                                                </div>
                                            </div>
                                            <div className='left-indented'>
                                                <RepoAuthor author={{ name: authorName, ...author }} action={null} showBio={true} />
                                            </div>
                                        </td>
                                        {
                                            author.recentBlog.error
                                                ?
                                                <td className='width-35-percent'>
                                                    <div className='centered-xy'>
                                                        {author.recentBlog.error}
                                                    </div>
                                                </td>
                                                :
                                                <td className="top-align width-35-percent">
                                                    <ul className='cell-flex-column padding-right-1rem list-bullet-blue'>
                                                        {
                                                            author.recentBlog.method == 'main content'
                                                                ?
                                                                <div className='small-text'>
                                                                    {
                                                                        author.recentBlog.main_content.map((line, index) =>
                                                                            <span key={index}>
                                                                                {line}
                                                                                {index == author.recentBlog.main_content.length - 1 ?
                                                                                    <>&nbsp;&nbsp;...&nbsp;&nbsp;</>
                                                                                    :
                                                                                    <span>&emsp;....&emsp;</span>
                                                                                }
                                                                            </span>)
                                                                    }
                                                                </div>
                                                                :
                                                                <div className='text-block-flex-column-big-gap'>
                                                                    {
                                                                        author.recentBlog.posts.map((postDict, index) =>
                                                                            <li key={index}>
                                                                                {
                                                                                    postDict.title ?
                                                                                        <a className='link-no-color' href={postDict.url} target='_blank'>{postDict.title}</a>
                                                                                        :
                                                                                        <a className='link-no-color' href={postDict.url} target='_blank'>
                                                                                            {postDict.post.length ?
                                                                                                (postDict.post.map((line, index) =>
                                                                                                    <span key={index}>
                                                                                                        {line}
                                                                                                        {index == postDict.post.length - 1 ?
                                                                                                            <>&nbsp;&nbsp;...&nbsp;&nbsp;</>
                                                                                                            :
                                                                                                            <span>&emsp;....&emsp;</span>
                                                                                                        }
                                                                                                    </span>)) : postDict.url

                                                                                            }
                                                                                        </a>}
                                                                            </li>
                                                                        )}
                                                                </div>}
                                                    </ul>
                                                </td>}
                                        {
                                            author.recentRepos.error ?
                                                <td className='width-35-percent'>
                                                    <div className='centered-xy'>
                                                        {author.recentRepos.error}
                                                    </div>
                                                </td>
                                                :
                                                <td className="top-align width-35-percent">
                                                    <ul className='cell-flex-column padding-right-1rem list-style-none'>
                                                        <div className='text-block-flex-column-big-gap'>
                                                            {author.recentRepos.map((repo, index) =>
                                                                <li key={index}>
                                                                    <div className='flex-row-small-gap indent-left'>
                                                                        <span className='body-icon'
                                                                            title='Download this repo'
                                                                        >
                                                                            <img src={chrome.runtime.getURL('./images/download.svg')} />
                                                                        </span>
                                                                        <a title={repo.url} className='repo-name-small repo-link' target='_blank' href={repo.url}>{repo.name}</a>
                                                                    </div>
                                                                    {repo.description && <span>{repo.description}</span>}
                                                                </li>
                                                            )}
                                                        </div>
                                                    </ul>
                                                </td>}
                                    </tr>))
                                }
                            </tbody>
                        </table>
                    </div> :
                    <div className="default-panel">
                        <div>No authors added to watch list.</div>
                    </div>
            }
        </div >
    )
}

export default AuthorPanel;
