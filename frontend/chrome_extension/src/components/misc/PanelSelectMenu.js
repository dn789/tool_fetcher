import React from "react";
import UpdateDot from "./UpdateDot";
import { useEffect } from "react";
const PanelSelectMenu = ({ panelStatus, panelStatusSetter, selectActive, activePanel }) => {

    useEffect(() => {
        if (panelStatus[activePanel].updated && activePanel != 'RecentPanel') {
            panelStatusSetter(activePanel, 'updated', false);
        }
    }, [activePanel])

    return (
        <div
            id='menu-panel'>

            <div id='menu-panel-content'>
                {
                    Object.entries(panelStatus).map(([panel, panelProps]) =>
                        <div
                            key={panel}
                            title={panelProps.title}
                            className={`menu-panel-item ${panel == activePanel ? `active-panel-item` : ''}`}
                            onClick={() => {
                                selectActive(panel);
                            }}
                        >
                            {
                                `${panelProps.name} 
                            ${'count' in panelProps ? `(${panelProps.count}) ` : ''}`}
                            <div>
                                <UpdateDot condition={(panel == activePanel && panel != 'RecentPanel') ? false : panelProps.updated} />
                            </div>
                            {panelProps.loading && <div className='loading-spinner'></div>}
                        </div>
                    )
                }
            </div>
        </div >)

}
export default PanelSelectMenu;
