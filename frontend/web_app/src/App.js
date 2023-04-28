import React from 'react';
import { useEffect, useState, createContext } from 'react';
import Split from 'react-split';
import Panel from './components/panels/Panel';
import PanelSelectMenu from './components/misc/PanelSelectMenu';
import TermResultsPanel from './components/panels/TermResultsPanel';
import AuthorPanel from './components/panels/AuthorPanel';
import RecentPanel from './components/panels/RecentPanel';
import SearchBar from './components/misc/SearchBar';
import {
  getFileNameAndUrl,
  serverRequest,
  findTerms,
  embedFile,
  dummyResults,
  formatTextAndHighlightMatches
} from './utils/utils';
import { panelSelectLegend } from './utils/panelSelectLegend';


const App = () => {

  const [darkMode, setDarkMode] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [displayedFile, setDisplayedFile] = useState(null);
  const [termResults, setTermResults] = useState(null);
  const [termResultsSource, setTermResultsSource] = useState(null);
  const [authorWatchlist, setAuthorWatchlist] = useState({});
  const [recentActivity, setRecentActivity] = useState({})
  const [recentActivityUpdate, setRecentActivityUpdate] = useState(null);
  const [addedToWatchlist, setAddedToWatchlist] = useState([]);
  const [activePanel, setActivePanel] = useState('AuthorPanel');
  const [panelStatus, setPanelStatus] = useState(panelSelectLegend)

  function panelStatusSetter(panel, setting, value, updated) {
    setPanelStatus((panelStatus) => ({
      ...panelStatus,
      [panel]: {
        ...panelStatus[panel],
        [setting]: value,
        updated: (updated && activePanel != panel) && true
      },
    }))
  }

  useEffect(() => {
    let darkModeAttr = darkMode ? 'dark' : '';
    document.documentElement.setAttribute('data-theme', darkModeAttr);
  }, [darkMode])

  useEffect(async () => {
    let update = await serverRequest('recentActivityGet', 'GET');
    setAuthorWatchlist(update.watchlist);
    delete update.watchlist;
    setRecentActivityUpdate(update);
  }, [])

  useEffect(() => {
    if (recentActivityUpdate) {
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
    if (termResults) {
      let newAddedToWatchlist = new Array(termResults.length).fill(false);
      termResults.forEach((result, index) => {
        if (!result.error && result.repos[0].author.name in authorWatchlist) {
          newAddedToWatchlist[index] = true;
        }
      })
      setAddedToWatchlist(newAddedToWatchlist);
    }
    panelStatusSetter('AuthorPanel', 'count', Object.keys(authorWatchlist).length);
  }, [authorWatchlist, termResults])

  useEffect(() => {
    if (termResults) {
      panelStatusSetter('TermResultsPanel', 'loading', false);
      panelStatusSetter('TermResultsPanel', 'count', termResults.length, true);
    }
  }, [termResults])

  async function handleFindTerms(option, source) {
    source = source ? source : displayedFile ? displayedFile.name : 'DummyResults';
    setTermResultsSource(source);
    if (option == 'file') {
      panelStatusSetter('TermResultsPanel', 'loading', true);
      let [taggedFile, termsFromServer] = await findTerms(uploadedFile.url, 'PDF');
      setDisplayedFile({ name: uploadedFile.name, embed: embedFile(taggedFile), type: 'file' });
      setTermResults(termsFromServer);
    }
    else if (option == 'web') {
      panelStatusSetter('TermResultsPanel', 'loading', true);
      let results = await serverRequest('findTermsInURL', 'POST', source);
      let displayedText;
      if (results.error) {
        displayedText = results.error;
      }
      else {
        setTermResults(results.termResults);
        displayedText = formatTextAndHighlightMatches(results.termResults, results.webPageText)
      }
      panelStatusSetter('TermResultsPanel', 'loading', false);
      displayedText = <div className='text-panel'>{displayedText}</div>
      setDisplayedFile({ name: source, text: displayedText, type: 'web' });
    }
    else if (option == 'dummyResults') {
      dummyResults.forEach(termDict => {
        termDict.excluded = false;
      })
      setTermResults(dummyResults);
    }
  }

  function handleUpload(e) {
    let [fileName, fileURL] = getFileNameAndUrl(e);
    setUploadedFile({ name: fileName, url: fileURL });
    setDisplayedFile({ name: fileName, embed: embedFile(fileURL), type: 'file' });
    return fileName;
  }

  async function termsAndAuthorSelect(selection, type) {
    if (type == 'authorWatchlistAdd') {
      let author = selection;
      let update = await serverRequest('authorWatchlistAdd', 'POST', author);
      let newAuthor = update.newAuthor;
      newAuthor = { ...author, ...newAuthor }
      setAuthorWatchlist(authorWatchlist => ({
        ...authorWatchlist,
        [author.name]: newAuthor,
      }))
      delete update.newAuthor;
      Object.keys(update).forEach(key => {
        if (update[key]) {
          panelStatusSetter('RecentPanel', `updated_${key}`, true, true);
        }
      })
      setRecentActivityUpdate(update);
    }
    else if (type == 'authorWatchlistRemove') {
      if (!selection) {
        serverRequest(type, 'POST', {});
        setAuthorWatchlist({});
        setRecentActivity({});
        return;
      }
      let newAuthorWatchlist = { ...authorWatchlist };
      selection.forEach(authorName =>
        delete newAuthorWatchlist[authorName]
      )
      setAuthorWatchlist(newAuthorWatchlist);
      serverRequest(type, 'POST', selection);
      let newRecentActivity = { recentPosts: [], recentRepos: [] };
      recentActivity.recentPosts.forEach(post => {
        if (!selection.includes(post.author.name)) {
          newRecentActivity.recentPosts.push(post)
        }
      })
      recentActivity.recentRepos.forEach(repo => {
        if (!selection.includes(repo.author.name)) {
          newRecentActivity.recentRepos.push(repo)
        }
      })
      setRecentActivity(newRecentActivity);
    }

    else if (type == 'findResultsForTerms') {
      let updatedTerms = await serverRequest(type, 'POST', selection);
      let newFoundTerms = [...termResults]
      termResults.forEach((result, index) => {
        if (updatedTerms[result.term]) {
          newFoundTerms[index] = updatedTerms[result.term];
        }
      })
      setTermResults(newFoundTerms);
    }
    else if (type == 'markBadTermResult') {
      serverRequest('rateResults', 'POST', { source: termResultsSource, term: termResults[selection].term, rating: false });
      setTermResults(termResults => {
        let newTermResults = termResults.filter((item, index) => index != selection);
        termResults[selection].bad = true;
        newTermResults.push(termResults[selection]);
        return newTermResults;
      })
    }
    else if (type == 'unMarkBadTermResult') {
      serverRequest('rateResults', 'POST', { source: termResultsSource, term: termResults[selection].term, rating: true });
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
      <header id="app-header">
        <div className='logo'>
          <img src={darkMode ? "./images/logo_white_text.svg" : "./images/logo.svg"} />
        </div>
        <div className="settings">
          <div
            className='settings-icon'
            title='Toggle dark mode'
            onClick={() => setDarkMode(!darkMode)}>
            <img src='./images/theme_icon.svg' />
          </div>
          <SearchBar
            handleUpload={handleUpload}
            handleFindTerms={handleFindTerms}
          />
        </div>
        {/* <div
          title='Get dummy results'
          onClick={() => handleFindTerms('dummyResults')}>
          <div style={{ fontSize: 'medium', marginLeft: '1rem' }}><button className='reg-button'>Test Results</button></div>
        </div> */}
      </header>
      <div id='main-content'>
        <PanelSelectMenu
          panelStatus={panelStatus}
          panelStatusSetter={panelStatusSetter}
          selectActive={(panel) => { setActivePanel(panel) }}
          activePanel={activePanel}
        />
        <Split
          id='main-split'
          sizes={[65, 35]}
          minSize={150}
        >
          <div
            style={{ display: 'flex' }}
          >
            <AuthorPanel
              show={activePanel == 'AuthorPanel'}
              authorWatchlist={authorWatchlist}
            />
            <TermResultsPanel
              show={activePanel == 'TermResultsPanel'}
              status={panelStatus.TermResultsPanel}
              termResults={termResults || []}
              handleSelectMain={termsAndAuthorSelect}
              authorWatchlist={authorWatchlist}
              source={displayedFile ? displayedFile.name : null}
            />
            <RecentPanel
              show={activePanel == 'RecentPanel'}
              status={panelStatus.RecentPanel}
              panelStatusSetter={panelStatusSetter}
              recentPosts={recentActivity.recentPosts || []}
              recentRepos={recentActivity.recentRepos || []}
            />
          </div>
          <Panel
            heading={displayedFile ? displayedFile.name : 'No file selected'}
            content={
              (displayedFile && displayedFile.embed)
                ? displayedFile.embed
                : (displayedFile && displayedFile.text)
                && displayedFile.text}
            fileType={displayedFile && displayedFile.type}
            handleFindTerms={handleFindTerms}
          />
        </Split>
      </div>
    </TermsAndAuthorSelectContext.Provider>
  );
}

export default App;
export const TermsAndAuthorSelectContext = createContext();
