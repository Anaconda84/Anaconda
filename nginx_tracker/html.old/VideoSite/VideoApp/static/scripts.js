  var ip;

  function init(url, torrent)
  {
    alert('url='+url+'   torrent='+torrent);
    var conn = new SockJS('http://localhost:6868/websocket');
    var err = true;

    function sendRequest()
    {
      err = false;
      conn.send('VERSION');
    };

    conn.onopen = function() 
    {
      alert('onopen');
      sendRequest();
    };

    conn.onmessage = function(e) 
    {
      chk_version(e.data);
      window.location.href = 'http://localhost:6878/get_video?url='+url+'&torrent='+torrent;
    };

    conn.onclose = function() {
      alert('onclose');
      if(err == true)
      {
        alert('Error !!!');
	error();
      }

    };


    conn.onerror = function() {
      alert('Error !!!');
    };
  }

  function error()
  {
    var parent = document.getElementsByTagName('BODY')[0];
    var par = document.createElement('parent_popup');
    par.id = 'parent_popup';
    var pop = document.createElement('popup');
    pop.id = 'popup';
    var par_r = parent.appendChild(par);
    var pop_r = par_r.appendChild(pop);

    pop_r.innerHTML = '<input type=\"button\" name=\"install\" value=\" Install \" onclick=\"install()\;\">';
    pop_r.innerHTML = pop_r.innerHTML + '<input type=\"button\" name=\"continue\" value=\" Continue \" onclick=\"next()\;\">';
    pop_r.innerHTML = pop_r.innerHTML + ' <p>Text in window.</p>';

  }

  function install() {
     alert('Button1');
     document.getElementById('parent_popup').style.display='none';
  }

  function next() {
//     var torrent = {{ str.torrent }};
//     alert(torrent);
     var sss = get_seeders('Volk');
     ip = sss.split(",");
     alert('ip='+ip[0]);
     document.getElementById('parent_popup').style.display='none';
     //document.getElementById('content').innerHTML = get_url('player.html');
     //window.open('http://107.22.233.233:8080/static/player.html');
     document.location.href = 'http://107.22.233.233:8080/static/player.html';
  }


  function getXmlHttp(){
    var xmlhttp;
    try {
      xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
      try {
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
      } catch (E) {
        xmlhttp = false;
      }
    }
    if (!xmlhttp && typeof XMLHttpRequest!='undefined') {
      xmlhttp = new XMLHttpRequest();
    }
    return xmlhttp;
  }

  function chk_version(swarm_version) {
      var req = getXmlHttp();
      req.onreadystatechange = function() { 
          if (req.readyState == 4) {
              if(req.status == 200) {
		  if(parseFloat(swarm_version) < parseFloat(req.responseText) )
		  {
		    error();
		  }
		  //alert('swarm_version=' + swarm_version);
		  //alert('Am server = ' + req.responseText);

              }
          }
      }
      req.open('GET', '/version', true); 
      req.send(null);
  }

  function get_seeders(torrent) {
      var req = getXmlHttp();
      var str = '/seeders/'+torrent;
      req.open('GET', str, false);
      req.send(null);
      if(req.status == 200) {
          return req.responseText;
      }
  }


  function get_url(url) {
      var req = getXmlHttp();
      var str = '/static/'+url;
      req.open('GET', str, false);
      req.send(null);
      if(req.status == 200) {
          return req.responseText;
      }
  }

  function get_async(url) {
      var req = getXmlHttp();
      var str = '/static/'+url;
      //var str = url;
      req.open('GET', str, true);

      req.onreadystatechange = function() {
        if (req.readyState == 4) {
           if(req.status == 200) {
             alert(req.responseText);
             return req.responseText;
           }
        }
      };

      req.send(null);
  }



