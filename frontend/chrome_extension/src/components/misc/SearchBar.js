import React from 'react'
import { useState } from 'react';
// import { serverRequest } from '../../utils/utils';

const SearchBar = ({ handleUpload, handleFindTerms }) => {

    const [urlInput, setURLInput] = useState('')
    const [filenameInBar, setFilenameInBar] = useState(false);

    return (
        <div className='flex-row-small-gap'>
            <label htmlFor='file-upload'
                className='settings-icon settings-icon-label'
                title='Load file'
                onChange={async (e) => {
                    const fileName = handleUpload(e);
                    setFilenameInBar(fileName);
                }}
            >
                <img src={chrome.runtime.getURL('./images/folder.svg')} />
                <input type="file" id='file-upload' className='hidden'></input>
            </label>
            <div className='search-bar-div'>
                {filenameInBar ?
                    <div className='search-bar-wrapper file-label'>
                        <input
                            type='text'
                            className='search-bar-input'
                            readOnly
                            value={filenameInBar} />
                        <div
                            className='body-icon'
                            onClick={() => setFilenameInBar(false)}
                        >
                            <img src={chrome.runtime.getURL('./images/close_icon.svg')} />
                        </div>
                    </div>
                    :
                    <div className='search-bar-wrapper'>
                        <input
                            type='text'
                            className='search-bar-input'
                            placeholder='Enter URL or select a file...'
                            value={urlInput}
                            onChange={(e) => setURLInput(e.target.value)}
                        />
                        {urlInput &&
                            <div
                                className='body-icon'
                                onClick={() => setURLInput('')}
                            >
                                <img src={chrome.runtime.getURL('./images/close_icon.svg')} />
                            </div>}


                    </div>
                }
            </div>
            <div
                className='settings-icon'
                title={filenameInBar ? 'Find terms in file' : urlInput ? 'Find terms in url' : 'Find terms'}
                onClick={
                    async (e) => {
                        if (filenameInBar) {
                            handleFindTerms('file', filenameInBar);
                        }
                        else if (urlInput) {
                            handleFindTerms('web', urlInput);
                        }
                        e.target.blur()
                    }}


            >
                <img className='underlay-image' src={filenameInBar ? './images/file.svg' : urlInput && './images/globe.svg'} />
                <img src={chrome.runtime.getURL('./images/search.svg')} />
            </div>
        </div>
    )
}

export default SearchBar