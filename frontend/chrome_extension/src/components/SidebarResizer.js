import React, { useEffect } from 'react';
import { useState } from 'react';


const SidebarResizer = ({ parentWidth, parentLeft, handle, tabType }) => {

    const [mouseX, setMouseX] = useState(null);
    const [dragging, setDragging] = useState(false);

    const onMouseDown = (e) => {
        e.preventDefault();
        if (tabType == 'PDF') {
            document.querySelector('#blank-fill').style.display = 'block';
        }
        setMouseX(e.clientX);
        setDragging(true);
    };

    const onMouseMove = (e) => {
        e.preventDefault();
        if (dragging && mouseX) {
            let newSideBarWidth;
            if (parentLeft) {
                newSideBarWidth = parentWidth + e.clientX - mouseX;
            }
            else {
                newSideBarWidth = parentWidth - e.clientX + mouseX;
            }
            setMouseX(e.clientX);
            let handleReturn = handle(newSideBarWidth);
            if (!handleReturn && tabType == 'PDF') {
                document.querySelector('#blank-fill').style.display = 'none';
            }
        }
    };

    const onMouseUp = () => {
        if (tabType == 'PDF') {
            document.querySelector('#blank-fill').style.display = 'none';
        }
        setMouseX(null);
        setDragging(false);
    };

    useEffect(() => {
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        return () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
    });

    return <div
        className='sidebar-resizer'
        style={{
            left: !parentLeft && 0,
            right: parentLeft && 0
        }}
        onMouseDown={onMouseDown}>
    </div>;
};

export default SidebarResizer;
