# Web server that controls a Séguin dobby loom

This server is intended to allow you to control your loom from any phone, tablet or other device that has wifi and a web browser.

For for usage and installation instructions please see the [documentation](https://r-owen.github.io/base_loom_server/).

**Warning**: this software has not yet been tested on a real loom.
The documentation from Séguin is good, so I think the code is very close.
Meanwhile, trying it cannot hurt your loom, the only risk is that it will do nothing or raise the wrong shafts. I think it more likely that it will work, but may show incorrect status, as I had to make a guess about what one of the less important status bits means.
Initially I suggest running the server with command-line option `-v` (verbose) so you have more information for [filing a ticket](https://github.com/r-owen/seguin_loom_server/issues).

Links:

* seguin_loom_server depends on [base_loom_server](https://r-owen.github.io/base_loom_server/), which does most of the work.
* seguin_loom_server is served on [PyPI](https://pypi.org/project/seguin-loom-server/).
* Source code is on [github](https://r-owen.github.io/seguin_loom_server/).
* Please report issues using base_loom_server's [issue tracker](https://github.com/r-owen/base_loom_server/issues).
* Help with [translations to other languages](https://r-owen.github.io/base_loom_server/translations) is much appreciated. 
