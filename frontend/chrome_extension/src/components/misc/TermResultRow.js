import React from 'react';
import { useContext } from 'react'
import RepoAuthor from "../misc/RepoAuthor";
import Term from "../misc/Term";
import { TermsAndAuthorSelectContext } from "../MainContent";


const TermResultRow = ({ index, showAll, multipleRepos, topResult, term, fromModel, error, bad, repo, authorWatchlist, handleExpand }) => {
    const select = useContext(TermsAndAuthorSelectContext);

    return (
        <tr >
            {topResult ?

                <td className='top-align top-term-result' title={term}>

                    <div
                        className={`body-icon mark-as-bad-icon  ${bad ? 'red' : 'red-on-hover'}`}
                        title={bad ? 'Undo mark as bad' : 'Mark bad term result'}
                        onClick={() => {
                            select(index, bad ? 'unMarkBadTermResult' : 'markBadTermResult')
                        }}
                    >
                        <img src={chrome.runtime.getURL('./images/close_icon.svg')} />
                    </div>

                    <Term index={index} term={term} error={error} fromModel={fromModel} />



                </td>

                :
                <td className='top-align'></td>
            }
            {
                error ?
                    <td className='top-align width-35-percent'>
                        <div>{error}</div>
                    </td>
                    :
                    <td className='top-align  width-35-percent'>
                        <div className='flex-column'>
                            {topResult &&
                                <div
                                    className='body-icon expand-icon'
                                    onClick={() => handleExpand(index)}
                                    title={showAll ? 'Show fewer repos for ' + term : 'Show more repos for ' + term}
                                >
                                    <img src={chrome.runtime.getURL(showAll ? './images/expand_icon_down.svg' : './images/expand_icon_right.svg')} />
                                </div>}
                            <div className='heading-text-small-gap-div left-margin-1-5em'>
                                <div className='cell-flex-row repo-name indent-left'>
                                    <div className='body-icon'
                                        title='Download this repo'
                                    >
                                        <img src={chrome.runtime.getURL('./images/download.svg')} />
                                    </div>
                                    <a className='repo-link' target='_blank' href={repo.url} title={repo.url} >{repo.name}</a>
                                </div>
                                {repo.description &&
                                    <div className='small-text'>
                                        {repo.description}
                                    </div>}
                            </div>
                        </div>
                    </td>

            }

            <td className='top-align  width-35-percent'>
                {topResult &&
                    <div
                        className='body-icon expand-icon invisible'
                    >
                        <img src={chrome.runtime.getURL(showAll ? './images/expand_icon_down.svg' : './images/expand_icon_right.svg')} />
                    </div>}
                {/* <div className='top-bottom-margin'> */}
                {
                    repo.author &&
                    <RepoAuthor
                        author={repo.author}
                        action={'add'}
                        authorWatchlist={authorWatchlist}
                        showBio={true}
                    />
                }
                {/* </div> */}
            </td>
        </tr>
    )
}

export default TermResultRow