/////////////////////////////////////
(function(jwplayer){

  var template = function(player, config, div) {
    function setup(evt) {
      if(document.getElementById('mediaplayer').mode == undefined)
      {
        document.getElementById('mediaplayer').mode = 'run';
        div.style.color = 'white';
        var conn = new SockJS('http://localhost:6868/websocket');


        function refresh(text) {
          div.innerHTML = text;
        }

        conn.onopen = function() {
          function sendRequest()
          {
            conn.send('START http://neb.ucoz.ru/333.torrent');
          }

          sendRequest();
        };

        conn.onmessage = function(e) {
          if( (myArray = /^PLAY\s(.+)/.exec(e.data)) != null)
          {
            //refresh(myArray[1]);
            refresh(e.data);
            jwplayer().load(myArray[1]);    
            jwplayer().play();    
          }
          else
          { 
	    refresh(e.data);
          }
        }

        conn.onclose = function() {
        };
      }
    };
    player.onBeforePlay(setup);
    player.onPlay(function() { div.innerHTML = ""; });
    player.onPause(function() { div.innerHTML = "The video paused."; });
    player.onBuffer(function() { div.innerHTML = "Video is buffering..."; });
    player.onIdle(function() { div.innerHTML = "The video stopped."; });

    this.resize = function(width, height) {};
  };


  jwplayer().registerPlugin('infomessages', template);

})(jwplayer);
