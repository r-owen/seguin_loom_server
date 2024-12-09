# Web server that controls a Séguin dobby loom.

This server is intended to allow you to control your loom from any phone, tablet or other device that has wifi and a web browser.

This server must run on a computer that is connected (via a USB cable) to your loom.
This code has only been tested on macOS but should also work on any flavor of linux.

Warning: this software has not yet been tested on a real loom.
I will do that once I have access to a loom (I am trying to order one now).

## Installing and Running the Web Server

* Decide which computer you will use to run the server.
  A macOS compute will work.
  A Raspberry Pi (probably a model 4 or better) is very likely to work; it is the computer I had in mind when I wrote this software.
  A Windows computer will probably work.

* Install [Python](https://www.python.org/downloads/) 3.11 or later on the computer.

* Install this "seguin_loom_server" package on the computer with command: **pip install seguin_loom_server**

* Determine the name of the port that your computer is using to connect to the loom.
  On macOS or linux:

    * Run the command **ls /dev/tty.usb\*** to see which USB ports already in use, if any.

    * Connect your computer to the loom with a USB cable.

    * Turn on the loom and wait a few seconds to let it connect.

    * Run the command **ls /dev/tty.usb\*** again. There should be one new entry,
      which is the name of the port connected to the loom.
  
* If you are using a Raspberry Pi, I strongly recommend [setting a permanent host name](https://www.tomshardware.com/how-to/static-ip-raspberry-pi), you can always connect your web browser to the same address.
  This step is not necessary for macOS, because it always has a permanent host name.

* If you don't know the host name of the computer, you can query it with command: **hostname**

* Run the web server with command: **run_seguin_loom** ***port_name***

  Note: special port name "mock" will run a simulated loom (no USB connection required).
  This can give you a chance to try out the user interface.
  
* You may stop the web server by typing ctrl-C (probably twice).
  Your current pick number and all uploaded patterns will be lost.

## Running the Loom

Using any modern web browser, connect to the loom server at address **http://***hostname***:8000** where ***hostname*** is the host name you determined above.
In the resulting window:

* Upload one or more weaving pattern files (.wif or FiberWorks .dtx files).
  You can push the "Upload" button or drop the files anywhere onto the web page
  (please make sure the page is gray before you drop the files).

* Select the desired pattern using the "Pattern" drop-down menu.
  You may switch patterns at any time, and the server remembers where you left off for each of them.
  This allows you to load several treadlings for one threading (each as a separate pattern file) and switch between them at will.

You are now ready to weave.

* The pattern display shows woven fabric below and potential future fabric above.
  (This is the opposite of the usual US drawdown).

* There are two buttons to the right of the pattern display:

    * The upper button shows the current pick color (blank if pick 0).
      Press it to advance to the next pick. 
      You may also advance by pressing the loom's pedal, or the "PICK"" button on the loom's control panel.
  
    * The lower button shows whether you are weaving (green down arrow) or unweaving (red up arrow).
      The arrow points in the direction cloth is moving through the loom.
      Press this button to change the direction.
      You may change direction by pressing the "UNW" button on the loom's control panel.

* To jump to a different pick and/or repeat:

    * Enter the desired value in the pick and repeat boxes.
      The boxes will turn pink and the Jump and Reset buttons will be enabled.

    * Type carriage return or press the "Jump" button to jump.
      Note: if a box is empty when you press "Jump", it will not change that value.

    * Press the "Reset" button to reset the displayed values.

    * Advancing to the next pick or choosing a new pattern will also reset the displayed values.

* The software will automatically repeat patterns if you weave or unweave beyond the end.
  However, you must advance twice, when you reach an end, before the next set of shafts is raised.
  This is meant as a signal that you have finished one pattern repeat.
  On the first advance the display will show pick 0 and the repeat number will change.

*  Subtleties:

    * Every time you connected to the web server or reload the page, the server refreshes
      its connection to the loom (by disconnecting and immediately reconnecting).
      So if the server is reporting a problem with its connection to the loom,
      and it is not due to the loom losing power or the USB cable becoming disconnected,
      you might try reloading the page.

    * The server only allows one web browser to connect, and the most recent connection attempt wins.
      (This prevents an old zombie connection from hogging the loom).
      If the connection is dropped on the device (e.g. phone or tablet) you want to use for weaving,
      simply reload the page on that device to regain the connection.

## Remembering Patterns

The web server keeps track of the most recent 25 patterns you have loaded (including the most recent pick number and number of repeats, which are restored when you select a pattern).

However, at present this information is only contained in memory.
It will be lost if the server loses power (or if you shut it down).
Thus it is safest to write down where you are at the end of a weaving session.

## Planned Improvements

* Test this software on a real loom.

* Add support for other languages.

* Use a database to store patterns and the current pick.

## Developer Tips

* Download the source code from [github](https://github.com/r-owen/seguin_loom_server.git),
  or make a fork and download that.

* Inside the directory, issue the following commands:

    * **pip install -e .** (note the final period) to install an "editable" version of the package.
      Meaning a version that runs from the source code, so any changes you make can be run without reinstalling.

    * **pre-commit install** to activate the pre-commit hooks.

* You may run a mock loom by starting the server with: **run_seguin_loom mock**.
  The mock loom does not use a serial port.

* In mock mode the web page shows a few extra controls for debugging.

* Warning: automatic reload when you change the python code does not work;
  instead you have to kill the server with two control-C, then run it again.
  This may be a bug in uvicorn; see [this discussion](https://github.com/encode/uvicorn/discussions/2075) for more information.
