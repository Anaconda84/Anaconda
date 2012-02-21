// -*- coding: utf-8 -*-
// vi:si:et:sw=2:sts=2:ts=2
/*
  TribeProtocolHandler - Torrent video for <video>
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

function checkDependencies() {
  var em = Cc["@mozilla.org/extensions/manager;1"].getService(Ci.nsIExtensionManager);
  var file = em.getInstallLocation('tribe@tribler.org').getItemFile('tribe@tribler.org', 'tribler/checkdep');
  file.permissions = 0755;
  var process = Cc["@mozilla.org/process/util;1"].createInstance(Ci.nsIProcess);
  process.init(file);
  process.run(false, [], 0);
}

function TribeProtocol() {
  this.prefService = Cc["@mozilla.org/preferences-service;1"].getService(Ci.nsIPrefBranch).QueryInterface(Ci.nsIPrefService);
  try {
    tribeLoggingEnabled = this.prefService.getBoolPref("tribe.logging.enabled");
  } catch (e) {}
}

TribeProtocol.prototype =
{
  classDescription: "tribe protocol",
  classID: Components.ID("bcb8d306-66cf-4358-8473-807981ffe365"),
  contractID: "@mozilla.org/network/protocol;1?name=tribe",
  extensionID: 'tribe@tribler.org',
  QueryInterface: XPCOMUtils.generateQI([Ci.nsIProtocolHandler,
                                         Ci.nsISupports]),
  _xpcom_factory : TribeProtocolFactory,
  scheme: "tribe",
  defaultPort: -1,
  protocolFlags: Ci.nsIProtocolHandler.URI_NORELATIVE |
             Ci.nsIProtocolHandler.URI_NOAUTH |
             Ci.nsIProtocolHandler.URI_LOADABLE_BY_ANYONE,

  allowPort: function(port, scheme)
  {
    return false;
  },

  newURI: function(spec, charset, baseURI)
  {
    var uri = Cc["@mozilla.org/network/simple-uri;1"].createInstance(Ci.nsIURI);
    uri.spec = spec;
    return uri;
  },

  newChannel: function(input_uri)
  {
    // aURI is a nsIUri, so get a string from it using .spec
    var key = input_uri.spec;

    // strip away the kSCHEME: part
    var torrent_url = key.substring(key.indexOf("://") + 3, key.length);    
    torrent_url = encodeURI(torrent_url);
    LOG('\nopening: '+torrent_url+'\n');

    var channel = Cc["@tribler.org/tribe/channel;1"].createInstance(Ci.tribeIChannel);
    channel.setTorrentUrl(torrent_url);
    return channel;
  },

} 

var TribeProtocolFactory =
{
  createInstance: function (outer, iid)
  {
    if (outer != null)
      throw Components.results.NS_ERROR_NO_AGGREGATION;

    if (!iid.equals(Ci.nsIProtocolHandler) &&
        !iid.equals(Ci.nsISupports) )
      throw Components.results.NS_ERROR_NO_INTERFACE;
    return (new TribeProtocol()).QueryInterface(iid);
  }
};

function NSGetModule(compMgr, fileSpec) {
  return XPCOMUtils.generateModule([TribeProtocol]);
}

