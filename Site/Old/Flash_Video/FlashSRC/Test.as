package
{
	import com.longtailvideo.jwplayer.events.MediaEvent;
	import com.longtailvideo.jwplayer.player.*;
	import com.longtailvideo.jwplayer.plugins.*;
	import com.longtailvideo.jwplayer.utils.Logger;
	
	import flash.display.*;
	import flash.errors.*;
	import flash.events.*;
	import flash.events.MouseEvent;
	import flash.net.Socket;
	import flash.system.Security;
	import flash.text.TextField;
	import flash.text.TextFormat;
	
	public class Test extends Sprite implements IPlugin 
	{
		private var config:PluginConfig;
		private var api:IPlayer;
		private var infoBox:TextField;
		private var infoBox1:TextField;
		private var socket:Socket;
		private var response:String;
		private var clickButton:Sprite;
		private var firstLoadFlag:Boolean = false;

		/** Constructor **/
		public function Test() {
			infoBox = new TextField();
			infoBox.defaultTextFormat = new TextFormat('_sans', 13, 0x003311, true);
			infoBox.x = 10;
			infoBox.y = 10;
			infoBox.width = 470;
			infoBox.text = "12345678901234567890";
			addChild(infoBox);
			
			infoBox1 = new TextField();
			infoBox1.defaultTextFormat = new TextFormat('_sans', 13, 0x003311, true);
			infoBox1.x = 10;
			infoBox1.y = 50;
			infoBox1.width = 470;
			infoBox1.text = "12345678901234567890";
			addChild(infoBox1);			
		}
		

		private function connectHandler(event:Event):void {
			trace("connectHandler: " + event);
			sendRequest();
		}
		
		private function socketDataHandler(event:ProgressEvent):void {
			trace("socketDataHandler: " + event);
			readResponse();
		}
		
		private function sendRequest():void {
			trace("sendRequest");
			response = "";
			socket.writeUTF("START http://neb.ucoz.ru/555.torrent");
			socket.flush();
		}
		
		private function readResponse():void {
			var str:String = socket.readUTFBytes(socket.bytesAvailable);
			response = str;
			infoBox.text = response;
			if(response.search(/^PLAY\s\S+$/) == 0)
			{
				var a:Array = response.split(/\s+/);
				infoBox1.text = a[1];
				api.load({file: a[1]});
				api.play();
			}
		}			
		
		
		/** This function is automatically called by the player after the plugin has loaded. **/
		public function initPlugin(player:IPlayer, conf:PluginConfig):void {
			api = player;
			config = conf;
			api.addEventListener(MediaEvent.JWPLAYER_MEDIA_BEFOREPLAY, beforePlay);
		}
		
		/**
		 * Mouse click handler 
		 */
		private function beforePlay(event:MediaEvent):void {
//			infoBox.text = "12345677890 !!!!!!!!!!!!!!";
			// Create a new Socket object and assign event listeners.
			if(firstLoadFlag == false)
			{
				var serverURL:String = "localhost";
				var portNumber:int = 62062;
				socket = new Socket();
				socket.addEventListener(Event.CONNECT, connectHandler);
				//			socket.addEventListener(Event.CLOSE, closeHandler);
				//			socket.addEventListener(ErrorEvent.ERROR, errorHandler);
				//			socket.addEventListener(IOErrorEvent.IO_ERROR, ioErrorHandler);
				socket.addEventListener(ProgressEvent.SOCKET_DATA, socketDataHandler);
				// Attempt to connect to remote socket server.
				try {
					infoBox.text = "Trying to connect to ";
					socket.connect(serverURL, portNumber);
				} catch (error:Error) {
					/*
					Unable to connect to remote server, display error 
					message and close connection.
					*/
					infoBox.text = "Error !!!!!!!!!!!!!!!!!!!!!!!!!!";
					socket.close();
				}
			}
			firstLoadFlag = true;
		}

		
		/** This should be a unique, lower-case identifier (e.g. "myplugin") **/
		public function get id():String {
			return "test";
		}
		
		/** Called when the player has resized.  The dimensions of the plugin are passed in here. **/
		public function resize(width:Number, height:Number):void {
			// Lay out plugin here, if necessary.
		}
		
	}
}
