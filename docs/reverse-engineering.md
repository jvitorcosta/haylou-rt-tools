# How this was worked out

This is the method, in case you want to extend it to another watch.

1. **Survey the watch.** `haylou scan` and `haylou survey` showed its services without writing
   anything, including a firmware-update service to avoid.
2. **Study the app.** The commands aren't documented, so the Android app was decompiled locally with
   [jadx](https://github.com/skylot/jadx) to find the frame format, command ids and pairing steps.
   Decompiled code is never added to this repository. Please keep it out of pull requests too.
3. **Confirm on the device.** Each finding was tested with harmless queries before anything else.
   That caught real surprises: alerts are acknowledged even when they aren't shown, and pairing
   stalls until each state change is acknowledged.
4. **Choose the safest route.** Sending a compiled face directly looked possible but could go wrong
   in ways that are hard to recover from. Community `.tbwf` files showed the app could do that part,
   so this project only writes a file format and leaves uploading to the app.
5. **Reimplement the app's drawing rules.** Generated faces looked misaligned because the preview guessed at
   text layout. Reading the app's drawing code gave the [real rules](drawing-rules.md).

## Lessons

- Treat an acknowledgement as "received", not "done".
- Check claims against the code: a "tenths of an hour" note here turned out to be hundredths.
- Keep the riskiest thing out of scope. The lack of an upload path is a feature.
