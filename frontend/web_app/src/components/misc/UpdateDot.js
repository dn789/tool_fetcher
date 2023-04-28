import React from 'react'
import { CSSTransition } from 'react-transition-group';

const UpdateDot = ({ condition }) => {

    const nodeRef = React.useRef(null);

    return (
        <CSSTransition
            in={condition}
            unmountOnExit
            nodeRef={nodeRef}
            timeout={1000}
            classNames='update-dot'>
            <div ref={nodeRef} className='update-dot'></div>
        </CSSTransition>
    )
}

export default UpdateDot