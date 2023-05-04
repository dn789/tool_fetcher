import React from 'react';
import RepoAuthor from '../misc/RepoAuthor';
import { useState, useEffect } from 'react';
import UpdateDot from '../misc/UpdateDot';
import { formatExtractedText } from '../utils/utils';

const RecentPanel = ({ show, status, panelStatusSetter, recentPosts, recentRepos }) => {

    const [showPosts, setShowPosts] = useState(true);

    useEffect(() => {
        if (show) {
            if (showPosts && status.updated_recentPostIndices) {
                panelStatusSetter('RecentPanel', 'updated_recentPostIndices', false);
                if (!status.updated_recentRepoIndices) {
                    panelStatusSetter('RecentPanel', 'updated', false);
                }
            }
            if (!showPosts && status.updated_recentRepoIndices) {
                panelStatusSetter('RecentPanel', 'updated_recentRepoIndices', false);
                if (!status.updated_recentPostIndices) {
                    panelStatusSetter('RecentPanel', 'updated', false);
                }
            }
        }

    }, [showPosts, show, recentPosts, recentRepos])

    return (
        <div className='panel attached-left' style={{ display: !show && 'none' }} >
            <div className='panel-header p-header-2-center'>
                <span
                    className={!showPosts ? 'hidden-tab-header' : undefined}
                    onClick={() => setShowPosts(true)}
                >
                    <span className='header-title'>
                        Recent posts
                        <span>
                            <UpdateDot condition={status.updated_recentPostIndices} />
                        </span>
                    </span>
                </span>

                <span
                    className={showPosts ? 'hidden-tab-header' : undefined}
                    onClick={() => setShowPosts(false)}
                >
                    <span className='header-title'>
                        Recent repos
                        <span >
                            <UpdateDot condition={status.updated_recentRepoIndices} />
                        </span>
                    </span>
                </span>
            </div>
            {showPosts ?
                !!recentPosts.length ?

                    <div className='scrollable-y'>
                        {recentPosts.map((postDict, index) =>
                            <div
                                key={index}
                                className={`recent-cell-container
                            ${index % 2 ? ` shaded` : ''}
                            ${!index ? ` rounded-bottom-left` : index == recentPosts.length - 1 ? ` rounded-top-left` : ` rounded-left-side`}`}
                            >
                                <div className='recent-cell-flex-column'
                                >
                                    {postDict.title ?
                                        <>
                                            <a href={postDict.url} target='_blank'>
                                                <div className='post-title'>{postDict.title}</div>
                                            </a>
                                            <div className='post-text'>
                                                {
                                                    postDict.post.map((line, index) =>
                                                        <p className='recent-paragraph' key={index}>
                                                            {line}{index == postDict.post.length - 1 && <>&nbsp;&nbsp;...&nbsp;&nbsp;</>}
                                                        </p>)
                                                }
                                            </div>
                                        </>
                                        :
                                        <div className='post-text'>
                                            {
                                                postDict.post.map((line, index) =>
                                                    <p className='recent-paragraph' key={index}>
                                                        {line}{index == postDict.post.length - 1 && <>&nbsp;&nbsp;...&nbsp;&nbsp;</>}
                                                    </p>)
                                            }&nbsp;&nbsp;...&nbsp;&nbsp;
                                            <a href={postDict.url} target='_blank'>Full post</a>
                                        </div>}


                                    <div className='author-row'>
                                        by <RepoAuthor author={postDict.author} />
                                        <span className='bullet'>&#8226;</span>
                                        {postDict.date}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div> :
                    <div className='default-panel'>
                        Recent posts and articles from followed authors go here.
                    </div>
                :
                recentRepos.length ?
                    <div className='scrollable-y'>
                        {

                            recentRepos.map((repo, index) =>
                                <div
                                    key={index}
                                    className={`recent-cell-container
                                        ${index % 2 ? ` shaded` : ''}
                                        ${!index ? ` rounded-bottom-left` : index == recentRepos.length - 1 ? ` rounded-top-left` : ` rounded-left-side`}`}
                                >
                                    <div className='recent-cell-flex-column'>

                                        <div className='flex-row-small-gap indent-left'>
                                            <span className='body-icon'
                                                title='Download this repo'
                                            >
                                                <img src={chrome.runtime.getURL('./images/download.svg')} />
                                            </span>
                                            <a className='repo-name-larger repo-link repo-title' title={repo.url} target='_blank' href={repo.url}>
                                                {repo.name}
                                            </a>
                                        </div>
                                        <div className='post-text'>
                                            <p className='recent-paragraph'>{repo.description && repo.description}</p>
                                        </div>
                                        <div className='author-row'>
                                            by <RepoAuthor author={repo.author} flat={true} />
                                            <span className='bullet'>&#8226;</span>
                                            Updated: {repo.date}
                                        </div>
                                    </div>
                                </div>
                            )
                        }
                    </div>
                    :
                    <div className='default-panel'>
                        Recently updated repos from followed authors go here.
                    </div>
            }
        </div >
    )
}

export default RecentPanel;
