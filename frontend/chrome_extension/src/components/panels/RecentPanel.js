import React from 'react';
import RepoAuthor from '../misc/RepoAuthor';
import { useState, useEffect } from 'react';
import UpdateDot from '../misc/UpdateDot';

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
        <div className='panel' style={{ display: !show && 'none' }} >
            <div className='panel-header p-header-2-center'>
                <span
                    className={!showPosts ? 'hidden-tab-header' : undefined}
                    onClick={() => setShowPosts(true)}
                >
                    <span className='header-title'>
                        Latest posts
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
                        Latest repos
                        <span >
                            <UpdateDot condition={status.updated_recentRepoIndices} />
                        </span>
                    </span>
                </span>
            </div>
            {showPosts ?
                recentPosts.length ?

                    <div className='scrollable-y'>
                        {recentPosts.map((postDict, index) =>
                            <div
                                key={index}
                                className={`latest-cell ${index % 2 ? ` shaded` : ''}`}
                            >
                                {postDict.title ?
                                    <>
                                        <a href={postDict.url} target='_blank'>
                                            {postDict.title}
                                        </a>
                                        <div className='line-height-1-3em'>
                                            {
                                                postDict.post.map((line, index) =>
                                                    <p className='margin-t-b-point-8em' key={index}>
                                                        {line}{index == postDict.post.length - 1 && <>&nbsp;&nbsp;...&nbsp;&nbsp;</>}
                                                    </p>)
                                            }
                                        </div>
                                    </>
                                    :
                                    <div className='line-height-1-3em'>
                                        {
                                            postDict.post.map((line, index) =>
                                                <p className='margin-t-b-point-8em' key={index}>
                                                    {line}{index == postDict.post.length - 1 && <>&nbsp;&nbsp;...&nbsp;&nbsp;</>}
                                                </p>)
                                        }&nbsp;&nbsp;...&nbsp;&nbsp;
                                        <a href={postDict.url} target='_blank'>Full post</a>
                                    </div>
                                }


                                <div className='flex-row-align-down-small-gap'>
                                    by <RepoAuthor author={postDict.author} flat={true} />
                                    <span className='bullet'>&#8226;</span>
                                    <span className='font-point-85em'>{postDict.date}</span>
                                </div>
                            </div>
                        )}
                    </div> :
                    <div className='empty-panel'>
                        {showPosts ?
                            ' Latest posts from users you\'re following go here.'
                            :
                            ' Latest repos from users you\'re following go here.'}
                    </div>
                :
                recentRepos.length ?
                    <div className='scrollable-y'>
                        {recentRepos.map((repo, index) =>
                            <div
                                key={index}
                                className={`latest-cell ${index % 2 ? ` shaded` : ''}`}
                            >
                                <div className='flex-row-align-down-small-gap pull-left-slight'>
                                    <a href={repo.downloadLink}>
                                        <span className='body-icon med-icon'
                                            title='Download this repo'
                                        >
                                            <img src={chrome.runtime.getURL('./images/download.svg')} />
                                        </span>
                                    </a>
                                    <a className='repo-link' title={repo.url} target='_blank' href={repo.url}>
                                        {repo.name}
                                    </a>
                                </div>
                                <div className='line-height-1-3em'>
                                    <p className='margin-t-b-point-8em'>{repo.description && repo.description}</p>
                                </div>
                                <div className='flex-row-align-down-small-gap'>
                                    by <RepoAuthor author={repo.author} flat={true} />
                                    <span className='bullet'>&#8226;</span>
                                    <span className='font-point-85em'>Updated: {repo.date}</span>
                                </div>
                            </div>
                        )
                        }
                    </div>
                    :
                    <div className='empty-panel'>
                        Most recently updated repos from users your'e following go here.
                    </div>
            }
        </div >
    )
}

export default RecentPanel;

