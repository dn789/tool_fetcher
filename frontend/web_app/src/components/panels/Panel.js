const Panel = ({ heading, content, footer, fileType, handleFindTerms }) => {

    return (
        <div
            className='panel'>
            <div className='panel-header p-header-1-left-1-center'>
                {fileType ?
                    <div
                        className='settings-icon left-aligned'
                        title={fileType == 'file' ? 'Find terms in file' : 'Find terms in web page'}
                        onClick={() => {
                            if (fileType == 'file') {
                                handleFindTerms('file');
                            }
                            else {
                                handleFindTerms('web');
                            }
                        }}
                    >
                        <img className='underlay-image' src={fileType == 'file' ? './images/file.svg' : './images/globe.svg'} />
                        <img src='./images/search.svg' />
                    </div>
                    :
                    <div></div>
                }

                <div >{heading}</div>
            </div>
            {content}
            {footer && <div className="panel-footer">{footer}</div>}
        </div >)

}
export default Panel;
