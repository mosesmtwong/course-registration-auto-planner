# Changelog

## v0.3

### v0.3 proper

#### Changes/Bugfixes

- Refactor API to remove any dependencies on `DefaultWindow`
- Change `process_all` to use a pipeline instead of just cramming EVERYTHING in one function
- Refactor `gui_helpers.py`
- Move functions from `gui_helpers` to `base_gui_helpers` to avoid circular import dependency
- Refactor `modules/course` and `modules/timetable` to include static/class functions
- Make the docs actually mean something instead of weirdly vague things
- Make the private time implementation actually make sense instead of it behaving very weirdly before

#### Known bugs

- Sometimes scraper does not work as intended, but this is easily solved by just retrying

## v0.2

Process all has been completed, additional functionalities are getting added!

### v0.2.3 ([commit link](https://github.com/mosesmtwong/RegFourMachine/commit/10a401661bd345b1950b84da89cdbd79e2d9ad43))

#### Additions

- Add credit viewer.

#### Changes/Bugfixes

- Fixed private time causing some conflicts with preassigned courses
- Minor patch on Course class (to accomodate new shitty style of course IDs)
- Fix major elective on browse program information bugging somehow
- Update internal functions of preferred courses to reflect credit count.
- Fixed the stupid select course just softlocking the program when it encounters an error in reading courses
- Patched the conflict resolver window just exploding due to an RGB glitch
- Hotfix: Fix tutorial sessions without any alphabet indicator just not showing up in the thing
- Hotfix: Error handling in assigning credits of _temp_filtered_course

#### Known bugs

- GUI just dies when there are no options left instead of showing the proper pop-up dialogue

### v0.2.2 ([commit link](https://github.com/mosesmtwong/RegFourMachine/commit/311125fd270b43fee010e2beafed8f6183041f56))

#### Additions

- Browse program information (for major) has been added (press the browse program information button to use)
- api updated with functions that can help with browsing program information

#### Changes/Bugfixes

- Split window module files into additional_windows and config_windows to avoid circular imports
- api should be able to be called by itself now

### v0.2.1 ([commit link](https://github.com/mosesmtwong/RegFourMachine/commit/632138bf045fb05091144752a2f2ec60e7d72494))

#### Additions

- Added private time window
- Added a link to [this site](https://cucampus.one/courses) to allow for further details on the course

#### Changes/Bugfixes

- updated README.md (it is now more humorous)

### v0.2 proper ([commit link](https://github.com/mosesmtwong/RegFourMachine/commit/ccd1e83e03d35c5bc5516f1a2d3071d03285ad92))

#### Additions

- Added selected_course functionality to process all button
- Non-draggable priority implemented for courses
- ConflictResolverWindow class to deal with user selection of preferred

## v0.1

"Major" update.

### v0.1.1

#### Additions

- Added a browser previewing function

#### Bugfixes

- Fixed timetable frame hogging memory (with too much widgets)
- Attempted to fix update_courses triggering more than once when changing faculty selection (unintended action)

### v0.1 proper

#### Additions

- Created an API to help with the Process all! button
- Created functions to make future scoring classes more easier
- Implemented dark mode functionality
- Moved previous window choosing functionality to *only* preassigned courses

#### Bugfixes

- Made scraper check if the inputs are proper and raise an exception if not
