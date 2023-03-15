NOTE
====

This branch is currently in a very unfinished, alpha state. As of right now, only buttons are supported. Help with development would be very much appreciated. If you're interested in helping, please keep an eye on the repo's issues and [the TODO-section of this readme](https://github.com/DisnakeCommunity/disnake-ext-components/tree/rewrite#to-do).

disnake-ext-components
======================

An extension for [disnake](https://github.com/DisnakeDev/disnake) aimed at making component interactions with listeners somewhat less cumbersome.  
Requires disnake version 2.5.0 or above and python 3.8.0 or above.

Key Features
------------
- Smoothly integrates with disnake,
- Uses an intuitive dataclass-like syntax to create stateless persistent components,
- `custom_id` matching, conversion, and creation are automated for you,
- (TODO for rewrite!) Allows you to implement custom RegEx for your listeners if you need more customized behavior.

Installing
----------

**Python 3.8 or higher and disnake 2.5.0 or higher are required**

To install the extension, run the following command in your command prompt/shell:

``` sh
# Linux/macOS
python3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-ext-components.git@rewrite

# Windows
py -3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-ext-components@rewrite
```
It will be installed to your existing [disnake](https://github.com/DisnakeDev/disnake) installation as an extension. From there, it can be imported as:

```py
from disnake.ext import components
```

Examples
--------
Coming soon!

To-Do
-----
- Implement customisable RegEx-based custom id,
- PyPI release,
- Contribution guidelines,

Contributing
------------
Any contributions are welcome, feel free to open an issue or submit a pull request if you would like to see something added. Contribution guidelines will come soon.
