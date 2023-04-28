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
            id='side-panel'>
            <div className='panel-header'>Menu</div>

            <div id='side-panel-content'>
                {
                    Object.entries(panelStatus).map(([panel, panelProps]) =>
                        <div
                            key={panel}
                            title={panelProps.title}
                            className={`side-panel-item ${panel == activePanel ? `active-panel-item` : ''}`}
                            onClick={() => {
                                selectActive(panel);
                            }}
                        >
                            {
                                `${panelProps.name} 
                            ${'count' in panelProps ? `(${panelProps.count}) ` : ''}`}
                            <UpdateDot condition={(panel == activePanel && panel != 'RecentPanel') ? false : panelProps.updated} />
                            {panelProps.loading && <div className='loading-spinner'></div>}
                        </div>
                    )
                }
            </div>
        </div >)

}
export default PanelSelectMenu;
