if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined' ?
        args[number] :
        match;
    });
  };
}

var samples = {};

$(document).ready(function() {
  connect_to_ws();

  $.ajaxSetup({
    async: false
  });
  var tables = ['gachi', 'bulldog', 'others', 'personalities', 'weeb'];

  for (i = 0; i < tables.length; ++i) {
    $.getJSON("http://178.128.205.181:7379/HGETALL/playsounds:" + tables[i], function(result) {
      $.each(result["HGETALL"], function(name, url) {
        console.log(`samples[${name}] = ${url}`);
        samples[name] = {};
        samples[name]['url'] = url;
      });
    });
  };

  for (var key in samples) {
    sample = samples[key];
    var all_samples = [].concat(sample['url']);
    console.log(all_samples);
    sample['audio'] = [];
    for (url in all_samples) {
      sample['audio'].push(new Audio(all_samples[url]));
    }
  }
});

var isopen = false;

function add_random_box(color) {
  var divsize = 50;
  var posx = (Math.random() * ($(document).width() - divsize)).toFixed();
  var posy = (Math.random() * ($(document).height() - divsize)).toFixed();
  var $newdiv = $("<div class='exploding'></div>").css({
    'left': posx + 'px',
    'top': posy + 'px',
    'background-color': color,
    'opacity': 0
  });
  $newdiv.appendTo('body');
  $newdiv.animate({
    opacity: 1
  }, 500);
  setTimeout(function() {
    $newdiv.animate({
      opacity: 0,
    }, 1000);
    setTimeout(function() {
      $newdiv.remove();
    }, 1000);
  }, 5000);
}

function add_emote(emote) {
  var url = '';
  if ('bttv_hash' in emote && emote['bttv_hash'] !== null) {
    url = 'https://cdn.betterttv.net/emote/' + emote['bttv_hash'] + '/3x';
  } else if ('ffz_id' in emote && emote['ffz_id'] !== null) {
    url = 'http://cdn.frankerfacez.com/emoticon/' + emote['ffz_id'] + '/4';
  } else if ('twitch_id' in emote) {
    url = 'https://static-cdn.jtvnw.net/emoticons/v1/' + emote['twitch_id'] + '/3.0';
  } else {
    if (emote['code'] == 'xD') {
      url = 'https://cdn.pajlada.se/emoticons/XD.gif';
    }
  }
  var divsize = 120;
  var posx = (Math.floor(Math.random() * (1600 - 320) + 320)).toFixed();
  var posy = (Math.floor(Math.random() * (800 - 230) + 230)).toFixed();
  var $newdiv = $('<img class="absemote" src="' + url + '">').css({
    'left': posx + 'px',
    'top': posy + 'px',
    'opacity': 0
  });
  $newdiv.appendTo('body');
  $newdiv.animate({
    opacity: 1
  }, 1500);
  setTimeout(function() {
    $newdiv.animate({
      opacity: 0,
    }, 1000);
    setTimeout(function() {
      $newdiv.remove();
    }, 1000);
  }, 8500);
}

function remove_element() {
  var element = document.getElementById("clickme");
  element.parentNode.removeChild(element);
}

function show_custom_image(data) {
  var url = data.url;
  var divsize = 120;
  var posx = (Math.random() * ($(document).width() - divsize)).toFixed();
  var posy = (Math.random() * ($(document).height() - divsize)).toFixed();
  var css_data = {
    'left': posx + 'px',
    'top': posy + 'px',
    'opacity': 0
  }
  if (data.width !== undefined) {
    css_data.width = data.width;
  }
  if (data.height !== undefined) {
    css_data.height = data.height;
  }
  if (data.x !== undefined) {
    css_data.left = data.x + 'px';
  }
  if (data.y !== undefined) {
    css_data.top = data.y + 'px';
  }
  var $newdiv = $('<img class="absemote" src="' + url + '">').css(css_data);
  $newdiv.appendTo('body');
  $newdiv.animate({
    opacity: 1
  }, 500);
  setTimeout(function() {
    $newdiv.animate({
      opacity: 0,
    }, 1000);
    setTimeout(function() {
      $newdiv.remove();
    }, 1000);
  }, 5000);
}

var message_id = 0;

function add_notification(message, length) {
  var new_notification = $('<div>' + message + '</div>').prependTo('div.notifications');
  new_notification.textillate({
    autostart: false,
    in: {
      effect: 'bounceInLeft',
      delay: 5,
      delayScale: 1.5,
      sync: false,
      shuffle: false,
      reverse: false,
    },
    out: {
      effect: 'bounceOutLeft',
      sync: true,
      shuffle: false,
      reverse: false,
    },
    type: 'word',
  });
  new_notification.on('inAnimationEnd.tlt', function() {
    setTimeout(function() {
      new_notification.textillate('out');
      new_notification.animate({
        height: 0,
        opacity: 0,
      }, 1000);
    }, length * 1000);
  });
  new_notification.on('outAnimationEnd.tlt', function() {
    setTimeout(function() {
      new_notification.remove();
    }, 250);
  });
}

var current_emote_code = null;
var close_down_combo = null;

function refresh_combo_count(count) {
  $('#emote_combo span.count').html(count);
  $('#emote_combo span.count').addClass('animated pulsebig');
  $('#emote_combo span.count').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
    $(this).removeClass('animated pulsebig');
  });
  $('#emote_combo img').addClass('animated pulsebig');
  $('#emote_combo img').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
    $(this).removeClass('animated pulsebig');
  });
}

function refresh_combo_emote(emote) {
  var url = '';
  if ('bttv_hash' in emote && emote['bttv_hash'] !== null) {
    url = 'https://cdn.betterttv.net/emote/' + emote['bttv_hash'] + '/3x';
  } else if ('ffz_id' in emote && emote['ffz_id'] !== null) {
    url = 'http://cdn.frankerfacez.com/emoticon/' + emote['ffz_id'] + '/4';
  } else if ('twitch_id' in emote) {
    url = 'https://static-cdn.jtvnw.net/emoticons/v1/' + emote['twitch_id'] + '/3.0';
  } else {
    if (emote['code'] == 'xD') {
      url = 'https://cdn.pajlada.se/emoticons/XD.gif';
    }
  }
  $('#emote_combo img').attr('src', url);
}

function debug_text(text) {
  //add_notification(text);
}

function refresh_emote_combo(emote, count) {
  var emote_combo = $('#emote_combo');
  if (emote_combo.length == 0) {
    if ('bttv_hash' in emote && emote['bttv_hash'] !== null) {
      var url = 'https://cdn.betterttv.net/emote/' + emote['bttv_hash'] + '/2x';
    } else {
      var url = 'https://static-cdn.jtvnw.net/emoticons/v1/' + emote['twitch_id'] + '/2.0';
    }
    current_emote_code = emote['code'];
    var message = 'x<span class="count">{0}</span> <img class="comboemote" src="{1}" /> combo!'.format(count, url)
    var new_notification = $('<div id="emote_combo">' + message + '</div>').prependTo('div.notifications');
    new_notification.addClass('animated bounceInLeft');

    new_notification.on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
      if (new_notification.hasClass('ended')) {
        new_notification.animate({
          height: 0,
          opacity: 0,
        }, 500);
        setTimeout(function() {
          new_notification.remove();
        }, 500);
      }
    });

    clearTimeout(close_down_combo);
    close_down_combo = setTimeout(function() {
      new_notification.addClass('animated bounceOutLeft ended');
    }, 4000);
  } else {
    clearTimeout(close_down_combo);
    close_down_combo = setTimeout(function() {
      emote_combo.addClass('animated bounceOutLeft ended');
    }, 3000);
    refresh_combo_emote(emote);
    refresh_combo_count(count);
  }
}

function create_object_for_win(points) {
  return {
    value: points,
    color: '#64DD17',
  }
}

function create_object_for_loss(points) {
  return {
    value: points,
    color: '#D50000',
  }
}

var hsbet_chart = false;

function hsbet_set_data(win_points, loss_points) {
  if (hsbet_chart !== false) {
    hsbet_chart.segments[0].value = win_points;
    hsbet_chart.segments[1].value = loss_points;
    hsbet_chart.update();
  }
}

function dotabet_update_data(win_betters, loss_betters, win_points, loss_points) {
  $('#winbetters').text(win_betters);
  $('#lossbetters').text(loss_betters);
  $('#winpoints').text(parseInt($('#winpoints').text()) + win_points);
  $('#losspoints').text(parseInt($('#losspoints').text()) + loss_points);
}

function create_graph(win, loss) {
  var ctx = $('#hsbet .chart').get(0).getContext('2d');
  if (win == 0) {
    win = 1;
  }
  if (loss == 0) {
    loss = 1;
  }
  var data = [
    create_object_for_win(win),
    create_object_for_loss(loss),
  ];
  var options = {
    animationSteps: 100,
    animationEasing: 'easeInOutQuart',
    segmentShowStroke: false,
  };
  if (hsbet_chart === false || true) {
    hsbet_chart = new Chart(ctx).Pie(data, options);
  } else {
    hsbet_set_data(win, loss);
  }
}

function dotabet_new_game() {
  var dotabet_el = $('#dotabet');
  dotabet_el.find('.left').css({
    'visibility': 'visible',
    'opacity': 1
  });

  dotabet_el.hide();

  $('#winbetters').text('0');
  $('#lossbetters').text('0');
  $('#winpoints').text('0');
  $('#losspoints').text('0');

  dotabet_el.find('.left').show();
  dotabet_el.fadeIn(1000, function() {
    console.log('Faded in');
  });
}

function dotabet_close_bet() {
  var dotabet_el = $('#dotabet')
  dotabet_el.fadeOut(10000, function() {
    dotabet_el.find('.left').css('visibility', 'hidden');
  });
}

function play_sound(sample) {
  sample = sample.toLowerCase();
  if (sample in samples) {
    var r = Math.floor(Math.random() * samples[sample]['audio'].length);
    console.log(r);
    var cloned_sample = samples[sample]['audio'][r].cloneNode();
    console.log(cloned_sample);
    cloned_sample.volume = 0.25;
    const playPromise = cloned_sample.play();
    if (playPromise !== null){
      playPromise.catch(() => { cloned_sample.play(); })
    }
  }
}

function play_custom_sound(url) {
  var audio = new Audio(url);
  audio.volume = 0.4;
  audio.play();
}

function connect_to_ws() {
  if (isopen) {
    return;
  }
  console.log('Connecting to websocket....');
  var host = ws_host;
  var port = ws_port;
  socket = new WebSocket(host + ':' + port);
  console.log('Starting website on ' + host + ':' + port);
  socket.binaryType = "arraybuffer";
  socket.onopen = function() {
    console.log('Connected!');
    isopen = true;
  }

  socket.onmessage = function(e) {
    if (typeof e.data == "string") {
      var json_data = JSON.parse(e.data);
      console.log(json_data);
      if (json_data['event'] !== undefined) {
        switch (json_data['event']) {
          case 'new_box':
            add_random_box(json_data['data']['color']);
            break;
          case 'new_emote':
            add_emote(json_data['data']['emote']);
            break;
          case 'notification':
            !('length' in json_data['data']) && (json_data['data'].length = 2)
            add_notification(json_data['data']['message'], json_data['data']['length']);
            break;
          case 'timeout':
            add_notification('<span class="user">' + json_data['data']['user'] + '</span> timed out <span class="victim">' + json_data['data']['victim'] + '</span> with !paidtimeout EleGiggle', 2);
            break;
          case 'play_sound':
            play_sound(json_data['data']['sample']);
            break;
          case 'play_custom_sound':
            play_custom_sound(json_data['data']['url']);
            break;
          case 'emote_combo':
            refresh_emote_combo(json_data['data']['emote'], json_data['data']['count']);
            break;
          case 'dotabet_new_game':
            dotabet_new_game();
            break;
          case 'dotabet_update_data':
            dotabet_update_data(json_data['data']['win_betters'], json_data['data']['loss_betters'],
              json_data['data']['win'], json_data['data']['loss']);
            break;
          case 'dotabet_close_game':
            dotabet_close_bet();
            break;
          case 'show_custom_image':
            show_custom_image(json_data['data']);
            break;
          case 'refresh':
          case 'reload':
            location.reload(true);
            break;
        }
      }
    } else {
      var arr = new Uint8Array(e.data);
      var hex = '';
      for (var i = 0; i < arr.length; i++) {
        hex += ('00' + arr[i].toString(16)).substr(-2);
      }
      //add_row('Binary message received: ' + hex);
    }
  }

  socket.onclose = function(e) {
    socket = null;
    isopen = false;
    setTimeout(connect_to_ws, 2500);
  }
}
