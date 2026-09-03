## 1. Recognise the link and the readable title

- [x] 1.1 Give a task a way to report its display title and its link from its stored fields alone; verify against synthetic titles covering an HTML anchor embedded in surrounding words, a plain `https` address, a bare domain with no scheme, a title with no address, a title with two addresses, and an anchor whose visible text differs from its target — asserting for each both what is displayed and what would be opened.
- [x] 1.2 Restrict what may be opened to `http` and `https`; verify a synthetic title carrying some other scheme yields no openable link, and that the allowlist is what decides rather than a list of blocked schemes.
- [x] 1.3 Confirm the rules against the five real stored links, read-only: verify each yields an openable `https` address, that the one stored as a bare domain gains a scheme, and that each display title keeps the words around the anchor and shows no tags. Do not modify any of them.

## 2. Show it and open it

- [x] 2.1 Render the row's title from the display title, escaping the task's own characters before adding any markup; verify an ordinary title is unchanged, a title containing square brackets shows them literally rather than losing them, and an anchor title shows the readable address with no tags.
- [x] 2.2 Present the address as a link span so a capable terminal can make it clickable, with the address quoted as Textual requires; verify the rendered content carries a link span over the address and that rendering raises no markup error. Note in the verification that whether a click works is a property of the terminal and is not being asserted.
- [x] 2.3 Show the readable title in the focus card too; verify a task whose title holds an anchor displays the address and surrounding words, with no tags, and that a long one is still shown in full.
- [x] 2.4 Bind opening the link to `o` and add it to the help overlay; verify the key opens the selected task's address by intercepting the framework's open call and asserting the exact address, so no browser is launched. Verify also that a task without a link opens nothing and says so, that an empty view opens nothing, and that the key bar and overlay both list the new key.

## 3. Verify end to end

- [x] 3.1 Confirm opening a link changes nothing: with a request spy, open the link of a synthetic task and verify no POST, PATCH or DELETE was sent and the task's stored fields are identical afterwards.
- [x] 3.2 Confirm it works wherever a task is selected: verify the action opens the address for a synthetic task selected in a day view, in the inbox and in the someday view.
- [x] 3.3 Confirm the wider blast radius of the escaping change: verify the inbox, today's view with its past-due ages, and the someday view all still render their titles correctly, that past-due colouring and the strike-through on finished tasks still apply, and that the row count and counts in the header are unchanged.
- [x] 3.4 Confirm nothing else regressed and no real task was touched: the focus card, date picker and delete confirmation still open, and a before-and-after snapshot of today and both buckets is identical — with any destructive keypress confined to a day holding no real tasks.
