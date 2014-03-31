CS3240Project
=============

##Sprint 2 Notes
###Brian's work: Authentication & Sessions
So guys I implemented some very basic session and authentication measures. 

For password creation, its hashed on the client side and just stored on the server. When you go to login, the client hashes the entered password and the server decides if its equal and responds accordingly. Pretty simple.

Now for sessions, I made it as easy as possible in order to do everything automagically. When you login successfully, you will get a UUID that will act as a session cookie essentially. My idea is that every time the client implements a server command, it uses the form /<action>/<session_cookie>/DATA. So on the server side I created a new sessions table, and every command will just ensure that the session cookie supplied is still valid (For now it always is) and you can get the username from the db. 

So I didn't have time to change all of your functions on server code to reflect that. So can someone do it? If not I can take care of it later. The code shouldn't be too hard to understand, its still pretty small.

~BTW

###Marbo:
Added two functions on serve side, upload function to upload a file through server and a send file function to be able to send a file from server to be downloaded.
