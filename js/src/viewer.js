let $ = require('jquery')
let plotly = require('plotly.js-dist')
let env = require('./env')
let util = require('./util')
let filesize = require('filesize')

/********** Log viewer frontend ********/
function _build_repolog_card(repo, repo_data) {

  var repo_id=repo.replace(/[ -.:;#]/g, "")
  var card_html = `<div class="card text-white bg-secondary">
    <div class="card-header">
      <a class="repo-card-collapse" data-toggle="collapse" href="#logcard-content-${repo_id}">${repo}</a>
      <span class="badge badge-pill badge-dark repo-badge">
        ${repo_data.length}
      </span>
    </div>
    <div class="card-body collapse" id="logcard-content-${repo_id}">
      <table class="backup-table table table-dark table-striped table-bordered table-sm">
        <thead><tr><th scope="col">Filename</th></tr></thead>
        <tbody>`;
  repo_data.forEach(function (item, index) {
    card_html += `          <tr><td>
          <span class='backup-${item.status}' style="text-align:right">
            <span class="icon-success fas fa-check-circle"></span>
            <span class="icon-warning fas fa-exclamation-circle"></span>
            <span class="icon-error fas fa-times-circle"></span>
            <span class="loglink" onclick='window.getLogData("${repo}", "${item.filename}")'>
              ${item.filename}
            </span>
          </span></td></tr>`;

  });
  card_html +='</tbody></table></div></div>';

  return card_html;
}

function updateRepoList () {
  $.getJSON("logs", (data)=>{
    let repocards = "";
    $.each(data, function(repo, repo_data) {
        // Build the repo global info
        repocards += _build_repolog_card(repo, repo_data);
    });
    $("#repologs-card-list").empty().append(repocards);
  });
}

function getLogData(repo, filename) {
  var log_path = repo+"/"+filename;
  $.getJSON("logs/"+log_path, (data)=>{
    $("#logcontent_name").empty().append(`
    <span class='backup-${data.status}' style="text-align:right">
      <span class="icon-success fas fa-check-circle"></span>
      <span class="icon-warning fas fa-exclamation-circle"></span>
      <span class="icon-error fas fa-times-circle"></span>
      <span'>${log_path}</span>
    </span>`);
    $("#logcontent_data").empty().append(data.content);
  });
}

function switchToLog(repo, filename) {
  viewRepositories();
  getLogData(repo, filename);
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
      <span class='backup-${repo_data.last_result} loglink' style="text-align:right" onclick='window.switchToLog("${repo}", "${repo_data.last_log}")'>

        <span class="icon-success fas fa-check-circle"></span>
        <span class="icon-warning fas fa-exclamation-circle"></span>
        <span class="icon-error fas fa-times-circle"></span>
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
  $("#logs-container").hide();
  $("#backups-container").show();
}

// Log page entry point
function viewRepositories(){
  updateRepoList();
  $("#backups-container").hide();
  $("#logs-container").show();
}

module.exports = {
  viewBackups: viewBackups,
  viewRepositories: viewRepositories,
  updateRepoList: updateRepoList,
  cacheInvalidate:cacheInvalidate,
  getLogData: getLogData,
  switchToLog: switchToLog,
}
