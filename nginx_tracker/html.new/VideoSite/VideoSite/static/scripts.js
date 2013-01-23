  var ip;
  var torrent_file;

  function init(url, torrent)
  {
    BrowserDetect.init();
    var browser = BrowserDetect.browser;
    var version = BrowserDetect.version;
    var os = BrowserDetect.OS;
    
    alert('Cookie='+document.cookie);
    myCookie = getCookie("req");
    alert('cooke='+myCookie);
    alert('url='+url+'   torrent='+torrent);
    torrent_file = torrent;

    if(os == 'Windows' && (browser == 'Chrome' || browser == 'Firefox' || browser == 'Opera') && myCookie == null)
    {
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
    else
    {
      next();
    }
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
    
    setCookie("req", "answer", 5); // 60 min cookie
    alert('Set Cookie !!!!');
  }

  function install() {
     alert('Button1');
     document.getElementById('parent_popup').style.display='none';
  }

  function next() {
     var t = torrent_file.split("/");
     var webm_name = t[t.length-1].split(".")[0]+'.webm';
     alert('webm='+webm_name);
     var sss = get_seeders('Volk');
     ip = sss.split(",");
     alert('ip='+ip[0]);
     if(document.getElementById('parent_popup') != null) { document.getElementById('parent_popup').style.display='none'; }
     //document.location.href = '/static/player.html?ip='+sss+'&webm='+webm_name;
     var el = document.createElement("iframe");
     document.body.appendChild(el);
     el.id = 'iframe';
     el.src = '/static/player.html?ip='+sss+'&webm='+webm_name';

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

  function getParam(sParamName){
    var Params = location.search.substring(1).split("&");
    var variable = "";
    for (var i = 0; i < Params.length; i++){
        if (Params[i].split("=")[0] == sParamName){
            if (Params[i].split("=").length > 1) variable = Params[i].split("=")[1];
            return variable;
        }
    }
    return "";
  }

  function setCookie (name, value, expires, path, domain, secure) {
      alert(expires*1000 * 60);
      var today = new Date();
      today.setTime( today.getTime() );
      var expires_date = new Date( today.getTime() + (expires*1000 * 60) );

      document.cookie = name + "=" + escape(value) +
        ((expires) ? "; expires=" + expires_date.toGMTString() : "") +
        ((path) ? "; path=" + path : "") +
        ((domain) ? "; domain=" + domain : "") +
        ((secure) ? "; secure" : "");
  }

  function getCookie(name) {
	var cookie = " " + document.cookie;
	var search = " " + name + "=";
	var setStr = null;
	var offset = 0;
	var end = 0;
	if (cookie.length > 0) {
		offset = cookie.indexOf(search);
		if (offset != -1) {
			offset += search.length;
			end = cookie.indexOf(";", offset)
			if (end == -1) {
				end = cookie.length;
			}
			setStr = unescape(cookie.substring(offset, end));
		}
	}
        alert(setStr);
	return(setStr);
  }

   