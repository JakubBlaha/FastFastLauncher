# FastFastLauncher

## v1.3.2
**Features**
 - Drag and drop to add a custom path.
 - Removed the *plus button* and the *file selector* for adding new paths.
 - Remebers the last window state.

**Bugfixes**
 - Fixed bug causing that it was needed to click twice when the window focus was lost in order to interact with the widgets.

**Other**
 - Window hide/show delay is now *1.5s*.
 - Few UI tweaks.

## v1.3.1
**Bugfixes**
 - Fixed bug which caused that you could do headbang with hide action.
 - Fixed bug which caused animation to stutter after some amout of times the hide/show action was triggered.

## v1.3
**New features**
 - Added a system tray icon.
 - Quit option in the *Context menu*.
 - Hide/Show window toggle in the *Context menu* and on tray icon double click.

**Tweaks**
 - Changed timeout when hovering from .5 sec to 1 sec.
 - RecycleView is now hidden when searched term is deleted.
 - Now hides under the top side of the screen when hovering over the window.
 - Now uses `KivyOnTop` library at https://github.com/JakubBlaha/KivyOnTop.
 - Cleaned up imports.
 - Tweaked up some animations.
 - Changed config file store location from `~\\Xtremeware\\FastFastLauncher\\paths.txt` to `~\\.xtremeware\\FastFastLauncher\\paths.txt`.

**Bugfixes**
 - Fixed PermissionDenied error on the first launch.
 - Fixed bug which caused RecycleView to not reset on text deletion in search filed.
 - Fixed bug which caused dropdown button to "fly away".
 - Fixed freeze when adding custom directory.
 - Fixed bug which caused custom items didn't appear during and after search.

## v1.2
**New features**
 - Support for adding custom files.
 - Support for window moving.

## v1.1
**New features**
 - You can now open file by hitting the *Enter* key after typing search expression.
 - Window now stays always on top of other windows.
 - Updated *dropdown* showing logic.

## v1.0
*Initial release*

**Supports**
 - Desktop files indexing.
 - Search tool.
 - File opening by clicking .
