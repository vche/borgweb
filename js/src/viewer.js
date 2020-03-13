let $ = require('jquery')
let plotly = require('plotly.js-dist')
let env = require('./env')
let util = require('./util')
let filesize = require('filesize')

/********** Log viewer frontend ********/
let logText = $('#log-text')
let noLogsError = $('#no-logs-error')
let currentRepo = "";

function updateRepoList () {
  let repoListHtml = []
  $.getJSON('repos', res => {
    let i = 0
    $.each(res, (name, value) => {
      repoListHtml += `
        <li>
          <a onClick="window.getLogFiles('${ name }')" >
          <span class="glyphicon glyphicon-hdd"
          aria-hidden="true"></span>
            ${ name }
          </a>
        </li>`
      i++
    })

    $('#repo-list').html(repoListHtml)

  })
}

function highlightListEntry (id) {
  $('.shown-log').toggleClass('shown-log')
  $(`#log-${ id }`).toggleClass('shown-log')
}

function setListItemStatus () {
  for (let i = 0; i < env.fetchRecentLogsStatus; i++) {
    $.getJSON('logs/' + currentRepo + "/" + i, res => {
      let search = `#log-${i} .glyphicon`
      let elem = $(search)
      elem.css('color', env.icon[res.status][1])
      elem.removeClass('glyphicon-time')
      elem.addClass(`glyphicon-${ env.icon[res.status][0]}`)
    })
  }
}

function updateLogFileList (repo) {
  let logFilesListHTML = []
  let indicatorHTML = `
    <span class="glyphicon glyphicon-time list-status-indicator"
      aria-hidden="true"></span>`;

  $.getJSON('logs/' + repo, res => {
    let i = 0
    $.each(res.files, (key, value) => {
      logFilesListHTML += `
        <li class='list-group-item'>
          <a onClick="window.switchToLog(${ value[0] + 1 })" id="log-${ value[0] }">
            ${ indicatorHTML }
            ${ value[1] }
          </a>
        </li>`
      i++
    })

    if(res.files.length > 0){
        env.fetchRecentLogsStatus = res.files.length;
        setListItemStatus()
    }else{
      logFilesListHTML = "<li><a>" + indicatorHTML + " No Log Files</a></li>";
    }

    $('#log-files').html(logFilesListHTML)

  })
}

function getSetState (state) {
  state = state || {}
  let anchor = util.parseAnchor()
  anchor = {
    log: state.log || anchor.log || 1,
    offset: state.offset || anchor.offset || 1
  }
  document.location.hash =
    `#log:${ anchor.log };offset:${ anchor.offset }`
  return anchor
}

function updatePathAndStatus (id) {
  if ((id + 1) === env.lastLogID) {
      return;
  }
  $.getJSON('logs/' + currentRepo + "/" + id, function (res) {

    $('#log-path').html(`
      <!-- js generated -->
        <span class="glyphicon glyphicon-${ env.icon[res.status][0] }"
          aria-hidden="true" style="font-size: 34px;
          color: ${ env.icon[res.status][1] }; width: 42px;
          margin-right: 4px; vertical-align: middle;"></span
        ><input class="form-control" type="text"
          value="${ res.filename }" readonly onClick="this.select();">
      <!-- /js generated -->`)
    highlightListEntry(id)
  })
}

function insertLogData (linesArray) {
  let [html, lineStatus] = [``, ``]
  linesArray.forEach((val, index) => {
    lineStatus = env.logLine[val[0]]
    html = lineStatus ? `<mark class="${ env.logLine[val[0]][0] }"
      style="background-color: ${ env.logLine[val[0]][1] };">` : ``
    html += val[1] + '\n'
    html += lineStatus ? `</mark>` : ``
    logText.append(html)
  })
}

function clearLog () { logText.html('') }

let fadeLog = {
  out: x => {
    setTimeout(clearLog, env.transitionTime * 0.5)
    logText.fadeOut(env.transitionTime * 0.5)
  },
  in: x => {
    logText.fadeIn(env.transitionTime * 0.5)
  }
}

function displayLogSection (state, availableLines) {
  let url = `logs/` + currentRepo + "/" + `${ state.log - 1 }/${ state.offset - 1 }:${ availableLines }:1`
  $.get(url, res => {
    noLogsError.hide()
    if (state.log === env.lastLogID) {
      clearLog()
      insertLogData(res.lines)
    } else {
      env.lastLogID = state.log
      fadeLog.out()
      setTimeout(x => {
        insertLogData(res.lines)
        fadeLog.in()
      }, env.transitionTime * 0.5)
    }
  }).fail(err => {
    noLogsError.show()
    logText.hide()
  })
}

function render (availableLines) {
  console.log("rendering")
  // availableLines = availableLines || util.determineLineCount()
  // let state = getSetState()
  // updatePathAndStatus(state.log - 1)
  // displayLogSection(state, availableLines)
}

function switchToLog (id) {
  $("#log-path").show();
  getSetState({ log: id, offset: 1 })
  render()
}

function addLogViewAdvise() {
  $("#log-files").append("<li><a>Select a respository to see logs</a></li>");
  $("#log-text").empty().text("Select a log to view its contents");
}

function getLogFiles (repo) {
    $("#log-files").empty();
    addLogViewAdvise();
    currentRepo = repo;
    updateLogFileList(repo);
}

function getNextOffset (state, direction, availableLines, callback) {

  let url = `logs/` + currentRepo + "/" + `${ state.log - 1 }/${ state.offset - 1 }` +
    `:${ availableLines }:${ direction }`
  $.get(url, res => {
    let subsequentUrl = `logs/` + currentRepo + "/" + `${ state.log - 1 }/${ res.offset + 1 }` +
      `:${ availableLines }:${ direction }`
    $.get(subsequentUrl, subsequentRes => {
      if (subsequentRes.lines.length === 0) getSetState(state)
      else callback(state, res, availableLines)
    })
  })
}

function switchPage (direction) {
  var availableLines = util.determineLineCount()
  getNextOffset(getSetState(), direction, availableLines,
    (state, res, availableLines) => {
      getSetState({ log: state.log, offset: res.offset + 1 })
      render(availableLines)
    }
  )
}

function lastPage () {
  let state = getSetState()
  let url = `logs/` + currentRepo + "/" + + `${ state.log - 1 }`
  $.get(url, res => {
    let logLength = res.length
    state.offset = logLength
    getSetState(state)
    switchPage(-1)
  })
}

function nextPage () { switchPage(1) }

function previousPage () { switchPage(-1) }

function firstPage () {
  let state = getSetState()
  state.offset = 1
  setTimeout(x => { getSetState(state) }, 1) // prevent anchor loss
  // switchToLog(state.log)
}

function getCurrentRepo(){
  return currentRepo;
}

/********** Backup viewer frontend ********/
function _build_repo_card(repo, repo_data, backup_table_body) {
  // Optionally add the start button
  var reporun = "";
  if (("script" in repo_data) && (repo_data.script != "")) {
      reporun = `<button class='btn btn-dark pull-right btn-sm'>Run</button>`;
  }

  var repo_id=repo.replace(/[ -.:;#]/g, "")
  return `<div class="card text-white bg-secondary">
    <div class="card-header">
      <a class="repo-card-collapse" data-toggle="collapse" href="#card-content-${repo_id}">${repo}</a>
      <span class="badge badge-pill badge-dark repo-badge">
        ${repo_data.archives}
      </span>
      <span class='backup-${repo_data.last_result}' style="text-align:right">
        <span class="icon-success fas fa-check-circle"></span>
        <span class="icon-error fas fa-exclamation-circle"></span>
        <span  style="text-align:right">Last backup ${repo_data.last_date} at ${repo_data.last_time}</span>
      </span>
    </div>
    <div class="card-body collapse" id="card-content-${repo_id}">
      <div class="card text-white bg-dark">
        <div class="card-header"> Repo info</div>
        <div class="card-body">
          <ul class="list-group list-group-horizontal-md">
            <li class="list-group-item list-group-item-dark">
              Total size: ${filesize(repo_data.size)}
            </li>
            <li class="list-group-item list-group-item-dark">
              Compressed size: ${filesize(repo_data.csize)}
            </li>
            <li class="list-group-item list-group-item-dark">
              Deduped size: ${filesize(repo_data.dsize)}
            </li>
            <li class="list-group-item list-group-item-dark ">
              ${reporun}
            </li>
          </ul>
        </div>
      </div>
      <div class="card text-white bg-dark">
        <div class="card-header"> Backups info</div>
        <div class="card-body">
          <table class="backup-table table table-dark table-striped table-bordered table-sm">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Size</th>
                <th scope="col">Compr.</th>
                <th scope="col">Deduped</th>
              </tr>
            </thead>
            <tbody>${backup_table_body}</tbody>
          </table>
        </div>
      </div>
    </div></div>
  `;
}

/********** Pages entrypoints ********/
function cacheInvalidate(){
  $.get("cacheflush", (data)=>{
    $("#loadsign").show();
    viewBackups();
  });
}

// Backup page entry point
function viewBackups(){
  $.getJSON("backups", (data)=>{
    let repocards = "";
    $.each(data.repos, function(repo, repo_data){
        let backup_table_body = "";
        $.each(repo_data.backups, function(p, backup){
          // Add a line to the table for this backup
          backup_table_body = `<tr>
              <td>${backup.date}</td>
              <td>${filesize(backup.size)}</td>
              <td>${filesize(backup.csize)}</td>
              <td>${filesize(backup.dsize)}</td>
            </tr>` + backup_table_body;
        });

        // Build the repo global info
        repocards += _build_repo_card(repo, repo_data, backup_table_body)
    });

    // Update the backup graph
    var layout = {
      xaxis: {title: 'Backup date'},
      yaxis: {title: 'Backup size'},
      title: 'Stored backups'
    };
    var config = {
      scrollZoom: true,
      responsive: true
    }
    plotly.newPlot('backup-plot', data.bargraph, layout, config);

    // Add the repo html
    $("#refresh-time").empty().append(data.ctime);
    $("#repo-card-list").empty().append(repocards);
    $("#loadsign").hide();
    $("#backups-container").show();
  });

  // Display results
  $("#backups-container").show();
  $("#log-viewer, #pagination-row, #log-path, #repo-list-container").hide();
}

// Log page entry point
function viewRepositories(){
  // updateRepoList();
  // $("#log-files").empty();
  // addLogViewAdvise();
  // $("#backups-overview").hide();
  // $("#logs-overview").show();
  // $("#log-viewer, #log-list-container, #pagination-row, #repo-list-container").show();
}

module.exports = {
  getCurrentRepo: getCurrentRepo,
  updateRepoList: updateRepoList,
  viewBackups: viewBackups,
  cacheInvalidate:cacheInvalidate,
  viewRepositories: viewRepositories,
  render: render,
  switchToLog: switchToLog,
  getLogFiles: getLogFiles,
  nextPage: nextPage,
  previousPage: previousPage,
  updateLogFileList: updateLogFileList,
  firstPage: firstPage,
  lastPage: lastPage
}
