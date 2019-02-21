$(document).ready(function() {
  var tables = ['gachi', 'bulldog', 'others', 'personalities', 'weeb'];
  var tableElements = ['playsoundgachi', 'playsoundbulldog', 'playsoundother', 'playsoundpersonality', 'playsoundweeb'];

  $.ajaxSetup({
    async: false
  });

  for (i = 0; i < tables.length; ++i) {
    var tableName = tables[i];
    var tableVar = document.getElementById(tableElements[i]);

    $.getJSON("http://178.128.205.181:7379/HGETALL/playsounds:" + tableName, function(result) {
      $.each(result["HGETALL"], function(name, url) {
        var row = tableVar.insertRow(0);

        // Fix all the spaghetti and make it into a normal meal
        row.insertAdjacentHTML('beforebegin', '\n      ')
        row.insertAdjacentHTML('afterend', '\n      ')

        var cell1 = row.insertCell(0);
        cell1.insertAdjacentHTML('beforebegin', '\n   	    ')
        var cell2 = row.insertCell(1);
        cell2.insertAdjacentHTML('beforebegin', '\n        ')
        cell2.insertAdjacentHTML('afterend', '\n      ')
        cell1.innerHTML = name;
        cell2.innerHTML = "\n          <audio id =\"" + name + "\" src = \"" + url + "\" onended=\"playOrStopSound(null, this);\"></audio>\n " +
          "<button name=\"" + name + "\" onclick=\"playOrStopSound(this, " + name + "); \" class=\"playsound-button\" alt=\"Added\">Play</button>\n        ";
        var audioObj = document.getElementById(name);
        audioObj.volume = 0.4;
      })
    });
  };
});

function playOrStopSound(elem, audio) {
  if (elem === null) {
    elem = document.getElementsByName(audio.id)[0];
  }

  if (elem.innerHTML === 'Stop') {
    elem.innerHTML = 'Play';
    audio.pause();
    audio.currentTime = 0;
    console.log('Ending ' + audio.id);
  } else {
    elem.innerHTML = 'Stop';
    audio.play();
    console.log('Playing ' + audio.id);
  }
}