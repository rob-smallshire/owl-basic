# Proposal: SkiaSharp graphics, windowing and input for OwlRuntime

Status: **draft for review**

## 1. Goal

Give compiled OWL BASIC programs a real interactive display: pixel graphics
(`PLOT`/`MOVE`/`DRAW`/`CIRCLE`/`FILL`/…), text rendered in the graphics modes,
**keyboard** input (`GET`/`INKEY`/`INPUT`), and **mouse**/pointer input
(`MOUSE`). Cross-platform (macOS, Linux, Windows).

This replaces the GDI+/WinForms graphics layer that is currently excluded from
the build (`OwlRuntime.csproj` `<Compile Remove>` of `*GraphicsScreenMode.cs`,
`VduForm.cs`, `AcornFont.cs`).

The headless text path (console + the grid-capture mode) must keep working
untouched, and console-only programs (the test suite, Sphinx) must **not** need
a window.

## 2. Current state (from the code)

- **Rendering model is simple and already buffer-based.** `BaseGraphicsScreenMode`
  draws every primitive into a single `System.Drawing.Bitmap` through a
  coordinate-transform matrix, then sets `NeedsRepaint` and the old `VduForm`
  (a WinForms `Form`) blits the bitmap in `OnPaint`. Paletted modes encode the
  logical colour in the blue channel and resolve it at paint time.
- **Drawing is synchronous** with VDU command processing — no game loop, no
  separate UI thread today.
- **The window was display-only.** `VduForm` had **no keyboard or mouse
  handlers**. So input from a window is entirely new.
- **Input today is console/stdin only.** `INPUT` uses `Console.ReadLine`;
  `INKEY` is a stub returning 100; there is no `GET`/`GET$` runtime, and **no
  `MOUSE` support at all**.
- **No NuGet dependencies.** `net10.0`, zero `PackageReference`s. We will add
  SkiaSharp and a windowing/input host.
- **The screen-mode interface is well-defined.** `AbstractScreenMode` declares
  the primitive family (`SolidLine…`, `PointPlot`, `RectangleFill`,
  `CircleFill`, `TriangleFill`, flood fill, `PrintCharAtGraphics/Text`, colour/
  palette updates, `ScrollTextArea`, `Dispose`). A SkiaSharp graphics mode
  implements these; the text modes already implement only the text subset.

## 3. Key decisions (need review)

### D1 — Windowing / input host

SkiaSharp **only renders**; it does not create windows or read input. We must
pick a host. The `.csproj` note said "SkiaSharp/Avalonia", but for a single
retro display with a game-loop feel, a lighter host fits better.

| Option | Window+input | Fit | Cost |
|---|---|---|---|
| **SDL2** (via `Silk.NET.SDL`) **+ SkiaSharp CPU raster** *(recommended)* | window, keyboard, mouse, present a pixel buffer (`SDL_Texture` streaming) | excellent — the emulator-standard model; matches our existing "draw to a buffer, blit" flow | native `libSDL2` to bundle per platform |
| **Silk.NET** windowing+input (GLFW) + SkiaSharp GPU (GL) | window, keyboard, mouse | good, but GL-centric: Skia renders to a GL surface | native GLFW; GPU backend complexity |
| **Avalonia** (uses SkiaSharp internally) | full UI framework | heavier; wants to own the app lifecycle/Main; MVVM overkill for one canvas | large dependency; awkward to host a synchronous BASIC program |

**Recommendation: SDL2 + SkiaSharp CPU raster.** Smallest conceptual gap from
today's "render into a bitmap, blit it", best fit for keyboard+mouse in a tight
loop, and the de-facto choice for this kind of program. Avalonia is the option
if a richer host GUI is wanted later.

### D2 — Threading & entrypoint (the load-bearing decision)

**macOS requires all windowing on the main thread (thread 0).** So the UI/event
loop must own the main thread, and the BASIC program must run on a worker
thread. That inverts today's model, where the generated `Main` *is* the program.

Proposed model:
- The runtime owns the real process entry. It decides **windowed vs headless**
  at startup (a graphics window can't be created lazily after the BASIC program
  has taken the main thread).
- **Windowed:** main thread runs the SDL event loop (poll input → buffers,
  present the Skia surface ~60 Hz / on dirty); the BASIC program runs on a
  worker thread; graphics commands mutate the render state (guarded), input
  commands read the thread-safe buffers.
- **Headless (default):** BASIC runs on the main thread exactly as now; no
  window, no UI loop. The console and grid-capture paths are unchanged.
- **Selection:** an env var (e.g. `OWL_WINDOW=1`), or auto when a graphics
  `MODE` is requested *and* a display is available. Open question (Q1).
- **Emitter impact:** the generated `Main` must hand its body to a runtime
  bootstrap (`OwlRuntime.Host.Run(programBody)`), rather than being the entry
  itself. Small, mechanical change in the `.NET` emitter's method template.

### D3 — Rendering target: CPU raster vs GPU

**Recommend CPU raster** (`SKSurface`/`SKBitmap` over a managed pixel buffer):
it is a near-direct translation of the existing `Bitmap` code, has no GL/Metal
context to manage, is trivially **capturable headless as a PNG** (see D4), and
is more than fast enough for BBC-resolution screens. GPU can come later if
needed.

### D4 — Windowless PNG capture as a first-class mode (not just a stepping stone)

Mirror what we did for text (`OWL_CAPTURE_SCREEN` → grid dump). A
`OWL_CAPTURE_GRAPHICS=<file.png>` mode renders the graphics screen with
SkiaSharp into an off-screen `SKSurface`, accumulating every primitive as the
program runs, and writes a PNG when the program exits (a `ProcessExit` handler,
exactly as `GridTextScreenMode` dumps its grid) — **no windowing, no threading,
no input**.

This is a genuinely useful end in itself, not only a de-risking step: a
non-interactive program (flexure is entirely non-interactive) never needs a
window — it just produces an image. So this mode:
- delivers flexure's actual plot as a viewable, diff-able image immediately;
- is fully testable (assert on pixels / a checked-in reference PNG), the same
  way the grid capture is;
- separates *rendering* (Phase 1) cleanly from *windowing and input* (later),
  letting us ship real graphics output long before the interactive window.

## 4. Proposed architecture

```
                 +-------------------------+
   BASIC program |  generated Main body    |   (worker thread when windowed)
   (worker)      +-----------+-------------+
                             | VDU stream
                       +-----v------+
                       | VduSystem  |  (existing state: cursors, colours, …)
                       +-----+------+
                             | screen-mode calls
        +--------------------+---------------------+
        |                    |                     |
  text modes        SkiaGraphicsScreenMode   (paletted / true variants)
  (unchanged)        renders into SKSurface
                             |
                       SKSurface (CPU raster pixels)
                       /                      \
            Phase 1: PNG capture        Phase 2: SDL window
            (headless, testable)        present pixels + event loop (main thread)
                                              |
                                        input events
                                              v
                                   KeyboardBuffer / MouseState  -> GET/INKEY/INPUT/MOUSE
```

- New `SkiaGraphicsScreenMode : BaseGraphicsScreenMode`-equivalent implementing
  the primitive family with `SKCanvas` (lines, fills, circles, triangles,
  flood-fill, char blit). Paletted vs true-colour as today, but Skia handles
  colour directly (the blue-channel trick can probably go away).
- `AcornFont` re-expressed as `SKBitmap` glyphs (or drawn as filled rects from
  the 8×8 bit patterns).
- The window/host is a separate, swappable component behind a small interface
  (`IDisplayHost`: present(pixels), pollInput()), so SDL can be replaced.

## 5. Input design

- **KeyboardBuffer**: a thread-safe queue of key events fed by the UI loop.
  `INKEY n` (timeout) and `GET`/`GET$` dequeue; `INKEY -n` tests a specific key
  (needs key-down state, not just a queue). `INPUT` reads a line from the buffer
  (with echo + editing) instead of `Console.ReadLine` when windowed.
- **MouseState**: current x/y (in BASIC graphics coords) and button mask,
  updated by the UI loop. `MOUSE x,y,b` reads it. This is new in the AST/
  grammar/emitter as well as the runtime (today there is a `MousePointer`/
  `MouseColour` node but no `MOUSE` read). Scope to confirm (Q2).
- Headless/console programs keep stdin behaviour; only the windowed host swaps
  the input source.

## 6. Incremental plan

1. **Phase 1 — SkiaSharp rendering, headless, PNG capture.** Add SkiaSharp;
   implement `SkiaGraphicsScreenMode` (primitives + font); wire a graphics
   `MODE` to it; `OWL_CAPTURE_GRAPHICS` writes a PNG. Tests assert on rendered
   output. *Delivers flexure's plot as an image. No windowing/threading.*
2. **Phase 2 — Windowing host (SDL).** `IDisplayHost` + SDL implementation; the
   runtime bootstrap and thread model (UI on main, BASIC on worker); present the
   Skia surface; window opens for graphics modes. *Delivers a live window.*
3. **Phase 3 — Keyboard from the window.** KeyboardBuffer; `GET`/`GET$`, real
   `INKEY`, windowed `INPUT`.
4. **Phase 4 — Mouse.** MouseState; `MOUSE` statement (AST/grammar/emitter/
   runtime); pointer.
5. **Phase 5 — Polish.** Palette/`COLOUR`/`GCOL` in graphics, `CLG`, rectangle
   copy/move, refresh throttling, mode geometry/aspect, fonts.

Each phase is independently testable and commits cleanly; Phase 1 is the
high-value, low-risk start.

## 7. Packaging

SkiaSharp ships a managed assembly plus a **native** `libSkiaSharp` per RID; SDL
adds native `libSDL2`. This intersects the earlier single-file/self-contained
discussion: a self-contained or NativeAOT publish must include the right native
libraries per platform. Framework-dependent runs need them beside the assembly
(the `owl-basic` copy step already does this for `OwlRuntime.dll`; it would copy
the natives too). To confirm in Phase 2 (Q3).

## 8. Risks & open questions

- **Q1 — Windowed vs headless selection:** explicit (`OWL_WINDOW`) or automatic
  on first graphics `MODE`? Automatic is nicer but conflicts with the main-thread
  constraint (we can't start the UI loop after the program is running on the
  main thread). Likely: decide at startup from the env var, with a future "auto"
  that inspects the program.
- **Q2 — Mouse scope:** how faithful to BBC/RISC OS `MOUSE` (coords, buttons,
  `MOUSE ON/OFF`, pointer shapes)? Minimal `MOUSE x,y,b` first?
- **Q3 — Native packaging:** bundling `libSkiaSharp`/`libSDL2` for self-contained
  and NativeAOT publishes; per-RID testing.
- **Q4 — Threading correctness:** the BASIC worker mutates render state read by
  the UI thread; needs a clear, cheap synchronisation (dirty flag + lock, or
  render from an immutable snapshot). Keep the BASIC side simple.
- **Q5 — Coordinate systems / aspect:** BBC graphics use a 1280×1024-ish logical
  space mapped to the mode's pixels with non-square pixels in some modes; get
  the transform and window aspect right (the old code had a matrix for this).
- **Risk — scope.** This is multi-phase. Phase 1 alone is a satisfying,
  shippable milestone (the plot becomes a real image); later phases can follow
  as appetite allows.

## 9. Recommendation

Build **Phase 1 (windowless SkiaSharp PNG capture) as a shippable feature**: it
makes flexure's plot a real, testable image and needs only SkiaSharp — no
windowing, threading or input. Defer the interactive window (SDL host,
UI-on-main/BASIC-on-worker, keyboard, mouse) until appetite calls for it; the
target there is still **SkiaSharp (CPU raster) + SDL2**, and the rendering code
written in Phase 1 is reused unchanged.
