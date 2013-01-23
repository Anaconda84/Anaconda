    var exclude = '109.161.127.46';
    var number = 0;
    var cur_time = 0;
    var replay_time = 0;
  
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

          var ip = getParam("ip");
	  var ips = ip.split(",");

          var num = 0;
	  var newip = new Array()
	  for (var i=0; i <= ips.length-1; i++)
	  {
	    if(ips[i].toString() != exclude.toString()) { newip[num] = ips[i]; num++; }
	  }

          //alert('ip1='+ip);
	  //alert('ip2='+newip);

	  for (var i=0; i <= newip.length-1; i++)
	  {
	    var randomnumber=Math.floor(Math.random()*newip.length);
	    var buff = newip[i];
	    newip[i] = newip[randomnumber];
            newip[randomnumber] = buff;
	  }

	  alert('random='+newip);

	  var webm = getParam("webm");

	  var source = "http://"+newip[number]+":8888/"+webm;
          number++;
	  alert('source='+source);

	  myPlayer.addEvent("play", function()
  	  {
	    if(first == true)
	    {
	      first = false;
	      //myPlayer.src({ type: "video/webm", src: "http://localhost:6878/get_http_video?file=KKK.webm" });
	      myPlayer.src({ type: "video/webm", src: source });
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
	    alert('replay_time='+replay_time);
	    myPlayer.currentTime(replay_time);
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
  	    alert("ERROR !!!");
	    refresh('Error !!!');
	    // myPlayer.src({ type: "video/webm", src: "http://107.22.233.233:6878/KKK.webm" });


	    //myPlayer.currentTime(myPlayer.currentTime);

	    alert('Current time = '+cur_time);
	    replay_time = cur_time;

	    var source = "http://"+newip[number]+":8888/"+webm;
            number++;
	    alert('source='+source);
            myPlayer.src({ type: "video/webm", src: source });

            myPlayer.play();

	  });

	  myPlayer.addEvent("timeupdate", function()
	  {
	    cur_time = myPlayer.currentTime();
	    refresh('Time: '+cur_time);
	  });

    });
