# FastFastLauncher

## V 1.3
### New features:
 - FastFastLauncher now has a system tray icon
    - Context menu
        - Quit
        - Hide / Show window toggle
    - Hide / Show on icon double click
 - You can now hide FastFastLauncher toolbar from the tray icon
 - You can now also terminate the app from the tray icon

##### Tweaks:
 - Changed timeout when hovering from .5 sec to 1 sec
 - RecycleView is now hidden when searched term is deleted
 - Now hides under the top side of the screen when hovering over the window
 - Now uses `KivyOnTop` library at https://github.com/JakubBlaha/KivyOnTop
 - Cleaned up imports
 - Tweaked up some animations
 - Changed config file store location from `~\\Xtremeware\\FastFastLauncher\\paths.txt` to `~\\.xtremeware\\FastFastLauncher\\paths.txt`

##### Bugfixes:
 - Fixed PermissionDenied error on the first launch
 - Fixed bug which caused RecycleView to not reset on text deletion in search filed
 - Fixed bug which caused dropdown button to "fly away"
 - Fixed freeze when adding custom directory
 - Fixed bug which caused custom items didn't appear during and after search

##### Known Issues:
 - When hitting enter key on search, RecycleView does not collapse
 - FastFastLauncher can sometimes make other windows stay on top and resize them when quitting the app

## V 1.2
### New features:
 - Support for adding custom files
 - Support for window moving

## V 1.1
### New features:
 - You can now open file by hitting the *Enter* key after typing search expression
 - Window now stays always on top of other windows
 - Updated *dropdown* showing logic
 - Fixed few bugs

## V 1.0
*Initial release*
### Supports:
 - Desktop files indexing
 - Search tool
 - File opening by clicking 

*Please note that this version does not support opening files with Enter key hit*