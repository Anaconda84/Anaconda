// -*- coding: utf-8 -*-
// vi:si:et:sw=2:sts=2:ts=2
/*
  TribeChannel - Torrent video for <video>
  j@mailb.org 2009 - GPL 3.0
 */

Components.utils.import("resource://gre/modules/XPCOMUtils.jsm");

const Cc = Components.classes;
const Ci = Components.interfaces;

var tribeLoggingEnabled = false;

function LOG(aMsg) {
  if (tribeLoggingEnabled)
  {
    aMsg = ("*** Tribe : " + aMsg);
    Cc["@mozilla.org/consoleservice;1"].getService(Ci.nsIConsoleService).logStringMessage(aMsg);
    dump(aMsg);
  }
}


function TribeChannel() {
  this.prefService = Cc["@mozilla.org/preferences-service;1"].getService(Ci.nsIPrefBranch).QueryInterface(Ci.nsIPrefService);
  try {
    tribeLoggingEnabled = this.prefService.getBoolPref("tribe.logging.enabled");
  } catch (e) {}

}

TribeChannel.prototype =
{
  classDescription: "Tribe channel",
  classID: Components.ID("68bfe8e9-c7ec-477d-a26c-2391333a7a24"),
  contractID: "@tribler.org/tribe/channel;1",
  extensionID: 'tribe@tribler.org',
  QueryInterface: XPCOMUtils.generateQI([Ci.tribeIChannel,
                                         Ci.nsIChannel,
                                         Ci.nsISupports]),
  _xpcom_factory : TribeChannelFactory,
  init: false,
  torrent_url: '',
  setTorrentUrl: function(url) {
    this.torrent_url = url;
  },
  shutdown: function() {
    LOG("shutdown called\n"); 
    var msg = 'SHUTDOWN\r\n';
    this.outputStream.write(msg, msg.length);

    //this.outputStream.close();
    //this.inputStream.close();
    this.transport.close(Components.results.NS_OK);
  },
  asyncOpen: function(aListener, aContext)
  {
    var _this = this;
    if(this.init) {
      LOG('asyncOpen called again\n');
      throw Components.results.NS_ERROR_ALREADY_OPENED;
    }
    this.init = true;
    var socketTransportService = Cc["@mozilla.org/network/socket-transport-service;1"].getService(Ci.nsISocketTransportService);
    
    var hostIPAddr = "127.0.0.1";
    var hostPort = "62062";
    try {
      hostIPAddr = this.prefService.getCharPref("tribe.host.ipaddr");
    } catch (e) {}

    try {
      hostPort = this.prefService.getCharPref("tribe.host.port");
    } catch (e) {}

    this.transport = socketTransportService.createTransport(null, 0, hostIPAddr, hostPort, null);
    this.outputStream = this.transport.openOutputStream(0,0,0);
    this.inputStream = this.transport.openInputStream(0,0,0);

    var msg = 'START ' + this.torrent_url + '\r\n';
    this.outputStream.write(msg, msg.length);

    var dataListener = {
      onStartRequest: function(request, context) {},
      onStopRequest: function(request, context, status) {
        //background process not running, start it and try to connect in a second
        if(status == Components.results.NS_ERROR_CONNECTION_REFUSED) {
          _this.startBackgroundDaemon();
          _this.init=false;
          var timer = Cc["@mozilla.org/timer;1"].createInstance(Ci.nsITimer);
          timer.initWithCallback(function() { _this.asyncOpen(aListener, aContext) },
                                 1000, Ci.nsITimer.TYPE_ONE_SHOT);

        }
      },
      onDataAvailable: function(request, context, inputStream, offset, count) {
        var sInputStream = Cc["@mozilla.org/scriptableinputstream;1"].createInstance(Ci.nsIScriptableInputStream);
        sInputStream.init(inputStream);

        var s = sInputStream.read(count).split('\r\n');
        for(var i=0;i<s.length;i++) {
          var cmd = s[i];
          if (cmd.substr(0,4) == 'PLAY') {
            var video_url = cmd.substr(5);
            LOG('PLAY !!!!!! '+video_url+'\n');
            var ios = Cc["@mozilla.org/network/io-service;1"].getService(Ci.nsIIOService);
            var video_channel = ios.newChannel(video_url, null, null);
            video_channel.asyncOpen(aListener, aContext);

            //terminate connection to background daemon if the window gets closed
            var windowMediator = Cc["@mozilla.org/appshell/window-mediator;1"].getService(Ci.nsIWindowMediator);
            var nsWindow = windowMediator.getMostRecentWindow("navigator:browser");
            nsWindow.content.addEventListener("unload", function() { _this.shutdown() }, false);
            break;
          }
        }
      }
    };
    var pump = Cc["@mozilla.org/network/input-stream-pump;1"].createInstance(Ci.nsIInputStreamPump);
    pump.init(this.inputStream, -1, -1, 0, 0, false);
    pump.asyncRead(dataListener, null);
  },
  startBackgroundDaemon: function() {
    var em = Cc["@mozilla.org/extensions/manager;1"].getService(Ci.nsIExtensionManager);
    var file = em.getInstallLocation(this.extensionID).getItemFile(this.extensionID, 'tribler/triblerd');
    file.permissions = 0755;
    var process = Cc["@mozilla.org/process/util;1"].createInstance(Ci.nsIProcess);
    process.init(file);
    var args = [];
    if (tribeLoggingEnabled)
      args.push('debug');
    process.run(false, args, args.length);
  },
} 

var TribeChannelFactory =
{
  createInstance: function (outer, iid)
  {
    if (outer != null)
      throw Components.results.NS_ERROR_NO_AGGREGATION;

    if (!iid.equals(Ci.tribeIChannel) &&
        !iid.equals(Ci.nsIChannel) &&
        !iid.equals(Ci.nsISupports) )
      throw Components.results.NS_ERROR_NO_INTERFACE;

    return (new TribeChannel()).QueryInterface(iid);
  }
};

function NSGetModule(compMgr, fileSpec) {
  return XPCOMUtils.generateModule([TribeChannel]);
}

