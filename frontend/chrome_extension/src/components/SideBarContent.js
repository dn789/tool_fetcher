import React from 'react';
import { useEffect, useState, createContext, useContext, useRef } from 'react';
import PanelSelectMenu from './misc/PanelSelectMenu';
import { SidebarRefContext } from './SideBar';
import TermResultsPanel from './panels/TermResultsPanel';
import AuthorPanel from './panels/AuthorPanel';
import RecentPanel from './panels/RecentPanel';
import {
  getFileNameAndUrl,
  serverRequest,
  findTerms,
  embedFile,
  formatTextAndHighlightMatches
} from './utils/utils';
import { panelSelectLegend } from './utils/panelSelectLegend';


const SideBarContent = ({ termResultsFromServer }) => {
  const [termResults, setTermResults] = useState(null);
  const [authorWatchlist, setAuthorWatchlist] = useState({});
  const [recentActivity, setRecentActivity] = useState({})
  const [recentActivityUpdate, setRecentActivityUpdate] = useState(null);
  const [addedToWatchlist, setAddedToWatchlist] = useState([]);
  const [activePanel, setActivePanel] = useState('TermResultsPanel');
  const [panelStatus, setPanelStatus] = useState(panelSelectLegend)
  const setError = useContext(SidebarRefContext).setError;


  function panelStatusSetter(panel, setting, value, updated) {
    const panelStatusUpdate = {
      [setting]: value,
    };
    if (updated !== undefined) {
      panelStatusUpdate.updated = updated;
    };
    setPanelStatus((panelStatus) => ({
      ...panelStatus,
      [panel]: {
        ...panelStatus[panel],
        ...panelStatusUpdate
        // [setting]: value,
        // updated: updated
        // updated: (updated && activePanelRef.current != panel) && true,
      },
    }));
  }



  useEffect(() => {
    setTermResults(termResultsFromServer);
  }, [termResultsFromServer])


  useEffect(async () => {
    let update = await serverRequest('recentActivityGet', 'GET', null, null, setError);
    setAuthorWatchlist(update.watchlist);
    delete update.watchlist;
    setRecentActivityUpdate(update);
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type == 'updateWatchlist_to_content') {
        if (message.action == 'add') {
          setAuthorWatchlist(authorWatchlist => ({
            ...authorWatchlist,
            [message.author.name]: message.author,
          }));
          ['recentPostIndices', 'recentRepoIndices'].forEach(key => {
            if (message.update[key].length) {
              panelStatusSetter('RecentPanel', `updated_${key}`, true, true);
            }
          })
          setRecentActivityUpdate(message.update);
        }
        else if (message.action == 'remove') {
          if (message.authorName) {
            setAuthorWatchlist(authorWatchlist => {
              let newAuthorWatchlist = { ...authorWatchlist };
              delete newAuthorWatchlist[message.authorName];
              return newAuthorWatchlist;
            });
          }
          else {
            setAuthorWatchlist({});
          }
          let newRecentActivityUpdate = { authorName: message.authorName, remove: true };
          setRecentActivityUpdate(newRecentActivityUpdate);
        }
      }
    }
    );
  }, [])

  useEffect(() => {
    if (recentActivityUpdate) {
      if (recentActivityUpdate.remove) {
        let authorName = recentActivityUpdate.authorName
        let newRecentActivity = { recentPosts: [], recentRepos: [] };
        if (authorName) {
          recentActivity.recentPosts.forEach(post => {
            if (!authorName.includes(post.author.name)) {
              newRecentActivity.recentPosts.push(post)
            }
          })
          recentActivity.recentRepos.forEach(repo => {
            if (!authorName.includes(repo.author.name)) {
              newRecentActivity.recentRepos.push(repo)
            }
          })
        }
        setRecentActivity(newRecentActivity);
        return;

      }
      let recentPosts;
      if (recentActivityUpdate.recentPostIndices) {
        recentPosts = recentActivityUpdate.recentPostIndices;
        recentPosts.forEach((postDict, index) => {
          let author = authorWatchlist[postDict.author.name];
          recentPosts[index] = {
            ...postDict, ...author.recentBlog.posts[postDict.index]
          };
        })
      }
      let recentRepos;
      if (recentActivityUpdate.recentRepoIndices) {
        recentRepos = recentActivityUpdate.recentRepoIndices;
        recentRepos.forEach((repoDict, index) => {
          let author = authorWatchlist[repoDict.author.name];
          recentRepos[index] = {
            ...repoDict, ...author.recentRepos[repoDict.index]
          };
        })
      }
      let newRecentActivity = {
        recentPosts: recentPosts ? recentPosts : recentActivity.recentPosts,
        recentRepos: recentRepos ? recentRepos : recentActivity.recentRepos
      }
      setRecentActivity(newRecentActivity);
    }
  }, [recentActivityUpdate])

  useEffect(() => {
    if (Array.isArray(termResultsFromServer)) {
      let newAddedToWatchlist = new Array(termResultsFromServer.length).fill(false);
      termResultsFromServer.forEach((result, index) => {
        if (!result.error && result.repos[0].author.name in authorWatchlist) {
          newAddedToWatchlist[index] = true;
        }
      })
      setAddedToWatchlist(newAddedToWatchlist);
    }
    panelStatusSetter('AuthorPanel', 'count', Object.keys(authorWatchlist).length);
  }, [authorWatchlist, termResultsFromServer])

  useEffect(() => {
    if (termResults == 'loading') {
      panelStatusSetter('TermResultsPanel', 'loading', true);
    }
    else if (Array.isArray(termResults)) {
      panelStatusSetter('TermResultsPanel', 'loading', false);
      panelStatusSetter('TermResultsPanel', 'count', termResults.length, true);

    }
  }, [termResults])


  async function termsAndAuthorSelect(selection, type, action) {
    if (type == 'updateWatchlist') {
      let update;
      let authorName;
      let author;
      let newAuthorWatchlist;
      if (action == 'add') {
        author = selection;
        authorName = author.name;
        update = await serverRequest(type, 'POST', { action: action, author: author }, null, setError);
        author = update.newAuthor;
        setAuthorWatchlist(authorWatchlist => ({
          ...authorWatchlist,
          [author.name]: author,
        }))
        delete update.author;
        ['recentPostIndices', 'recentRepoIndices'].forEach(key => {
          if (update[key].length) {
            panelStatusSetter('RecentPanel', `updated_${key}`, true, true);
          }
        })
        setRecentActivityUpdate(update);
      }
      else if (action == 'update_all') {
        panelStatusSetter('AuthorPanel', 'loading', true);
        update = await serverRequest(type, 'POST', { action: action }, null, setError);
        setAuthorWatchlist(update.watchlist);
        panelStatusSetter('AuthorPanel', 'loading', false, true);
        delete update.watchlist;
        setRecentActivityUpdate(update);
      }
      else {
        authorName = selection;
        if (authorName) {
          setAuthorWatchlist(authorWatchlist => {
            let newAuthorWatchlist = { ...authorWatchlist };
            delete newAuthorWatchlist[authorName];
            return newAuthorWatchlist;
          })
        }
        else {
          setAuthorWatchlist({});
        }
        let newRecentActivityUpdate = { authorName: authorName, remove: true };
        setRecentActivityUpdate(newRecentActivityUpdate);
        serverRequest(type, 'POST', { action: action, authorName: authorName }, null, setError)
      }
      chrome.runtime.sendMessage({
        type: 'updateWatchlist_to_background',
        action: action,
        update: update,
        authorName: authorName,
        author: author,
        watchlist: newAuthorWatchlist
      });
    }

    else if (type == 'findResultsForTerms') {
      let updatedTerms = await serverRequest(type, 'POST', selection, null, setError);
      let newFoundTerms = [...termResults]
      termResults.forEach((result, index) => {
        if (updatedTerms[result.term]) {
          newFoundTerms[index] = updatedTerms[result.term];
        }
      })
      setTermResults(newFoundTerms);
    }
    else if (type == 'markBadTermResult') {
      serverRequest('rateResults', 'POST', { term: termResults[selection].term, rating: false }, null, setError);
      setTermResults(termResults => {
        let newTermResults = termResults.filter((item, index) => index != selection);
        termResults[selection].bad = true;
        newTermResults.push(termResults[selection]);
        return newTermResults;
      })
    }
    else if (type == 'unMarkBadTermResult') {
      serverRequest('rateResults', 'POST', { source: termResults, term: termResults[selection].term, rating: true }, null, setError);
      setTermResults(termResults => {
        let newTermResults = termResults.filter((item, index) => index != selection);
        termResults[selection].bad = false;
        newTermResults.unshift(termResults[selection]);
        return newTermResults;
      })
    }
    return true;
  }


  return (
    <TermsAndAuthorSelectContext.Provider value={termsAndAuthorSelect}>

      <div id='main-content'>
        <PanelSelectMenu
          panelStatus={panelStatus}
          panelStatusSetter={panelStatusSetter}
          selectActive={(panel) => { setActivePanel(panel) }}
          activePanel={activePanel}
        />
        <div id='panel-container'>
          <AuthorPanel
            show={activePanel == 'AuthorPanel'}
            authorWatchlist={authorWatchlist}
          />
          <TermResultsPanel
            show={activePanel == 'TermResultsPanel'}
            status={panelStatus.TermResultsPanel}
            termResults={termResults}
            handleSelectMain={termsAndAuthorSelect}
            authorWatchlist={authorWatchlist}
          />
          <RecentPanel
            show={activePanel == 'RecentPanel'}
            status={panelStatus.RecentPanel}
            panelStatusSetter={panelStatusSetter}
            recentPosts={recentActivity.recentPosts || []}
            recentRepos={recentActivity.recentRepos || []}
          />
        </div>
      </div>
    </TermsAndAuthorSelectContext.Provider>
  );
}

export default SideBarContent;
export const TermsAndAuthorSelectContext = createContext();
