
    function refresh(text) {
	document.getElementById('output').innerHTML = text;
    }

    function supports_video() {
      return !!document.createElement('video').canPlayType;
    }

    function supports_webm_video() {
      if (!supports_video()) { return false; }
      var v = document.createElement("video");
      return v.canPlayType('video/webm; codecs="vp8, vorbis"');
    }

////  Video player //////////////////////////////////////////////
    _V_("video").ready(function()
    {
          var first = true;
          var myPlayer = this;
          var hide_play_message = false;
	  var time = 0;
	  myPlayer.addEvent("play", function()
  	  {
	    if(first == true)
	    {
	      first = false;
	      //myPlayer.src({ type: "video/webm", src: "http://localhost:6878/get_http_video?file=KKK.webm" });
	      myPlayer.src({ type: "video/webm", src: "http://107.21.204.102:8888/Volk.webm" });
              myPlayer.play();
          }
	    else
	    {
	      if(hide_play_message == false) refresh('Playing ...');
	    }
	  });

	  myPlayer.addEvent("loadstart", function()
	  {
	    hide_play_message = true;
            refresh('Prepare to start ...');
	  });

	  myPlayer.addEvent("loadeddata", function()
	  {
	    hide_play_message = false;
	    refresh('Playing ...');
	    myPlayer.pause();
	    myPlayer.currentTime(180);
	    myPlayer.play();
	  });

	  myPlayer.addEvent("pause", function()
	  {
	    refresh('Pause ...');
	  });

	  myPlayer.addEvent("ended", function()
	  {
	    refresh('Ended !!!');
	  });

	  myPlayer.addEvent("error", function()
	  {
	    refresh('Error !!!');
	    myPlayer.src({ type: "video/webm", src: "http://107.22.233.233:6878/KKK.webm" });
	    myPlayer.currentTime(time);

            myPlayer.play();

	  });

	  myPlayer.addEvent("timeupdate", function()
	  {
	    time = myPlayer.currentTime();
	  });

    });
