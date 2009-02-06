using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    internal class VduSystem : IDisposable
    {
        #region Official VDU Variables

        // TODO: Rename variable with longer more readable names. Leave the original names in the comments.
        //                    Acorn name - Acorn description
        [VduVariable(128)]
        private int graphicsWindowLeftCol;   // gWLCol - Left-hand column of the graphics window (ic)

        [VduVariable(129)]
        private int graphicsWindowBottomRow; // gWBRow - Bottom row of the graphics window (ic)

        [VduVariable(130)]
        private int graphicsWindowRightCol;  // gWRCol - Right-hand column of the graphics window (ic)

        [VduVariable(131)]
        private int graphicsWindowTopRow;    // gWTRow - Top row of the graphics window (ic)

        [VduVariable(132)]
        private int textWindowLeftCol;       // TWLCol - Left-hand column of the text window

        [VduVariable(133)]
        private int textWindowBottomRow;     // TWBRow - Bottom row of the text window

        [VduVariable(134)]
        private int textWindowRightCol;      // TWRCol - Right-hand column of the text window

        [VduVariable(135)]
        private int textWindowTopRow;        // TWTRow - Top row of the text window

        [VduVariable(136)]
        private int originX;                  // OrgX - x coordinate of the graphics origin (ec)

        [VduVariable(137)]
        private int originY;                  // OrgY - Y coordinate of the graphics origin (ec)

        [VduVariable(138)]
        private int graphicsCursorX;         // GCsX - x coordinate of the graphics cursor (ec)

        [VduVariable(139)]
        private int graphicsCursorY;         // GCsY - Y coordinate of the graphics cursor (ec)

        [VduVariable(140)]
        private short olderCsX; // olderCsX - x coordinate of oldest graphics cursor (ic)

        [VduVariable(141)]
        private short olderCsY; // olderCsY - Y coordinate of oldest graphics cursor (ic)

        [VduVariable(142)]
        private short oldCsX; // oldCsX - x coordinate of previous graphics cursor (ic)

        [VduVariable(143)]
        private short oldCsY; // oldCsY - Y coordinate of previous graphics cursor (ic)

        [VduVariable(144)]
        private short gCsIX; // gCsIX - x coordinate of graphics cursor (ic)

        [VduVariable(145)]
        private short gCsIY; // gCsIY - Y coordinate of graphics cursor (ic)

        [VduVariable(146)]
        private short newPtX; // newPtX - x coordinate of new point (ic)

        [VduVariable(147)]
        private short newPtY; // newPtY - Y coordinate of new point (ic)
        [VduVariable(148)]
        private int ScreenStart; // ScreenStart - Address of the start of screen used by VDU driver
        [VduVariable(149)]
        private int DisplayStart; // DisplayStart - Address of the start of screen used by display hardware
        [VduVariable(150)]
        private int TotalScreenSize; // TotalScreenSize - Amount of memory currently allocated to the screen
        [VduVariable(151)]
        private int GPLFMD; // GPLFMD - GCOL action for foreground colour
        [VduVariable(152)]
        private int GPLBMD; // GPLBMD - GCOL action for background colour
        [VduVariable(153)]
        private int graphicsForegroundColour; // GFCOL - Graphics foreground colour
        [VduVariable(154)]
        private int graphicsBackgroundColour; // GBCOL - Graphics background colour
        [VduVariable(155)]
        private int textForegroundColour; // TForeCol - TForeCol Text foreground colour
        [VduVariable(156)]
        private int textBackgroundColour; // TBackCol - TBackCol Text background colour
        [VduVariable(157)]
        private int graphicsForegroundTint; // GFTint - Tint for graphics foreground colour
        [VduVariable(158)]
        private int graphicsBackgroundTint; // GBTint - Tint for graphics background colour
        [VduVariable(159)]
        private int textForegroundTint; // TFTint - Tint for text foreground colour
        [VduVariable(160)]
        private int textBackgroundTint; // TBTint - Tint for text background colour
        [VduVariable(161)]
        private int MaxMode; // MaxMode - Highest mode number available
        [VduVariable(162)]
        private int graphicsCharSizeX; // GCharSizeX - x size of VDU 5 chars (in pixels)
        [VduVariable(163)]
        private int graphicsCharSizeY; // GCharSizeY - Y size of VDU 5 chars (in pixels)
        [VduVariable(164)]
        private int graphicsCharSpaceX; // GCharSpaceX - x spacing of VDU 5 chars (in pixels)
        [VduVariable(165)]
        private int graphicsCharSpaceY; // GCharSpaceY - Y spacing of VDU 5 chars (in pixels)
        [VduVariable(166)]
        private int HLineAddr; // HLineAddr - Address of fast line-draw routine
        [VduVariable(167)]
        private int textCharSizeX; // TCharSizeX - x size of VDU 4 chars (in pixels)
        [VduVariable(168)]
        private int textCharSizeY; // TCharSizeY - Y size of VDU 4 chars (in pixels)
        [VduVariable(169)]
        private int textCharSpaceX; // TCharSpaceX - x spacing of VDU 4 chars (in pixels)
        [VduVariable(170)]
        private int textCharSpaceY; // TCharSpaceY - Y spacing of VDU 4 chars (in pixels)
        [VduVariable(171)]
        private int GcolOraEorAddr; // GcolOraEorAddr - Address of colour blocks for current GCOL
        [VduVariable(172)]
        private int VIDCClockSpeed; // VIDCClockSpeed - VIDC clock speed in kHz (eg 24000 Þ 24 MHz) – not available in RISC OS 2.0
        [VduVariable(256)]
        private int WindowWidth; // WindowWidth - Characters that will fit on a row of the text window without a newline being generated
        [VduVariable(257)]
        private int WindowHeight; // WindowHeight - Rows that will fit in the text window without scrolling it
        #endregion

        private VduForm vduForm;
        private byte modeNumber;
        private AbstractScreenMode screenMode = AbstractScreenMode.CreateScreenMode(7);

        private int graphicsBackgroundPaletteIndex ;

        // The VDU queue
        private readonly Queue<byte> queue = new Queue<byte>();
        private int requiredBytes;
        private Action nextCommand;
        private bool hasBeenDisposed = false;


        public VduSystem()
        {
            ExpectVduCommand();
        }

        public int GraphicsBackgroundColour
        {
            get { return graphicsBackgroundColour; }
            private set
            {
                graphicsBackgroundColour = value;
                if (screenMode.BitsPerPixel == 8)
                {
                    graphicsBackgroundPaletteIndex = 0;
                    graphicsBackgroundPaletteIndex |= (graphicsForegroundColour & 33) << 2;
                    graphicsBackgroundPaletteIndex |= (graphicsForegroundColour & 14) << 3;
                    graphicsBackgroundPaletteIndex |= (graphicsForegroundColour & 16) >> 1;
                    graphicsBackgroundPaletteIndex |= graphicsForegroundTint >> 6;
                }
            }
        }

        public byte ModeNumber
        {
            get { return modeNumber; }
        }

        public void Enqueue(byte b)
        {
            // If all bytes in the queue have been consumed, wait for the
            // next VDU command
            queue.Enqueue(b);
            ExecutePendingCommand();
        }

        public void Enqueue(params byte[] bs)
        {
            foreach (byte b in bs)
            {
                Enqueue(b);
            }
        }

        public void Enqueue(short s)
        {
            // TODO: Check order!
            Enqueue((byte) (s & 0xFF)); // lo byte
            Enqueue((byte) (s >> 8));   // hi byte
        }

        public void Enqueue(params short[] ss)
        {
            foreach (short s in ss)
            {
                Enqueue(s);
            }
        }

        private void ExecutePendingCommand()
        {
            if (queue.Count >= requiredBytes)
            {
                nextCommand();
                Refresh();
            }
        }

        private void Refresh()
        {
            if (vduForm != null)
            {
                vduForm.Refresh();
            }
        }

        public void DoVduDispatch()
        {
            byte code = DequeueByte();
            // PRM 1-513
            if (code <= 31)
            {
                Control(code);
            }
            else if (code <= 126)
            {
                DisplayCharacter(code);
            }
            else if (code == 127)
            {
                DeleteCharacter();
            }
            else if (code <= 159)
            {
                DisplayUserCharacter(code);
            }
            else
            {
                DisplayCharacter(code);
            }
        }

        private void DisplayUserCharacter(byte code)
        {
            throw new NotImplementedException();
        }

        private void DeleteCharacter()
        {
            throw new NotImplementedException();
        }

        private void DisplayCharacter(byte code)
        {
            throw new NotImplementedException();
        }

        private void Control(byte code)
        {
            switch (code)
            {
                case 0:
                    // no-op
                    break;
                case 1:
                    NextCharacterPrinterOnly();
                    break;
                case 2:
                    EnablePrinterStream();
                    break;
                case 3:
                    DisablePrinterStream();
                    break;
                case 4:
                    SplitCursors();
                    break;
                case 5:
                    JoinCursors();
                    break;
                case 6:
                    EnableConsoleStream();
                    break;
                case 7:
                    Bell();
                    break;
                case 8:
                    Backspace();
                    break;
                case 9:
                    HorizontalTab();
                    break;
                case 10:
                    LineFeed();
                    break;
                case 11:
                    VerticalTab();
                    break;
                case 12:
                    ClearConsole();
                    break;
                case 13:
                    CarriageReturn();
                    break;
                case 14:
                    PagedModeOn();
                    break;
                case 15:
                    PagedModeOff();
                    break;
                case 16:
                    ClearGraphicsWindow();
                    break;
                case 17:
                    requiredBytes = 1;
                    nextCommand = SetTextColour;
                    break;
                case 18:
                    requiredBytes = 2;
                    nextCommand = SetGraphicsColour;
                    break;
                case 19:
                    SetPalette();
                    break;
                case 20:
                    SetPaletteDefault();
                    break;
                case 21:
                    DisableConsoleStream();
                    break;
                case 22:
                    requiredBytes = 1;
                    nextCommand = DoSetMode;
                    break;
                case 23:
                    requiredBytes = 9;
                    nextCommand = DoMiscellaneousCommands;
                    break;
                case 24:
                    requiredBytes = 8;
                    nextCommand = DoDefineGraphicsWindow;
                    break;
                case 25:
                    requiredBytes = 5;
                    nextCommand = DoPlot;
                    break;
                case 27:
                    // no-op
                    break;
                case 28:
                    requiredBytes = 8;
                    nextCommand = DoDefineTextWindow;
                    break;
                case 29:
                    requiredBytes = 4;
                    nextCommand = DoSetOrigin;
                    break;
                case 30:
                    CursorHome();
                    break;
                case 31:
                    requiredBytes = 2;
                    nextCommand = DoSetCursorPos;
                    break; 
                default:
                    throw new ArgumentOutOfRangeException();
            }
        }

        private void DoSetCursorPos()
        {
            // TODO i dont know where the cursor position is stored
            // x = DequeueByte();
            // y = DequeueByte();
            throw new NotImplementedException();
        }

        private void CursorHome()
        {
            throw new NotImplementedException();
        }

        private void DoSetOrigin()
        {
            originX = DequeueShort();
            originX = DequeueShort();
        }

        private void SetGraphicsColour()
        {
            // prm1-586
            // is equiv to GCOL k,c
            int k = DequeueByte();
            if ((k & 128) != 0) // if top bit set then background GCOL action
            {
                GPLBMD = (k & 127);
            }
            else
            {
                GPLFMD = k;
            }
            
            int c = DequeueByte();
            if ((c & 128) != 0)// if top bit set then background GCOL color
            {
                graphicsBackgroundColour = c & 63; // only bottom 6 bits used for color
            }
            else
            {
                graphicsForegroundColour = c & 63;
            }
            ExpectVduCommand();
        }

        private void DoDefineTextWindow()
        {
            graphicsWindowLeftCol = DequeueShort();
            graphicsWindowBottomRow = DequeueShort();
            graphicsWindowRightCol = DequeueShort();
            graphicsWindowTopRow = DequeueShort();
            ExpectVduCommand();
        }

        private void DisablePrinterStream()
        {
            throw new NotImplementedException();
        }

        private void SplitCursors()
        {
            throw new NotImplementedException();
        }

        private void JoinCursors()
        {
            throw new NotImplementedException();
        }

        private void EnableConsoleStream()
        {
            throw new NotImplementedException();
        }

        private void Backspace()
        {
            throw new NotImplementedException();
        }

        private void HorizontalTab()
        {
            throw new NotImplementedException();
        }

        private void LineFeed()
        {
            throw new NotImplementedException();
        }

        private void VerticalTab()
        {
            throw new NotImplementedException();
        }

        private void ClearConsole()
        {
            throw new NotImplementedException();
        }

        private void EnablePrinterStream()
        {
            throw new NotImplementedException();
        }

        private void DoMiscellaneousCommands()
        {
            byte miscCmd = DequeueByte();

            byte[] bytes = { DequeueByte(), DequeueByte(), DequeueByte(), DequeueByte(),
                             DequeueByte(), DequeueByte(), DequeueByte(), DequeueByte()  };

            switch (miscCmd)
            {
                case 0:
                    // interlace and cursor apearance
                    break;
                case 1:
                    cursorDisplay(bytes[0]);
                    break;
                case 6:
                    // ignore this command - dotDashLineStyle
                    break;
                case 7:
                    scrollTextWindow(bytes[0], bytes[1], bytes[2]);
                    break;
                case 8:
                    // clears a block of the current text viewport
                    break;
                // 9 - set colour flash timing
                // 10 - set colour flash timing
                // 11 - set colour patterns to their default values
                // 12-15 - ECF 1-4
                case 16:
                    // Alter the direction of printing on the screen
                    setPrintDirection(bytes[0]);
                    break;
                case 17:
                    // TINT n,m and two others that may not be implimented
                    setTint(bytes[0], bytes[1]);
                    break;
                // 18-26 reserved
                case 27:
                    //select a sprite
                    break;
                // 28-31 reserved
                // 32-255 user definable chars
            }
            ExpectVduCommand();
        }

        private void cursorDisplay(byte b)
        {
            throw new NotImplementedException();
        }

        private void scrollTextWindow(byte b, byte b1, byte b2)
        {
            throw new NotImplementedException();
        }

        private void setPrintDirection(byte flags)
        {
            throw new NotImplementedException();
        }

        private void setTint(byte n, byte m)
        {
            // m & 192 because only the top 2 bits are used
            // prm1-616
            switch (n)
            {
                case 0:
                    textForegroundTint=m & 192;
                    break;
                case 1:
                    textBackgroundTint = m & 192;
                    break;
                case 2:
                    graphicsForegroundTint = m & 192;
                    break;
                case 3:
                    graphicsBackgroundTint = m & 192;
                    break;
                case 4:
                    // prm1-617
                    throw new NotImplementedException();
                    break;
                case 5:
                    // prm1-618
                    throw new NotImplementedException();
                    break;
                default:
                    throw new NotImplementedException();
            }
        }

        private void PagedModeOn()
        {
            throw new NotImplementedException();
        }

        private void PagedModeOff()
        {
            throw new NotImplementedException();
        }

        private void ClearGraphicsWindow()
        {
            throw new NotImplementedException();
        }

        private void SetPalette()
        {
            throw new NotImplementedException();
        }

        private void SetPaletteDefault()
        {
            throw new NotImplementedException();
        }

        private void DisableConsoleStream()
        {
            throw new NotImplementedException();
        }

        private void NextCharacterPrinterOnly()
        {
            throw new NotImplementedException();
        }

        enum PlotEffect
        {
            MOVE = 0,
            FOREGROUND = 1,
            INVERSE = 2,
            BACKGROUND = 3
        }

        private void DoPlot()
        {
            // PRM 1-628
            byte plotType = DequeueByte();
            short x = DequeueShort();
            short y = DequeueShort();
            bool absolute = (plotType & 4) != 0;
            PlotEffect plotEffect = (PlotEffect) (plotType & 3);

            newPtX = absolute ? x : (short) (gCsIX + x);
            newPtY = absolute ? y : (short) (gCsIY + y);

            olderCsX = oldCsX;
            olderCsY = oldCsY;

            oldCsX = gCsIX;
            oldCsY = gCsIY;

            gCsIX = newPtX;
            gCsIY = newPtY;

            if (plotEffect != PlotEffect.MOVE)
            {
                switch (plotType & 248)
                {
                    case 0:
                        SolidLineIncludingBothEndPoints();
                        break;

                    case 8:
                        SolidLineExcludingTheFinalPoint();
                        break;

                    case 16:
                        DottedLineIncludingBothEndPointsPatternRestarted();
                        break;

                    case 24:
                        DottedLineExcludingtheFinalPointPatternRestarted();
                        break;

                    case 32:
                        SolidLineExcludingtheInitialPoint();
                        break;

                    case 40:
                        SolidLineExcludingBothEndPoints();
                        break;

                    case 48:
                        DottedLineExcludingtheInitialPointPatternContinued();
                        break;

                    case 56:
                        DottedLineExcludingBothEndPointsPatternContinued();
                        break;

                    case 64:
                        PointPlot();
                        break;

                    case 72:
                        HorizontalLineFillLeftRightToNonBackground();
                        break;

                    case 80:
                        TriangleFill();
                        break;

                    case 88:
                        HorizontalLineFillRightToBackground();
                        break;

                    case 96:
                        RectangleFill();
                        break;

                    case 104:
                        HorizontalLineFillLeftToForeground();
                        break;

                    case 112:
                        ParallelogramFill();
                        break;

                    case 120:
                        HorizontalLineFillRightOnlyToNonForeground();
                        break;

                    case 128:
                        FloodToNonBackground();
                        break;

                    case 136:
                        FloodToForeground();
                        break;

                    case 144:
                        CircleOutline();
                        break;

                    case 152:
                        CircleFill();
                        break;

                    case 160:
                        CircularArc();
                        break;

                    case 168:
                        Segment();
                        break;

                    case 176:
                        Sector();
                        break;

                    case 184:
                        switch (plotType)
                        {
                            case 184:
                                MoveRelative();
                                break;

                            case 185:
                                RelativeRectangleMove();
                                break;

                            case 186:
                                RelativeRectangleCopy();
                                break;

                            case 187:
                                RelativeRectangleCopy();
                                break;

                            case 188:
                                MoveAbsolute();
                                break;

                            case 189:
                                AbsoluteRectangleMove();
                                break;

                            case 190:
                                AbsoluteRectangleCopy();
                                break;

                            case 191:
                                AbsoluteRectangleCopy();
                                break;
                        }
                        break;
                    case 192:
                        EllipseOutline();
                        break;

                    case 200:
                        EllipseFill();
                        break;

                    case 208:
                        FontPrinting();
                        break;

                    case 232:
                        SpritePlot();
                        break;
                }
            }
            ExpectVduCommand();
        }

        private void ExpectVduCommand()
        {
            requiredBytes = 1;
            nextCommand = DoVduDispatch;
        }

        private void DottedLineIncludingBothEndPointsPatternRestarted()
        {
            throw new NotImplementedException();
        }

        private void DottedLineExcludingtheFinalPointPatternRestarted()
        {
            throw new NotImplementedException();
        }

        private void SolidLineExcludingtheInitialPoint()
        {
            throw new NotImplementedException();
        }

        private void SolidLineExcludingBothEndPoints()
        {
            throw new NotImplementedException();
        }

        private void DottedLineExcludingtheInitialPointPatternContinued()
        {
            throw new NotImplementedException();
        }

        private void DottedLineExcludingBothEndPointsPatternContinued()
        {
            throw new NotImplementedException();
        }

        private void HorizontalLineFillLeftRightToNonBackground()
        {
            throw new NotImplementedException();
        }

        private void PointPlot()
        {
            throw new NotImplementedException();
        }

        private void TriangleFill()
        {
            throw new NotImplementedException();
        }

        private void HorizontalLineFillRightToBackground()
        {
            throw new NotImplementedException();
        }

        private void RectangleFill()
        {
            // TODO some how need to get and use the absolute and plot type (xor/and atc) to here.
            // most are global vars available
            // TODO swap Y co-ords over
            // TODO use the EX and EY to scale output
            Graphics g = vduForm.CreateGraphics();

            int paletteColour = 0;
            paletteColour |= (graphicsForegroundColour & 33) << 2;
            paletteColour |= (graphicsForegroundColour & 14) << 3;
            paletteColour |= (graphicsForegroundColour & 16) >> 1;
            paletteColour |= graphicsForegroundTint >> 6;

            Color physicalColour = screenMode.LogicalToPhysical(paletteColour); SolidBrush brush = new SolidBrush(physicalColour);
            g.FillRectangle(brush, oldCsX, oldCsY, gCsIX - oldCsX, gCsIY - oldCsY);
        }

        private void HorizontalLineFillLeftToForeground()
        {
            throw new NotImplementedException();
        }

        private void ParallelogramFill()
        {
            throw new NotImplementedException();
        }

        private void HorizontalLineFillRightOnlyToNonForeground()
        {
            throw new NotImplementedException();
        }

        private void FloodToNonBackground()
        {
            throw new NotImplementedException();
        }

        private void FloodToForeground()
        {
            throw new NotImplementedException();
        }

        private void CircleOutline()
        {
            throw new NotImplementedException();
        }

        private void CircleFill()
        {
            throw new NotImplementedException();
        }

        private void CircularArc()
        {
            throw new NotImplementedException();
        }

        private void Segment()
        {
            throw new NotImplementedException();
        }

        private void Sector()
        {
            throw new NotImplementedException();
        }

        private void MoveRelative()
        {
            throw new NotImplementedException();
        }

        private void RelativeRectangleMove()
        {
            throw new NotImplementedException();
        }

        private void RelativeRectangleCopy()
        {
            throw new NotImplementedException();
        }

        private void SpritePlot()
        {
            throw new NotImplementedException();
        }

        private void FontPrinting()
        {
            throw new NotImplementedException();
        }

        private void EllipseFill()
        {
            throw new NotImplementedException();
        }

        private void EllipseOutline()
        {
            throw new NotImplementedException();
        }

        private void AbsoluteRectangleCopy()
        {
            throw new NotImplementedException();
        }

        private void AbsoluteRectangleMove()
        {
            throw new NotImplementedException();
        }

        private void MoveAbsolute()
        {
            throw new NotImplementedException();
        }

        private void SolidLineExcludingTheFinalPoint()
        {
            throw new NotImplementedException();
        }

        private void SolidLineIncludingBothEndPoints()
        {
            Graphics g = vduForm.CreateGraphics();
            Color physicalColour = screenMode.LogicalToPhysical(graphicsForegroundColour);
            Pen pen = new Pen(Color.Red, 1); // TODO: Get current colour
            pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Solid;
            g.DrawLine(pen, oldCsX, oldCsY, gCsIX, gCsIY);
        }

        private void CarriageReturn()
        {
            // make sure cursor editing is disabled if enabled (PRM 1-550)
            throw new NotImplementedException();
        }

        private void Bell()
        {
            // PRM 1-552 console.beep may not be good enough
            // the tone can be altered
            System.Media.SystemSounds.Beep.Play();
        }

        private void SetTextColour()
        {
            requiredBytes = 1;
            nextCommand = DoSetTextColour;
        }

        private void DoSetTextColour()
        {
            // PRM 1-585
            byte colour = DequeueByte();
            byte logicalColour = (byte) (colour % screenMode.BitsPerPixel);

            Action<Color> setAction;
            if ((logicalColour & 0x80) != 0)
            {
                setAction = SetTextForeground;
            }
            else
            {
                setAction = SetTextBackground;
            }

            // TODO: Move this into the ScreenMode class
            if (screenMode.BitsPerPixel > 4)
            {
                Color color = Color.FromArgb(logicalColour & 0x03, (logicalColour & 0x0C) >> 2, (logicalColour & 0x30) >> 4);
                setAction(color);
            }
            else
            {
                Color color = screenMode.LogicalToPhysical(logicalColour);
                setAction(color);
            }
            ExpectVduCommand();
        }

        private void SetTextForeground(Color color)
        {

        }

        private void SetTextBackground(Color color)
        {

        }

        private void DoSetMode()
        {
            //prm 1-594
            modeNumber = DequeueByte();
            screenMode = AbstractScreenMode.CreateScreenMode(this.ModeNumber);
            // TODO: Set default colours
            switch (screenMode.BitsPerPixel)
            {
                case 8:
                    textForegroundColour = 63; // TODO: Call property
                    textForegroundTint = 192; // TODO: Call property

                    textBackgroundColour = 0; // TODO: Call property
                    textBackgroundTint = 0; // TODO: Call property

                    graphicsForegroundColour = 63; // TODO: Call property
                    graphicsForegroundTint = 192; // TODO: Call property

                    GraphicsBackgroundColour = 0;
                    graphicsBackgroundTint = 0; // TODO: Call property
                    break;
                default:
                    throw new ApplicationException();
            }

            // Create the window
            if (vduForm != null)
            {
                vduForm.Close();
            }
            vduForm = new VduForm(screenMode.SquarePixelWidth, screenMode.SquarePixelHeight);
            vduForm.Show();

            ExpectVduCommand();
        }

        private void DoDefineGraphicsWindow()
        {
            graphicsWindowLeftCol = DequeueShort();
            graphicsWindowBottomRow = DequeueShort();
            graphicsWindowRightCol = DequeueShort();
            graphicsWindowTopRow = DequeueShort();
            // TODO do the work
            ExpectVduCommand();
        }

        private byte DequeueByte()
        {
            return queue.Dequeue();
        }

        private short DequeueShort()
        {
            // PRM 1-556 - VDU n; sends the number n as two bytes, first n MOD &100, then n DIV &100.
            byte lo = queue.Dequeue();
            byte hi = queue.Dequeue();
            short s = (short) ((hi << 8) | lo);
            return s;
        }

        /// <summary>
        /// Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources.
        /// </summary>
        /// <filterpriority>2</filterpriority>
        public void Dispose()
        {
            Dispose(true);
        }

        protected virtual void Dispose(bool disposeManagedObjs)
        {
            if (!hasBeenDisposed)
            {
                try
                {
                    if (disposeManagedObjs)
                    {
                        vduForm.Dispose();
                    }
                    GC.SuppressFinalize(this);
                }
                catch (Exception)
                {
                    hasBeenDisposed = false;
                    throw;
                }

                hasBeenDisposed = true;
            }
        }

        ~VduSystem()
        {
            Dispose();
        }
    }
}
