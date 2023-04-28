import React from 'react'
import RepoAuthor from "../misc/RepoAuthor";
import Term from "../misc/Term";


const TermResultRow = ({ index, showAll, multipleRepos, topResult, term, fromModel, error, bad, repo, authorWatchlist, handleExpand }) => {
    return (
        <tr >
            <td className='top-align width-half-rem'>
                {
                    (topResult && multipleRepos) &&
                    <div className='cell-flex-row top-bottom-margin' >
                        <div
                            className='body-icon'
                            onClick={() => handleExpand(index)}
                            title={showAll ? 'Hide extra results' : 'Show more results'}
                        >
                            <img src={showAll ? './images/expand_icon_down.svg' : './images/expand_icon_right.svg'} />
                        </div>
                    </div>
                }
            </td>
            {topResult ?

                <td className='top-align' title={term}>
                    <div className='top-bottom-margin'>
                        <Term index={index} term={term} error={error} bad={bad} fromModel={fromModel} />
                    </div>
                </td>

                :
                <td className='top-align'></td>
            }
            {
                error ?
                    <td className='top-align width-35-percent'>
                        <div className='top-bottom-margin'>{error}</div>
                    </td>
                    :
                    <td className='top-align  width-35-percent'>
                        <div className='heading-text-small-gap-div top-bottom-margin'>
                            <div className='cell-flex-row repo-name indent-left'>
                                <div className='body-icon'
                                    title='Download this repo'
                                >
                                    <img src='./images/download.svg' />
                                </div>
                                <a className='repo-link' target='_blank' href={repo.url} title={repo.url} >{repo.name}</a>
                            </div>
                            {repo.description &&
                                <div className='small-text'>
                                    {repo.description}
                                </div>}
                        </div>
                    </td>

            }

            <td className='top-align  width-35-percent'>
                <div className='top-bottom-margin'>
                    {
                        repo.author &&
                        <RepoAuthor
                            author={repo.author}
                            action={'add'}
                            authorWatchlist={authorWatchlist}
                            showBio={true}
                        />
                    }
                </div>
            </td>
        </tr>
    )
}

export default TermResultRow