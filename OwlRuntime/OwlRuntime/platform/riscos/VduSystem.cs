using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class VduSystem : IDisposable
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
        private short olderGraphicsCursorX; // olderCsX - x coordinate of oldest graphics cursor (ic)

        [VduVariable(141)]
        private short olderGraphicsCursorY; // olderCsY - Y coordinate of oldest graphics cursor (ic)

        [VduVariable(142)]
        private short oldGraphicsCursorX; // oldCsX - x coordinate of previous graphics cursor (ic)

        [VduVariable(143)]
        private short oldGraphicsCursorY; // oldCsY - Y coordinate of previous graphics cursor (ic)

        [VduVariable(144)]
        private short graphicsCursorIX; // gCsIX - x coordinate of graphics cursor (ic)

        [VduVariable(145)]
        private short graphicsCursorIY; // gCsIY - Y coordinate of graphics cursor (ic)

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
        private int logicalGraphicsForegroundColour; // GFCOL - Graphics foreground colour
        [VduVariable(154)]
        private int logicalGraphicsBackgroundColour; // GBCOL - Graphics background colour
        [VduVariable(155)]
        private int logicalTextForegroundColour; // TForeCol - TForeCol Text foreground colour
        [VduVariable(156)]
        private int logicalTextBackgroundColour; // TBackCol - TBackCol Text background colour
        [VduVariable(157)]
        private int logicalGraphicsForegroundTint; // GFTint - Tint for graphics foreground colour
        [VduVariable(158)]
        private int logicalGraphicsBackgroundTint; // GBTint - Tint for graphics background colour
        [VduVariable(159)]
        private int logicalTextForegroundTint; // TFTint - Tint for text foreground colour
        [VduVariable(160)]
        private int logicalTextBackgroundTint; // TBTint - Tint for text background colour
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

        #region unofficial VDU variables
        private int textCursorX;
        private int textCursorY;
        private Boolean plotTextAtGraphics = false; // vdu 4/5


        #endregion

        private AcornFont acornFont;

        private byte modeNumber;
        private AbstractScreenMode screenMode;
        private bool hasBeenDisposed = false;

        // The VDU queue
        private readonly Queue<byte> queue = new Queue<byte>();
        private int requiredBytes;
        private Action nextCommand;

        public VduSystem()
        {
            screenMode = AbstractScreenMode.CreateScreenMode(this, 7);
            acornFont = new AcornFont();
            ExpectVduCommand();


            
        }


        #region getters and setters for VDU variables



        public Boolean PlotTextAtGraphics
        {
            // vdu 4/5
            get { return plotTextAtGraphics; }
            set { plotTextAtGraphics = value; }
        }
        
        public int TextCursorX
        {
            get { return textCursorX; }
            set { textCursorX = value; }
        }

        public int TextCursorY
        {
            get { return textCursorY; }
            set { textCursorY = value; }
        }
        
        public int TextWindowLeftCol
        {
            get { return textWindowLeftCol; }
            set {
                // also need to update WindowWidth vdu var
                // ???? is it best to calculate when asked for or calculate when another variable changed
                textWindowLeftCol = value;
            }
        }
        
        public int TextWindowRightCol
        {
            // also need to update WindowWidth vdu var
            get { return textWindowRightCol; }
            set { textWindowRightCol = value; }
        }

        public int TextWindowBottomRow
        {
            get { return textWindowBottomRow; }
            set { textWindowBottomRow = value; }
        }

        public int TextWindowTopRow
        {
            get { return textWindowTopRow; }
            set { textWindowTopRow = value; }
        }


        public int TextCharSizeX
        {
            get { return textCharSizeX; }
            set { textCharSizeX = value; }
        }

        public int TextCharSizeY
        {
            get { return textCharSizeY; }
            set { textCharSizeY = value; }
        }

        public int TextCharSpaceX
        {
            get { return textCharSpaceX; }
            set { textCharSpaceX = value; }
        }

        public int TextCharSpaceY
        {
            get { return textCharSpaceY; }
            set { textCharSpaceY = value; }
        }

        public int GraphicsCharSizeX
        {
            get { return graphicsCharSizeX; }
            set { graphicsCharSizeX = value; }
        }

        public int GraphicsCharSizeY
        {
            get { return graphicsCharSizeY; }
            set { graphicsCharSizeY = value; }
        }

        public int GraphicsCharSpaceX
        {
            get { return graphicsCharSpaceX; }
            set { graphicsCharSpaceX = value; }
        }

        public int GraphicsCharSpaceY
        {
            get { return graphicsCharSpaceY; }
            set { graphicsCharSpaceY = value; }
        }

        public AcornFont AcornFont
        {
            get { return acornFont; }
            set { acornFont = value; }
        }


        public int LogicalGraphicsBackgroundColour
        {
            get { return logicalGraphicsBackgroundColour; }
            private set
            {
                logicalGraphicsBackgroundColour = value;
                ScreenMode.UpdateGraphicsBackgroundColour(logicalGraphicsBackgroundColour, logicalGraphicsBackgroundTint);
            }
        }

        public int LogicalGraphicsForegroundColour
        {
            get { return logicalGraphicsForegroundColour; }
            private set
            {
                logicalGraphicsForegroundColour = value;
                ScreenMode.UpdateGraphicsForegroundColour(logicalGraphicsForegroundColour, logicalGraphicsForegroundTint);
            }
        }

        public int LogicalTextBackgroundColour
        {
            get { return logicalTextBackgroundColour; }
            private set
            {
                logicalTextBackgroundColour = value;
                ScreenMode.UpdateTextBackgroundColour(logicalTextBackgroundColour, logicalTextBackgroundTint);
            }
        }

        public int LogicalTextForegroundColour
        {
            get { return logicalTextForegroundColour; }
            private set
            {
                logicalTextForegroundColour = value;
                ScreenMode.UpdateTextForegroundColour(logicalTextForegroundColour, logicalTextForegroundTint);
            }
        }

        public int LogicalGraphicsBackgroundTint
        {
            get { return logicalGraphicsBackgroundTint; }
            private set
            {
                logicalGraphicsBackgroundTint = value;
                ScreenMode.UpdateGraphicsBackgroundColour(logicalGraphicsBackgroundColour, logicalGraphicsBackgroundTint);
            }
        }

        public int LogicalGraphicsForegroundTint
        {
            get { return logicalGraphicsForegroundTint; }
            private set
            {
                logicalGraphicsForegroundTint = value;
                ScreenMode.UpdateGraphicsForegroundColour(logicalGraphicsForegroundColour, logicalGraphicsForegroundTint);
            }
        }

        public int LogicalTextBackgroundTint
        {
            get { return logicalTextBackgroundTint; }
            private set
            {
                logicalTextBackgroundTint = value;
                ScreenMode.UpdateTextBackgroundColour(logicalTextBackgroundColour, logicalTextBackgroundTint);
            }
        }

        public int LogicalTextForegroundTint
        {
            get { return logicalTextForegroundTint; }
            private set
            {
                logicalTextForegroundTint = value;
                ScreenMode.UpdateTextForegroundColour(logicalTextForegroundColour, logicalTextForegroundTint);
            }
        }

        public byte ModeNumber
        {
            get { return modeNumber; }
        }

        public short OlderGraphicsCursorX
        {
            get { return olderGraphicsCursorX; }
        }

        public short OlderGraphicsCursorY
        {
            get { return olderGraphicsCursorY; }
        }

        public short OldGraphicsCursorX
        {
            get { return oldGraphicsCursorX; }
        }

        public short OldGraphicsCursorY
        {
            get { return oldGraphicsCursorY; }
        }

        public short GraphicsCursorIX
        {
            get { return graphicsCursorIX; }
        }

        public short GraphicsCursorIY
        {
            get { return graphicsCursorIY; }
        }

        internal AbstractScreenMode ScreenMode
        {
            get { return screenMode; }
        }

        #endregion

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

        public void Enqueue(string bs)
        {
            foreach (byte b in bs)
            {
                Enqueue(b);
            }
        }

        public void Enqueue(short s)
        {
            // TODO: Check order!
            Enqueue((byte) (s & 0xFF)); // hi byte
            Enqueue((byte) (s >> 8));   // lo byte
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
            // TODO: Only the graphics modes need Refresh...
            //screenMode.Refresh();
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
            else
            {
                DisplayCharacter(code);
            }
        }


        private void DeleteCharacter()
        {
            throw new NotImplementedException();
        }

        private void DisplayCharacter(byte code)
        {
            // TODO: Should look at encoding to be used here maybe...
            char c = Convert.ToChar(code);
            screenMode.PrintChar(c);
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
                    ClearTextWindow();
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
                    requiredBytes = 5;
                    nextCommand = SetPalette;
                    break;
                case 20:
                    RestoreDefaultColours();
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
                case 26:
                    // TODO restore default windows
                    // this is part of the setup of a mode
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
            textCursorX = DequeueByte();
            textCursorY = DequeueByte();
            ExpectVduCommand();
        }

        private void CursorHome()
        {
            throw new NotImplementedException();
        }

        private void DoSetOrigin()
        {
            originX = DequeueShort();
            originX = DequeueShort();
            ExpectVduCommand();
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
                LogicalGraphicsBackgroundColour = c & 63; // only bottom 6 bits used for color
            }
            else
            {
                LogicalGraphicsForegroundColour = c & 63;
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

        /// <summary>
        /// Reset the text window to the default for the supplied mode.
        /// </summary>
        /// <param name="mode">
        /// A screen mode from which to take the default text window size.
        /// </param>
        public void ResetTextWindow(AbstractScreenMode mode)
        {
            // The mode parameter is required since the screenMode data member
            // may not be initialized at the time of the call to this method
            graphicsWindowLeftCol = 0;
            graphicsWindowBottomRow = mode.TextHeight - 1;
            graphicsWindowRightCol = mode.TextWidth - 1;
            graphicsWindowTopRow = 0;
        }

        public void ResetGraphicsWindow(AbstractScreenMode mode)
        {
            // The mode parameter is required since the screenMode data member
            // may not be initialized at the time of the call to this method
            // TODO: Reset the graphics window
        }

        /// <summary>
        /// Set the default text cursor position
        /// </summary>
        public void ResetTextCursor()
        {
            TextCursorX = 0;
            TextCursorY = 0;    
        }

        private void DisablePrinterStream()
        {
            throw new NotImplementedException();
        }

        private void SplitCursors()
        {
            plotTextAtGraphics = false;
            //throw new NotImplementedException();
        }

        private void JoinCursors()
        {
            plotTextAtGraphics = true;
            //throw new NotImplementedException();
        }

        private void EnableConsoleStream()
        {
            throw new NotImplementedException();
        }

        private void Backspace()
        {
            textCursorX -= screenMode.TextCursor.MovementX;
            textCursorY -= screenMode.TextCursor.MovementY;
        }

        private void HorizontalTab()
        {
            textCursorX += screenMode.TextCursor.MovementX;
            textCursorY += screenMode.TextCursor.MovementY;
        }

        private void LineFeed()
        {
            textCursorX += screenMode.TextCursor.MovementXEOL;
            textCursorY += screenMode.TextCursor.MovementYEOL;
        }

        private void VerticalTab()
        {
            textCursorX -= screenMode.TextCursor.MovementXEOL;
            textCursorY -= screenMode.TextCursor.MovementYEOL;
        }

        private void ClearTextWindow()
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
                case 1:
                    CursorDisplay(bytes[0]);
                    break;
                case 2:
                case 3:
                case 4:
                case 5:
                    DefineExtendedColourFill((byte) (miscCmd - 1), bytes);
                    break;
                case 6:
                    DotDashStyle(bytes);
                    break;
                case 7:
                    ScrollTextWindow(bytes[0], bytes[1], bytes[2]);
                    break;
                case 8:
                    ClearTextBlock(bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5]);
                    break;
                case 9:
                    ColourFlashTimingFirst(bytes[0]);
                    break;
                case 10:
                    ColourFlashTimingSecond(bytes[0]);
                    break;
                case 11:
                    // - set colour patterns to their default values
                    ResetColourFills();
                    break;
                case 12:
                case 13:
                case 14:
                case 15:
                    DefineSimpleExtendedColourFill((byte) (miscCmd - 11), bytes);
                    break;
                case 16:
                    // Alter the direction of printing on the screen
                    SetPrintDirection(bytes[0], bytes[1]);
                    break;
                case 17:
                    switch (bytes[0])
                    {
                        case 0:
                        case 1:
                        case 2:
                        case 3:
                            SetTint(bytes[0], bytes[1]);
                            break;
                        case 4:
                            ColourPatternInterpretation(bytes[1]);
                            break;
                        case 5:
                            ExchangeTextForegroundAndBackgroundColours();
                            break;
                        case 6:
                            short xOrigin = TwoBytesToShort(bytes[1], bytes[2]);
                            short yOrigin = TwoBytesToShort(bytes[3], bytes[4]);
                            SetExtendedColourFillOrigin(xOrigin, yOrigin);
                            break;
                        case 7:
                            short xSize = TwoBytesToShort(bytes[3], bytes[2]);
                            short ySize = TwoBytesToShort(bytes[5], bytes[4]);
                            SetCharacterSizeSpacing(bytes[1], xSize, ySize);
                            break;
                    }
                    break;
                // According to the PRMs 18-24 are reserved for future expansion
                // Some of these values are used by BBC BASIC for Windows
                case 22:
                    short pixelWidth = TwoBytesToShort(bytes[0], bytes[1]);
                    short pixelHeight = TwoBytesToShort(bytes[2], bytes[3]);
                    byte charX = bytes[4];
                    byte charY = bytes[5];
                    byte numColours = bytes[6];
                    byte charSet = bytes[7];
                    SetUserDefinedMode(pixelWidth, pixelHeight, charX, charY, numColours, charSet);
                    break;
                case 23:
                    short lineWidth = TwoBytesToShort(bytes[0], bytes[1]);
                    SetLineThickness(lineWidth);
                    break;
                case 27:
                    //select a sprite
                    break;
                // 28-31 Reserved for use by application programs.
                // We use these for OWL BASIC extensions
                case 28:
                    RenderingQuality(bytes[0]);
                    break;
                default:
                    if (miscCmd > 31)
                    {
                        // needs testing
                        acornFont.Define(miscCmd, bytes);
                    }
                    else
                    {
                        throw new NotImplementedException();
                    }
                    break;
                // 32-255 user definable chars
            }
            ExpectVduCommand();
        }

        /// <summary>
        /// Used to set the level of antialiasing
        /// 0 - No antialiasing (the default)
        /// 1 - Standard antialiasing
        /// </summary>
        /// <param name="quality">Quality level</param>
        private void RenderingQuality(byte quality)
        {
            screenMode.UpdateRenderingQuality(quality);
        }

        /// <summary>
        /// Set the line thickness.
        /// This is a BBC BASIC for Windows extension.
        /// </summary>
        /// <param name="width">width in pixels</param>
        private void SetLineThickness(short width)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Set a user defined screen mode.
        /// This is a BBC BASIC for Windows extension.
        /// </summary>
        /// <param name="pixelWidth"></param>
        /// <param name="pixelHeight"></param>
        /// <param name="charX"></param>
        /// <param name="charY"></param>
        /// <param name="numColours"></param>
        /// <param name="charSet"></param>
        private void SetUserDefinedMode(short pixelWidth, short pixelHeight, byte charX, byte charY, byte numColours, byte charSet)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// This command allows changing the size and spacing of VDU 5 characters. They are 
        /// reset when a mode change occurs. Bit 1 of the flags refers to the size of VDU 5 
        /// characters. Bit 2 refers to the spacing between VDU 5 characters. x and y are sizes in 
        /// pixels.
        /// </summary>
        /// <param name="flags">What to set the size of</param>
        /// <param name="xSize">x size in pixels</param>
        /// <param name="ySize">y size in pixels</param>
        private void SetCharacterSizeSpacing(byte flags, short xSize, short ySize)
        {
            //bbcbasic.pdf p186
            //The bits in the flag byte have the following meanings:
            //Bit Meaning if set
            //0 Set VDU 4 character size from dx,dy    The bit 0 option is not implemented at present
            //1 Set VDU 5 character size from dx,dy
            //2 Set VDU 5 character spacing from dx,dy

            // todo test this section
            if ((flags & 2) != 0)
            {
                graphicsCharSizeX = xSize;
                graphicsCharSizeY = ySize;
            }
            if ((flags & 4) != 0)
            {
                graphicsCharSpaceX = xSize;
                graphicsCharSpaceY = ySize;
            }
        }

        /// <summary>
        /// By default, the alignment of ECF patterns is with the bottom left corner of the screen. 
        /// This command changes it so that the bottom left pixel of the pattern coincides with the 
        /// pixel at the specified point.
        /// The origin is restored to the default after a mode change.
        /// </summary>
        /// <param name="x">x-coordinate of origin</param>
        /// <param name="y">y-coordinate of origin</param>
        private void SetExtendedColourFillOrigin(short x, short y)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Exchange text foreground and background colours.
        /// This command exchanges the current text foreground and background colours. After the 
        /// first time it’s called, subsequent characters printed are in inverse video. After the second 
        /// time it’s called, subsequent characters printed are of normal appearance.
        /// </summary>
        private void ExchangeTextForegroundAndBackgroundColours()
        {
            int tempColour = LogicalTextForegroundColour;
            LogicalTextForegroundColour = LogicalTextBackgroundColour;
            LogicalTextBackgroundColour = tempColour;

            int tempTint = LogicalTextForegroundTint;
            LogicalTextForegroundTint = LogicalTextBackgroundTint;
            LogicalTextBackgroundTint = tempTint;
        }

        /// <summary>
        /// Choose the patterns used to interpret subsequent VDU 23,2 - 5... calls
        /// </summary>
        /// <param name="patterns">0 - use 6502 BBC Micro colour patterns. 1 - Use native colour patterns.</param>
        private void ColourPatternInterpretation(byte patterns)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// define the four colour patterns in a simpler way than that 
        /// provided by VDU 23,2-5. The limitation is that you can only set a two-by-four pattern of 
        /// pixels. 
        /// The pixels of the top row of the resulting pattern are assigned alternating logical colours 
        /// n1 and n2, those of the next row have colours n3 and n4 etc.
        /// In any 256 colour mode, the declared use of the parameters does not apply. In this case, 
        /// each parameter refers to the colour of each line, from 1 to 8. Use the colour byte as 
        /// described by VDU 19.
        /// </summary>
        /// <param name="pattern">Pattern number 1-4</param>
        /// <param name="colours">Array defining a two by four block of pixels.</param>
        private void DefineSimpleExtendedColourFill(byte pattern, byte[] colours)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Selects the Master 128 compatible pattern mode and causes the four colour 
        /// patterns to be reset to their defaults for the current screen mode.
        /// </summary>
        private void ResetColourFills()
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// sets the flash time for the first flashing colour. The length is determined by 
        /// the value of duration
        /// </summary>
        /// <param name="durationInFrames">Number of frames</param>
        private void ColourFlashTimingFirst(byte durationInFrames)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// sets the flash time for the first flashing colour. The length is determined by 
        /// the value of duration
        /// </summary>
        /// <param name="durationInFrames">Number of frames</param>
        private void ColourFlashTimingSecond(byte durationInFrames)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Causes a block of the current text window to be cleared to the text background 
        /// colour. The parameters baseStart and baseEnd indicate base positions relating to the 
        /// start and end of the block to be cleared respectively:
        /// 0 top left of window
        /// 1 top of cursor column
        /// 2 off top right of window
        /// 4 left end of cursor line
        /// 5 cursor position
        /// 6 off right of cursor line
        /// 8 bottom left of window
        /// 9 bottom of cursor column
        /// 10 off bottom right of window
        /// </summary>
        /// <param name="baseStart">Base position of start of block</param>
        /// <param name="baseEnd">Base position of end of block</param>
        /// <param name="x1">Displacement from base start in x direction</param>
        /// <param name="y1">Displacement from base start in y direction</param>
        /// <param name="x2">Displacement from base end in x direction</param>
        /// <param name="y2">Displacement from base end in y direction</param>
        private void ClearTextBlock(byte baseStart, byte baseEnd, byte x1, byte y1, byte x2, byte y2)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// sets the dot-dash line style used by dotted line PLOT commands (see also 
        /// VDU 25 – which does the plotting.
        /// Each of the integers n1 to n8 defines eight elements of the line style, n1 being at the start 
        /// and n8 at the end. The bits in each byte are read from most significant to least 
        /// significant, each 1-bit indicating a dot and each 0-bit a space. The default is 
        /// &AAAAAAAA (alternating dots and spaces) with a repeat length of eight (so only n1 is 
        /// used).
        /// </summary>
        /// <param name="bytes"></param>
        private void DotDashStyle(byte[] bytes)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Each of the integers n1 to n8 defines the colours of one row of the pattern, n1 being the 
        /// top row and n8 being the bottom. For a given parameter, the logical colours of the pixels 
        /// in each row depend upon the number of colours available in the current screen mode and 
        /// which pattern mode is used. There are two available pattern modes. The default is the 
        /// BBC/Master compatible mode. The other is the native RISC OS mode which decodes 
        /// the values in a simpler fashion. To change between these modes use VDU 23,17,4.
        /// </summary>
        /// <param name="pattern">A pattern number 1 to 4</param>
        /// <param name="colours">An array of eight bytes for n1 to n8</param>
        private void DefineExtendedColourFill(byte pattern, byte[] colours)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Controls the appearance of the text cursor on the screen depending on the 
        /// value of mode
        /// </summary>
        /// <param name="mode">
        /// 0 - stops the cursor appearing
        /// 1 - makes the cursor re-appear
        /// 2 - makes the cursor steady
        /// 3 - makes the cursor flash
        /// </param>
        private void CursorDisplay(byte mode )
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Allows the current text window or whole screen to be scrolled directly in any 
        /// direction without moving the cursor. The extent, direction and movement determine the 
        /// area to be scrolled, the direction of scrolling and the amount of scrolling
        /// </summary>
        /// <param name="extent">Text window or screen. 0 - scroll the current text window. 1 - scroll the entire screen</param>
        /// <param name="direction">Direction to scroll</param>
        /// <param name="movement">How much movement. 0 - scroll by one character cell. 1 - scroll by one character cell vertically or one byte horizontally</param>
        private void ScrollTextWindow(byte extent, byte direction, byte movement)
        {
            throw new NotImplementedException();
        }

        private void SetPrintDirection(byte x, byte y)
        {
            // prm 1-594 this needs some thinking about how to impliment.
            // May need to impliment windows and scrolling first.
            
            // also risc os 2 and 3 prm's say two params
            byte flags = screenMode.TextCursor.Flags;
            screenMode.TextCursor.Flags = (byte)((flags & y) ^ x);

        }

        /// <summary>
        /// used to set the amount of white tint given to a colour in the 256-colour 
        /// modes. The action determines which colour’s tint is set, as follows:
        /// action Colour
        /// 0 sets the tint for the text foreground colour
        /// 1 sets the tint for the text background colour
        /// 2 sets the tint for the graphics foreground colour
        /// 3 sets the tint for the graphics background colour
        /// </summary>
        /// <param name="action"></param>
        /// <param name="tint"></param>
        private void SetTint(byte action, byte tint)
        {
            // m & 192 because only the top 2 bits are used
            // prm1-616
            switch (action)
            {
                case 0:
                    LogicalTextForegroundTint= tint & 192;
                    break;
                case 1:
                    LogicalTextBackgroundTint = tint & 192;
                    break;
                case 2:
                    LogicalGraphicsForegroundTint = tint & 192;
                    break;
                case 3:
                    LogicalGraphicsBackgroundTint = tint & 192;
                    break;
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
            byte logicalColour = DequeueByte();
            byte mode = DequeueByte();
            byte red = DequeueByte();
            byte green = DequeueByte();
            byte blue = DequeueByte();

            bool supremacy = (mode & 128) != 0;

            mode &= 127;

            if (mode >=0 && mode <= 15)
            {
                // logical colour = physical colour specified by mode
                byte physcialColour =  mode; // index in the physical palette
                ScreenMode.UpdatePalette(logicalColour, physcialColour);
            }
            else
            {
                switch (mode)
                {
                    case 16:
                        ScreenMode.UpdatePalette(logicalColour, red, green, blue);
                        // both flash palettes for logical colour = red units red, green units green, blue units blue
                        break;
                    case 17:
                        // first flash palette for logical colour = red units red, green units green, blue units blue
                        ScreenMode.UpdatePaletteFirstFlash(logicalColour, red, green, blue);
                        break;
                    case 18:
                        // second flash palette for logical colour = red units red, green units green, blue units blue
                        ScreenMode.UpdatePaletteSecondFlash(logicalColour, red, green, blue);
                        break;
                    case 24:
                        // border colour = red units red, green units green, blue units blue; logical colour is not used, and should be zero
                        ScreenMode.UpdatePaletteBorder(logicalColour, red, green, blue);
                        break;
                    case 25:
                        // logical colour (1 - 3) of pointer = red units red, green units green, blue units blue
                        ScreenMode.UpdatePointerPalette(logicalColour, red, green, blue);
                        break;
                    case 255:
                        // BBC BASIC for Windows compatibility: the physical colour is determined by interpreting
                        // the remaining three parameters as red, green and blue values in the range 0 to 63
                        ScreenMode.UpdatePalette(logicalColour, (byte) (red * 4), (byte) (green * 4), (byte) (blue * 4));
                        break;
                }
            }
        }

        private void RestoreDefaultColours()
        {
            ScreenMode.ResetPaletteAndColours();
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

            newPtX = absolute ? x : (short) (GraphicsCursorIX + x);
            newPtY = absolute ? y : (short) (GraphicsCursorIY + y);

            olderGraphicsCursorX = OldGraphicsCursorX;
            olderGraphicsCursorY = OldGraphicsCursorY;

            oldGraphicsCursorX = GraphicsCursorIX;
            oldGraphicsCursorY = GraphicsCursorIY;

            graphicsCursorIX = newPtX;
            graphicsCursorIY = newPtY;

            if (plotEffect != PlotEffect.MOVE)
            {
                switch (plotType & 248)
                {
                    case 0:
                        ScreenMode.SolidLineIncludingBothEndPoints();
                        break;

                    case 8:
                        ScreenMode.SolidLineExcludingTheFinalPoint();
                        break;

                    case 16:
                        ScreenMode.DottedLineIncludingBothEndPointsPatternRestarted();
                        break;

                    case 24:
                        ScreenMode.DottedLineExcludingtheFinalPointPatternRestarted();
                        break;

                    case 32:
                        ScreenMode.SolidLineExcludingtheInitialPoint();
                        break;

                    case 40:
                        ScreenMode.SolidLineExcludingBothEndPoints();
                        break;

                    case 48:
                        ScreenMode.DottedLineExcludingtheInitialPointPatternContinued();
                        break;

                    case 56:
                        ScreenMode.DottedLineExcludingBothEndPointsPatternContinued();
                        break;

                    case 64:
                        ScreenMode.PointPlot();
                        break;

                    case 72:
                        ScreenMode.HorizontalLineFillLeftRightToNonBackground();
                        break;

                    case 80:
                        ScreenMode.TriangleFill();
                        break;

                    case 88:
                        ScreenMode.HorizontalLineFillRightToBackground();
                        break;

                    case 96:
                        ScreenMode.RectangleFill();
                        break;

                    case 104:
                        ScreenMode.HorizontalLineFillLeftToForeground();
                        break;

                    case 112:
                        ScreenMode.ParallelogramFill();
                        break;

                    case 120:
                        ScreenMode.HorizontalLineFillRightOnlyToNonForeground();
                        break;

                    case 128:
                        ScreenMode.FloodToNonBackground();
                        break;

                    case 136:
                        ScreenMode.FloodToForeground();
                        break;

                    case 144:
                        ScreenMode.CircleOutline();
                        break;

                    case 152:
                        ScreenMode.CircleFill();
                        break;

                    case 160:
                        ScreenMode.CircularArc();
                        break;

                    case 168:
                        ScreenMode.Segment();
                        break;

                    case 176:
                        ScreenMode.Sector();
                        break;

                    case 184:
                        switch (plotType)
                        {
                            case 184:
                                MoveRelative();
                                break;

                            case 185:
                                ScreenMode.RelativeRectangleMove();
                                break;

                            case 186:
                                ScreenMode.RelativeRectangleCopy();
                                break;

                            case 187:
                                ScreenMode.RelativeRectangleCopy();
                                break;

                            case 188:
                                MoveAbsolute();
                                break;

                            case 189:
                                ScreenMode.AbsoluteRectangleMove();
                                break;

                            case 190:
                                ScreenMode.AbsoluteRectangleCopy();
                                break;

                            case 191:
                                ScreenMode.AbsoluteRectangleCopy();
                                break;
                        }
                        break;
                    case 192:
                        ScreenMode.EllipseOutline();
                        break;

                    case 200:
                        ScreenMode.EllipseFill();
                        break;

                    case 208:
                        ScreenMode.FontPrinting();
                        break;

                    case 232:
                        ScreenMode.SpritePlot();
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

        
        private void MoveRelative()
        {
            throw new NotImplementedException();
        }

        private void MoveAbsolute()
        {
            throw new NotImplementedException();
        }

        private void CarriageReturn()
        {
            // make sure cursor editing is disabled if enabled (PRM 1-550)
            throw new NotImplementedException();
        }

        private static void Bell()
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
            // todo do we need to impliment 6 bit colour for old style palette
            byte logicalColour = (byte) (colour % ((1 << ScreenMode.BitsPerPixel) -1));

            if ((colour & 0x80) == 0)
            {
                
                LogicalTextForegroundColour = logicalColour;
                
            }
            else
            {
                LogicalTextBackgroundColour = logicalColour;
            }
            


            //Color color = screenMode.PhysicalTextColour;
            //setAction(color);

            //// TODO: Move this into the ScreenMode class
            //if (screenMode.BitsPerPixel > 4)
            //{
            //    Color color = Color.FromArgb(logicalColour & 0x03, (logicalColour & 0x0C) >> 2, (logicalColour & 0x30) >> 4);
            //    setAction(color);
            //}
            //else
            //{
            //    Color color = screenMode.LogicalToPhysical(logicalColour);
            //    setAction(color);
            //}
            ExpectVduCommand();
        }

        private void DoSetMode()
        {
            //prm 1-594
            modeNumber = DequeueByte();
            screenMode = AbstractScreenMode.CreateScreenMode(this, ModeNumber);
            // TODO: Set default colours
            switch (ScreenMode.BitsPerPixel)
            {
                // TODO: Other default logical colours needed

                case 8:
                    LogicalTextForegroundColour = 63;
                    LogicalTextForegroundTint = 192;

                    LogicalTextBackgroundColour = 0;
                    LogicalTextBackgroundTint = 0;

                    LogicalGraphicsForegroundColour = 63;
                    LogicalGraphicsForegroundTint = 192;

                    LogicalGraphicsBackgroundColour = 0;
                    LogicalGraphicsBackgroundTint = 0;
                    break;
                //case 24:
                    // logical colours are physical colours

                //default:
                    //throw new ApplicationException();
            }

            //// Create the window
            //if (vduForm != null)
            //{
            //    vduForm.Close();
            //}
            //vduForm = new VduForm(screenMode.SquarePixelWidth, screenMode.SquarePixelHeight);
            //vduForm.Show();

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
            short s = TwoBytesToShort(hi, lo);
            return s;
        }

        private static short TwoBytesToShort(byte hi, byte lo)
        {
            return (short) ((hi << 8) | lo);
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
                        ScreenMode.Dispose();
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
    }
}
