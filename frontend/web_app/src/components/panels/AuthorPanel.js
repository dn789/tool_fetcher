import React from 'react';
import { useState, useContext } from "react";
import { TermsAndAuthorSelectContext } from '../../App';
import RepoAuthor from '../misc/RepoAuthor';
import { formatExtractedText } from '../../utils/utils';

const AuthorPanel = ({ show, authorWatchlist }) => {

    const select = useContext(TermsAndAuthorSelectContext);
    const [loading, setLoading] = useState([]);

    const test = `       |      `;
    return (
        <div className='panel attached-left' style={{ display: !show && 'none' }} >

            <div className='panel-header p-header-1-left-1-center'>
                {Object.keys(authorWatchlist).length ?
                    <div
                        className="body-icon body-icon-large"
                        title='Clear watchlist'
                        onClick={() => (select(null, 'authorWatchlistRemove'))}
                    >
                        <img src='./images/close_icon.svg' />
                    </div>
                    :
                    <div></div>}
                <div>Watchlist</div>
            </div>
            {Object.keys(authorWatchlist).length ?
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
                                        <div className="top-left flex-row-very-small-gap">
                                            <div
                                                className="body-icon scale-point-8"
                                                title='Remove from watchlist'
                                                onClick={() => select([authorName], 'authorWatchlistRemove')}
                                            >
                                                <img src='./images/close_icon.svg' />
                                            </div>
                                            <div
                                                className={loading.includes(index) ? 'loading-spinner' : 'body-icon'}
                                                title={loading.includes(index) ? 'Refreshing' : 'Refresh author info'}
                                                onClick={async () => {
                                                    setLoading([index, ...loading]);
                                                    await select({ name: authorName, ...author }, 'authorWatchlistAdd');
                                                    setLoading(loading.filter(item => item != index));
                                                }}
                                            >
                                                {!loading.includes(index) && <img src='./images/refresh.svg' />}
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
                                                                        <img src='./images/download.svg' />
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
