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
  
* If you are using a Raspberry Pi, I strongly recommend [setting a permanent host name](https://www.tomshardware.com/how-to/static-ip-raspberry-pi), so you can always connect your web browser to the same address.
  This step is not necessary for macOS, because it always has a permanent host name.

* If you don't know the host name of the computer, you can query it with command: **hostname**

* Run the web server with command: **run_seguin_loom** ***port_name***

    * Special port name "mock" will run a simulated loom (no USB connection required).
      This can give you a chance to try out the user interface.
    
    * If you want to clear out old patterns, you can add the --reset-db argument: **run_seguin_loom** ***port_name*** **--reset-db**
      or select Clear Recents in the pattern menu in the web interface, see below.
  
* You may stop the web server by typing ctrl-C (probably twice).

## Running the Loom

Using any modern web browser, connect to the loom server at address **http://***hostname***:8000** where ***hostname*** is the host name you determined above.
In the resulting window:

* Upload one or more weaving pattern files (standard .wif or FiberWorks .dtx files).
  You can push the "Upload" button or drop the files anywhere onto the web page
  (please make sure the page is gray before you drop the files).

* Select the desired pattern using the "Pattern" drop-down menu.
  The menu shows the 25 most recent patterns you have used.
  You may switch patterns at any time, and the server remembers where were weaving in each of them.
  This allows you to load several treadlings for one threading (each as a separate pattern file) and switch between them at will.

* To clear out the pattern menu (which may become cluttered over time),
  select "Clear Recents", the last item in the menu.
  This clears out information for all patterns except the current pattern.
  If you want to get rid of the current pattern as well, first load a new pattern
  (or restart the server with the **--reset-db** command-line argument, as explained above).

You are now ready to weave.

* The pattern display shows woven fabric below and potential future fabric above.
  (This is the opposite of the usual US drawdown).

* There are two rectangles to the right of the pattern display:

    * The short upper rectangle shows the color of the current pick (blank if pick 0),
      or, if you have specified a pick to jump to, then it is the color of that pick.
  
    * The square lower rectangle is a button that shows whether you are weaving (green down arrow) or unweaving (red up arrow).
      The arrow points in the direction cloth is moving through the loom.
      You can change the weave direction by pressing this button, or by pressing the "UNW" button on the loom's control panel.

* To advance to the next pick (weaving or unweave, depending on the current direction):
  press the loom's pedal or the "PICK" button on the loom's control panel.

* To jump to a different pick and/or repeat is a two-step process:
  first you request the jump, then you advance to it by pressing the pedal or PICK button.
  (Two steps are necessary because the loom will not accept an unsolicited command to raise shafts.)
  In detail:

    * Enter the desired pick and/or repeat values.
      The input area(s) will turn pink and the Jump button will be enabled.

    * Press the "return" keyboard key, or press the "Jump" button on the web page
      to send the jump information to the server.
      You will see several changes:

      * The jump input areas will have a white background and the jump button will be disabled.

      * The pattern display will show this new pick in the center row, with a dotted box around it

    * Advance to the next pick (by pressing the loom's pedal or the PICK button on the loom's control panel).
      Until you advance to the new pick, you can request a different jump (in case you got it wrong the first time) or cancel the jump in several ways:
    
      * Press the "Reset" button to the right of "Jump".

      * Reload the page.

      * Select a new pattern.

* The software will automatically repeat patterns if you weave or unweave beyond the end.
  However, you must advance twice, when you reach an end, before the next set of shafts is raised.
  This is meant as a signal that you have finished one pattern repeat.
  On the first advance the display will show pick 0 and the repeat number will increase or decrease by 1,
  but the shed will not change.

*  Subtleties:

    * The server only allows one web browser to connect, and the most recent connection attempt wins.
      (This prevents a mystery connection from hogging the loom).
      If the connection is dropped on the device you want to use for weaving,
      simply reload the page to regain the connection.

    * Every time you connected to the web server or reload the page, the server refreshes
      its connection to the loom (by disconnecting and immediately reconnecting).
      So if the server is reporting a problem with its connection to the loom,
      and it is not due to the loom losing power or the USB cable becoming disconnected,
      you might try reloading the page.

## Remembering Patterns

The web server keeps track of the most recent 25 patterns you have used in a database
(including the most recent pick number and number of repeats, which are restored when you select a pattern).
The patterns in the database are displayed in the pattern menu.
If you shut down the server or there is a power failure, all this information should be retained.

If you are worried that the pattern database is corrupted, or just want to clear it, you can start the server with the **--reset-db** argument, as explained above.

## Developer Tips

* Download the source code from [github](https://github.com/r-owen/seguin_loom_server.git),
  or make a fork and download that.

* Inside the directory, issue the following commands:

    * **pip install -e .** (note the final period) to make an "editable installation" of the package.
      An editable installation runs from the source code, so changes you make to the source are used when you run or test the code, without the need to reinstall the package.

    * **pre-commit install** to activate the pre-commit hooks.

* You may run a mock loom by starting the server with: **run_seguin_loom mock**.
  The mock loom does not use a serial port.
  **run_seguin_loom mock** also accepts these command-line arguments:

    * **--reset-db** Reset the pattern database. Try this if you think the database is corrupted.

    * **--verbose** Print more diagnostic information.

* In mock mode the web page shows a few extra controls for debugging.

* Warning: automatic reload when you change the python code does not work;
  instead you have to kill the server with two control-C, then run it again.
  This may be a bug in uvicorn; see [this discussion](https://github.com/encode/uvicorn/discussions/2075) for more information.
