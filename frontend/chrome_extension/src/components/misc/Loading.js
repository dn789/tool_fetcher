import React from 'react';

const Loading = ({ message }) => {
    return (
        <div className='loading-div-container'>
            <div className='loading-div' >
                <div className="loading-spinner-large"></div>
                <div>
                    {message}
                </div>
            </div >
        </div>
    );
};

export default Loading;
