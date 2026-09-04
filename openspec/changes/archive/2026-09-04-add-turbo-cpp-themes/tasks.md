## 1. Define the two themes

- [x] 1.1 Define the dark Turbo theme from the editor theme's own values — its ordinary text, selection, error, link, chrome, surface and muted colours; verify each equals the value the editor theme file declares for that role, reading that file rather than trusting a transcription. Its ground is a deliberate departure to pure black, so verify instead that it is black and that the reason is recorded at the definition.
- [x] 1.2 Define the blue variant sharing the first's text, selection, error and link colours and differing only where the editor theme differs; verify the shared colours are identical between the two and that the ground and chrome are the blue theme's own.
- [x] 1.3 State the blue variant's muted colour outright rather than letting it derive, since deriving from a foreground identical to ordinary text yields no distinction; verify the resolved muted colour differs from the resolved ordinary text colour under that theme.

## 2. Put them on the board

- [x] 2.1 Register both themes and start the board in the black-ground one; verify both appear among the selectable themes, that the board's active theme at startup is the black-ground Turbo one, and that the framework's own themes are still available.
- [x] 2.2 Switch between them at runtime; verify choosing the other Turbo theme redraws the board in it, and that switching back and forth leaves the view, the selected row and the counts unchanged.
- [x] 2.3 Make the bars take an automatically contrasting foreground so one stylesheet serves both; verify the resolved text colour on the day header and the key bar is dark under the blue theme and light under the black-ground one, reading the rendered output rather than the requested style, since the automatic value only resolves at paint time.

- [x] 2.4 Make the task list render on the ground it is given rather than over the raised surface, with no shading of alternate rows and no tint blended over it; verify under each theme that the colour filling the list equals the theme's ground, that no intermediate shade between the ground and the chrome is painted, and that the row count and past-due count are unaffected.

## 3. Verify the board stays legible

- [x] 3.1 Under each offered theme, verify a past-due title and an ordinary title resolve to different colours, and that neither equals the ground behind it.
- [x] 3.2 Under each offered theme, verify muted text — the status line, the project column, the detail strip, the key bar's labels — resolves to a different colour from an ordinary task title.
- [x] 3.3 Under each offered theme, verify the selected row's background differs from the surrounding rows and that its text is legible against it, and that a link in a title is drawn differently from the rest of the title.
- [x] 3.4 Confirm this change alters nothing but colour: with a request spy, switch themes and move between all three views and verify no POST, PATCH or DELETE was sent; that the inbox counts, today's past-due count and ages, the focus card, the date picker and the delete confirmation all behave as before; and that a before-and-after snapshot of today and both buckets is identical.
