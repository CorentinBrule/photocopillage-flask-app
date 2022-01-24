
function getJSON(status_url){

  var request = new XMLHttpRequest();
  request.open('GET', status_url, true);

  request.onload = function() {
    if (request.status >= 200 && request.status < 400) {
      // Success!
      var data = JSON.parse(request.responseText);
      percent = parseInt(data['current'] * 100 / data['total']);

      status_div.querySelector("#step").innerText = data['current'];
      status_div.querySelector("#total").innerText = data['total'];
      status_div.querySelector("#percent").innerText = String(percent) + "%";
      status_div.querySelector("#status").innerText = data['status'];
      if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
          if ('result' in data) {
              hide_header();
              reload_images();
          }
          else {
              // something unexpected happened
              status_div.childNodes[3].innerText = 'Result: ' + data['state'];
          }
      }
      else {
          // rerun in 2 seconds
          setTimeout(function() {
              update_progress(status_url, status_div);
          }, 2000);
      }
    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.onerror = function() {
    // There was a connection error of some sort
  };

  request.send();

}

function hide_header(){
  console.log("plzidqzodqzhduqzz");
  document.querySelector("header").style.display = "none";
}

function reload_images(){
  var timestamp = new Date().getTime();
  var cover1 = document.querySelector(".cover1").firstElementChild;
  var cover4 = document.querySelector(".cover4").firstElementChild;
  cover1.src = cover1.src + "?t="+timestamp
  cover4.src = cover4.src + "?t="+timestamp
}

function update_progress(status_url, status_div) {
       // send GET request to status URL
       getJSON(status_url);
   }

function setup(){
  task_id = document.querySelector("#task_id").innerText;
  if(task_id !== "0"){
    status_div = document.querySelector(".progress");
    update_progress("/status/"+task_id, status_div);
  }else{
    hide_header();
  }
}

setup();
