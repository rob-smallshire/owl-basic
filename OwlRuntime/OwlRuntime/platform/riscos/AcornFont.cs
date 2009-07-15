using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Drawing.Imaging;
using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class AcornFont
    {
        private Collection<Bitmap> acornAscii = new Collection<Bitmap>();
        private Color foregroundColour;
        private Color backgroundColour;
        private Boolean transparentBackground = false;

        public AcornFont()
        {
            // populate the array for defined characters with blanks
            acornAscii.Clear();
            for (int i = 0; i < 256; ++i)
            {
                acornAscii.Add(new Bitmap(8, 8, PixelFormat.Format1bppIndexed));
            }

            foregroundColour = Color.FromArgb(255, 255, 255);
            backgroundColour = Color.FromArgb(0, 0, 0);

            #region define Acorn Font
            define(32, new byte[8] { 0, 0, 0, 0, 0, 0, 0, 0 });
            define(33, new byte[8] { 24, 24, 24, 24, 24, 0, 24, 0 });
            define(34, new byte[8] { 108, 108, 108, 0, 0, 0, 0, 0 });
            define(35, new byte[8] { 54, 54, 127, 54, 127, 54, 54, 0 });
            define(36, new byte[8] { 12, 63, 104, 62, 11, 126, 24, 0 });
            define(37, new byte[8] { 96, 102, 12, 24, 48, 102, 6, 0 });
            define(38, new byte[8] { 56, 108, 108, 56, 109, 102, 59, 0 });
            define(39, new byte[8] { 24, 24, 24, 0, 0, 0, 0, 0 });
            define(40, new byte[8] { 12, 24, 48, 48, 48, 24, 12, 0 });
            define(41, new byte[8] { 48, 24, 12, 12, 12, 24, 48, 0 });
            define(42, new byte[8] { 0, 24, 126, 60, 126, 24, 0, 0 });
            define(43, new byte[8] { 0, 24, 24, 126, 24, 24, 0, 0 });
            define(44, new byte[8] { 0, 0, 0, 0, 0, 24, 24, 48 });
            define(45, new byte[8] { 0, 0, 0, 126, 0, 0, 0, 0 });
            define(46, new byte[8] { 0, 0, 0, 0, 0, 24, 24, 0 });
            define(47, new byte[8] { 0, 6, 12, 24, 48, 96, 0, 0 });
            define(48, new byte[8] { 60, 102, 110, 126, 118, 102, 60, 0 });
            define(49, new byte[8] { 24, 56, 24, 24, 24, 24, 126, 0 });
            define(50, new byte[8] { 60, 102, 6, 12, 24, 48, 126, 0 });
            define(51, new byte[8] { 60, 102, 6, 28, 6, 102, 60, 0 });
            define(52, new byte[8] { 12, 28, 60, 108, 126, 12, 12, 0 });
            define(53, new byte[8] { 126, 96, 124, 6, 6, 102, 60, 0 });
            define(54, new byte[8] { 28, 48, 96, 124, 102, 102, 60, 0 });
            define(55, new byte[8] { 126, 6, 12, 24, 48, 48, 48, 0 });
            define(56, new byte[8] { 60, 102, 102, 60, 102, 102, 60, 0 });
            define(57, new byte[8] { 60, 102, 102, 62, 6, 12, 56, 0 });
            define(58, new byte[8] { 0, 0, 24, 24, 0, 24, 24, 0 });
            define(59, new byte[8] { 0, 0, 24, 24, 0, 24, 24, 48 });
            define(60, new byte[8] { 12, 24, 48, 96, 48, 24, 12, 0 });
            define(61, new byte[8] { 0, 0, 126, 0, 126, 0, 0, 0 });
            define(62, new byte[8] { 48, 24, 12, 6, 12, 24, 48, 0 });
            define(63, new byte[8] { 60, 102, 12, 24, 24, 0, 24, 0 });
            define(64, new byte[8] { 60, 102, 110, 106, 110, 96, 60, 0 });
            define(65, new byte[8] { 60, 102, 102, 126, 102, 102, 102, 0 });
            define(66, new byte[8] { 124, 102, 102, 124, 102, 102, 124, 0 });
            define(67, new byte[8] { 60, 102, 96, 96, 96, 102, 60, 0 });
            define(68, new byte[8] { 120, 108, 102, 102, 102, 108, 120, 0 });
            define(69, new byte[8] { 126, 96, 96, 124, 96, 96, 126, 0 });
            define(70, new byte[8] { 126, 96, 96, 124, 96, 96, 96, 0 });
            define(71, new byte[8] { 60, 102, 96, 110, 102, 102, 60, 0 });
            define(72, new byte[8] { 102, 102, 102, 126, 102, 102, 102, 0 });
            define(73, new byte[8] { 126, 24, 24, 24, 24, 24, 126, 0 });
            define(74, new byte[8] { 62, 12, 12, 12, 12, 108, 56, 0 });
            define(75, new byte[8] { 102, 108, 120, 112, 120, 108, 102, 0 });
            define(76, new byte[8] { 96, 96, 96, 96, 96, 96, 126, 0 });
            define(77, new byte[8] { 99, 119, 127, 107, 107, 99, 99, 0 });
            define(78, new byte[8] { 102, 102, 118, 126, 110, 102, 102, 0 });
            define(79, new byte[8] { 60, 102, 102, 102, 102, 102, 60, 0 });
            define(80, new byte[8] { 124, 102, 102, 124, 96, 96, 96, 0 });
            define(81, new byte[8] { 60, 102, 102, 102, 106, 108, 54, 0 });
            define(82, new byte[8] { 124, 102, 102, 124, 108, 102, 102, 0 });
            define(83, new byte[8] { 60, 102, 96, 60, 6, 102, 60, 0 });
            define(84, new byte[8] { 126, 24, 24, 24, 24, 24, 24, 0 });
            define(85, new byte[8] { 102, 102, 102, 102, 102, 102, 60, 0 });
            define(86, new byte[8] { 102, 102, 102, 102, 102, 60, 24, 0 });
            define(87, new byte[8] { 99, 99, 107, 107, 127, 119, 99, 0 });
            define(88, new byte[8] { 102, 102, 60, 24, 60, 102, 102, 0 });
            define(89, new byte[8] { 102, 102, 102, 60, 24, 24, 24, 0 });
            define(90, new byte[8] { 126, 6, 12, 24, 48, 96, 126, 0 });
            define(91, new byte[8] { 124, 96, 96, 96, 96, 96, 124, 0 });
            define(92, new byte[8] { 0, 96, 48, 24, 12, 6, 0, 0 });
            define(93, new byte[8] { 62, 6, 6, 6, 6, 6, 62, 0 });
            define(94, new byte[8] { 60, 102, 0, 0, 0, 0, 0, 0 });
            define(95, new byte[8] { 0, 0, 0, 0, 0, 0, 0, 255 });
            define(96, new byte[8] { 48, 24, 0, 0, 0, 0, 0, 0 });
            define(97, new byte[8] { 0, 0, 60, 6, 62, 102, 62, 0 });
            define(98, new byte[8] { 96, 96, 124, 102, 102, 102, 124, 0 });
            define(99, new byte[8] { 0, 0, 60, 102, 96, 102, 60, 0 });
            define(100, new byte[8] { 6, 6, 62, 102, 102, 102, 62, 0 });
            define(101, new byte[8] { 0, 0, 60, 102, 126, 96, 60, 0 });
            define(102, new byte[8] { 28, 48, 48, 124, 48, 48, 48, 0 });
            define(103, new byte[8] { 0, 0, 62, 102, 102, 62, 6, 60 });
            define(104, new byte[8] { 96, 96, 124, 102, 102, 102, 102, 0 });
            define(105, new byte[8] { 24, 0, 56, 24, 24, 24, 60, 0 });
            define(106, new byte[8] { 24, 0, 56, 24, 24, 24, 24, 112 });
            define(107, new byte[8] { 96, 96, 102, 108, 120, 108, 102, 0 });
            define(108, new byte[8] { 56, 24, 24, 24, 24, 24, 60, 0 });
            define(109, new byte[8] { 0, 0, 54, 127, 107, 107, 99, 0 });
            define(110, new byte[8] { 0, 0, 124, 102, 102, 102, 102, 0 });
            define(111, new byte[8] { 0, 0, 60, 102, 102, 102, 60, 0 });
            define(112, new byte[8] { 0, 0, 124, 102, 102, 124, 96, 96 });
            define(113, new byte[8] { 0, 0, 62, 102, 102, 62, 6, 7 });
            define(114, new byte[8] { 0, 0, 108, 118, 96, 96, 96, 0 });
            define(115, new byte[8] { 0, 0, 62, 96, 60, 6, 124, 0 });
            define(116, new byte[8] { 48, 48, 124, 48, 48, 48, 28, 0 });
            define(117, new byte[8] { 0, 0, 102, 102, 102, 102, 62, 0 });
            define(118, new byte[8] { 0, 0, 102, 102, 102, 60, 24, 0 });
            define(119, new byte[8] { 0, 0, 99, 107, 107, 127, 54, 0 });
            define(120, new byte[8] { 0, 0, 102, 60, 24, 60, 102, 0 });
            define(121, new byte[8] { 0, 0, 102, 102, 102, 62, 6, 60 });
            define(122, new byte[8] { 0, 0, 126, 12, 24, 48, 126, 0 });
            define(123, new byte[8] { 12, 24, 24, 112, 24, 24, 12, 0 });
            define(124, new byte[8] { 24, 24, 24, 24, 24, 24, 24, 0 });
            define(125, new byte[8] { 48, 24, 24, 14, 24, 24, 48, 0 });
            define(126, new byte[8] { 0, 0, 0, 0, 0, 0, 0, 0 });
            define(128, new byte[8] { 3, 3, 6, 6, 118, 28, 12, 0 });
            define(129, new byte[8] { 28, 99, 107, 107, 127, 119, 99, 0 });
            define(130, new byte[8] { 28, 54, 0, 107, 107, 127, 54, 0 });
            define(131, new byte[8] { 254, 146, 146, 242, 130, 130, 254, 0 });
            define(132, new byte[8] { 102, 153, 129, 66, 129, 153, 102, 0 });
            define(133, new byte[8] { 24, 102, 66, 102, 60, 24, 24, 0 });
            define(134, new byte[8] { 24, 102, 0, 102, 102, 62, 6, 60 });
            define(135, new byte[8] { 7, 1, 2, 100, 148, 96, 144, 96 });
            define(136, new byte[8] { 24, 40, 79, 129, 79, 40, 24, 0 });
            define(137, new byte[8] { 24, 20, 242, 129, 242, 20, 24, 0 });
            define(138, new byte[8] { 60, 36, 36, 231, 66, 36, 24, 0 });
            define(139, new byte[8] { 24, 36, 66, 231, 36, 36, 60, 0 });
            define(140, new byte[8] { 0, 0, 0, 0, 0, 219, 219, 0 });
            define(141, new byte[8] { 241, 91, 85, 81, 0, 0, 0, 0 });
            define(142, new byte[8] { 192, 204, 24, 48, 96, 219, 27, 0 });
            define(143, new byte[8] { 0, 0, 60, 126, 126, 60, 0, 0 });
            define(144, new byte[8] { 12, 24, 24, 0, 0, 0, 0, 0 });
            define(145, new byte[8] { 12, 12, 24, 0, 0, 0, 0, 0 });
            define(146, new byte[8] { 0, 12, 24, 48, 48, 24, 12, 0 });
            define(147, new byte[8] { 0, 48, 24, 12, 12, 24, 48, 0 });
            define(148, new byte[8] { 27, 54, 54, 0, 0, 0, 0, 0 });
            define(149, new byte[8] { 54, 54, 108, 0, 0, 0, 0, 0 });
            define(150, new byte[8] { 0, 0, 0, 0, 0, 54, 54, 108 });
            define(151, new byte[8] { 0, 0, 0, 60, 0, 0, 0, 0 });
            define(152, new byte[8] { 0, 0, 0, 255, 0, 0, 0, 0 });
            define(153, new byte[8] { 0, 0, 0, 126, 0, 0, 0, 0 });
            define(154, new byte[8] { 119, 204, 204, 207, 204, 204, 119, 0 });
            define(155, new byte[8] { 0, 0, 110, 219, 223, 216, 110, 0 });
            define(156, new byte[8] { 24, 24, 126, 24, 24, 24, 24, 24 });
            define(157, new byte[8] { 24, 24, 126, 24, 126, 24, 24, 24 });
            define(160, new byte[8] { 0, 0, 0, 0, 0, 0, 0, 0 });
            define(161, new byte[8] { 24, 0, 24, 24, 24, 24, 24, 0 });
            define(162, new byte[8] { 8, 62, 107, 104, 107, 62, 8, 0 });
            define(163, new byte[8] { 28, 54, 48, 124, 48, 48, 126, 0 });
            define(164, new byte[8] { 0, 102, 60, 102, 102, 60, 102, 0 });
            define(165, new byte[8] { 102, 60, 24, 24, 126, 24, 24, 0 });
            define(166, new byte[8] { 24, 24, 24, 0, 24, 24, 24, 0 });
            define(167, new byte[8] { 60, 96, 60, 102, 60, 6, 60, 0 });
            define(168, new byte[8] { 102, 0, 0, 0, 0, 0, 0, 0 });
            define(169, new byte[8] { 60, 66, 153, 161, 161, 153, 66, 60 });
            define(170, new byte[8] { 28, 6, 30, 54, 30, 0, 62, 0 });
            define(171, new byte[8] { 0, 51, 102, 204, 204, 102, 51, 0 });
            define(172, new byte[8] { 126, 6, 0, 0, 0, 0, 0, 0 });
            define(173, new byte[8] { 0, 0, 0, 126, 0, 0, 0, 0 });
            define(174, new byte[8] { 60, 66, 185, 165, 185, 165, 66, 60 });
            define(175, new byte[8] { 126, 0, 0, 0, 0, 0, 0, 0 });
            define(176, new byte[8] { 60, 102, 60, 0, 0, 0, 0, 0 });
            define(177, new byte[8] { 24, 24, 126, 24, 24, 0, 126, 0 });
            define(178, new byte[8] { 56, 4, 24, 32, 60, 0, 0, 0 });
            define(179, new byte[8] { 56, 4, 24, 4, 56, 0, 0, 0 });
            define(180, new byte[8] { 12, 24, 0, 0, 0, 0, 0, 0 });
            define(181, new byte[8] { 0, 0, 51, 51, 51, 51, 62, 96 });
            define(182, new byte[8] { 3, 62, 118, 118, 54, 54, 62, 0 });
            define(183, new byte[8] { 0, 0, 0, 24, 24, 0, 0, 0 });
            define(184, new byte[8] { 0, 0, 0, 0, 0, 0, 24, 48 });
            define(185, new byte[8] { 16, 48, 16, 16, 56, 0, 0, 0 });
            define(186, new byte[8] { 28, 54, 54, 54, 28, 0, 62, 0 });
            define(187, new byte[8] { 0, 204, 102, 51, 51, 102, 204, 0 });
            define(188, new byte[8] { 64, 192, 64, 72, 72, 10, 15, 2 });
            define(189, new byte[8] { 64, 192, 64, 79, 65, 15, 8, 15 });
            define(190, new byte[8] { 224, 32, 224, 40, 232, 10, 15, 2 });
            define(191, new byte[8] { 24, 0, 24, 24, 48, 102, 60, 0 });
            define(192, new byte[8] { 48, 24, 0, 60, 102, 126, 102, 0 });
            define(193, new byte[8] { 12, 24, 0, 60, 102, 126, 102, 0 });
            define(194, new byte[8] { 24, 102, 0, 60, 102, 126, 102, 0 });
            define(195, new byte[8] { 54, 108, 0, 60, 102, 126, 102, 0 });
            define(196, new byte[8] { 102, 102, 0, 60, 102, 126, 102, 0 });
            define(197, new byte[8] { 60, 102, 60, 60, 102, 126, 102, 0 });
            define(198, new byte[8] { 63, 102, 102, 127, 102, 102, 103, 0 });
            define(199, new byte[8] { 60, 102, 96, 96, 102, 60, 48, 96 });
            define(200, new byte[8] { 48, 24, 126, 96, 124, 96, 126, 0 });
            define(201, new byte[8] { 12, 24, 126, 96, 124, 96, 126, 0 });
            define(202, new byte[8] { 60, 102, 126, 96, 124, 96, 126, 0 });
            define(203, new byte[8] { 102, 0, 126, 96, 124, 96, 126, 0 });
            define(204, new byte[8] { 48, 24, 0, 126, 24, 24, 126, 0 });
            define(205, new byte[8] { 12, 24, 0, 126, 24, 24, 126, 0 });
            define(206, new byte[8] { 60, 102, 0, 126, 24, 24, 126, 0 });
            define(207, new byte[8] { 102, 102, 0, 126, 24, 24, 126, 0 });
            define(208, new byte[8] { 120, 108, 102, 246, 102, 108, 120, 0 });
            define(209, new byte[8] { 54, 108, 0, 102, 118, 110, 102, 0 });
            define(210, new byte[8] { 48, 24, 60, 102, 102, 102, 60, 0 });
            define(211, new byte[8] { 12, 24, 60, 102, 102, 102, 60, 0 });
            define(212, new byte[8] { 60, 102, 60, 102, 102, 102, 60, 0 });
            define(213, new byte[8] { 54, 108, 60, 102, 102, 102, 60, 0 });
            define(214, new byte[8] { 102, 0, 60, 102, 102, 102, 60, 0 });
            define(215, new byte[8] { 0, 99, 54, 28, 28, 54, 99, 0 });
            define(216, new byte[8] { 61, 102, 110, 126, 118, 102, 188, 0 });
            define(217, new byte[8] { 48, 24, 102, 102, 102, 102, 60, 0 });
            define(218, new byte[8] { 12, 24, 102, 102, 102, 102, 60, 0 });
            define(219, new byte[8] { 60, 102, 0, 102, 102, 102, 60, 0 });
            define(220, new byte[8] { 102, 0, 102, 102, 102, 102, 60, 0 });
            define(221, new byte[8] { 12, 24, 102, 102, 60, 24, 24, 0 });
            define(222, new byte[8] { 240, 96, 124, 102, 124, 96, 240, 0 });
            define(223, new byte[8] { 60, 102, 102, 108, 102, 102, 108, 192 });
            define(224, new byte[8] { 48, 24, 60, 6, 62, 102, 62, 0 });
            define(225, new byte[8] { 12, 24, 60, 6, 62, 102, 62, 0 });
            define(226, new byte[8] { 24, 102, 60, 6, 62, 102, 62, 0 });
            define(227, new byte[8] { 54, 108, 60, 6, 62, 102, 62, 0 });
            define(228, new byte[8] { 102, 0, 60, 6, 62, 102, 62, 0 });
            define(229, new byte[8] { 60, 102, 60, 6, 62, 102, 62, 0 });
            define(230, new byte[8] { 0, 0, 63, 13, 63, 108, 63, 0 });
            define(231, new byte[8] { 0, 0, 60, 102, 96, 102, 60, 96 });
            define(232, new byte[8] { 48, 24, 60, 102, 126, 96, 60, 0 });
            define(233, new byte[8] { 12, 24, 60, 102, 126, 96, 60, 0 });
            define(234, new byte[8] { 60, 102, 60, 102, 126, 96, 60, 0 });
            define(235, new byte[8] { 102, 0, 60, 102, 126, 96, 60, 0 });
            define(236, new byte[8] { 48, 24, 0, 56, 24, 24, 60, 0 });
            define(237, new byte[8] { 12, 24, 0, 56, 24, 24, 60, 0 });
            define(238, new byte[8] { 60, 102, 0, 56, 24, 24, 60, 0 });
            define(239, new byte[8] { 102, 0, 0, 56, 24, 24, 60, 0 });
            define(240, new byte[8] { 24, 62, 12, 6, 62, 102, 62, 0 });
            define(241, new byte[8] { 54, 108, 0, 124, 102, 102, 102, 0 });
            define(242, new byte[8] { 48, 24, 0, 60, 102, 102, 60, 0 });
            define(243, new byte[8] { 12, 24, 0, 60, 102, 102, 60, 0 });
            define(244, new byte[8] { 60, 102, 0, 60, 102, 102, 60, 0 });
            define(245, new byte[8] { 54, 108, 0, 60, 102, 102, 60, 0 });
            define(246, new byte[8] { 102, 0, 0, 60, 102, 102, 60, 0 });
            define(247, new byte[8] { 0, 24, 0, 255, 0, 24, 0, 0 });
            define(248, new byte[8] { 0, 2, 60, 110, 118, 102, 188, 0 });
            define(249, new byte[8] { 48, 24, 0, 102, 102, 102, 62, 0 });
            define(250, new byte[8] { 12, 24, 0, 102, 102, 102, 62, 0 });
            define(251, new byte[8] { 60, 102, 0, 102, 102, 102, 62, 0 });
            define(252, new byte[8] { 102, 0, 0, 102, 102, 102, 62, 0 });
            define(253, new byte[8] { 12, 24, 102, 102, 102, 62, 6, 60 });
            define(254, new byte[8] { 96, 96, 124, 102, 124, 96, 96, 0 });
            define(255, new byte[8] { 102, 0, 102, 102, 102, 62, 6, 60 });
            #endregion
        }

        public void define(int index, byte[] data)
        {
            Bitmap tempBitmap = acornAscii[index];
            BitmapData asciiBitmapData = tempBitmap.LockBits(new Rectangle(0, 0, tempBitmap.Width, tempBitmap.Height), ImageLockMode.ReadWrite, PixelFormat.Format1bppIndexed);
            unsafe
            {
                for (int y = 0; y < tempBitmap.Height; ++y)
                {
                    byte* destRow = (byte*)asciiBitmapData.Scan0 + (y * asciiBitmapData.Stride);
                    destRow[0] = data[7-y]; // store the font upside down because of the translation matrix on the graphics viewport.
                }
            }
            tempBitmap.UnlockBits(asciiBitmapData);
            acornAscii[index] = tempBitmap;
        }
        
        // may override this with a method for scaling the output and see if the interpolation problem can be fixed by scaling the 1bpp image

        public Bitmap getBitmap(int index)
        {
            Bitmap tempBitmap = acornAscii[index];

            Bitmap cloneBitmap = (Bitmap)tempBitmap.Clone();
            // add the palette to the char
            ColorPalette asciipal = cloneBitmap.Palette;
            asciipal.Entries[0] = this.backgroundColour;
            asciipal.Entries[1] = this.foregroundColour;
            cloneBitmap.Palette = asciipal;

            if (transparentBackground == true)
            {
                cloneBitmap.MakeTransparent(this.backgroundColour);
            }

            return cloneBitmap;
        }

        public Bitmap getBitmap(int index, int width, int height)
        {
            // TODO this is not working and need to work out why!!
            Bitmap tempBitmap = acornAscii[index];

            Bitmap cloneBitmap = new Bitmap(width, height, PixelFormat.Format1bppIndexed);

            

            // add the palette to the char
            ColorPalette asciipal = cloneBitmap.Palette;
            asciipal.Entries[0] = this.backgroundColour;
            asciipal.Entries[1] = this.foregroundColour;
            cloneBitmap.Palette = asciipal;

            if (transparentBackground == true)
            {
                //cloneBitmap.MakeTransparent(this.backgroundColour);
            }

            Graphics g = Graphics.FromImage(cloneBitmap);
            g.DrawImage(tempBitmap, 0, 0, width, height);
            g.Dispose();

            return cloneBitmap;
        }

        public Boolean setTransparentBackground
        {
            set { transparentBackground = value; }
        }

        public Color setForegroundColour
        {
            set { foregroundColour = value; }
        }

        public Color setBackgroundColour
        {
            set { backgroundColour = value; }
        }
        
    }
}
