const Loading = ({ message }) => {
    return <div className='loading-div' >
        <div>{message}</div>
        {/* <img src='./images/loading.gif' /> */}
        <div className="loading-spinner-large"></div>
    </div >;
};

export default Loading;
