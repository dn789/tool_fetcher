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

        <div id='panel-select'>
            {
                Object.entries(panelStatus).map(([panel, panelProps]) =>
                    <div
                        key={panel}
                        title={panelProps.title}
                        className="panel-select-item-wrapper"
                        onClick={() => {
                            selectActive(panel);
                        }}
                    >
                        <div
                            className={`panel-select-item ${panel == activePanel ? `active-panel-item` : ''}`}
                        >
                            {
                                `${panelProps.name}
                                ${'count' in panelProps ? `(${panelProps.count}) ` : ''}`}
                        </div>
                        <div className='update-and-loading'>
                            <UpdateDot condition={(panel == activePanel && panel != 'RecentPanel') ? false : panelProps.updated} />
                            {panelProps.loading && <div className='loading-spinner'></div>}
                        </div>

                    </div>
                )
            }
        </div>)

}
export default PanelSelectMenu;
