## Sid Meier's Civilization 4 - Copyright Firaxis Games 2005
from CvPythonExtensions import *
from RectLayout import * # advc.092
import CvUtil
import ScreenInput
import CvScreenEnums
import CvEventInterface
import time
import BugDll # BUG - DLL
# BUG - Options - start
import BugCore
import BugOptions
import BugOptionsScreen
import BugPath
import BugUtil
import CityUtil
ClockOpt = BugCore.game.NJAGC
ScoreOpt = BugCore.game.Scores
MainOpt = BugCore.game.MainInterface
CityScreenOpt = BugCore.game.CityScreen
# BUG - Options - end
import ReligionUtil # BUG - Limit/Extra Religions
# BUG - Align Icons - start
import Scoreboard
import PlayerUtil
# BUG - Align Icons - end
import AttitudeUtil # BUG - Worst Enemy, Refuses to Talk
import DiplomacyUtil # BUG - Refuses to Talk
import TradeUtil # BUG - Fractional Trade
import BugUnitPlot
# globals
gc = CyGlobalContext()
ArtFileMgr = CyArtFileMgr()
localText = CyTranslator()
PleOpt = BugCore.game.PLE # BUG - PLE
import GameUtil # BUG - 3.17 No Espionage
import ReminderEventManager # BUG - Reminders
import GGUtil # BUG - Great General Bar
import GPUtil # BUG - Great Person Bar
import ProgressBarUtil # BUG - Progress Bar
import PLE # PLE Code
import MinimapOptions # advc.002a
import RawYields # BUG - Raw Yields
# <advc.090>
import math
def floor(f):
	return int(math.floor(f))
def ceil(f):
	return int(math.ceil(f))
def iround(f):
	return int(round(f))
# </advc.090>

# <advc.092>
gRectLayoutDict = {} # Global dictionary for (rectangular) layout data
def gSetRectangle(szKeyName, lRect):
	gRectLayoutDict[szKeyName] = lRect
	if (not szKeyName.startswith("PlotListButton") or
			szKeyName.startswith("PlotListButton315")): # lower left unit button
		print(szKeyName + " " + str(lRect)) # advc.tmp
def gSetRect(szKeyName, szParentKey, fX, fY, fWidth, fHeight, bOffScreen = False):
	gSetRectangle(szKeyName, RectLayout(gRect(szParentKey),
			fX, fY, fWidth, fHeight, bOffScreen))
def gSetSquare(szKeyName, szParentKey, fX, fY, fSideLen, bOffScreen = False):
	gSetRectangle(szKeyName, SquareLayout(gRect(szParentKey),
			fX, fY, fSideLen, bOffScreen))
def gRect(szKeyName): # Called externally
	return gRectLayoutDict[szKeyName]
# Same deal for 2D points
gPointLayoutDict = {}
def gSetPoint(szKeyName, lPoint):
	gPointLayoutDict[szKeyName] = lPoint
	print(szKeyName + " " + str(lPoint)) # advc.tmp
def gPoint(szKeyName):
	return gPointLayoutDict[szKeyName]
def gOffSetPoint(szPointKeyName, szRectKeyName, fDeltaX, fDeltaY):
	gSetPoint(szPointKeyName, RectLayout.offsetPoint(gRect(szRectKeyName), fDeltaX, fDeltaY))
# These global variables should be set based on the screen resolution.
# All positional data that goes through the functions below will then
# be scaled accordingly. Global because some of these will have lots of
# call locations, so I want the calls to be compact.
gHorizontalScaleFactor = 1.0
gVerticalScaleFactor = 1.0
gSquareButtonScaleFactor = 1.0
# This one should be smaller than 1 - space in between widgets should (if at all)
# be only slighty affected by the screen resolution.
gSpaceScaleFactor = 1.0
# Tbd.: Scaling should arguably not be linear; small widgets should be
# magnified disproportionately. In particular, 0 space shouldn't necessarily
# map to 0.
def HLEN(iWidth):
	return iround(gHorizontalScaleFactor * iWidth)
def VLEN(iHeight):
	return iround(gVerticalScaleFactor * iHeight)
def BTNSZ(iSize):
	return iround(gSquareButtonScaleFactor * iSize)
# Tbd.: Negative arguments should assumed to be overlap,
# i.e. those should move closer to 0 on higher resolution.
# Callers should pass negative values only when there is overlap!
def HSPACE(iWidth):
	return iround(gHorizontalScaleFactor * gSpaceScaleFactor * iWidth)
def VSPACE(iHeight):
	return iround(gVerticalScaleFactor * gSpaceScaleFactor * iHeight)
gStackBarDefaultHeight = 27
# </advc.092>
# BUG - city specialist - start
#SUPER_SPECIALIST_STACK_WIDTH = 15 # (advc: unused)
SPECIALIST_ROW_HEIGHT = 34
SPECIALIST_ROWS = 3
MAX_SPECIALIST_BUTTON_SPACING = 30
SPECIALIST_AREA_MARGIN = 45
g_iSuperSpecialistCount = 0
g_iCitySpecialistCount = 0
g_iAngryCitizensCount = 0
# BUG - city specialist - end
# advc: unused
#iCityCenterRow1Xa = 347
#iCityCenterRow2Xa = 482
#g_iNumTradeRoutes = 0
#g_iNumBuildings = 0
g_iNumLeftBonus = 0
g_iNumCenterBonus = 0
g_iNumRightBonus = 0
# advc: Most of this stuff is unused
#MAX_SELECTED_TEXT = 5
#MAX_DISPLAYABLE_BUILDINGS = 15
#MAX_DISPLAYABLE_TRADE_ROUTES = 4
#MAX_BONUS_ROWS = 10
MAX_CITIZEN_BUTTONS = 8
#SELECTION_BUTTON_COLUMNS = 8
#SELECTION_BUTTON_ROWS = 2
#NUM_SELECTION_BUTTONS = SELECTION_BUTTON_ROWS * SELECTION_BUTTON_COLUMNS
#g_iNumBuildingWidgets = MAX_DISPLAYABLE_BUILDINGS
#g_iNumTradeRouteWidgets = MAX_DISPLAYABLE_TRADE_ROUTES

g_NumEmphasizeInfos = 0
g_NumCityTabTypes = 0
g_NumHurryInfos = 0
g_NumUnitClassInfos = 0
g_NumBuildingClassInfos = 0
g_NumProjectInfos = 0
g_NumProcessInfos = 0
g_NumActionInfos = 0
g_eEndTurnButtonState = -1
g_pSelectedUnit = 0
g_szTimeText = ""
# BUG - NJAGC - start
g_bShowTimeTextAlt = False
g_iTimeTextCounter = -1
# BUG - NJAGC - end
# BUG - Raw Yields - start
g_bRawShowing = False
g_bYieldView, g_iYieldType = RawYields.getViewAndType(0)
g_iYieldTiles = RawYields.WORKED_TILES
RAW_YIELD_HELP = (	"TXT_KEY_RAW_YIELD_VIEW_TRADE",
					"TXT_KEY_RAW_YIELD_VIEW_FOOD",
					"TXT_KEY_RAW_YIELD_VIEW_PRODUCTION",
					"TXT_KEY_RAW_YIELD_VIEW_COMMERCE",
					"TXT_KEY_RAW_YIELD_TILES_WORKED",
					"TXT_KEY_RAW_YIELD_TILES_CITY",
					"TXT_KEY_RAW_YIELD_TILES_OWNED",
					"TXT_KEY_RAW_YIELD_TILES_ALL"	)
# BUG - Raw Yields - end
# BUG - field of view slider:
#DEFAULT_FIELD_OF_VIEW = 42 # disabled (replaced) by K-Mod


class CvMainInterface:
	"Main Interface Screen"
	# <advc.092> CyGInterfaceScreen wrappers that look up global layout data
	def addPanel(self, szName, eStyle = None):
		if eStyle is None:
			eStyle = PanelStyles.PANEL_STYLE_STANDARD
		lRect = gRect(szName)
		self.screen.addPanel(szName, u"", u"", True, False,
				lRect.x(), lRect.y(), lRect.width(), lRect.height(),
				eStyle)
	def addDDS(self, szName,
			# Can be either an interface art info string
			# or a CvInfo object with a getButton method
			textureInfo,
			eWidgetType = None, iData1 = -1, iData2 = -1, szAttachTo = None):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lRect = gRect(szName)
		if isinstance(textureInfo, basestring):
			szTexture = ArtFileMgr.getInterfaceArtInfo(textureInfo).getPath()
		else:
			szTexture = textureInfo.getButton()
		if szAttachTo:
			lParent = gRect(szAttachTo)
			self.screen.addDDSGFCAt(szName, szAttachTo, szTexture,
					lRect.x() - lParent.x(), lRect.y() - lParent.y(), lRect.width(), lRect.height(),
					eWidgetType, iData1, iData2, False)
		else:
			self.screen.addDDSGFC(szName, szTexture,
					lRect.x(), lRect.y(), lRect.width(), lRect.height(),
					eWidgetType, iData1, iData2)
	def addDDSAt(self, szName, szAttachTo, textureInfo,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		self.addDDS(szName, textureInfo, eWidgetType, iData1, iData2, szAttachTo)
	def _setStyledImageButton(self, szName, szAttachTo, szTexture, style,
			eWidgetType, iData1, iData2):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lRect = gRect(szName)
		if isinstance(style, basestring):
			szStyle = style
		else:
			szStyle = None
		if szAttachTo:
			lParent = gRect(szAttachTo)
			assert szStyle
			self.screen.setImageButtonAt(szName, szAttachTo, szTexture,
					lRect.x() - lParent.x(), lRect.y() - lParent.y(), lRect.width(), lRect.height(),
					eWidgetType, iData1, iData2)
		else:
			if szStyle or style is None:
				self.screen.setImageButton(szName, szTexture,
						lRect.x(), lRect.y(), lRect.width(), lRect.height(),
						eWidgetType, iData1, iData2)
			else:
				self.screen.setButtonGFC(szName, u"", "",
						lRect.x(), lRect.y(), lRect.width(), lRect.height(),
						eWidgetType, iData1, iData2, style)
		if szStyle:
			self.screen.setStyle(szName, szStyle)
	def setStyledButton(self, szName, style, # Style can be a key string or ID
			eWidgetType = None, iData1 = -1, iData2 = -1, szAttachTo = None):
		self._setStyledImageButton(szName, szAttachTo, "", style,
				eWidgetType, iData1, iData2)
	def setStyledButtonAt(self, szName, szAttachTo, szStyle,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		self.setStyledButton(szName, szStyle, eWidgetType, iData1, iData2, szAttachTo)
	def setImageButton(self, szName, szTexture,
			eWidgetType = None, iData1 = -1, iData2 = -1, szAttachTo = None):
		artInfo = ArtFileMgr.getInterfaceArtInfo(szTexture)
		if artInfo:
			szTexture = artInfo.getPath()
		self._setStyledImageButton(szName, szAttachTo, szTexture, None,
				eWidgetType, iData1, iData2)
	def setImageButtonAt(self, szName, szAttachTo, szTexture,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		self.setImageButton(szName, szTexture, eWidgetType, iData1, iData2, szAttachTo)
	def addCheckBox(self, szName, szTextureKey, szHLTextureKey, eStyle,
			eWidgetType = None, iData1 = -1, iData2 = -1, szAttachTo = None):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lSquare = gRect(szName)
		szTexturePath = ArtFileMgr.getInterfaceArtInfo(szTextureKey).getPath()
		szHLTexturePath = ArtFileMgr.getInterfaceArtInfo(szHLTextureKey).getPath()
		if szAttachTo:
			lParent = gRect(szAttachTo)
			self.screen.addCheckBoxGFCAt(szAttachTo, szName,
					szTexturePath, szHLTexturePath,
					lSquare.x() - lParent.x(), lSquare.y() - lParent.y(), lSquare.size(), lSquare.size(),
					eWidgetType, iData1, iData2, eStyle, True)
		else:
			self.screen.addCheckBoxGFC(szName,
					szTexturePath, szHLTexturePath,
					lSquare.x(), lSquare.y(), lSquare.size(), lSquare.size(),
					eWidgetType, iData1, iData2, eStyle)
	def addCheckBoxAt(self, szName, szAttachTo, szTextureKey, szHLTextureKey, eStyle,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		self.addCheckBox(szName, szTextureKey, szHLTextureKey, eStyle, eWidgetType, iData1, iData2, szAttachTo)
	def addSlider(self, szName, iDefault, iMin = 0, iMax = -1, bVertical = False,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lRect = gRect(szName)
		if iMax < 0:
			iMax = lRect.width()
		self.screen.addSlider(szName,
				lRect.x(), lRect.y(), lRect.width(), lRect.height(),
				iDefault, iMin, iMax,
				eWidgetType, iData1, iData2, bVertical)
	def setLabel(self, szName, szAttachTo, szText, uiFlags, eFont, fZ = 0,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lPoint = gPoint(szName)
		self.screen.setLabel(szName, szAttachTo, szText, uiFlags,
				lPoint.x(), lPoint.y(), fZ,
				eFont, eWidgetType, iData1, iData2)
	def setText(self, szName, szAttachTo, szText, uiFlags, eFont, fZ = 0,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lPoint = gPoint(szName)
		self.screen.setText(szName, szAttachTo, szText, uiFlags,
				lPoint.x(), lPoint.y(), fZ,
				eFont, eWidgetType, iData1, iData2)
	# color can be either a key string or a color id
	def createProgressBar(self, szName, color, uiMarks, bForward):
		lRect = gRect(szName)
		if isinstance(color, basestring):
			eColor = gc.getInfoTypeForString(color)
		else:
			eColor = color
		return ProgressBarUtil.ProgressBar(szName + "-Canvas",
				lRect.x(), lRect.y(), lRect.width(), lRect.height(),
				eColor, uiMarks, bForward)
	def addStackedBar(self, szName,
			eWidgetType = None, iData1 = -1, iData2 = -1,
			szAttachTo = None):
		if eWidgetType is None:
			eWidgetType = WidgetTypes.WIDGET_GENERAL
		lRect = gRect(szName)
		if szAttachTo:
			lParent = gRect(szAttachTo)
			self.screen.addStackedBarGFCAt(szName, szAttachTo,
					lRect.x() - lParent.x(), lRect.y() - lParent.y(), lRect.width(), lRect.height(),
					InfoBarTypes.NUM_INFOBAR_TYPES,
					eWidgetType, iData1, iData2)
		else:
			self.screen.addStackedBarGFC(szName,
					lRect.x(), lRect.y(), lRect.width(), lRect.height(),
					InfoBarTypes.NUM_INFOBAR_TYPES,
					eWidgetType, iData1, iData2)
	def addStackedBarAt(self, szName, szAttachTo,
			eWidgetType = None, iData1 = -1, iData2 = -1):
		self.addStackedBar(szName, eWidgetType, iData1, iData2, szAttachTo)
	def setDefaultHelpTextArea(self, bMinMargin = False):
		# <advc.009b> Work around exceptions upon reloading scripts
		if not hasattr(self, "screen"):
			return # </advc.009b>
		if bMinMargin:
			# As in BtS; pretty arbitrary and overlaps the unit pane.
			iBottomMargin = VSPACE(50)
		else:
			iBottomMargin = (VSPACE(5) + gRect("CenterBottomPanel").height() +
					self.plotListUnitButtonSize())
		# (I don't think the HLENs will have any effect; seems that the EXE
		# ignores the fWidth and iMinWidth params.)
		self.screen.setHelpTextArea(HLEN(350), FontTypes.SMALL_FONT,
				HSPACE(7), gRect("Top").yBottom() - iBottomMargin, -0.1,
				False, "", True, False, CvUtil.FONT_LEFT_JUSTIFY, HLEN(300))
	# </advc.092>

	def __init__(self):
		# advc.009b: This hack is no longer needed. I've moved the global onSwitchHotSeatPlayer function to BugUtil.py.
		# BUG - start
		#global g_mainInterface
		#g_mainInterface = self
		# BUG - end

# BUG - draw method
		self.DRAW_METHOD_PLE = "DRAW_METHOD_PLE"
		self.DRAW_METHOD_VAN = "DRAW_METHOD_VAN"
		self.DRAW_METHOD_BUG = "DRAW_METHOD_BUG"
		# advc.069: No longer used
		#self.DRAW_METHODS = (self.DRAW_METHOD_PLE,
		#					 self.DRAW_METHOD_VAN,
		#					 self.DRAW_METHOD_BUG)
#		self.sDrawMethod = self.DRAW_METHOD_PLE
# BUG - draw method


# BUG - PLE - start
		self.PLE = PLE.PLE()
#		self.PLE.PLE_initialize()

		self.MainInterfaceInputMap = {
			self.PLE.PLOT_LIST_BUTTON_NAME	: self.PLE.getPlotListButtonName,
			self.PLE.PLOT_LIST_MINUS_NAME	: self.PLE.getPlotListMinusName,
			self.PLE.PLOT_LIST_PLUS_NAME	: self.PLE.getPlotListPlusName,
			self.PLE.PLOT_LIST_UP_NAME		: self.PLE.getPlotListUpName,
			self.PLE.PLOT_LIST_DOWN_NAME 	: self.PLE.getPlotListDownName,

			"PleViewModeStyle1"				: self.PLE.onClickPLEViewMode,
			self.PLE.PLE_VIEW_MODE			: self.PLE.onClickPLEViewMode,
			self.PLE.PLE_MODE_STANDARD		: self.PLE.onClickPLEModeStandard,
			self.PLE.PLE_MODE_MULTILINE		: self.PLE.onClickPLEModeMultiline,
			self.PLE.PLE_MODE_STACK_VERT	: self.PLE.onClickPLEModeStackVert,
			self.PLE.PLE_MODE_STACK_HORIZ	: self.PLE.onClickPLEModeStackHoriz,

			self.PLE.PLOT_LIST_PROMO_NAME	: self.PLE.unitPromotion,
			self.PLE.PLOT_LIST_UPGRADE_NAME	: self.PLE.unitUpgrade,

			self.PLE.PLE_RESET_FILTERS		: self.PLE.onClickPLEResetFilters,
			self.PLE.PLE_FILTER_CANMOVE		: self.PLE.onClickPLEFilterCanMove,
			self.PLE.PLE_FILTER_CANTMOVE	: self.PLE.onClickPLEFilterCantMove,
			self.PLE.PLE_FILTER_NOTWOUND	: self.PLE.onClickPLEFilterNotWound,
			self.PLE.PLE_FILTER_WOUND		: self.PLE.onClickPLEFilterWound,
			self.PLE.PLE_FILTER_LAND		: self.PLE.onClickPLEFilterLand,
			self.PLE.PLE_FILTER_SEA			: self.PLE.onClickPLEFilterSea,
			self.PLE.PLE_FILTER_AIR			: self.PLE.onClickPLEFilterAir,
			self.PLE.PLE_FILTER_MIL			: self.PLE.onClickPLEFilterMil,
			self.PLE.PLE_FILTER_DOM			: self.PLE.onClickPLEFilterDom,
			self.PLE.PLE_FILTER_OWN			: self.PLE.onClickPLEFilterOwn,
			self.PLE.PLE_FILTER_FOREIGN		: self.PLE.onClickPLEFilterForeign,

			self.PLE.PLE_GRP_UNITTYPE		: self.PLE.onClickPLEGrpUnittype,
			self.PLE.PLE_GRP_GROUPS			: self.PLE.onClickPLEGrpGroups,
			self.PLE.PLE_GRP_PROMO			: self.PLE.onClickPLEGrpPromo,
			self.PLE.PLE_GRP_UPGRADE		: self.PLE.onClickPLEGrpUpgrade,
		}

#		self.iVisibleUnits 			= 0
		self.iMaxPlotListIcons 		= 0


		self.bPLECurrentlyShowing	= False
		self.bVanCurrentlyShowing	= False
# BUG - draw method
		self.bBUGCurrentlyShowing	= False
# BUG - draw method

		self.xResolution = 0
		self.yResolution = 0
# BUG - PLE - end

# BUG - field of view slider - start
		self.sFieldOfView_Text = ""
		self.iField_View_Prev = -1
		self.iFoVPos_Prev = -1 # advc.090
# BUG - field of view slider - end


############## Basic operational functions ###################

	# advc.092 (note): Called externally (from PLE)
	def numPlotListButtonsPerRow(self):
		try: # advc.009b
			return self.m_iNumPlotListButtonsPerRow
		# <advc.009b>
		except AttributeError:
			return 0 # </advc.009b>
	# advc.092: So that PLE can access it
	def plotListUnitButtonSize(self):
		return BTNSZ(34)

	def unitButtonOverlaySize(self):
		return (12 * self.plotListUnitButtonSize()) / 34

# I know that this is redundant, but CyInterface().getPlotListOffset() (and prob the column one too)
# uses this function
# it is also used in "...\EntryPoints\CvScreensInterface.py"
	def numPlotListButtons(self):
		return self.numPlotListButtonsPerRow()

	def numPlotListRows(self):
		return gc.getMAX_PLOT_LIST_ROWS()

	def numPlotListButtons_Total(self):
		return self.numPlotListButtonsPerRow() * self.numPlotListRows()

	def initState (self, screen=None):
		"""
		Initialize screen instance (self.foo) and global variables.

		This function is called before drawing the screen (from interfaceScreen() below)
		and anytime the Python modules are reloaded (from CvEventInterface).

		THIS FUNCTION MUST NOT ALTER THE SCREEN -- screen.foo()
		"""
		if screen is None:
			screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		self.xResolution = screen.getXResolution()
		self.yResolution = screen.getYResolution()
		# <advc.092>
		gSetRectangle("Top", RectLayout(None, 0, 0, self.xResolution, self.yResolution))
		# Tbd.: Set based on a BUG option. And, if True, set the global scale factors.
		self.bScaleHUD = False # </advc.092>
		# advc.061:
		gc.getGame().setScreenDimensions(self.xResolution, self.yResolution)
# BUG - Raw Yields - begin
		global g_bYieldView
		global g_iYieldType
		g_bYieldView, g_iYieldType = RawYields.getViewAndType(
				CityScreenOpt.getRawYieldsDefaultView())
# BUG - Raw Yields - end

		# Set up our global variables...
		global g_NumEmphasizeInfos
		global g_NumCityTabTypes
		global g_NumHurryInfos
		global g_NumUnitClassInfos
		global g_NumBuildingClassInfos
		global g_NumProjectInfos
		global g_NumProcessInfos
		global g_NumActionInfos

		g_NumEmphasizeInfos = gc.getNumEmphasizeInfos()
		g_NumCityTabTypes = CityTabTypes.NUM_CITYTAB_TYPES
		g_NumHurryInfos = gc.getNumHurryInfos()
		g_NumUnitClassInfos = gc.getNumUnitClassInfos()
		g_NumBuildingClassInfos = gc.getNumBuildingClassInfos()
		g_NumProjectInfos = gc.getNumProjectInfos()
		g_NumProcessInfos = gc.getNumProcessInfos()
		g_NumActionInfos = gc.getNumActionInfos()

		# advc.092: Static positional data
		# Start with the mini map b/c that's the number one thing that I would
		# like to be adjusted to the screen resolution. Then base the size of
		# the corner panels on the mini map size etc.
		# Will first need the Globe button (its size affects the thickness of the
		# frame around the minimap). This gets positioned at (0,0) as some sort of
		# dummy/ template and later gets moved through moveItem. (Not my idea.)
		gSetSquare("GlobeButton", "Top", 0, 0, BTNSZ(28))
		self.setMiniMapRects()
		gSetRect("LowerLeftCornerPanel", "Top",
				RectLayout.LEFT, RectLayout.BOTTOM,
				HLEN(304), gRect("MiniMapPanel").height() + 17)
		gSetRect("LowerRightCornerPanel", "Top",
				RectLayout.RIGHT, RectLayout.BOTTOM,
				gRect("LowerLeftCornerPanel").width(), gRect("LowerLeftCornerPanel").height())
		gSetRect("LowerLeftCornerBackgr", "Top",
				0, 4,
				RectLayout.MAX, RectLayout.MAX)
		# The panel dimensions include decorations. The rest of the HUD is mostly
		# based on the undecorated size, so let's define ...
		gSetRect("LowerLeftCorner", "LowerLeftCornerPanel",
				0, 0, -8, -19)
		gSetRect("LowerRightCorner", "LowerRightCornerPanel",
				8, 0, RectLayout.MAX, -19)
		gSetRect("CenterBottomPanel", "Top",
				gRect("LowerLeftCorner").xRight(), RectLayout.BOTTOM,
				-gRect("LowerRightCorner").width(), HLEN(133))
		# Sans the decoration on top
		gSetRect("CenterBottom", "CenterBottomPanel",
				0, 17, RectLayout.MAX, RectLayout.MAX)

		gSetRect("CityLeftPanel", "Top",
				0, 0,
				HLEN(258), -gRect("LowerLeftCorner").height())
		gSetRect("CityRightPanel", "Top",
				RectLayout.RIGHT, 0,
				gRect("CityLeftPanel").width(), -gRect("LowerRightCorner").height())
		self.setTopBarRects()
		gSetRect("CityAdjustPanel", "CityLeftPanel",
				RectLayout.CENTER, gRect("TopBarsOneLineContainer").yBottom() + VSPACE(15),
				-HSPACE(10), VLEN(105))
		gSetRect("CityCenterColumn", "Top",
				gRect("CityLeftPanel").xRight(), 0,
				-gRect("CityRightPanel").width(), RectLayout.MAX)
		gSetRect("TopCityPanelCenter", "CityCenterColumn",
				0, 0,
				RectLayout.MAX, -gRect("CityLeftPanel").yBottom())
		gSetRect("CityNameBackground", "CityCenterColumn",
				RectLayout.CENTER, gRect("TopBarsOneLineContainer").yBottom() + 2,
				-HSPACE(2), VSPACE(38))

		gSetRect("LeftHalf", "Top",
				0, 0,
				gRect("Top").width() / 2, RectLayout.MAX)
		gSetRect("RightHalf", "Top",
				gRect("LeftHalf").xRight(), 0,
				RectLayout.MAX, RectLayout.MAX)
		# Background for top bars
		gSetRect("TopCityPanelLeft", "LeftHalf",
				gRect("CityNameBackground").x(), gRect("CityNameBackground").yBottom() + 1,
				RectLayout.MAX, 2 * (gStackBarDefaultHeight + VSPACE(3)))
		gSetRect("TopCityPanelRight", "RightHalf",
				0, gRect("TopCityPanelLeft").y(),
				gRect("CityNameBackground").width() / 2, gRect("TopCityPanelLeft").height())
		# The two panels above really form a single panel; they're separate only
		# so that the color fades away toward the middle. Let's put them together:
		# (Could also define this as a child of TopCityPanelCenter - which includes
		# CityNameBackground as well.) 
		gSetRect("TopCityPanelLeftAndRight", "Top",
				gRect("TopCityPanelLeft").x(), gRect("TopCityPanelLeft").y(),
				gRect("TopCityPanelLeft").width() + gRect("TopCityPanelRight").width(),
				gRect("TopCityPanelLeft").height())
		gSetRect("CityScreenTopWidget", "Top",
				0, -2,
				RectLayout.MAX, gRect("TopBarsOneLineContainer").yBottom() + VLEN(12), True)
		gSetRect("InterfaceTopCenter", "Top",
				gRect("CityLeftPanel").xRight() + 1, -2,
				-(gRect("CityRightPanel").width() - 1),
				gRect("TopBarsOneLineContainer").yBottom() + 19, True)
		gSetRect("InterfaceTopLeft", "Top",
				RectLayout.LEFT, gRect("InterfaceTopCenter").y(),
				gRect("CityLeftPanel").width() + 9,
				gRect("InterfaceTopCenter").height() + 12, True)
		gSetRect("InterfaceTopRight", "Top",
				RectLayout.RIGHT, gRect("InterfaceTopLeft").y(),
				gRect("InterfaceTopLeft").width(),
				gRect("InterfaceTopLeft").height(), True)

		self.setCityCenterBarRects()

		self.setAdvisorButtonRects()
		self.setTopRightButtonRects()
		# advc: BtS had used 27, BUG (always) 10.
		if self.bScaleHUD or MainOpt.isShowOptionsButton():
			iTurnLogBtnMargin = 10
		else:
			iTurnLogBtnMargin = 18
		gSetSquare("TurnLogButton", "Top",
				iTurnLogBtnMargin, gRect("AdvisorButtons").y() - 2,
				gRect("AdvisorButtons").height())

		iEndTurnBtnSz = BTNSZ(32)
		gSetSquare("EndTurnButton", "Top",
				-gRect("LowerRightCorner").width() + iEndTurnBtnSz / 2,
				-gRect("LowerRightCorner").height() + iEndTurnBtnSz / 2 + 2,
				32)
		iFlagWidth = 68
		gSetRect("CivilizationFlag", "LowerRightCorner",
				HSPACE(8), VSPACE(30),
				iFlagWidth, iFlagWidth * 250 / 68)

		self.setCityTabRects()
		# The height of the bottom button list isn't known here,
		# but the width is - and that width is needed in other places.
		# So let's define a helper rectangle with maximal height.
		iRMargin = gRect("CenterBottom").xRight() - gRect("CityTabs").x()
		iLMargin = iRMargin / 2
		iRMargin += 8
		iLMargin += 8
		gSetRect("BottomButtonMaxSpace", "CenterBottom",
				iLMargin, 0, -iRMargin, RectLayout.MAX)
# BUG - field of view slider - start
		# <advc.090>
		self.iFoVLabelLower = 10
		self.iFoVLabelUpper = 100
		#self.iW_FoVSlider = 100
		iW_FoVSlider = min(max(100, self.xResolution / 12), 200)
		iW_FoVSlider -= (iW_FoVSlider % 2)
		#self.iX_FoVSlider = self.xResolution - 120
		gSetRect("FoVSlider", "Top",
				-HSPACE(18), gRect("AdvisorButtons").yBottom() + VSPACE(4),
				iW_FoVSlider, VLEN(15))
		gOffSetPoint("FoVSliderText", "FoVSlider",
				-HSPACE(6), VSPACE(3))
		# </advc.090>
		self.sFieldOfView_Text = localText.getText(
				"TXT_KEY_BUG_OPT_MAININTERFACE__FIELDOFVIEW_TEXT", ())
		# K-Mod (bigger FoW for bigger monitors. They'll appreciate it. Trust me.)
		#self.DEFAULT_FIELD_OF_VIEW = max(40, min(80, self.xResolution / 30))
		#if MainOpt.isRememberFieldOfView():
			#self.iField_View = int(MainOpt.getFieldOfView())
			# K-Mod
			#if self.iField_View < 0:
				#self.iField_View = self.DEFAULT_FIELD_OF_VIEW
			# K-Mod end
		#else:
			#self.iField_View = self.DEFAULT_FIELD_OF_VIEW

		# <advc.004m> Replacing the above. Will have to ignore the XML setting
		# (like K-Mod does) to avoid recursion - BUG stores the
		# value computed for self.DEFAULT_FIELD_OF_VIEW in CvGlobals,
		# overwriting the FIELD_OF_VIEW set through XML until the game is restarted.
		# 42.0 originally (FIELD_OF_VIEW in GlobalDefines)
		self.DEFAULT_FIELD_OF_VIEW = 35.0
		#aspectFactor = pow((0.8 * self.xResolution) / self.yResolution, 0.72)
		if ((not MainOpt.isRememberFieldOfView() and
				not MainOpt.isShowFieldOfView()) or
				int(MainOpt.getFieldOfView())) < 0:
		#	self.DEFAULT_FIELD_OF_VIEW = int(max(self.DEFAULT_FIELD_OF_VIEW, min(2 * self.DEFAULT_FIELD_OF_VIEW, (aspectFactor * self.xResolution) / max(70 - self.DEFAULT_FIELD_OF_VIEW, 10))))
		# The above might be fine if resource bubbles scaled properly - but they don't.
			if self.yResolution > 1024:
				self.DEFAULT_FIELD_OF_VIEW = int(
						(self.DEFAULT_FIELD_OF_VIEW * self.yResolution) / 1024)
			self.iField_View = self.DEFAULT_FIELD_OF_VIEW
		else:
			self.iField_View = int(MainOpt.getFieldOfView())
		# </advc.004m>
# BUG - field of view slider - end
# BUG - Progress Bar - Tick Marks - start
		self.pTwoLineResearchBar = self.createProgressBar(
				"TwoLineResearchBar", "COLOR_RESEARCH_RATE",
				ProgressBarUtil.TICK_MARKS, True)
		self.pTwoLineResearchBar.addBarItem("TwoLineResearchBar")
		self.pTwoLineResearchBar.addBarItem("ResearchText")
		# BUG - Bars on single line for higher resolution screens - start
		self.pOneLineResearchBar = self.createProgressBar(
				"OneLineResearchBar", "COLOR_RESEARCH_RATE",
				ProgressBarUtil.TICK_MARKS, True)
		self.pOneLineResearchBar.addBarItem("OneLineResearchBar")
		self.pOneLineResearchBar.addBarItem("ResearchText")
		# BUG - Bars on single line for higher resolution screens - end
		self.pBarPopulationBar = self.createProgressBar("PopulationBar",
				gc.getYieldInfo(YieldTypes.YIELD_FOOD).getColorType(),
				ProgressBarUtil.SOLID_MARKS, True)
		self.pBarPopulationBar.addBarItem("PopulationBar")
		self.pBarPopulationBar.addBarItem("PopulationText")
		self.pBarProductionBar = self.createProgressBar("ProductionBar",
				gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getColorType(),
				ProgressBarUtil.TICK_MARKS, True)
		self.pBarProductionBar.addBarItem("ProductionBar")
		self.pBarProductionBar.addBarItem("ProductionText")
		self.pBarProductionBar_Whip = self.createProgressBar(
				"ProductionBar-Whip", "COLOR_YELLOW",
				ProgressBarUtil.CENTER_MARKS, False)
		self.pBarProductionBar_Whip.addBarItem("ProductionBar")
		self.pBarProductionBar_Whip.addBarItem("ProductionText")
# BUG - Progress Bar - Tick Marks - end

		iPlotListUnitBtnSz = self.plotListUnitButtonSize()
		self.m_iNumPlotListButtonsPerRow = (
				(gRect("BottomButtonMaxSpace").width() - 2 * iPlotListUnitBtnSz) /
				iPlotListUnitBtnSz)
		# advc.092: Moved down so that PLE can access the above
		self.PLE.PLE_CalcConstants(screen) # BUG - PLE
# BUG - BUG unit plot draw method - start
		# BUG unit panel
		self.BupPanel = BugUnitPlot.BupPanel(screen,
				gRect("Top").width(), gRect("Top").height(),
				gRect("BottomButtonMaxSpace").width(),
				self.numPlotListButtonsPerRow(), self.numPlotListRows())
# BUG - BUG unit plot draw method - end

	def setMiniMapRects(self):
		# <advc.137>
		iMiniMapHeight = VLEN(128) # was 122
		iDefaultMiniMapPanelWidth = iMiniMapHeight * 1625 / 1000 # BtS value
		# We can go a little wider
		iMaxMiniMapPanelWidth = iDefaultMiniMapPanelWidth + 8
		iMiniMapPanelWidth = iDefaultMiniMapPanelWidth
		iMiniMapPanelRMargin = HSPACE(6)
		if gc.getMap().isWrapX():
			# Avoid black bars on the sides
			iMiniMapPanelWidth = iMiniMapHeight * gc.getMap().getGridWidth()
			iMiniMapPanelWidth /= gc.getMap().getGridHeight()
			# Somehow the adjustment to map dimensions doesn't quite work out
			iMiniMapPanelWidth += iMiniMapPanelRMargin
			iMiniMapPanelWidth = min(iMiniMapPanelWidth, iMaxMiniMapPanelWidth)
		# Center the panel within the available space
		iMiniMapPanelRMargin += (iDefaultMiniMapPanelWidth - iMiniMapPanelWidth) / 2
		# </advc.137>
		iMiniMapVMargin = HSPACE(3)
		gSetRect("MiniMapPanel",
				# Ideally should be placed inside the LowerRightCorner rect,
				# but it's more intuitive to me to set the LowerRightCorner size
				# based on the mini map (panel) size than vice versa, so I'm
				# setting the mini map rects first.
				"Top",
				-iMiniMapPanelRMargin, RectLayout.BOTTOM,
				iMiniMapPanelWidth,
				iMiniMapHeight + gRect("GlobeButton").size() / 2 + 3 + 2 * iMiniMapVMargin)
		gSetRect("MiniMap", "MiniMapPanel",
				4, # As in BtS - and 3 indeed looks too thin on the left.
				-5, # advc.137: was 9
				-3, iMiniMapHeight)

# BUG - Great Person Bar - start
# Also BUG - Great General Bar,
# BUG - Bars on single line for higher resolution screens
	def setTopBarRects(self):
		gSetRect("TopBarsMaxSpace", "Top",
				gRect("CityLeftPanel").xRight() + HSPACE(8), VSPACE(2),
				-(gRect("CityRightPanel").width() + HSPACE(8)), 2 * VLEN(gStackBarDefaultHeight))
		fResearchBarWidth = fThinResearchBarWidth = 487
		fGGBarWidth = 100
		fThinGGBarWidth = 84
		iSpacing = HSPACE(7)
		iThinSpacing = HSPACE(6)
		fThinGPBarWidth = 320
		fOneLineTotalWidth = float(fResearchBarWidth + fThinGPBarWidth + fThinGGBarWidth +
				2 * iThinSpacing)
		if self.bScaleHUD: # Scale to use up the available space
			fMultOneLine = gRect("TopBarsMaxSpace").width() / fOneLineTotalWidth
			fResearchBarWidth *= fMultOneLine
			fThinGGBarWidth *= fMultOneLine
			fThinGPBarWidth *= fMultOneLine
			# Update total width
			fOneLineTotalWidth = (fResearchBarWidth + fThinGPBarWidth + fThinGGBarWidth +
					2 * iThinSpacing)
			fMultTwoLines = gRect("TopBarsMaxSpace").width() / float(fThinResearchBarWidth)
			fThinResearchBarWidth *= fMultTwoLines
			fGGBarWidth *= fMultTwoLines
		fGPBarWidth = fThinResearchBarWidth - fGGBarWidth - iSpacing
		gSetRect("TopBarsTwoLineContainer", "Top",
				RectLayout.CENTER, VSPACE(2),
				fThinResearchBarWidth, gRect("TopBarsMaxSpace").height())
		gSetRect("TopBarsOneLineContainer", "Top",
				RectLayout.CENTER, gRect("TopBarsTwoLineContainer").y(),
				fOneLineTotalWidth, gRect("TopBarsMaxSpace").height() / 2)
		gSetRect("OneLineGGBar", "TopBarsOneLineContainer",
				0, 0,
				fThinGGBarWidth, RectLayout.MAX)
		gSetRect("OneLineResearchBar", "TopBarsOneLineContainer",
				gRect("OneLineGGBar").width() + iThinSpacing, 0,
				fResearchBarWidth, RectLayout.MAX)
		gSetRect("OneLineGPBar", "TopBarsOneLineContainer",
				RectLayout.RIGHT, 0,
				fThinGPBarWidth, RectLayout.MAX)
		gSetRect("TwoLineResearchBar", "TopBarsTwoLineContainer",
				0, 0,
				fThinResearchBarWidth, gRect("TopBarsTwoLineContainer").height() / 2)
		gSetRect("TwoLineGGBar", "TopBarsTwoLineContainer",
				0, RectLayout.BOTTOM,
				fGGBarWidth, gRect("TopBarsTwoLineContainer").height() / 2)
		gSetRect("TwoLineGPBar", "TopBarsTwoLineContainer",
				RectLayout.RIGHT, RectLayout.BOTTOM,
				fGPBarWidth, gRect("TopBarsTwoLineContainer").height() / 2)
# BUG - Great Person Bar, BUG - Great General Bar - end

	def setCityCenterBarRects(self):
		iYieldTextWidth = HLEN(140)
		gSetRect("PopulationBar", "TopCityPanelLeftAndRight",
				iYieldTextWidth, VSPACE(4),
				-iYieldTextWidth, gStackBarDefaultHeight)
		gSetRect("ProductionBar", "TopCityPanelLeftAndRight",
				RectLayout.CENTER, -VSPACE(3),
				gRect("PopulationBar").width(), gStackBarDefaultHeight)
		gSetRectangle("ProductionBar-Whip", gRect("ProductionBar")) # BUG - Progress Bar - Tick Marks
		gOffSetPoint("PopulationText", "PopulationBar",
				RectLayout.CENTER, VSPACE(4))
		gOffSetPoint("ProductionText", "ProductionBar",
				RectLayout.CENTER, VSPACE(4))
		iTextVOffset = VSPACE(4)
		# NB: The "input texts" to the left will get right-aligned,
		# the happy and health text to the right will get left-aligned.
		# BUG - Food Rate Hover - start
		gOffSetPoint("PopulationInputText", "PopulationBar",
				-HSPACE(6), iTextVOffset)
		# BUG - Food Rate Hover - end
		gOffSetPoint("ProductionInputText", "ProductionBar",
				-HSPACE(6), iTextVOffset)
		gOffSetPoint("HealthText", "PopulationBar",
				HSPACE(6) + gRect("PopulationBar").width(), iTextVOffset)
		gOffSetPoint("HappinessText", "ProductionBar",
				HSPACE(6) + gRect("ProductionBar").width(), iTextVOffset)

	def setAdvisorButtonRects(self):
		iSize = BTNSZ(28)
		advisorNames = [ "Domestic", "Finance", "Civics", "Foreign", "Military", "Tech",
				"Religious", "Corporation", "Victory", "Info" ]
		if GameUtil.isEspionage():
			advisorNames.append("Espionage")
		iButtons = len(advisorNames)
		iSpacing = -iround(iSize / 10.0)
		if iButtons <= 10:
			iSpacing += 1
		lButtons = RowLayout(gRect("Top"),
				RectLayout.RIGHT, gRect("InterfaceTopRight").yBottom() - iSize - 3,
				iButtons, iSpacing, iSize)
		lButtons.move(-iSpacing / 3, 0)
		gSetRectangle("AdvisorButtons", lButtons)
		for szAdvisorName in advisorNames:
			gSetRectangle(szAdvisorName + "AdvisorButton", lButtons.next())

	def setTopRightButtonRects(self):
		lButtons = RowLayout(gRect("Top"),
				-HSPACE(4), VSPACE(2),
				2, HSPACE(2), BTNSZ(24))
		gSetRectangle("TopRightButtons", lButtons)
		gSetRectangle("MainMenuButton", lButtons.next())
		gSetRectangle("InterfaceHelpButton", lButtons.next())

	def setCityTabRects(self):
		iButtons = 3
		lButtons = ColumnLayout(gRect("CenterBottom"),
				-HSPACE(4), RectLayout.CENTER,
				iButtons, VSPACE(0), BTNSZ(24))
		gSetRectangle("CityTabs", lButtons)
		for i in range(iButtons):
			gSetRectangle("CityTab" + str(i), lButtons.next())

	def interfaceScreen (self):
		"""
		Draw all of the screen elements.
		This function is called once after starting or loading a game.
		THIS FUNCTION MUST NOT CREATE ANY INSTANCE OR GLOBAL VARIABLES.
		It may alter existing ones created in __init__() or initState(), however.
		"""
		if (CyGame().isPitbossHost()):
			return

		# This is the main interface screen, create it as such
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		self.screen = screen # advc.092
		self.initState(screen)
		screen.setForcedRedraw(True)
		screen.setDimensions(0, 0, self.xResolution, self.yResolution)

		xResolution = self.xResolution
		yResolution = self.yResolution
		lTop = gRect("Top")

		self.setDefaultHelpTextArea()

		self.addPanel("CityLeftPanel")
		screen.setStyle("CityLeftPanel", "Panel_City_Left_Style")
		screen.hide("CityLeftPanel")

		self.addPanel("CityRightPanel")
		screen.setStyle("CityRightPanel", "Panel_City_Right_Style")
		screen.hide("CityRightPanel")

		self.addPanel("TopCityPanelCenter")
		screen.setStyle("TopCityPanelCenter", "Panel_City_Top_Style")
		screen.hide("TopCityPanelCenter")

		self.addPanel("CityAdjustPanel")
		screen.setStyle("CityAdjustPanel", "Panel_City_Info_Style")
		screen.hide("CityAdjustPanel")

		self.addPanel("TopCityPanelLeft")
		screen.setStyle("TopCityPanelLeft", "Panel_City_TanTL_Style")
		screen.hide("TopCityPanelLeft")
		self.addPanel("TopCityPanelRight")
		screen.setStyle("TopCityPanelRight", "Panel_City_TanTR_Style")
		screen.hide("TopCityPanelRight")

		# Top Bar
		# SF CHANGE  (advc, note: This panel and the other marked by Firaxis with
		# "SF CHANGE" deal with decorations around the research bar. This one here
		# draws a line between the non-city info on top and the proper city screen.
		# The other one draws brackets around the research bar.)
		self.addPanel("CityScreenTopWidget")
		screen.setStyle("CityScreenTopWidget", "Panel_TopBar_Style")
		screen.hide("CityScreenTopWidget")

		self.addPanel("CityNameBackground")
		screen.setStyle("CityNameBackground", "Panel_City_Title_Style")
		screen.hide("CityNameBackground")

		self.addPanel("CenterBottomPanel")
		screen.setStyle("CenterBottomPanel", "Panel_Game_HudBC_Style")
		screen.hide("CenterBottomPanel")

		self.addPanel("LowerLeftCornerPanel")
		screen.setStyle("LowerLeftCornerPanel", "Panel_Game_HudBL_Style")
		screen.hide("LowerLeftCornerPanel")
		# advc: The BtS name for this graphic had clashed with the panel above and,
		# therefore, had had no effect. Fixed, and I've also added show and hide calls
		# throughout the module. It thickens the edges of the corner panel. I don't
		# ultimately like how that looks, so I've commented out the show calls.
		# (There's also an unused texture INTERFACE_BOTTOM_RIGHT, but that one
		# doesn't align with the Globe button, perhaps because the layout changed a bit
		# at some point.)
		self.addDDS("LowerLeftCornerBackgr", "INTERFACE_BOTTOM_LEFT")
		screen.hide("LowerLeftCornerBackgr")

		self.addPanel("LowerRightCornerPanel")
		screen.setStyle("LowerRightCornerPanel", "Panel_Game_HudBR_Style")
		screen.hide("LowerRightCornerPanel")

		self.addPanel("InterfaceTopCenter")
		screen.setStyle("InterfaceTopCenter", "Panel_Game_HudTC_Style")
		screen.hide("InterfaceTopCenter")

		self.addPanel("InterfaceTopLeft")
		screen.setStyle("InterfaceTopLeft", "Panel_Game_HudTL_Style")
		screen.hide("InterfaceTopLeft")

		self.addPanel("InterfaceTopRight")
		screen.setStyle("InterfaceTopRight", "Panel_Game_HudTR_Style")
		screen.hide("InterfaceTopRight")

		# Turn log Button
		self.setStyledButton("TurnLogButton", "Button_HUDLog_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_TURN_LOG).getActionInfoIndex())
		screen.hide("TurnLogButton")
		# Advisor Buttons...
		self.setStyledButton("DomesticAdvisorButton", "Button_HUDAdvisorDomestic_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_DOMESTIC_SCREEN).getActionInfoIndex())
		screen.hide("DomesticAdvisorButton")
		self.setStyledButton("FinanceAdvisorButton", "Button_HUDAdvisorFinance_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_FINANCIAL_SCREEN).getActionInfoIndex())
		screen.hide("FinanceAdvisorButton")
		self.setStyledButton("CivicsAdvisorButton", "Button_HUDAdvisorCivics_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_CIVICS_SCREEN).getActionInfoIndex())
		screen.hide("CivicsAdvisorButton")
		self.setStyledButton("ForeignAdvisorButton", "Button_HUDAdvisorForeign_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_FOREIGN_SCREEN).getActionInfoIndex())
		screen.hide("ForeignAdvisorButton")
		self.setStyledButton("MilitaryAdvisorButton", "Button_HUDAdvisorMilitary_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_MILITARY_SCREEN).getActionInfoIndex())
		screen.hide("MilitaryAdvisorButton")
		self.setStyledButton("TechAdvisorButton", "Button_HUDAdvisorTechnology_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_TECH_CHOOSER).getActionInfoIndex())
		screen.hide("TechAdvisorButton")
		self.setStyledButton("ReligiousAdvisorButton", "Button_HUDAdvisorReligious_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_RELIGION_SCREEN).getActionInfoIndex())
		screen.hide("ReligiousAdvisorButton")
		self.setStyledButton("CorporationAdvisorButton", "Button_HUDAdvisorCorporation_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_CORPORATION_SCREEN).getActionInfoIndex())
		screen.hide("CorporationAdvisorButton")
		self.setStyledButton("VictoryAdvisorButton", "Button_HUDAdvisorVictory_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_VICTORY_SCREEN).getActionInfoIndex())
		screen.hide("VictoryAdvisorButton")
		self.setStyledButton("InfoAdvisorButton", "Button_HUDAdvisorRecord_Style",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_INFO).getActionInfoIndex())
		screen.hide("InfoAdvisorButton")
# BUG - 3.17 No Espionage - start
		if GameUtil.isEspionage():
			self.setStyledButton("EspionageAdvisorButton", "Button_HUDAdvisorEspionage_Style",
					WidgetTypes.WIDGET_ACTION,
					gc.getControlInfo(ControlTypes.CONTROL_ESPIONAGE_SCREEN).getActionInfoIndex())
			screen.hide("EspionageAdvisorButton")
# BUG - 3.17 No Espionage - end
# BUG - field of view slider - start
		self.setFieldofView_Text(screen)
		self.addSlider("FoVSlider", self.FoVToSliderPos(self.iField_View))
		screen.hide("FoVSliderText")
		screen.hide("FoVSlider")
# BUG - field of view slider - end
		# City Tabs ...
		self.setStyledButton("CityTab0", "Button_HUDJumpUnit_Style",
				WidgetTypes.WIDGET_CITY_TAB, 0)
		screen.hide("CityTab0")
		self.setStyledButton("CityTab1", "Button_HUDJumpBuilding_Style",
				WidgetTypes.WIDGET_CITY_TAB, 1)
		screen.hide("CityTab1")
		self.setStyledButton("CityTab2", "Button_HUDJumpWonder_Style",
				WidgetTypes.WIDGET_CITY_TAB, 2)
		screen.hide("CityTab2")

		screen.setMainInterface(True)
		# Minimap initialization ...
		self.addPanel("MiniMapPanel")
		screen.setStyle("MiniMapPanel", "Panel_Game_HudMap_Style")
		screen.hide("MiniMapPanel")
		MinimapOptions.init() # advc.002a: Let DLL cache minimap options
		self.initMinimap() # advc: Moved into new function
		gc.getMap().updateMinimapColor()
		self.createMinimapButtons()

		# Help button (always visible), main menu button
		self.setImageButton("InterfaceHelpButton", "INTERFACE_GENERAL_CIVILOPEDIA_ICON",
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_CIVILOPEDIA).getActionInfoIndex())
		screen.hide("InterfaceHelpButton")
		self.setImageButton("MainMenuButton", "INTERFACE_GENERAL_MENU_ICON",
				WidgetTypes.WIDGET_MENU_ICON)
		screen.hide("MainMenuButton")

		self.createGlobeviewButtons()

		self.updateBottomButtonList()
		screen.hide("BottomButtonList")

		self.createPlotListFrames() # advc: Moved into subroutine

		# End Turn Text
		screen.setLabel("EndTurnText", "Background",
				u"", CvUtil.FONT_CENTER_JUSTIFY, 0,
				yResolution - 188, -0.1, FontTypes.GAME_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.setHitTest("EndTurnText", HitTestTypes.HITTEST_NOHIT)

		# Three states for end turn button...
		self.setStyledButton("EndTurnButton", "Button_HUDEndTurn_Style",
				WidgetTypes.WIDGET_END_TURN)
		screen.setEndTurnState("EndTurnButton", "Red")
		screen.hide("EndTurnButton")

		# *********************************************************************************
		# RESEARCH BUTTONS
		# *********************************************************************************

		i = 0
		for i in range(gc.getNumTechInfos()):
			szName = "ResearchButton" + str(i)
			screen.setImageButton(szName,
					gc.getTechInfo(i).getButton(),
					0, 0, 32, 32,
					WidgetTypes.WIDGET_RESEARCH, i, -1)
			screen.hide(szName)

		i = 0
		for i in range(gc.getNumReligionInfos()):
			szName = "ReligionButton" + str(i)
			if gc.getGame().isOption(GameOptionTypes.GAMEOPTION_PICK_RELIGION):
				szButton = gc.getReligionInfo(i).getGenericTechButton()
			else:
				szButton = gc.getReligionInfo(i).getTechButton()
			screen.setImageButton(szName, szButton,
					0, 0, 32, 32,
					WidgetTypes.WIDGET_RESEARCH, gc.getReligionInfo(i).getTechPrereq(), -1)
			screen.hide(szName)

		# *********************************************************************************
		# CITIZEN BUTTONS
		# *********************************************************************************

		szHideCitizenList = []

		# Angry Citizens
		i = 0
		for i in range(MAX_CITIZEN_BUTTONS):
			szName = "AngryCitizen" + str(i)
			screen.setImageButton(szName,
					ArtFileMgr.getInterfaceArtInfo("INTERFACE_ANGRYCITIZEN_TEXTURE").getPath(),
					xResolution - 74 - (26 * i),
					yResolution - 238,
					24, 24,
					WidgetTypes.WIDGET_ANGRY_CITIZEN, -1, -1)
			screen.hide(szName)

		iCount = 0

		# Increase Specialists...
		i = 0
		for i in range(gc.getNumSpecialistInfos()):
			if (gc.getSpecialistInfo(i).isVisible()):
				szName = "IncreaseSpecialist" + str(i)
				screen.setButtonGFC(szName, u"", "",
						xResolution - 46, (yResolution - 270 - (26 * iCount)), 20, 20,
						WidgetTypes.WIDGET_CHANGE_SPECIALIST, i, 1,
						ButtonStyles.BUTTON_STYLE_CITY_PLUS)
				screen.hide(szName)

				iCount = iCount + 1

		iCount = 0

		# Decrease specialists
		i = 0
		for i in range(gc.getNumSpecialistInfos()):
			if (gc.getSpecialistInfo(i).isVisible()):
				szName = "DecreaseSpecialist" + str(i)
				screen.setButtonGFC(szName, u"", "",
						xResolution - 24, (yResolution - 270 - (26 * iCount)), 20, 20,
						WidgetTypes.WIDGET_CHANGE_SPECIALIST, i, -1,
						ButtonStyles.BUTTON_STYLE_CITY_MINUS)
				screen.hide(szName)

				iCount = iCount + 1

		iCount = 0

		# Citizen Buttons
		i = 0
		for i in range(gc.getNumSpecialistInfos()):

			if (gc.getSpecialistInfo(i).isVisible()):

				szName = "CitizenDisabledButton" + str(i)
				screen.setImageButton(szName,
						gc.getSpecialistInfo(i).getTexture(),
						xResolution - 74, (yResolution - 272 - (26 * i)), 24, 24,
						WidgetTypes.WIDGET_DISABLED_CITIZEN, i, -1)
				screen.enable(szName, False)
				screen.hide(szName)

				for j in range(MAX_CITIZEN_BUTTONS):
					szName = "CitizenButton" + str((i * 100) + j)
					screen.addCheckBoxGFC(
							szName, gc.getSpecialistInfo(i).getTexture(), "",
							xResolution - 74 - (26 * j),
							(yResolution - 272 - (26 * i)),
							24, 24,
							WidgetTypes.WIDGET_CITIZEN, i, j,
							ButtonStyles.BUTTON_STYLE_LABEL)
					screen.hide(szName)

# BUG - city specialist - start
		screen.addPanel("SpecialistBackground", u"", u"", True, False,
				# advc.004: y position was yResolution minus 423.
				# That works well for the stacked specialists, but not for the other options.
				xResolution - 243, yResolution - 475, 230, 30,
				PanelStyles.PANEL_STYLE_STANDARD)
		screen.setStyle("SpecialistBackground", "Panel_City_Header_Style")
		screen.hide("SpecialistBackground")
		screen.setLabel("SpecialistLabel", "Background",
				localText.getText("TXT_KEY_CONCEPT_SPECIALISTS", ()),
				CvUtil.FONT_CENTER_JUSTIFY,
				xResolution - 128,
				# advc.004: y position was yResolution minus 415.
				yResolution - 467, -0.1,
				FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.hide("SpecialistLabel")
# BUG - city specialist - end

		# **********************************************************
		# GAME DATA STRINGS
		# **********************************************************
		szGameDataList = []

		self.addStackedBar("TwoLineResearchBar", WidgetTypes.WIDGET_RESEARCH)
		screen.setStackedBarColors("TwoLineResearchBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_RESEARCH_STORED"))
		screen.setStackedBarColors("TwoLineResearchBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_RESEARCH_RATE"))
		screen.setStackedBarColors("TwoLineResearchBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("TwoLineResearchBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("TwoLineResearchBar")
# BUG - Great General Bar - start
		self.addStackedBar("TwoLineGGBar", WidgetTypes.WIDGET_HELP_GREAT_GENERAL)
		screen.setStackedBarColors("TwoLineGGBar", InfoBarTypes.INFOBAR_STORED,
				#gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
				gc.getInfoTypeForString("COLOR_NEGATIVE_RATE"))
		screen.setStackedBarColors("TwoLineGGBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("TwoLineGGBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("TwoLineGGBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("TwoLineGGBar")
# BUG - Great General Bar - end
# BUG - Great Person Bar - start
		self.addStackedBar("TwoLineGPBar", WidgetTypes.WIDGET_GP_PROGRESS_BAR)
		screen.setStackedBarColors("TwoLineGPBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
		screen.setStackedBarColors("TwoLineGPBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_RATE"))
		screen.setStackedBarColors("TwoLineGPBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("TwoLineGPBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("TwoLineGPBar")
# BUG - Great Person Bar - end
# BUG - Bars on single line for higher resolution screens - start
		self.addStackedBar("OneLineGGBar", WidgetTypes.WIDGET_HELP_GREAT_GENERAL)
		screen.setStackedBarColors("OneLineGGBar", InfoBarTypes.INFOBAR_STORED,
				#gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
				gc.getInfoTypeForString("COLOR_NEGATIVE_RATE"))
		screen.setStackedBarColors("OneLineGGBar",
				InfoBarTypes.INFOBAR_RATE, gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("OneLineGGBar",
				InfoBarTypes.INFOBAR_RATE_EXTRA, gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("OneLineGGBar",
				InfoBarTypes.INFOBAR_EMPTY, gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("OneLineGGBar")

		self.addStackedBar("OneLineResearchBar", WidgetTypes.WIDGET_RESEARCH)
		screen.setStackedBarColors("OneLineResearchBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_RESEARCH_STORED"))
		screen.setStackedBarColors("OneLineResearchBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_RESEARCH_RATE"))
		screen.setStackedBarColors("OneLineResearchBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("OneLineResearchBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("OneLineResearchBar")

		self.addStackedBar("OneLineGPBar", WidgetTypes.WIDGET_GP_PROGRESS_BAR)
		screen.setStackedBarColors("OneLineGPBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
		screen.setStackedBarColors("OneLineGPBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_RATE"))
		screen.setStackedBarColors("OneLineGPBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("OneLineGPBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("OneLineGPBar")
# BUG - Bars on single line for higher resolution screens - end


		# *********************************************************************************
		# SELECTION DATA BUTTONS/STRINGS
		# *********************************************************************************

		szHideSelectionDataList = []

		self.addStackedBar("PopulationBar", WidgetTypes.WIDGET_HELP_POPULATION)
		screen.setStackedBarColors("PopulationBar", InfoBarTypes.INFOBAR_STORED,
				gc.getYieldInfo(YieldTypes.YIELD_FOOD).getColorType())
		screen.setStackedBarColorsAlpha("PopulationBar", InfoBarTypes.INFOBAR_RATE,
				gc.getYieldInfo(YieldTypes.YIELD_FOOD).getColorType(), 0.8)
		screen.setStackedBarColors("PopulationBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_NEGATIVE_RATE"))
		screen.setStackedBarColors("PopulationBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("PopulationBar")

		self.addStackedBar("ProductionBar", WidgetTypes.WIDGET_HELP_PRODUCTION)
		screen.setStackedBarColors("ProductionBar", InfoBarTypes.INFOBAR_STORED,
				gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getColorType())
		screen.setStackedBarColorsAlpha("ProductionBar", InfoBarTypes.INFOBAR_RATE,
				gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getColorType(), 0.8)
		screen.setStackedBarColors("ProductionBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getYieldInfo(YieldTypes.YIELD_FOOD).getColorType())
		screen.setStackedBarColors("ProductionBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("ProductionBar")

		screen.addStackedBarGFC("GreatPeopleBar",
				xResolution - 246, yResolution - 188,
				240, gStackBarDefaultHeight,
				InfoBarTypes.NUM_INFOBAR_TYPES,
				WidgetTypes.WIDGET_HELP_GREAT_PEOPLE, -1, -1)
		screen.setStackedBarColors("GreatPeopleBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
		screen.setStackedBarColors("GreatPeopleBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_RATE"))
		screen.setStackedBarColors("GreatPeopleBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("GreatPeopleBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("GreatPeopleBar")

		screen.addStackedBarGFC("CultureBar",
				6, yResolution - 188,
				240, gStackBarDefaultHeight,
				InfoBarTypes.NUM_INFOBAR_TYPES,
				WidgetTypes.WIDGET_HELP_CULTURE, -1, -1)
		screen.setStackedBarColors("CultureBar", InfoBarTypes.INFOBAR_STORED,
				gc.getInfoTypeForString("COLOR_CULTURE_STORED"))
		screen.setStackedBarColors("CultureBar", InfoBarTypes.INFOBAR_RATE,
				gc.getInfoTypeForString("COLOR_CULTURE_RATE"))
		screen.setStackedBarColors("CultureBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.setStackedBarColors("CultureBar", InfoBarTypes.INFOBAR_EMPTY,
				gc.getInfoTypeForString("COLOR_EMPTY"))
		screen.hide("CultureBar")

# BUG - Limit/Extra Religions - start
#		# Holy City Overlay
#		for i in range(gc.getNumReligionInfos()):
#			xCoord = xResolution - 242 + (i * 34)
#			yCoord = 42
#			szName = "ReligionHolyCityDDS" + str(i)
#			screen.addDDSGFC(szName, ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(), xCoord, yCoord, 24, 24, WidgetTypes.WIDGET_HELP_RELIGION_CITY, i, -1)
#			screen.hide(szName)
# BUG - Limit/Extra Religions - end

# BUG - Limit/Extra Corporations - start
#		for i in range(gc.getNumCorporationInfos()):
#			xCoord = xResolution - 242 + (i * 34)
#			yCoord = 66
#			szName = "CorporationHeadquarterDDS" + str(i)
#			screen.addDDSGFC(szName, ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(), xCoord, yCoord, 24, 24, WidgetTypes.WIDGET_HELP_CORPORATION_CITY, i, -1)
#			screen.hide(szName)
# BUG - Limit/Extra Corporations - end

		screen.addStackedBarGFC("NationalityBar",
				6, yResolution - 214,
				240, gStackBarDefaultHeight,
				InfoBarTypes.NUM_INFOBAR_TYPES,
				WidgetTypes.WIDGET_HELP_NATIONALITY, -1, -1)
		screen.hide("NationalityBar")

		screen.setButtonGFC("CityScrollMinus", u"", "",
				274, 32, 32, 32,
				WidgetTypes.WIDGET_CITY_SCROLL, -1, -1,
				ButtonStyles.BUTTON_STYLE_ARROW_LEFT)
		screen.hide("CityScrollMinus")

		screen.setButtonGFC("CityScrollPlus", u"", "",
				288, 32, 32, 32,
				WidgetTypes.WIDGET_CITY_SCROLL, 1, -1,
				ButtonStyles.BUTTON_STYLE_ARROW_RIGHT)
		screen.hide("CityScrollPlus")

# BUG - City Arrows - start
		screen.setButtonGFC("MainCityScrollMinus", u"", "",
				xResolution - 275, yResolution - 165, 32, 32,
				WidgetTypes.WIDGET_CITY_SCROLL, -1, -1,
				ButtonStyles.BUTTON_STYLE_ARROW_LEFT)
		screen.hide("MainCityScrollMinus")

		screen.setButtonGFC("MainCityScrollPlus", u"", "",
				xResolution - 255, yResolution - 165, 32, 32,
				WidgetTypes.WIDGET_CITY_SCROLL, 1, -1,
				ButtonStyles.BUTTON_STYLE_ARROW_RIGHT)
		screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end

		screen.addPanel("TradeRouteListBackground", u"", u"",
				True, False, 10, 157, 238, 30,
				PanelStyles.PANEL_STYLE_STANDARD)
		screen.setStyle("TradeRouteListBackground", "Panel_City_Header_Style")
		screen.hide("TradeRouteListBackground")

		screen.setLabel("TradeRouteListLabel", "Background",
				localText.getText("TXT_KEY_HEADING_TRADEROUTE_LIST", ()),
				CvUtil.FONT_CENTER_JUSTIFY,
				129, 165, -0.1, FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.hide("TradeRouteListLabel")

# BUG - Raw Yields - start
		nX = 10 + 24
		nY = 157 + 5
		nSize = 24
		nDist = 24
		nGap = 10
		szHighlightButton = ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_HIGHLIGHT").getPath()

		# Trade
		screen.addCheckBoxGFC("RawYieldsTrade0",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_TRADE").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 0, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsTrade0")

		# Yields
		nX += nDist + nGap
		screen.addCheckBoxGFC("RawYieldsFood1",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_FOOD").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 1, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsFood1")
		nX += nDist
		screen.addCheckBoxGFC("RawYieldsProduction2",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_PRODUCTION").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 2, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsProduction2")
		nX += nDist
		screen.addCheckBoxGFC("RawYieldsCommerce3",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_COMMERCE").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 3, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsCommerce3")

		# Tile Selection
		nX += nDist + nGap
		screen.addCheckBoxGFC("RawYieldsWorkedTiles4",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_WORKED_TILES").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 4, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsWorkedTiles4")
		nX += nDist
		screen.addCheckBoxGFC("RawYieldsCityTiles5",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_CITY_TILES").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 5, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsCityTiles5")
		nX += nDist
		screen.addCheckBoxGFC("RawYieldsOwnedTiles6",
				ArtFileMgr.getInterfaceArtInfo("RAW_YIELDS_OWNED_TILES").getPath(),
				szHighlightButton,
				nX, nY, nSize, nSize,
				WidgetTypes.WIDGET_GENERAL, 6, -1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.hide("RawYieldsOwnedTiles6")
# BUG - Raw Yields - end

# BUG - BUG Option Button - Start
		# <advc.092>
		iBtnWidth = 28
		iBtnY = iBtnWidth - 1 # </advc.092>
		iBtnX = 27
		iBtnX = 10

#		sBUGOptionsScreenButton = ArtFileMgr.getInterfaceArtInfo("BUG_OPTIONS_SCREEN_BUTTON").getPath()
#		screen.setImageButton("BUGOptionsScreenWidget", sBUGOptionsScreenButton, iBtnX + 30, iBtnY - 2, iBtnWidth, iBtnWidth, WidgetTypes.WIDGET_BUG_OPTION_SCREEN, -1, -1)
		screen.setImageButton("BUGOptionsScreenWidget", "",
				iBtnX + 30, iBtnY - 2, iBtnWidth, iBtnWidth,
				WidgetTypes.WIDGET_BUG_OPTION_SCREEN, -1, -1)
		screen.setStyle("BUGOptionsScreenWidget", "Button_HUDAdvisorCorporation_Style")
		screen.hide("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End

		screen.addPanel("BuildingListBackground", u"", u"",
				True, False, 10, 287, 238, 30,
				PanelStyles.PANEL_STYLE_STANDARD)
		screen.setStyle("BuildingListBackground", "Panel_City_Header_Style")
		screen.hide("BuildingListBackground")

		screen.setLabel("BuildingListLabel", "Background",
				localText.getText("TXT_KEY_CONCEPT_BUILDINGS", ()),
				CvUtil.FONT_CENTER_JUSTIFY,
				129, 295, -0.1, FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.hide("BuildingListLabel")

		# *********************************************************************************
		# UNIT INFO ELEMENTS
		# *********************************************************************************

		i = 0
		szCircleArt = ArtFileMgr.getInterfaceArtInfo("WHITE_CIRCLE_40").getPath()
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButton" + str(i)
			screen.addDDSGFC(szName,
					gc.getPromotionInfo(i).getButton(),
					180, yResolution - 18, 24, 24,
					WidgetTypes.WIDGET_PEDIA_JUMP_TO_PROMOTION, i, -1)
			screen.hide(szName)
# BUG - Stack Promotions - start
			szName = "PromotionButtonCircle" + str(i)
			x, y = self.calculatePromotionButtonPosition(screen, i)
			screen.addDDSGFC(szName,
					szCircleArt,
					x + 10, y + 10, 16, 16,
					WidgetTypes.WIDGET_PEDIA_JUMP_TO_PROMOTION, i, -1)
			screen.hide(szName)
# BUG - Stack Promotions - end

# BUG - PLE - begin
			szName = self.PLE.PLE_PROMO_BUTTONS_UNITINFO + str(i)
			screen.addDDSGFC(szName,
					gc.getPromotionInfo(i).getButton(),
					180, yResolution - 18,
					self.PLE.CFG_INFOPANE_BUTTON_SIZE, self.PLE.CFG_INFOPANE_BUTTON_SIZE,
					WidgetTypes.WIDGET_ACTION, gc.getPromotionInfo(i).getActionInfoIndex(), -1)
			screen.hide(szName)
# BUG - PLE - end

		# *********************************************************************************
		# SCORES
		# *********************************************************************************

		screen.addPanel("ScoreBackground", u"", u"",
				True, False, 0, 0, 0, 0,
				PanelStyles.PANEL_STYLE_HUD_HELP)
		screen.hide("ScoreBackground")

		for i in range(gc.getMAX_PLAYERS()):
			szName = "ScoreText" + str(i)
			screen.setText(szName, "Background",
					u"", CvUtil.FONT_RIGHT_JUSTIFY,
					996, 622, -0.3, FontTypes.SMALL_FONT,
					WidgetTypes.WIDGET_CONTACT_CIV, i, -1)
			screen.hide(szName)

		# This should be a forced redraw screen
		screen.setForcedRedraw(True)

		# This should show the screen immidiately and pass input to the game
		screen.showScreen(PopupStates.POPUPSTATE_IMMEDIATE, True)

		szHideList = []

		szHideList.append("CreateGroup")
		szHideList.append("DeleteGroup")

		# City Tabs
		for i in range(g_NumCityTabTypes):
			szButtonID = "CityTab" + str(i)
			szHideList.append(szButtonID)

		for i in range(g_NumHurryInfos):
			szButtonID = "Hurry" + str(i)
			szHideList.append(szButtonID)

		szHideList.append("Hurry0")
		szHideList.append("Hurry1")

		screen.registerHideList(szHideList, len(szHideList), 0)

		return 0

	def initMinimap(self): # advc (needed in two places)
		try: # advc.009b: Work around Python exceptions upon reloading scripts
			lRect = gRect("MiniMap")
		except KeyError:
			return
		try:
			# This should recreate the minimap on load games and returns if already exists -JW
			self.screen.initMinimap(
					lRect.x(), lRect.xRight(), lRect.y(), lRect.yBottom(), -0.1)
		except AttributeError:
			pass

	def updateBottomButtonList(self):
# BUG - Build/Action Icon Size - start
		if MainOpt.isBuildIconSizeLarge():
			iButtonSize = 64
		elif MainOpt.isBuildIconSizeMedium():
			iButtonSize = 48
		else:
			iButtonSize = 36
		# EF: minimum icon size for disabled buttons to work is 33 so these sizes won't fly
		# iButtonSize=32, iHeight=102
		# iButtonSize=24, iHeight=104
		# advc.092: Apply HUD scaling in addition to BUG option
		iButtonSize = BTNSZ(iButtonSize)
		# advc: I don't know why the BUG heights were chosen.
		# I think they should be multiples of the button size. That was
		# almost exactly the case for the three button sizes above 33.
		iMaxHeight = gRect("CenterBottom").height() - 2 * VSPACE(1)
		iHeight = max(iButtonSize, iMaxHeight - (iMaxHeight % iButtonSize)
				+ 4) # A little extra to avoid a vertical slider
		iVMargin = iMaxHeight - iHeight + 2 * VSPACE(1)
		# <advc.004> Lower position goes better with the filter buttons
		if PleOpt.isPLE_Style() and PleOpt.isShowButtons:
			iTMarginThresh = 8
		else: # </advc.004>
			iTMarginThresh = 3
		iTMargin = min(VSPACE(iTMarginThresh), iVMargin / 2)
		iBMargin = iVMargin - iTMargin
# BUG - Build/Action Icon Size - end
		lRect = RectLayout(gRect("BottomButtonMaxSpace"),
				0, iTMargin, RectLayout.MAX, -iBMargin)
		gSetRectangle("BottomButtonList", lRect)
		self.screen.addMultiListControlGFC("BottomButtonList", u"",
				lRect.x(), lRect.y(), lRect.width(), lRect.height(),
				4, iButtonSize, iButtonSize, # numLists, defaultWidth, defaultHeight
				TableStyles.TABLE_STYLE_STANDARD)

	def createPlotListFrames(self): # advc: Cut from interfaceScreen
		screen = self.screen
# BUG - PLE - begin
		iBtnSize = self.plotListUnitButtonSize()
		iRows = self.numPlotListRows()
		iCols = self.numPlotListButtonsPerRow()
		for j in range(iRows):
			szPanelName = "PlotListPanel" + str(j)
			gSetRect(szPanelName, "Top",
					gRect("LowerLeftCornerPanel").xRight() + HSPACE(8),
					gRect("CenterBottomPanel").y() - VSPACE(6)
					+ (j - iRows) * iBtnSize,
					iCols * iBtnSize + HSPACE(3),
					iBtnSize + VSPACE(1))
			self.addPanel(szPanelName, PanelStyles.PANEL_STYLE_EMPTY)
			for i in range(iCols):
				k = j * iCols + i
				xOffset = i * iBtnSize
				szBtn = "PlotListButton" + str(k)
# BUG - plot list - start
				szBtnPromoFrame = szBtn + "PromoFrame"
				iSizeDiff = 2
				iFrameSize = iBtnSize - iSizeDiff
				gSetRectangle(szBtnPromoFrame, SquareLayout(gRect(szPanelName),
						xOffset + iSizeDiff, iSizeDiff, iFrameSize))
				self.addDDSAt(szBtnPromoFrame, szPanelName,
						"OVERLAY_PROMOTION_FRAME",
						WidgetTypes.WIDGET_PLOT_LIST, k)
				screen.hide(szBtnPromoFrame)
# BUG - plot list - end
				gSetRectangle(szBtn, SquareLayout(gRect(szPanelName),
						xOffset + iSizeDiff + 1, iSizeDiff + 1, iFrameSize))
				self.addCheckBoxAt(szBtn, szPanelName,
						"INTERFACE_BUTTONS_GOVERNOR", "BUTTON_HILITE_SQUARE",
						ButtonStyles.BUTTON_STYLE_LABEL,
						WidgetTypes.WIDGET_PLOT_LIST, k)
				screen.hide(szBtn)
				szBtnHealth = szBtn + "Health"
				gSetRectangle(szBtnHealth, RectLayout(gRect(szPanelName),
						xOffset + iSizeDiff + 1, (26 * iBtnSize) / 32,
						iBtnSize, (11 * iBtnSize) / 32))
				self.addStackedBarAt(szBtnHealth, szPanelName,
						WidgetTypes.WIDGET_GENERAL, k)
				screen.hide(szBtnHealth)
				szBtnIcon = szBtn + "Icon"
				iOverlaySize = self.unitButtonOverlaySize()
				gSetRectangle(szBtnIcon, SquareLayout(gRect(szPanelName),
						xOffset, 0, iOverlaySize))
				self.addDDSAt(szBtnIcon, szPanelName, "OVERLAY_MOVE",
						WidgetTypes.WIDGET_PLOT_LIST, k)
				screen.hide(szBtnIcon)

		self.PLE.preparePlotListObjects(screen)
		lBottommostPanel = gRect("PlotListPanel" + str(iRows - 1))
		lPlusMinusButtons = RowLayout(gRect("Top"),
				lBottommostPanel.xRight() + HSPACE(8),
				lBottommostPanel.y() + VSPACE(3),
				2, HSPACE(5), BTNSZ(32))
		gSetRectangle("PlotListPlusMinus", lPlusMinusButtons)
		gSetRectangle("PlotListMinus", lPlusMinusButtons.next())
		gSetRectangle("PlotListPlus", lPlusMinusButtons.next())
		lUpDownButtons = ColumnLayout(gRect("Top"),
				gRect("PlotListPlusMinus").xCenter(),
				gRect("PlotListPlusMinus").y(),
				2, VSPACE(5), BTNSZ(24))
		lUpDownButtons.move(-lUpDownButtons.width() / 2.0, -lUpDownButtons.height() / 2.0)
		gSetRectangle("PlotListUpDown", lUpDownButtons)
		gSetRectangle(self.PLE.PLOT_LIST_UP_NAME, lUpDownButtons.next())
		gSetRectangle(self.PLE.PLOT_LIST_DOWN_NAME, lUpDownButtons.next())
		# Copies for the PLE module
		gSetRectangle(self.PLE.PLOT_LIST_MINUS_NAME, gRect("PlotListMinus"))
		gSetRectangle(self.PLE.PLOT_LIST_PLUS_NAME, gRect("PlotListPlus"))

		self.setStyledButton("PlotListMinus", ButtonStyles.BUTTON_STYLE_ARROW_LEFT,
				WidgetTypes.WIDGET_PLOT_LIST_SHIFT, -1)
		screen.hide("PlotListMinus")
		self.setStyledButton(self.PLE.PLOT_LIST_MINUS_NAME, ButtonStyles.BUTTON_STYLE_ARROW_LEFT)
		screen.hide(self.PLE.PLOT_LIST_MINUS_NAME)

		self.setStyledButton("PlotListPlus", ButtonStyles.BUTTON_STYLE_ARROW_RIGHT,
				WidgetTypes.WIDGET_PLOT_LIST_SHIFT, 1)
		screen.hide("PlotListPlus")
		self.setStyledButton(self.PLE.PLOT_LIST_PLUS_NAME, ButtonStyles.BUTTON_STYLE_ARROW_RIGHT)
		screen.hide(self.PLE.PLOT_LIST_PLUS_NAME)

		self.setImageButton(self.PLE.PLOT_LIST_UP_NAME, "PLE_ARROW_UP")
		screen.hide(self.PLE.PLOT_LIST_UP_NAME)
		self.setImageButton(self.PLE.PLOT_LIST_DOWN_NAME, "PLE_ARROW_DOWN")
		screen.hide(self.PLE.PLOT_LIST_DOWN_NAME)
# BUG - PLE - end

	# Will update the screen (every 250 MS)
	def updateScreen(self):

		global g_szTimeText
		global g_iTimeTextCounter

#		BugUtil.debug("update - Turn %d, Player %d, Interface %d, End Turn Button %d ===",
#				gc.getGame().getGameTurn(), gc.getGame().getActivePlayer(), CyInterface().getShowInterface(), CyInterface().getEndTurnState())

# BUG - Options - start
		BugOptions.write()
# BUG - Options - end

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		# Find out our resolution
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
#		self.m_iNumPlotListButtons = (xResolution - (iMultiListXL+iMultiListXR) - 2 * iPlotListUnitBtnSz) / iPlotListUnitBtnSz

		self.initMinimap()

		messageControl = CyMessageControl()

		bShow = False

		# Hide all interface widgets
		#screen.hide("EndTurnText")

		if (CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY):
			if (gc.getGame().isPaused()):
				# Pause overrides other messages
				acOutput = localText.getText("SYSTEM_GAME_PAUSED",
						(gc.getPlayer(gc.getGame().getPausePlayer()).getNameKey(),))
				#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
				screen.setEndTurnState("EndTurnText", acOutput)
				bShow = True
			elif (messageControl.GetFirstBadConnection() != -1 and
					# advc.706: Side effect of switching active player
					not gc.getGame().isOption(GameOptionTypes.GAMEOPTION_RISE_FALL)):
				# Waiting on a bad connection to resolve
				if (messageControl.GetConnState(messageControl.GetFirstBadConnection()) == 1):
					if (gc.getGame().isMPOption(MultiplayerOptionTypes.MPOPTION_ANONYMOUS)):
						acOutput = localText.getText("SYSTEM_WAITING_FOR_PLAYER",
								(gc.getPlayer(messageControl.GetFirstBadConnection()).getNameKey(), 0))
					else:
						acOutput = localText.getText("SYSTEM_WAITING_FOR_PLAYER",
								(gc.getPlayer(messageControl.GetFirstBadConnection()).getNameKey(),
								(messageControl.GetFirstBadConnection() + 1)))
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
				elif (messageControl.GetConnState(messageControl.GetFirstBadConnection()) == 2):
					if (gc.getGame().isMPOption(MultiplayerOptionTypes.MPOPTION_ANONYMOUS)):
						acOutput = localText.getText("SYSTEM_PLAYER_JOINING",
								(gc.getPlayer(messageControl.GetFirstBadConnection()).getNameKey(), 0))
					else:
						acOutput = localText.getText("SYSTEM_PLAYER_JOINING",
								(gc.getPlayer(messageControl.GetFirstBadConnection()).getNameKey(),
								(messageControl.GetFirstBadConnection() + 1)))
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
			else:
				# Flash select messages if no popups are present
				if (CyInterface().shouldDisplayReturn()):
					# advc.004t: Disable flashing "Press Esc to return"
					acOutput = ""#localText.getText("SYSTEM_RETURN", ())
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
				elif (CyInterface().shouldDisplayWaitingOthers() and
						# advc.127: No "Waiting" message during Auto Play
						not gc.getPlayer(gc.getGame().getActivePlayer()).isHumanDisabled()):
					acOutput = localText.getText("SYSTEM_WAITING", ())
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
				elif (CyInterface().shouldDisplayEndTurn()):
# BUG - Reminders - start
					if (ReminderEventManager.g_turnReminderTexts):
						acOutput = u"%s" % ReminderEventManager.g_turnReminderTexts
					elif MainOpt.isShowEndTurnMessage(): # advc.002n
						acOutput = localText.getText("SYSTEM_END_TURN", ())
					# advc.002n: So that toggling the option immediately hides the message
					else: acOutput = ""
# BUG - Reminders - end
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
				elif (CyInterface().shouldDisplayWaitingYou()):
					acOutput = localText.getText("SYSTEM_WAITING_FOR_YOU", ())
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
# BUG - Options - start
				# advc.004: Option disabled
				elif False:#MainOpt.isShowOptionsKeyReminder()
					if BugPath.isMac():
						acOutput = localText.getText("TXT_KEY_BUG_OPTIONS_KEY_REMINDER_MAC",
								(BugPath.getModName(),))
					else:
						acOutput = localText.getText("TXT_KEY_BUG_OPTIONS_KEY_REMINDER",
								(BugPath.getModName(),))
					#screen.modifyLabel("EndTurnText", acOutput, CvUtil.FONT_CENTER_JUSTIFY)
					screen.setEndTurnState("EndTurnText", acOutput)
					bShow = True
# BUG - Options - end

		if (bShow):
			screen.showEndTurn("EndTurnText")
			if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW or
					CyInterface().isCityScreenUp()):
				screen.moveItem("EndTurnText", 0, yResolution - 194, -0.1)
			else:
				screen.moveItem("EndTurnText", 0, yResolution - 86, -0.1)
		else:
			screen.hideEndTurn("EndTurnText")

		self.updateEndTurnButton()

# BUG - NJAGC - start
		global g_bShowTimeTextAlt
		if (CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_ADVANCED_START):
			# <advc.067> Moved out of the isEnabled block
			if ClockOpt.isShowEra():
				screen.show("EraText")
			else:
				screen.hide("EraText")
			# </advc.067>
			if ClockOpt.isEnabled():
				if (ClockOpt.isAlternateTimeText()):
					if (CyUserProfile().wasClockJustTurnedOn() or g_iTimeTextCounter <= 0):
						# reset timer, display primary
						g_bShowTimeTextAlt = False
						# advc.067: was getAlternatePeriod
						g_iTimeTextCounter = ClockOpt.getPrimaryPeriod() * 1000
						CyUserProfile().setClockJustTurnedOn(False)
					else:
						# countdown timer
						g_iTimeTextCounter -= 250
						if (g_iTimeTextCounter <= 0):
							# <advc.067>
							if g_bShowTimeTextAlt:
								iPeriod = ClockOpt.getPrimaryPeriod()
							else: # </advc.067>
								iPeriod = ClockOpt.getAlternatePeriod()
							# timer elapsed, toggle between primary and alternate
							g_iTimeTextCounter = iPeriod * 1000
							g_bShowTimeTextAlt = not g_bShowTimeTextAlt
				else:
					g_bShowTimeTextAlt = False

				self.updateTimeText()
				screen.setLabel("TimeText", "Background",
						g_szTimeText, CvUtil.FONT_RIGHT_JUSTIFY,
						xResolution - 56, 6, -0.3, FontTypes.GAME_FONT,
						WidgetTypes.WIDGET_GENERAL, -1, -1)
				screen.show("TimeText")
			else:
				#screen.hide("EraText") # advc.067
				self.updateTimeText()
				screen.setLabel("TimeText", "Background",
						g_szTimeText, CvUtil.FONT_RIGHT_JUSTIFY,
						xResolution - 56, 6, -0.3, FontTypes.GAME_FONT,
						WidgetTypes.WIDGET_GENERAL, -1, -1)
				screen.show("TimeText")
		else:
			screen.hide("TimeText")
			screen.hide("EraText")
# BUG - NJAGC - end

# BUG - PLE - start
		# this ensures that the info pane is closed after a greater mouse pos change
		self.PLE.checkInfoPane(CyInterface().getMousePos())
# BUG - PLE - end

		return 0

	# Will redraw the interface
	def redraw(self):
		# <advc.706> Freeze main interface during interlude
		if gc.getGame().isRFInterlude():
			return 0 # </advc.706>
#		BugUtil.debug("redraw - Turn %d, Player %d, Interface %d, End Turn Button %d",
#				gc.getGame().getGameTurn(), gc.getGame().getActivePlayer(), CyInterface().getShowInterface(), CyInterface().getEndTurnState())

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

# BUG - Field of View - start
		#self.setFieldofView(screen, CyInterface().isCityScreenUp())
		# K-Mod. Using the default for the city screen is an ok idea,
		# but it doesn't work properly because the screen is
		# drawn before the value is changed.
		self.setFieldofView(screen, False)
# BUG - Field of View - end

		# Check Dirty Bits, see what we need to redraw...
		if (CyInterface().isDirty(InterfaceDirtyBits.PercentButtons_DIRTY_BIT) == True):
			# Percent Buttons
			self.updatePercentButtons()
			CyInterface().setDirty(InterfaceDirtyBits.PercentButtons_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.Flag_DIRTY_BIT) == True):
			self.updateFlag()
			CyInterface().setDirty(InterfaceDirtyBits.Flag_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.MiscButtons_DIRTY_BIT) == True):
			# Miscellaneous buttons (civics screen, etc)
			self.updateMiscButtons()
			CyInterface().setDirty(InterfaceDirtyBits.MiscButtons_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.InfoPane_DIRTY_BIT) == True):
			# Info Pane Dirty Bit
			# This must come before updatePlotListButtons so that
			# the entity widget appears in front of the stats
			self.updateInfoPaneStrings()
			CyInterface().setDirty(InterfaceDirtyBits.InfoPane_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.PlotListButtons_DIRTY_BIT) == True):
#			BugUtil.debug("dirty PlotListButtons end - %s %s %s", self.bVanCurrentlyShowing, self.bPLECurrentlyShowing, self.bBUGCurrentlyShowing)
			# Plot List Buttons Dirty
			self.updatePlotListButtons()
			CyInterface().setDirty(InterfaceDirtyBits.PlotListButtons_DIRTY_BIT, False)
#			BugUtil.debug("dirty PlotListButtons start - %s %s %s", self.bVanCurrentlyShowing, self.bPLECurrentlyShowing, self.bBUGCurrentlyShowing)
		if (CyInterface().isDirty(InterfaceDirtyBits.SelectionButtons_DIRTY_BIT) == True):
			# Selection Buttons Dirty
			self.updateSelectionButtons()
			CyInterface().setDirty(InterfaceDirtyBits.SelectionButtons_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.ResearchButtons_DIRTY_BIT) == True):
			# Research Buttons Dirty
			self.updateResearchButtons()
			CyInterface().setDirty(InterfaceDirtyBits.ResearchButtons_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT) == True):
			# Citizen Buttons Dirty

# BUG - city specialist - start
			self.updateCitizenButtons_hide()
			# advc.004: Show the SpecialistLabel regardless of BUG options
			bShowingCitizenButtons = False
			if (CityScreenOpt.isCitySpecialist_Stacker()):
				bShowingCitizenButtons = self.updateCitizenButtons_Stacker()
			elif (CityScreenOpt.isCitySpecialist_Chevron()):
				bShowingCitizenButtons = self.updateCitizenButtons_Chevron()
			else:
				bShowingCitizenButtons = self.updateCitizenButtons()
			# <advc.004>
			if (bShowingCitizenButtons
				# Not quite enough room for this label on low res
				and self.yResolution > 900):
				# Cut from updateCitizenButtons_Stacker ...
				screen.show("SpecialistBackground")
				screen.show("SpecialistLabel") # </advc.004>
# BUG - city specialist - end

			CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.GameData_DIRTY_BIT) == True):
			# Game Data Strings Dirty
			self.updateGameDataStrings()
			CyInterface().setDirty(InterfaceDirtyBits.GameData_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.Help_DIRTY_BIT) == True):
			# Help Dirty bit
			self.updateHelpStrings()
			CyInterface().setDirty(InterfaceDirtyBits.Help_DIRTY_BIT, False)
		if (CyInterface().isDirty(InterfaceDirtyBits.CityScreen_DIRTY_BIT) == True):
			# Selection Data Dirty Bit
			self.updateCityScreen()
			CyInterface().setDirty(InterfaceDirtyBits.Domestic_Advisor_DIRTY_BIT, True)
			CyInterface().setDirty(InterfaceDirtyBits.CityScreen_DIRTY_BIT, False)
		bScoreStringsUpdated = False # advc.004z
		if (CyInterface().isDirty(InterfaceDirtyBits.Score_DIRTY_BIT) == True or
				CyInterface().checkFlashUpdate()):
			# Scores!
			self.updateScoreStrings()
			CyInterface().setDirty(InterfaceDirtyBits.Score_DIRTY_BIT, False)
			bScoreStringsUpdated = True # advc.004z
		if (CyInterface().isDirty(InterfaceDirtyBits.GlobeInfo_DIRTY_BIT) == True):
			# Globeview and Globelayer buttons
			CyInterface().setDirty(InterfaceDirtyBits.GlobeInfo_DIRTY_BIT, False)
			self.updateGlobeviewButtons()
			# <advc.004z>
			if not bScoreStringsUpdated and MainOpt.isScoresInGlobeView():
				# Show/hide scoreboard depending on whether the layer has options
				self.updateScoreStrings() # </advc.004z>

		return 0

	# K-Mod. There are some special rules for which buttons should be shown and when.
	# I'd rather have all those rules in one place. ie. here.
	def showCommercePercent(self, eCommerce, ePlayer):
		player = gc.getPlayer(ePlayer)
		if not player.isFoundedFirstCity():
			return False

		if eCommerce == CommerceTypes.COMMERCE_GOLD and not CyInterface().isCityScreenUp():
			return False

		if player.getCommercePercent(eCommerce) > 0:
			return True

		if (eCommerce == CommerceTypes.COMMERCE_ESPIONAGE and
				(gc.getGame().isOption(GameOptionTypes.GAMEOPTION_NO_ESPIONAGE) or
				gc.getTeam(player.getTeam()).getHasMetCivCount(True) == 0 or
				(gc.getPlayer(ePlayer).getCommercePercent(eCommerce) == 0 and # advc.120c
				not CyInterface().isCityScreenUp() and MainOpt.isHideEspSlider()))):
			return False

		if player.isCommerceFlexible(eCommerce):
			return True
		return False
	# K-Mod end

	# Will update the percent buttons
	def updatePercentButtons(self):

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		for iI in range(CommerceTypes.NUM_COMMERCE_TYPES):
			szString = "IncreasePercent" + str(iI)
			screen.hide(szString)
			szString = "DecreasePercent" + str(iI)
			screen.hide(szString)
# BUG - Min/Max Sliders - start
			szString = "MaxPercent" + str(iI)
			screen.hide(szString)
			szString = "MinPercent" + str(iI)
			screen.hide(szString)
# BUG - Min/Max Sliders - start

		pHeadSelectedCity = CyInterface().getHeadSelectedCity()

		#if (not CyInterface().isCityScreenUp() or (pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer()) or gc.getGame().isDebugMode()):
		if (not CyInterface().isCityScreenUp() or
				pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer()
				# K-Mod: Debug mode still doesn't allow us to use the buttons
				#or gc.getGame().isDebugMode()
				):
			iCount = 0

			if (CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
					CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY and
					CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_ADVANCED_START):
				for iI in range(CommerceTypes.NUM_COMMERCE_TYPES):
					# Intentional offset...
					eCommerce = (iI + 1) % CommerceTypes.NUM_COMMERCE_TYPES

					#if (gc.getActivePlayer().isCommerceFlexible(eCommerce) or (CyInterface().isCityScreenUp() and (eCommerce == CommerceTypes.COMMERCE_GOLD))):
					if self.showCommercePercent(eCommerce, gc.getGame().getActivePlayer()): # K-Mod
# BUG - Min/Max Sliders - start
						bEnable = gc.getActivePlayer().isCommerceFlexible(eCommerce)
						if (MainOpt.isShowMinMaxCommerceButtons() and
								not CyInterface().isCityScreenUp()):
							iMinMaxAdjustX = 20
							szString = "MaxPercent" + str(eCommerce)
							screen.setButtonGFC(szString, u"", "", 70, 50 + (19 * iCount), 20, 20,
									*BugDll.widget("WIDGET_SET_PERCENT", eCommerce, 100,
									WidgetTypes.WIDGET_CHANGE_PERCENT, eCommerce, 100,
									ButtonStyles.BUTTON_STYLE_CITY_PLUS))
							screen.show(szString)
							screen.enable(szString, bEnable)
							szString = "MinPercent" + str(eCommerce)
							screen.setButtonGFC(szString, u"", "", 130, 50 + (19 * iCount), 20, 20,
									*BugDll.widget("WIDGET_SET_PERCENT", eCommerce, 0,
									WidgetTypes.WIDGET_CHANGE_PERCENT, eCommerce, -100,
									ButtonStyles.BUTTON_STYLE_CITY_MINUS))
							screen.show(szString)
							screen.enable(szString, bEnable)
						else:
							iMinMaxAdjustX = 0

						szString = "IncreasePercent" + str(eCommerce)
						screen.setButtonGFC(szString, u"", "",
								70 + iMinMaxAdjustX, 50 + (19 * iCount), 20, 20,
								WidgetTypes.WIDGET_CHANGE_PERCENT, eCommerce,
								gc.getDefineINT("COMMERCE_PERCENT_CHANGE_INCREMENTS"),
								ButtonStyles.BUTTON_STYLE_CITY_PLUS)
						screen.show(szString)
						screen.enable(szString, bEnable)
						szString = "DecreasePercent" + str(eCommerce)
						screen.setButtonGFC(szString, u"", "",
								90 + iMinMaxAdjustX, 50 + (19 * iCount), 20, 20,
								WidgetTypes.WIDGET_CHANGE_PERCENT, eCommerce,
								-gc.getDefineINT("COMMERCE_PERCENT_CHANGE_INCREMENTS"),
								ButtonStyles.BUTTON_STYLE_CITY_MINUS)
						screen.show(szString)
						screen.enable(szString, bEnable)

						iCount = iCount + 1
						# moved enabling above
# BUG - Min/Max Sliders - end

		return 0

# BUG - start
	def resetEndTurnObjects(self):
		"""
		Clears the end turn text and hides it and the button.
		"""
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		screen.setEndTurnState("EndTurnText", u"")
		screen.hideEndTurn("EndTurnText")
		screen.hideEndTurn("EndTurnButton")
# BUG - end

	# Will update the end Turn Button
	def updateEndTurnButton(self):

		global g_eEndTurnButtonState

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		if (CyInterface().shouldDisplayEndTurnButton() and
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			eState = CyInterface().getEndTurnState()
			bShow = False
			if (eState == EndTurnButtonStates.END_TURN_OVER_HIGHLIGHT):
				screen.setEndTurnState("EndTurnButton", u"Red")
				bShow = True
			elif (eState == EndTurnButtonStates.END_TURN_OVER_DARK):
				screen.setEndTurnState("EndTurnButton", u"Red")
				bShow = True
			elif (eState == EndTurnButtonStates.END_TURN_GO):
				screen.setEndTurnState("EndTurnButton", u"Green")
				bShow = True

			if (bShow):
				screen.showEndTurn("EndTurnButton")
			else:
				screen.hideEndTurn("EndTurnButton")

			if (g_eEndTurnButtonState == eState):
				return

			g_eEndTurnButtonState = eState
		else:
			screen.hideEndTurn("EndTurnButton")
		return 0

	# Update the miscellaneous buttons
	def updateMiscButtons(self):

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		xResolution = screen.getXResolution()

# BUG - Great Person Bar - start
		if (CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_ADVANCED_START):
			self.updateGreatPersonBar(screen)
# BUG - Great Person Bar - end
		#CyInterface().shouldDisplayFlag() and
		# <advc.004y> Don't check shouldDisplayFlag for the Civilopedia button,
		# but do check if the city screen is up.
		if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW and
				not CyInterface().isCityScreenUp()):
			screen.show("InterfaceHelpButton")
			if CyInterface().shouldDisplayFlag():
				screen.show("CivilizationFlag")
				screen.show("MainMenuButton")
			else:
				screen.hide("CivilizationFlag")
				screen.hide("MainMenuButton")
			# </advc.004y>
		else:
			screen.hide("CivilizationFlag")
			screen.hide("InterfaceHelpButton")
			screen.hide("MainMenuButton")

		if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE_ALL or
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_MINIMAP_ONLY):
			screen.hide("LowerLeftCornerPanel")
			screen.hide("LowerLeftCornerBackgr")
			screen.hide("InterfaceTopBackgroundWidget")
			screen.hide("CenterBottomPanel")
			screen.hide("LowerRightCornerPanel")
			screen.hide("MiniMapPanel")
			screen.hide("InterfaceTopLeft")
			screen.hide("InterfaceTopCenter")
			screen.hide("InterfaceTopRight")
			screen.hide("TurnLogButton")
			screen.hide("EspionageAdvisorButton")
			screen.hide("DomesticAdvisorButton")
			screen.hide("ForeignAdvisorButton")
			screen.hide("TechAdvisorButton")
			screen.hide("CivicsAdvisorButton")
			screen.hide("ReligiousAdvisorButton")
			screen.hide("CorporationAdvisorButton")
			screen.hide("FinanceAdvisorButton")
			screen.hide("MilitaryAdvisorButton")
			screen.hide("VictoryAdvisorButton")
			screen.hide("InfoAdvisorButton")
# BUG - City Arrows - start
			screen.hide("MainCityScrollMinus")
			screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			screen.hide("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
# BUG - field of view slider - start
			screen.hide("FoVSliderText")
			screen.hide("FoVSlider")
# BUG - field of view slider - end
		elif (CyInterface().isCityScreenUp()):
			screen.show("LowerLeftCornerPanel")
			#screen.show("LowerLeftCornerBackgr")
			screen.show("InterfaceTopBackgroundWidget")
			screen.show("CenterBottomPanel")
			screen.show("LowerRightCornerPanel")
			screen.show("MiniMapPanel")
			screen.hide("InterfaceTopLeft")
			screen.hide("InterfaceTopCenter")
			screen.hide("InterfaceTopRight")
			screen.hide("TurnLogButton")
			screen.hide("EspionageAdvisorButton")
			screen.hide("DomesticAdvisorButton")
			screen.hide("ForeignAdvisorButton")
			screen.hide("TechAdvisorButton")
			screen.hide("CivicsAdvisorButton")
			screen.hide("ReligiousAdvisorButton")
			screen.hide("CorporationAdvisorButton")
			screen.hide("FinanceAdvisorButton")
			screen.hide("MilitaryAdvisorButton")
			screen.hide("VictoryAdvisorButton")
			screen.hide("InfoAdvisorButton")
# BUG - City Arrows - start
			screen.hide("MainCityScrollMinus")
			screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			screen.hide("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
# BUG - field of view slider - start
			screen.hide("FoVSliderText")
			screen.hide("FoVSlider")
# BUG - field of view slider - end
		elif (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE):
			screen.hide("LowerLeftCornerPanel")
			screen.hide("LowerLeftCornerBackgr")
			screen.show("InterfaceTopBackgroundWidget")
			screen.hide("CenterBottomPanel")
			screen.hide("LowerRightCornerPanel")
			screen.hide("MiniMapPanel")
			screen.show("InterfaceTopLeft")
			if self.isShowTopBarsFrame(): # advc.092
				screen.show("InterfaceTopCenter")
			screen.show("InterfaceTopRight")
			screen.show("TurnLogButton")
			screen.show("EspionageAdvisorButton")
			screen.show("DomesticAdvisorButton")
			screen.show("ForeignAdvisorButton")
			screen.show("TechAdvisorButton")
			screen.show("CivicsAdvisorButton")
			screen.show("ReligiousAdvisorButton")
			screen.show("CorporationAdvisorButton")
			screen.show("FinanceAdvisorButton")
			screen.show("MilitaryAdvisorButton")
			screen.show("VictoryAdvisorButton")
			screen.show("InfoAdvisorButton")
# BUG - City Arrows - start
			screen.hide("MainCityScrollMinus")
			screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			if MainOpt.isShowOptionsButton():
				screen.show("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
# BUG - field of view slider - start
			screen.hide("FoVSliderText")
			screen.hide("FoVSlider")
# BUG - field of view slider - end
			screen.moveToFront("TurnLogButton")
			screen.moveToFront("EspionageAdvisorButton")
			screen.moveToFront("DomesticAdvisorButton")
			screen.moveToFront("ForeignAdvisorButton")
			screen.moveToFront("TechAdvisorButton")
			screen.moveToFront("CivicsAdvisorButton")
			screen.moveToFront("ReligiousAdvisorButton")
			screen.moveToFront("CorporationAdvisorButton")
			screen.moveToFront("FinanceAdvisorButton")
			screen.moveToFront("MilitaryAdvisorButton")
			screen.moveToFront("VictoryAdvisorButton")
			screen.moveToFront("InfoAdvisorButton")
# BUG - BUG Option Button - Start
#			screen.moveToFront("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
		elif (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_ADVANCED_START):
			screen.hide("LowerLeftCornerPanel")
			screen.hide("LowerLeftCornerBackgr")
			screen.hide("InterfaceTopBackgroundWidget")
			screen.hide("CenterBottomPanel")
			screen.hide("LowerRightCornerPanel")
			screen.show("MiniMapPanel")
			screen.hide("InterfaceTopLeft")
			screen.hide("InterfaceTopCenter")
			screen.hide("InterfaceTopRight")
			screen.hide("TurnLogButton")
			screen.hide("EspionageAdvisorButton")
			screen.hide("DomesticAdvisorButton")
			screen.hide("ForeignAdvisorButton")
			screen.hide("TechAdvisorButton")
			screen.hide("CivicsAdvisorButton")
			screen.hide("ReligiousAdvisorButton")
			screen.hide("CorporationAdvisorButton")
			screen.hide("FinanceAdvisorButton")
			screen.hide("MilitaryAdvisorButton")
			screen.hide("VictoryAdvisorButton")
			screen.hide("InfoAdvisorButton")
# BUG - City Arrows - start
			screen.hide("MainCityScrollMinus")
			screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			screen.hide("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
		elif (CyEngine().isGlobeviewUp()):
			screen.hide("LowerLeftCornerPanel")
			screen.hide("LowerLeftCornerBackgr")
			screen.hide("InterfaceTopBackgroundWidget")
			screen.hide("CenterBottomPanel")
			screen.show("LowerRightCornerPanel")
			screen.show("MiniMapPanel")
			screen.show("InterfaceTopLeft")
			if self.isShowTopBarsFrame(): # advc.092
				screen.show("InterfaceTopCenter")
			screen.show("InterfaceTopRight")
			screen.show("TurnLogButton")
			screen.show("EspionageAdvisorButton")
			screen.show("DomesticAdvisorButton")
			screen.show("ForeignAdvisorButton")
			screen.show("TechAdvisorButton")
			screen.show("CivicsAdvisorButton")
			screen.show("ReligiousAdvisorButton")
			screen.show("CorporationAdvisorButton")
			screen.show("FinanceAdvisorButton")
			screen.show("MilitaryAdvisorButton")
			screen.show("VictoryAdvisorButton")
			screen.show("InfoAdvisorButton")
# BUG - City Arrows - start
			screen.hide("MainCityScrollMinus")
			screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			if MainOpt.isShowOptionsButton():
				screen.show("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
# BUG - field of view slider - start
			screen.hide("FoVSliderText")
			screen.hide("FoVSlider")
# BUG - field of view slider - end
			screen.moveToFront("TurnLogButton")
			screen.moveToFront("EspionageAdvisorButton")
			screen.moveToFront("DomesticAdvisorButton")
			screen.moveToFront("ForeignAdvisorButton")
			screen.moveToFront("TechAdvisorButton")
			screen.moveToFront("CivicsAdvisorButton")
			screen.moveToFront("ReligiousAdvisorButton")
			screen.moveToFront("CorporationAdvisorButton")
			screen.moveToFront("FinanceAdvisorButton")
			screen.moveToFront("MilitaryAdvisorButton")
			screen.moveToFront("VictoryAdvisorButton")
			screen.moveToFront("InfoAdvisorButton")
# BUG - BUG Option Button - Start
#			screen.moveToFront("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
		else:
			screen.show("LowerLeftCornerPanel")
			#screen.show("LowerLeftCornerBackgr")
			screen.show("InterfaceTopBackgroundWidget")
			screen.show("CenterBottomPanel")
			screen.show("LowerRightCornerPanel")
			screen.show("MiniMapPanel")
			screen.show("InterfaceTopLeft")
			if self.isShowTopBarsFrame(): # advc.092
				screen.show("InterfaceTopCenter")
			screen.show("InterfaceTopRight")
			screen.show("TurnLogButton")
			screen.show("EspionageAdvisorButton")
			screen.show("DomesticAdvisorButton")
			screen.show("ForeignAdvisorButton")
			screen.show("TechAdvisorButton")
			screen.show("CivicsAdvisorButton")
			screen.show("ReligiousAdvisorButton")
			screen.show("CorporationAdvisorButton")
			screen.show("FinanceAdvisorButton")
			screen.show("MilitaryAdvisorButton")
			screen.show("VictoryAdvisorButton")
			screen.show("InfoAdvisorButton")
# BUG - City Arrows - start
			if (MainOpt.isShowCityCycleArrows()):
				screen.show("MainCityScrollMinus")
				screen.show("MainCityScrollPlus")
			else:
				screen.hide("MainCityScrollMinus")
				screen.hide("MainCityScrollPlus")
# BUG - City Arrows - end
# BUG - BUG Option Button - Start
			if MainOpt.isShowOptionsButton():
				screen.show("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
# BUG - field of view slider - start
			if (MainOpt.isShowFieldOfView()):
				screen.show("FoVSliderText")
				screen.show("FoVSlider")
			else:
				screen.hide("FoVSliderText")
				screen.hide("FoVSlider")
# BUG - field of view slider - end
			screen.moveToFront("TurnLogButton")
			screen.moveToFront("EspionageAdvisorButton")
			screen.moveToFront("DomesticAdvisorButton")
			screen.moveToFront("ForeignAdvisorButton")
			screen.moveToFront("TechAdvisorButton")
			screen.moveToFront("CivicsAdvisorButton")
			screen.moveToFront("ReligiousAdvisorButton")
			screen.moveToFront("CorporationAdvisorButton")
			screen.moveToFront("FinanceAdvisorButton")
			screen.moveToFront("MilitaryAdvisorButton")
			screen.moveToFront("VictoryAdvisorButton")
			screen.moveToFront("InfoAdvisorButton")
# BUG - BUG Option Button - Start
#			screen.moveToFront("BUGOptionsScreenWidget")
# BUG - BUG Option Button - End
		screen.updateMinimapVisibility()
		return 0

	# Update plot List Buttons
	def updatePlotListButtons(self):
#		BugUtil.debug("updatePlotListButtons start - %s %s %s", self.bVanCurrentlyShowing, self.bPLECurrentlyShowing, self.bBUGCurrentlyShowing)
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		self.updatePlotListButtons_Hide(screen)
		self.updatePlotListButtons_Common(screen)
# BUG - draw methods
		#sDrawMethod = self.DRAW_METHODS[PleOpt.getDrawMethod()]
		# <advc.069> Replacing the above (getDrawMethod removed)
		if PleOpt.isPLE_Style():
			sDrawMethod = self.DRAW_METHOD_PLE
		elif PleOpt.isBUG_Style():
			sDrawMethod = self.DRAW_METHOD_BUG
		else:
			sDrawMethod = self.DRAW_METHOD_VAN
		# </advc.069>
		if sDrawMethod == self.DRAW_METHOD_PLE:
			self.PLE.updatePlotListButtons_PLE(
					screen, self.xResolution, self.yResolution)
			self.bPLECurrentlyShowing = True
		elif sDrawMethod == self.DRAW_METHOD_VAN:
			self.updatePlotListButtons_Orig(screen)
			self.bVanCurrentlyShowing = True
		else: # self.DRAW_METHOD_BUG
			self.updatePlotListButtons_BUG(screen)
			self.bBUGCurrentlyShowing = True
# BUG - draw methods
#		BugUtil.debug("updatePlotListButtons end - %s %s %s", self.bVanCurrentlyShowing, self.bPLECurrentlyShowing, self.bBUGCurrentlyShowing)
		return 0
#		if PleOpt.isPLE_Style():
#			self.updatePlotListButtons_PLE(screen)
#			self.bPLECurrentlyShowing = True
#		else:
#			self.updatePlotListButtons_Orig(screen)
#			self.bVanCurrentlyShowing = True
#		return 0

	def updatePlotListButtons_Hide(self, screen):
#		BugUtil.debug("updatePlotListButtons_Hide - %s %s %s", self.bVanCurrentlyShowing, self.bPLECurrentlyShowing, self.bBUGCurrentlyShowing)

		# hide all buttons
		if self.bPLECurrentlyShowing:
#			BugUtil.debug("updatePlotListButtons_Hide - hiding PLE")
			self.PLE.hidePlotListButtonPLEObjects(screen)
			self.PLE.hideUnitInfoPane()
			self.bPLECurrentlyShowing = False

		if self.bVanCurrentlyShowing:
#			BugUtil.debug("updatePlotListButtons_Hide - hiding Vanilla")
			self.hidePlotListButton_Orig(screen)
			self.bVanCurrentlyShowing = False

# BUG - BUG unit plot draw method - start
		if self.bBUGCurrentlyShowing:
#			BugUtil.debug("updatePlotListButtons_Hide - hiding BUG")
			self.hidePlotListButton_BUG(screen)
			self.bBUGCurrentlyShowing = False
# BUG - BUG unit plot draw method - end

	def updatePlotListButtons_Common(self, screen):
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		# Capture these for looping over the plot's units
		self.PLE.UnitPlotList_BUGOptions()
		bHandled = False
		if (CyInterface().shouldDisplayUnitModel() and
				not CyEngine().isGlobeviewUp() and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL):
			if (CyInterface().isCitySelection()):
				iOrders = CyInterface().getNumOrdersQueued()
				for i in range(iOrders):
					if (bHandled == False):
						eOrderNodeType = CyInterface().getOrderNodeType(i)
						if (eOrderNodeType == OrderTypes.ORDER_TRAIN):
							screen.addUnitGraphicGFC("InterfaceUnitModel",
									CyInterface().getOrderNodeData1(i),
									175, yResolution - 138, 123, 132,
									WidgetTypes.WIDGET_HELP_SELECTED, 0, -1,
									-20, 30, 1, False)
							bHandled = True
						elif (eOrderNodeType == OrderTypes.ORDER_CONSTRUCT):
							screen.addBuildingGraphicGFC("InterfaceUnitModel",
									CyInterface().getOrderNodeData1(i),
									175, yResolution - 138, 123, 132,
									WidgetTypes.WIDGET_HELP_SELECTED, 0, -1,
									-20, 30, 0.8, False)
							bHandled = True
						elif (eOrderNodeType == OrderTypes.ORDER_CREATE):
							if(gc.getProjectInfo(CyInterface().getOrderNodeData1(i)).isSpaceship()):
								modelType = 0
								screen.addSpaceShipWidgetGFC("InterfaceUnitModel",
										175, yResolution - 138, 123, 132,
										CyInterface().getOrderNodeData1(i), modelType,
										WidgetTypes.WIDGET_HELP_SELECTED, 0, -1)
							else:
								screen.hide("InterfaceUnitModel")
							bHandled = True
						elif (eOrderNodeType == OrderTypes.ORDER_MAINTAIN):
							screen.hide("InterfaceUnitModel")
							bHandled = True
				if (not bHandled):
					screen.hide("InterfaceUnitModel")
					bHandled = True
				screen.moveToFront("SelectedCityText")
			elif (CyInterface().getHeadSelectedUnit()):
				screen.addUnitGraphicGFC("InterfaceUnitModel",
						CyInterface().getHeadSelectedUnit().getUnitType(),
						175, yResolution - 138, 123, 132,
						WidgetTypes.WIDGET_UNIT_MODEL,
						CyInterface().getHeadSelectedUnit().getUnitType(), -1,
						-20, 30, 1, False)
#				screen.addSpecificUnitGraphicGFC("InterfaceUnitModel", CyInterface().getHeadSelectedUnit(), 175, yResolution - 138, 123, 132, WidgetTypes.WIDGET_UNIT_MODEL, CyInterface().getHeadSelectedUnit().getUnitType(), -1, -20, 30, 1, False)
				screen.moveToFront("SelectedUnitText")
			else:
				screen.hide("InterfaceUnitModel")
		else:
			screen.hide("InterfaceUnitModel")

	# hides all plot list objects
	def hidePlotListButton_Orig(self, screen):
#		BugUtil.debug("hidePlotListButton_Orig - %i", self.numPlotListButtons_Total())
		# hides all unit button objects
		for i in range(self.numPlotListButtons_Total()):
			szString = "PlotListButton" + str(i)
			screen.hide(szString)
			screen.hide(szString + "Icon")
			screen.hide(szString + "Health")
			screen.hide(szString + "MoveBar")
			screen.hide(szString + "PromoFrame")
			screen.hide(szString + "ActionIcon")
			screen.hide(szString + "Upgrade")

# BUG - draw method
	def hidePlotListButton_BUG(self, screen):
		#if self.DRAW_METHODS[PleOpt.getDrawMethod()] != self.DRAW_METHOD_BUG:
		# advc.069: Replacing the above (getDrawMethod removed)
		if PleOpt.isPLE_Style() or not PleOpt.isBUG_Style():
			self.BupPanel.clearUnits()
			self.BupPanel.Hide()
		return
		# hides all unit button objects
#		for i in range(self.iMaxPlotListIcons):
#			szString = "PlotListButton" + str(i)
#			screen.hide(szString)
#			screen.hide(szString + "Icon")
#			screen.hide(szString + "Health")
#			screen.hide(szString + "MoveBar")
#			screen.hide(szString + "PromoFrame")
#			screen.hide(szString + "ActionIcon")
#			screen.hide(szString + "Upgrade")
# BUG - draw method


	def updatePlotListButtons_Orig(self, screen):
# need to put in something similar to 	def displayUnitPlotListObjects(self, screen, pLoopUnit, nRow, nCol):
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		pPlot = CyInterface().getSelectionPlot()
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButton" + str(i)
			screen.moveToFront(szName)
# BUG - Stack Promotions - start
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButtonCircle" + str(i)
			screen.moveToFront(szName)
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButtonCount" + str(i)
			screen.moveToFront(szName)
# BUG - Stack Promotions - end
		screen.hide("PlotListMinus")
		screen.hide("PlotListPlus")
		BugUtil.debug("updatePlotListButtons_Orig - column %i, offset %i", CyInterface().getPlotListColumn(), CyInterface().getPlotListOffset())
		if (pPlot and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyEngine().isGlobeviewUp() == False):

			iVisibleUnits = CyInterface().getNumVisibleUnits()
			iCount = -(CyInterface().getPlotListColumn())
			bLeftArrow = False
			bRightArrow = False
			if (CyInterface().isCityScreenUp()):
				iMaxRows = 1
				iSkipped = (self.numPlotListRows() - 1) * self.numPlotListButtonsPerRow()
				iCount += iSkipped
			else:
				iMaxRows = self.numPlotListRows()
				iCount += CyInterface().getPlotListOffset()
				iSkipped = 0
			BugUtil.debug("updatePlotListButtons_Orig - iCount(%i), iSkipped(%i)", iCount, iSkipped)
			# <advc.069>
			bSimultaneousTurns = gc.getGame().isMPOption(MultiplayerOptionTypes.MPOPTION_SIMULTANEOUS_TURNS)
			bWoundedIndicator = PleOpt.isShowWoundedIndicator()
			bGGIndicator = PleOpt.isShowGreatGeneralIndicator()
			# </advc.069>
			CyInterface().cacheInterfacePlotUnits(pPlot)
			for i in range(CyInterface().getNumCachedInterfacePlotUnits()):
				pLoopUnit = CyInterface().getCachedInterfacePlotUnit(i)
				if (pLoopUnit):
					# advc.004n: Allow going back down to a single row on the city screen
					if (#iCount == 0 and
							CyInterface().getPlotListColumn() > 0):
						bLeftArrow = True
					#elif
					if ((iCount == (self.numPlotListRows() * self.numPlotListButtonsPerRow() - 1)) and
							((iVisibleUnits - iCount - CyInterface().getPlotListColumn() + iSkipped) > 1)):
						bRightArrow = True

					if ((iCount >= 0) and
							(iCount < self.numPlotListButtonsPerRow() * self.numPlotListRows())):
						# <advc.069>
						bShowMoveOverlay = (bSimultaneousTurns or
								pLoopUnit.getOwner() == gc.getGame().getActivePlayer() or
								(bWoundedIndicator and pLoopUnit.isHurt()) or
								(bGGIndicator and pLoopUnit.getLeaderUnitType() >= 0)) # </advc.069>
						if ((pLoopUnit.getTeam() != gc.getGame().getActiveTeam()) or
								pLoopUnit.isWaiting()):
							szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_FORTIFY").getPath()
						elif (pLoopUnit.canMove()):
							if (pLoopUnit.hasMoved()):
								szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_HASMOVED").getPath()
							else:
								szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_MOVE").getPath()
						else:
							szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_NOMOVE").getPath()
						szString = "PlotListButton" + str(iCount)
						#screen.changeImageButton(szString, gc.getUnitInfo(pLoopUnit.getUnitType()).getButton())
						# advc.003l: Replacing the above
						screen.changeImageButton(szString,
								gc.getPlayer(pLoopUnit.getOwner()).getUnitButton(pLoopUnit.getUnitType()))
						if (pLoopUnit.getOwner() == gc.getGame().getActivePlayer()):
							bEnable = True
						else:
							bEnable = False
						screen.enable(szString, bEnable)

						if (pLoopUnit.IsSelected()):
							screen.setState(szString, True)
						else:
							screen.setState(szString, False)
						screen.show(szString)

						# place the health bar
						if (pLoopUnit.isFighting()):
							bShowHealth = False
						elif (pLoopUnit.getDomainType() == DomainTypes.DOMAIN_AIR):
							bShowHealth = pLoopUnit.canAirAttack()
						else:
							bShowHealth = pLoopUnit.canFight()

						if bShowHealth:
							szStringHealth = szString + "Health"
							screen.setBarPercentage(szStringHealth, InfoBarTypes.INFOBAR_STORED,
									float(pLoopUnit.currHitPoints()) / float(pLoopUnit.maxHitPoints()))
							if (pLoopUnit.getDamage() >= ((pLoopUnit.maxHitPoints() * 2) / 3)):
								screen.setStackedBarColors(szStringHealth, InfoBarTypes.INFOBAR_STORED, gc.getInfoTypeForString("COLOR_RED"))
							elif (pLoopUnit.getDamage() >= (pLoopUnit.maxHitPoints() / 3)):
								screen.setStackedBarColors(szStringHealth, InfoBarTypes.INFOBAR_STORED, gc.getInfoTypeForString("COLOR_YELLOW"))
							else:
								screen.setStackedBarColors(szStringHealth, InfoBarTypes.INFOBAR_STORED, gc.getInfoTypeForString("COLOR_GREEN"))
							screen.show(szStringHealth)

						# Adds the overlay first
						if bShowMoveOverlay: # advc.069
							szStringIcon = szString + "Icon"
							screen.changeDDSGFC(szStringIcon, szFileName)
							screen.show(szStringIcon)

						if bEnable:
							iPlotListUnitBtnSz = self.plotListUnitButtonSize()
							x = 315 + ((iCount % self.numPlotListButtonsPerRow()) * iPlotListUnitBtnSz)
							y = yResolution - 169
							y += ((iCount / self.numPlotListButtonsPerRow() - self.numPlotListRows() + 1)
									* iPlotListUnitBtnSz)

							self.PLE._displayUnitPlotList_Dot(screen, pLoopUnit, szString,
									iCount, x, y + 4)
							self.PLE._displayUnitPlotList_Promo(screen, pLoopUnit, szString)
							self.PLE._displayUnitPlotList_Upgrade(screen, pLoopUnit, szString,
									iCount, x, y)
							self.PLE._displayUnitPlotList_Mission(screen, pLoopUnit, szString,
									iCount, x, y - 22, 12)

					iCount = iCount + 1
#			BugUtil.debug("updatePlotListButtons_Orig - vis units(%i), buttons per row(%i), max rows(%i)", iVisibleUnits, self.numPlotListButtonsPerRow(), iMaxRows)
			if (iVisibleUnits > self.numPlotListButtonsPerRow() * iMaxRows):
#				BugUtil.debug("updatePlotListButtons_Orig - show arrows %s %s", bLeftArrow, bRightArrow)
				screen.enable("PlotListMinus", bLeftArrow)
				screen.show("PlotListMinus")

				screen.enable("PlotListPlus", bRightArrow)
				screen.show("PlotListPlus")

		return 0

# BUG - BUG unit plot draw method - start
	def updatePlotListButtons_BUG(self, screen):
# need to put in something similar to 	def displayUnitPlotListObjects(self, screen, pLoopUnit, nRow, nCol):
#		xResolution = screen.getXResolution()
#		yResolution = screen.getYResolution()
		pPlot = CyInterface().getSelectionPlot()
		# this moves the promotions for the unit shown in the
		# bottom left so that they sit on top of the unit picture
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButton" + str(i)
			screen.moveToFront(szName)
# BUG - Stack Promotions - start
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButtonCircle" + str(i)
			screen.moveToFront(szName)
		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButtonCount" + str(i)
			screen.moveToFront(szName)
# BUG - Stack Promotions - end
#		screen.hide("PlotListMinus")
#		screen.hide("PlotListPlus")
#		BugUtil.debug("updatePlotListButtons_BUG - A")
#		if (pPlot and CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and CyEngine().isGlobeviewUp() == False):
		# skip this if we don't need to display any units
#		if not (pPlot
#		and CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL
#		and CyEngine().isGlobeviewUp() == False):
		if (not pPlot or
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE_ALL or
				CyEngine().isGlobeviewUp() == True):
			self.BupPanel.clearUnits()
			self.BupPanel.Hide()
			return 0
#		BugUtil.debug("updatePlotListButtons_BUG - B")
#		self.BupPanel.clearUnits()
		self.BupPanel.addPlot(pPlot.getX(), pPlot.getY())
		CyInterface().cacheInterfacePlotUnits(pPlot)
		for i in range(CyInterface().getNumCachedInterfacePlotUnits()):
			pLoopUnit = CyInterface().getCachedInterfacePlotUnit(i)
			if (pLoopUnit):
				self.BupPanel.addUnit(pLoopUnit)
#		BugUtil.debug("updatePlotListButtons_BUG - C")
#		self.BupPanel.UpdateBUGOptions()
		timer = BugUtil.Timer("draw plot list")
		self.BupPanel.Draw()
		timer.log()
		# (advc: Deleted a big chunk of code commented out. Largely the same as in
		# updatePlotListButtons_Orig I think.)
		return 0
# BUG - BUG unit plot draw method - end


	# This will update the flag widget for SP hotseat and dbeugging
	def updateFlag(self):
		eIFaceVis = CyInterface().getShowInterface()
		if (eIFaceVis != InterfaceVisibility.INTERFACE_HIDE_ALL and
				eIFaceVis != InterfaceVisibility.INTERFACE_MINIMAP_ONLY and
				eIFaceVis != InterfaceVisibility.INTERFACE_ADVANCED_START):
			lRect = gRect("CivilizationFlag")
			self.screen.addFlagWidgetGFC("CivilizationFlag",
					lRect.x(), lRect.y(), lRect.width(), lRect.height(),
					gc.getGame().getActivePlayer(),
					WidgetTypes.WIDGET_FLAG, gc.getGame().getActivePlayer(), -1)

	# Will hide and show the selection buttons and their associated buttons
	def updateSelectionButtons(self):
		# advc: unused
		#global SELECTION_BUTTON_COLUMNS
		#global MAX_SELECTION_BUTTONS
		global g_pSelectedUnit
		# <advc.009b> Workaround to avoid exceptions while reloading scripts
		if not hasattr(self, "screen"):
			return # </advc.009b>
		screen = self.screen

		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		pHeadSelectedUnit = CyInterface().getHeadSelectedUnit()

		global g_NumEmphasizeInfos
		global g_NumCityTabTypes
		global g_NumHurryInfos
		global g_NumUnitClassInfos
		global g_NumBuildingClassInfos
		global g_NumProjectInfos
		global g_NumProcessInfos
		global g_NumActionInfos

		# Find out our resolution
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		self.updateBottomButtonList()
		screen.clearMultiList("BottomButtonList")
		screen.hide("BottomButtonList")

		# All of the hides...
		self.setMinimapButtonVisibility(False)

		screen.hideList(0)

		for i in range (g_NumEmphasizeInfos):
			szButtonID = "Emphasize" + str(i)
			screen.hide(szButtonID)

		# Hurry button show...
		for i in range(g_NumHurryInfos):
			szButtonID = "Hurry" + str(i)
			screen.hide(szButtonID)

		# Conscript Button Show
		screen.hide("Conscript")
		#screen.hide("Liberate")
		screen.hide("AutomateProduction")
		screen.hide("AutomateCitizens")

		# <advc.154>
		self.hideUnitCyclingButtons()
		# Moved up:
		bHeadSelectionChanged = (g_pSelectedUnit != pHeadSelectedUnit)
		g_pSelectedUnit = pHeadSelectedUnit
		# </advc.154>

		if not CyEngine().isGlobeviewUp() and pHeadSelectedCity:

			self.setMinimapButtonVisibility(True)

			if (pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer() or
					gc.getGame().isDebugMode()):
				# advc.154: Moved up a bit (needed at all?)
				g_pSelectedUnit = 0

				iBtnX = xResolution - 284
				iBtnY = yResolution - 177
				iBtnW = 64
				iBtnH = 30

				# Liberate button
				#szText = "<font=1>" + localText.getText("TXT_KEY_LIBERATE_CITY", ()) + "</font>"
				#screen.setButtonGFC("Liberate", szText, "", iBtnX, iBtnY, iBtnW, iBtnH, WidgetTypes.WIDGET_LIBERATE_CITY, -1, -1, ButtonStyles.BUTTON_STYLE_STANDARD)
				#screen.setStyle("Liberate", "Button_CityT1_Style")
				#screen.hide("Liberate")

				iBtnSX = xResolution - 284

				iBtnX = iBtnSX
				iBtnY = yResolution - 140
				iBtnW = 64
				iBtnH = 30

				# Conscript button
				szText = "<font=1>" + localText.getText("TXT_KEY_DRAFT", ()) + "</font>"
				screen.setButtonGFC("Conscript", szText, "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_CONSCRIPT, -1, -1,
						ButtonStyles.BUTTON_STYLE_STANDARD)
				screen.setStyle("Conscript", "Button_CityT1_Style")
				screen.hide("Conscript")

				iBtnY += iBtnH
				iBtnW = 32
				iBtnH = 28

				# Hurry Buttons
				screen.setButtonGFC("Hurry0", "", "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_HURRY, 0, -1,
						ButtonStyles.BUTTON_STYLE_STANDARD)
				screen.setStyle("Hurry0", "Button_CityC1_Style")
				screen.hide("Hurry0")

				iBtnX += iBtnW

				screen.setButtonGFC("Hurry1", "", "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_HURRY, 1, -1,
						ButtonStyles.BUTTON_STYLE_STANDARD)
				screen.setStyle("Hurry1", "Button_CityC2_Style")
				screen.hide("Hurry1")

				iBtnX = iBtnSX
				iBtnY += iBtnH

				# Automate Production Button
				screen.addCheckBoxGFC("AutomateProduction", "", "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_AUTOMATE_PRODUCTION, -1, -1,
						ButtonStyles.BUTTON_STYLE_STANDARD)
				screen.setStyle("AutomateProduction", "Button_CityC3_Style")

				iBtnX += iBtnW

				# Automate Citizens Button
				screen.addCheckBoxGFC("AutomateCitizens", "", "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_AUTOMATE_CITIZENS, -1, -1,
						ButtonStyles.BUTTON_STYLE_STANDARD)
				screen.setStyle("AutomateCitizens", "Button_CityC4_Style")

				iBtnY += iBtnH
				iBtnX = iBtnSX

				iBtnW	= 22
				iBtnWa	= 20
				iBtnH	= 24
				iBtnHa	= 27

				# Set Emphasize buttons
				i = 0
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				i+=1
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX+iBtnW, iBtnY, iBtnWa, iBtnH,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				i+=1
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX+iBtnW+iBtnWa, iBtnY, iBtnW, iBtnH,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				iBtnY += iBtnH

				i+=1
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX, iBtnY, iBtnW, iBtnHa,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				i+=1
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX+iBtnW, iBtnY, iBtnWa, iBtnHa,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				i+=1
				szButtonID = "Emphasize" + str(i)
				screen.addCheckBoxGFC(szButtonID, "", "",
						iBtnX+iBtnW+iBtnWa, iBtnY, iBtnW, iBtnHa,
						WidgetTypes.WIDGET_EMPHASIZE, i, -1,
						ButtonStyles.BUTTON_STYLE_LABEL)
				szStyle = "Button_CityB" + str(i+1) + "_Style"
				screen.setStyle(szButtonID, szStyle)
				screen.hide(szButtonID)

				screen.setState("AutomateCitizens",
						pHeadSelectedCity.isCitizensAutomated())
				screen.setState("AutomateProduction",
						pHeadSelectedCity.isProductionAutomated())

				for i in range (g_NumEmphasizeInfos):
					szButtonID = "Emphasize" + str(i)
					screen.show(szButtonID)
					if (pHeadSelectedCity.AI_isEmphasize(i)):
						screen.setState(szButtonID, True)
					else:
						screen.setState(szButtonID, False)

				# City Tabs
				for i in range(g_NumCityTabTypes):
					szButtonID = "CityTab" + str(i)
					screen.show(szButtonID)

				# Hurry button show...
				for i in range(g_NumHurryInfos):
					szButtonID = "Hurry" + str(i)
					screen.show(szButtonID)
					screen.enable(szButtonID, pHeadSelectedCity.canHurry(i, False))

				# Conscript Button Show
				screen.show("Conscript")
				if (pHeadSelectedCity.canConscript()):
					screen.enable("Conscript", True)
				else:
					screen.enable("Conscript", False)

				# Liberate Button Show
				#screen.show("Liberate")
				#if (-1 != pHeadSelectedCity.getLiberationPlayer()):
				#	screen.enable("Liberate", True)
				#else:
				#	screen.enable("Liberate", False)

				iCount = 0
				iRow = 0
				bFound = False

				# Units to construct
				for i in range (g_NumUnitClassInfos):
					eLoopUnit = gc.getCivilizationInfo(
							pHeadSelectedCity.getCivilizationType()).getCivilizationUnits(i)
					# <advc.001>
					if eLoopUnit == UnitTypes.NO_UNIT:
						continue # </advc.001>
					if (pHeadSelectedCity.canTrain(eLoopUnit, False, True)):
						szButton = gc.getPlayer(pHeadSelectedCity.getOwner()).getUnitButton(eLoopUnit)
						screen.appendMultiListButton("BottomButtonList", szButton,
								iRow, WidgetTypes.WIDGET_TRAIN, i, -1, False)
						screen.show("BottomButtonList")
						if (not pHeadSelectedCity.canTrain(eLoopUnit, False, False)):
							screen.disableMultiListButton("BottomButtonList",
									iRow, iCount, szButton)
						iCount = iCount + 1
						bFound = True

				iCount = 0
				if (bFound):
					iRow = iRow + 1
				bFound = False

				# Buildings to construct
				for i in range (g_NumBuildingClassInfos):
					if (not isLimitedWonderClass(i)):
						eLoopBuilding = gc.getCivilizationInfo(
								pHeadSelectedCity.getCivilizationType()).getCivilizationBuildings(i)
						# <advc.001>
						if eLoopBuilding == BuildingTypes.NO_BUILDING:
							continue # </advc.001>
						if (pHeadSelectedCity.canConstruct(
								eLoopBuilding, False, True, False)):
							screen.appendMultiListButton("BottomButtonList",
									gc.getBuildingInfo(eLoopBuilding).getButton(), iRow,
									WidgetTypes.WIDGET_CONSTRUCT, i, -1, False)
							screen.show("BottomButtonList")
							if (not pHeadSelectedCity.canConstruct(
									eLoopBuilding, False, False, False)):
								screen.disableMultiListButton("BottomButtonList",
										iRow, iCount,
										gc.getBuildingInfo(eLoopBuilding).getButton())
							iCount = iCount + 1
							bFound = True

				iCount = 0
				if (bFound):
					iRow = iRow + 1
				bFound = False

				# Wonders to construct
				i = 0
				for i in range(g_NumBuildingClassInfos):
					if (isLimitedWonderClass(i)):
						eLoopBuilding = gc.getCivilizationInfo(pHeadSelectedCity.getCivilizationType()).getCivilizationBuildings(i)
						# <advc.001>
						if eLoopBuilding == BuildingTypes.NO_BUILDING:
							continue # </advc.001>
						if (pHeadSelectedCity.canConstruct(
								eLoopBuilding, False, True, False)):
							screen.appendMultiListButton("BottomButtonList",
									gc.getBuildingInfo(eLoopBuilding).getButton(), iRow,
									WidgetTypes.WIDGET_CONSTRUCT, i, -1, False)
							screen.show("BottomButtonList")
							if (not pHeadSelectedCity.canConstruct(
									eLoopBuilding, False, False, False)):
								screen.disableMultiListButton("BottomButtonList",
										iRow, iCount,
										gc.getBuildingInfo(eLoopBuilding).getButton())
							iCount = iCount + 1
							bFound = True

				iCount = 0
				if (bFound):
					iRow = iRow + 1
				bFound = False

				# Projects
				i = 0
				for i in range(g_NumProjectInfos):
					if (pHeadSelectedCity.canCreate(i, False, True)):
						screen.appendMultiListButton("BottomButtonList",
								gc.getProjectInfo(i).getButton(), iRow,
								WidgetTypes.WIDGET_CREATE, i, -1, False)
						screen.show("BottomButtonList")
						if (not pHeadSelectedCity.canCreate(i, False, False)):
							screen.disableMultiListButton("BottomButtonList",
									iRow, iCount,
									gc.getProjectInfo(i).getButton())
						iCount = iCount + 1
						bFound = True

				# Processes
				i = 0
				for i in range(g_NumProcessInfos):
					if (pHeadSelectedCity.canMaintain(i, False)):
						screen.appendMultiListButton("BottomButtonList",
								gc.getProcessInfo(i).getButton(), iRow,
								WidgetTypes.WIDGET_MAINTAIN, i, -1, False)
						screen.show("BottomButtonList")
						iCount = iCount + 1
						bFound = True

				screen.selectMultiList("BottomButtonList",
						CyInterface().getCityTabSelectionRow())

		elif (not CyEngine().isGlobeviewUp() and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY):
			self.setMinimapButtonVisibility(True)
			if CyInterface().getInterfaceMode() == InterfaceModeTypes.INTERFACEMODE_SELECTION:
				# advc.154: pHeadSelectedUnit moved from above. (Handling of g_pSelectedUnit moved up.)
				if (pHeadSelectedUnit and
						pHeadSelectedUnit.getOwner() == gc.getGame().getActivePlayer() and
						bHeadSelectionChanged):
					iCount = 0
					actions = CyInterface().getActionsToShow()
					# advc.004: Hide the Skip button while asleep, but keep the hotkey available? Maybe better not ...
					#bWaiting = pHeadSelectedUnit.isWaiting()
					for i in actions:
						# <advc.004> See above
						#if bWaiting and gc.getActionInfo(i).getHotKey() == "KB_SPACE":
						#	continue # </advc.004>
						screen.appendMultiListButton("BottomButtonList",
								gc.getActionInfo(i).getButton(), 0,
								WidgetTypes.WIDGET_ACTION, i, -1, False)
						screen.show("BottomButtonList")
						if (not CyInterface().canHandleAction(i, False)):
							screen.disableMultiListButton("BottomButtonList",
									0, iCount, gc.getActionInfo(i).getButton())
						if (pHeadSelectedUnit.isActionRecommended(i)
								#or gc.getActionInfo(i).getCommandType() == CommandTypes.COMMAND_PROMOTION
								):
							screen.enableMultiListPulse("BottomButtonList", True, 0, iCount)
						else:
							screen.enableMultiListPulse("BottomButtonList", False, 0, iCount)

						iCount = iCount + 1

					if (CyInterface().canCreateGroup()):
						screen.appendMultiListButton("BottomButtonList",
								ArtFileMgr.getInterfaceArtInfo("INTERFACE_BUTTONS_CREATEGROUP").getPath(), 0,
								WidgetTypes.WIDGET_CREATE_GROUP, -1, -1, False)
						screen.show("BottomButtonList")

						iCount = iCount + 1

					if (CyInterface().canDeleteGroup()):
						screen.appendMultiListButton("BottomButtonList",
								ArtFileMgr.getInterfaceArtInfo("INTERFACE_BUTTONS_SPLITGROUP").getPath(), 0,
								WidgetTypes.WIDGET_DELETE_GROUP, -1, -1, False)
						screen.show("BottomButtonList")

						iCount = iCount + 1
				# <advc.154>
				pUnit = None
				if bHeadSelectionChanged:
					pUnit = pHeadSelectedUnit
				self.updateUnitCyclingButtons(pUnit) # </advc.154>
		elif (CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY):
			self.setMinimapButtonVisibility(True)

		return 0
	# <advc.154>
	def hideUnitCyclingButtons(self):
		self.hideUnitCycleButtonGFC("UnitCycle")
		self.hideUnitCycleButtonGFC("WorkerCycle")
		self.hideUnitCycleButtonGFC("Unselect")

	def updateUnitCyclingButtons(self, pHeadSelectedUnit):
		if MainOpt.isUnitCyclingButtonsDisabled():
			return
		lButtons = ColumnLayout(gRect("CenterBottom"),
				-HSPACE(5), VSPACE(5),
				2, VSPACE(4), BTNSZ(32))
		gSetRectangle("UnitCycleButtons", lButtons)
		pNextUnit = gc.getGame().getNextUnitInCycle(True, False)
		if pNextUnit:
			# The button looks weird when the HUD is partly hidden and
			# no unit selected. Can be a nuisance when taking screenshots.
			if (not pHeadSelectedUnit and
					CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE):
				return
			if pNextUnit.hasMoved():
				szOverlay = "OVERLAY_HASMOVED"
			else:
				szOverlay = "OVERLAY_MOVE"
			self.showUnitCycleButtonGFC("UnitCycle", pNextUnit, lButtons.next(),
					False, False, ArtFileMgr.getInterfaceArtInfo(szOverlay).getPath())
			if (not MainOpt.isSingleUnitCyclingButton() and
					not pNextUnit.isWorker()):
				pNextWorker = gc.getGame().getNextUnitInCycle(True, True)
				if pNextWorker and pNextWorker.getID() != pNextUnit.getID():
					if pNextWorker.hasMoved():
						szOverlay = "OVERLAY_HASMOVED"
					else:
						szOverlay = "OVERLAY_MOVE"
					self.showUnitCycleButtonGFC("WorkerCycle", pNextWorker, lButtons.next(),
							True, False, ArtFileMgr.getInterfaceArtInfo(szOverlay).getPath())
		# If selected unit is not expecting orders, show unselect button (advc.088).
		elif (pHeadSelectedUnit and
				(pHeadSelectedUnit.isWaiting() or not pHeadSelectedUnit.canMove())):
			if pHeadSelectedUnit.canMove():
				szOverlay = "OVERLAY_FORTIFY"
			else:
				szOverlay = "OVERLAY_NOMOVE"
			self.showUnitCycleButtonGFC("Unselect", pHeadSelectedUnit, lButtons.next(),
					False, True, ArtFileMgr.getInterfaceArtInfo(szOverlay).getPath())

	def showUnitCycleButtonGFC(self, szName, kUnit, lRect,
			bWorkers, bUnselect, szOverlayPath):
		iWidgetData2 = -1
		if not bUnselect:
			iWidgetData2 = kUnit.getID()
		screen = self.screen
		screen.setButtonGFC(szName + "Button", "",
				gc.getPlayer(kUnit.getOwner()).getUnitButton(kUnit.getUnitType()),
				lRect.x(), lRect.y(), lRect.width(), lRect.height(),
				WidgetTypes.WIDGET_CYCLE_UNIT, bWorkers, iWidgetData2,
				ButtonStyles.BUTTON_STYLE_IMAGE)
		iOverlaySize = self.unitButtonOverlaySize()
		screen.addDDSGFCAt(szName + "Overlay", szName + "Button", szOverlayPath,
				0, 0, iOverlaySize, iOverlaySize,
				WidgetTypes.WIDGET_CYCLE_UNIT, bWorkers, iWidgetData2, False)
		screen.show(szName + "Button")
		screen.show(szName + "Overlay")

	def hideUnitCycleButtonGFC(self, szName):
		self.screen.hide(szName + "Button")
		self.screen.hide(szName + "Overlay") # </advc.154>

	# Will update the research buttons
	def updateResearchButtons(self):

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		for i in range(gc.getNumTechInfos()):
			szName = "ResearchButton" + str(i)
			screen.hide(szName)

		# Find out our resolution
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		#screen.hide("InterfaceOrnamentLeftLow")
		#screen.hide("InterfaceOrnamentRightLow")

		for i in range(gc.getNumReligionInfos()):
			szName = "ReligionButton" + str(i)
			screen.hide(szName)
		if (CyInterface().shouldShowResearchButtons() and
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			iCount = 0
			for i in range(gc.getNumTechInfos()):
				if (gc.getActivePlayer().canResearch(i, False)):
					if (iCount < 20):
						szName = "ResearchButton" + str(i)
						bDone = False
						for j in range(gc.getNumReligionInfos()):
							if (not bDone):
								if (gc.getReligionInfo(j).getTechPrereq() == i):
									if not (gc.getGame().isReligionSlotTaken(j)):
										szName = "ReligionButton" + str(j)
										bDone = True
						screen.show(szName)
						self.setResearchButtonPosition(szName, iCount)
					iCount = iCount + 1
		return 0

# BUG - city specialist - start
	def updateCitizenButtons_hide(self):
		global MAX_CITIZEN_BUTTONS
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		for i in range(MAX_CITIZEN_BUTTONS):
			szName = "FreeSpecialist" + str(i)
			screen.hide(szName)
			szName = "AngryCitizen" + str(i)
			screen.hide(szName)
			szName = "AngryCitizenChevron" + str(i)
			screen.hide(szName)

		for i in range(gc.getNumSpecialistInfos()):
			szName = "IncreaseSpecialist" + str(i)
			screen.hide(szName)
			szName = "DecreaseSpecialist" + str(i)
			screen.hide(szName)
			szName = "CitizenDisabledButton" + str(i)
			screen.hide(szName)
			for j in range(MAX_CITIZEN_BUTTONS):
				szName = "CitizenButton" + str((i * 100) + j)
				screen.hide(szName)
				szName = "CitizenButtonHighlight" + str((i * 100) + j)
				screen.hide(szName)
				szName = "CitizenChevron" + str((i * 100) + j)
				screen.hide(szName)

				szName = "IncresseCitizenButton" + str((i * 100) + j)
				screen.hide(szName)
				szName = "IncresseCitizenBanner" + str((i * 100) + j)
				screen.hide(szName)
				szName = "DecresseCitizenButton" + str((i * 100) + j)
				screen.hide(szName)
				szName = "CitizenButtonHighlight" + str((i * 100) + j)
				screen.hide(szName)

		global g_iSuperSpecialistCount
		global g_iCitySpecialistCount
		global g_iAngryCitizensCount

		screen.hide("SpecialistBackground")
		screen.hide("SpecialistLabel")

		for i in range(g_iSuperSpecialistCount):
			szName = "FreeSpecialist" + str(i)
			screen.hide(szName)
		for i in range(g_iAngryCitizensCount):
			szName = "AngryCitizen" + str(i)
			screen.hide(szName)

		for i in range(gc.getNumSpecialistInfos()):
			for k in range(g_iCitySpecialistCount):
				szName = "IncresseCitizenBanner" + str((i * 100) + k)
				screen.hide(szName)
				szName = "IncresseCitizenButton" + str((i * 100) + k)
				screen.hide(szName)
				szName = "DecresseCitizenButton" + str((i * 100) + k)
				screen.hide(szName)

		return 0
# BUG - city specialist - end


	# Will update the citizen buttons
	def updateCitizenButtons(self):

		if not CyInterface().isCityScreenUp():
			return False
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		if not (pHeadSelectedCity and
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			return False
		global MAX_CITIZEN_BUTTONS
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		if (pHeadSelectedCity.angryPopulation(0) < MAX_CITIZEN_BUTTONS):
			iCount = pHeadSelectedCity.angryPopulation(0)
		else:
			iCount = MAX_CITIZEN_BUTTONS

		bHandled = False

		for i in range(iCount):
			bHandled = True
			szName = "AngryCitizen" + str(i)
			screen.show(szName)

		iFreeSpecialistCount = 0
		for i in range(gc.getNumSpecialistInfos()):
			iFreeSpecialistCount += pHeadSelectedCity.getFreeSpecialistCount(i)

		iCount = 0
		bHandled = False
		if (iFreeSpecialistCount > MAX_CITIZEN_BUTTONS):
			for i in range(gc.getNumSpecialistInfos()):
				if (pHeadSelectedCity.getFreeSpecialistCount(i) > 0):
					if (iCount < MAX_CITIZEN_BUTTONS):
						szName = "FreeSpecialist" + str(iCount)
						screen.setImageButton(szName,
								gc.getSpecialistInfo(i).getTexture(),
								xResolution - 74 - (26 * iCount),
								yResolution - 214,
								24, 24,
								WidgetTypes.WIDGET_FREE_CITIZEN, i, 1)
						screen.show(szName)
						bHandled = true
					iCount += 1
		else:
			for i in range(gc.getNumSpecialistInfos()):
				for j in range(pHeadSelectedCity.getFreeSpecialistCount(i)):
					if (iCount < MAX_CITIZEN_BUTTONS):
						szName = "FreeSpecialist" + str(iCount)
						screen.setImageButton(szName,
								gc.getSpecialistInfo(i).getTexture(),
								xResolution - 74 - (26 * iCount),
								yResolution - 214,
								24, 24,
								WidgetTypes.WIDGET_FREE_CITIZEN, i, -1)
						screen.show(szName)
						bHandled = true
					iCount = iCount + 1

		for i in range(gc.getNumSpecialistInfos()):
			bHandled = False
			if (pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer() or
					gc.getGame().isDebugMode()):
				if (pHeadSelectedCity.isCitizensAutomated()):
					iSpecialistCount = max(pHeadSelectedCity.getSpecialistCount(i),
							pHeadSelectedCity.getForceSpecialistCount(i))
				else:
					iSpecialistCount = pHeadSelectedCity.getSpecialistCount(i)

				if (pHeadSelectedCity.isSpecialistValid(i, 1) and
						(pHeadSelectedCity.isCitizensAutomated() or
						iSpecialistCount < (pHeadSelectedCity.getPopulation() +
						pHeadSelectedCity.totalFreeSpecialists()))):
					szName = "IncreaseSpecialist" + str(i)
					screen.show(szName)
					szName = "CitizenDisabledButton" + str(i)
					screen.show(szName)

				if iSpecialistCount > 0:
					szName = "CitizenDisabledButton" + str(i)
					screen.hide(szName)
					szName = "DecreaseSpecialist" + str(i)
					screen.show(szName)

			if (pHeadSelectedCity.getSpecialistCount(i) < MAX_CITIZEN_BUTTONS):
				iCount = pHeadSelectedCity.getSpecialistCount(i)
			else:
				iCount = MAX_CITIZEN_BUTTONS

			for j in range(iCount):
				bHandled = True
				szName = "CitizenButton" + str((i * 100) + j)
				screen.addCheckBoxGFC(szName, gc.getSpecialistInfo(i).getTexture(), "",
						xResolution - 74 - (26 * j), (yResolution - 272 - (26 * i)), 24, 24,
						WidgetTypes.WIDGET_CITIZEN, i, j,
						ButtonStyles.BUTTON_STYLE_LABEL)
				screen.show(szName)
				szName = "CitizenButtonHighlight" + str((i * 100) + j)
				screen.addDDSGFC(szName,
						ArtFileMgr.getInterfaceArtInfo("BUTTON_HILITE_SQUARE").getPath(),
						xResolution - 74 - (26 * j), (yResolution - 272 - (26 * i)), 24, 24,
						WidgetTypes.WIDGET_CITIZEN, i, j)
				if (pHeadSelectedCity.getForceSpecialistCount(i) > j):
					screen.show(szName)
				else:
					screen.hide(szName)

			if (not bHandled):
				szName = "CitizenDisabledButton" + str(i)
				screen.show(szName)

		return True # advc.004: Signal success

# BUG - city specialist - start
	def updateCitizenButtons_Stacker(self):
		if not CyInterface().isCityScreenUp():
			return False
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		if not (pHeadSelectedCity and
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			return False
		global g_iSuperSpecialistCount
		global g_iCitySpecialistCount
		global g_iAngryCitizensCount

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		currentAngryCitizenCount = pHeadSelectedCity.angryPopulation(0)

		if(currentAngryCitizenCount > 0):
			stackWidth = 220 / currentAngryCitizenCount
			if (stackWidth > MAX_SPECIALIST_BUTTON_SPACING):
				stackWidth = MAX_SPECIALIST_BUTTON_SPACING

		bHandled = False
		for i in range(currentAngryCitizenCount):
			bHandled = True
			szName = "AngryCitizen" + str(i)
			screen.setImageButton(szName,
					ArtFileMgr.getInterfaceArtInfo("INTERFACE_ANGRYCITIZEN_TEXTURE").getPath(),
					xResolution - SPECIALIST_AREA_MARGIN - (stackWidth * i),
					yResolution - (282- SPECIALIST_ROW_HEIGHT),
					30, 30,
					WidgetTypes.WIDGET_ANGRY_CITIZEN, -1, -1)
			screen.show(szName)

		# update the max ever citizen counts
		if g_iAngryCitizensCount < currentAngryCitizenCount:
			g_iAngryCitizensCount = currentAngryCitizenCount

		iCount = 0
		bHandled = False
		currentSuperSpecialistCount = 0
		for i in range(gc.getNumSpecialistInfos()):
			if(pHeadSelectedCity.getFreeSpecialistCount(i) > 0):
				currentSuperSpecialistCount = currentSuperSpecialistCount
				currentSuperSpecialistCount += pHeadSelectedCity.getFreeSpecialistCount(i)
		if(currentSuperSpecialistCount > 0):
			stackWidth = 220 / currentSuperSpecialistCount
			if (stackWidth > MAX_SPECIALIST_BUTTON_SPACING):
				stackWidth = MAX_SPECIALIST_BUTTON_SPACING

		for i in range(gc.getNumSpecialistInfos()):
			for j in range(pHeadSelectedCity.getFreeSpecialistCount(i)):
				szName = "FreeSpecialist" + str(iCount)
				screen.setImageButton(szName,
						gc.getSpecialistInfo(i).getTexture(),
						xResolution - SPECIALIST_AREA_MARGIN - (stackWidth * iCount),
						yResolution - (282 - SPECIALIST_ROW_HEIGHT * 2),
						30, 30,
						WidgetTypes.WIDGET_FREE_CITIZEN, i, 1)
				screen.show(szName)
				bHandled = true
				iCount = iCount + 1

		# update the max ever citizen counts
		if g_iSuperSpecialistCount < iCount:
			g_iSuperSpecialistCount = iCount

		iXShiftVal = 0
		iYShiftVal = 0
		iSpecialistCount = 0
		for i in range(gc.getNumSpecialistInfos()):
			bHandled = False
			if(iSpecialistCount > SPECIALIST_ROWS):
				iXShiftVal = 115
				iYShiftVal = (iSpecialistCount % SPECIALIST_ROWS) + 1
			else:
				iYShiftVal = iSpecialistCount

			if (gc.getSpecialistInfo(i).isVisible()):
				iSpecialistCount = iSpecialistCount + 1

			if (gc.getPlayer(pHeadSelectedCity.getOwner()).isSpecialistValid(i) or i == 0):
				iCount = (pHeadSelectedCity.getPopulation() - pHeadSelectedCity.angryPopulation(0))
				iCount += pHeadSelectedCity.totalFreeSpecialists()
			else:
				iCount = pHeadSelectedCity.getMaxSpecialistCount(i)

			# update the max ever citizen counts
			if g_iCitySpecialistCount < iCount:
				g_iCitySpecialistCount = iCount

			RowLength = 110
			if (i == 0):
			#if (i == gc.getInfoTypeForString(gc.getDefineSTRING("DEFAULT_SPECIALIST"))):
			# advc.001 (note): If the above is uncommented (I didn't comment it out), the following should be used instead:
			#if i == gc.getDefineINT("DEFAULT_SPECIALIST"):
				RowLength *= 2

			HorizontalSpacing = MAX_SPECIALIST_BUTTON_SPACING
			if (iCount > 0):
				HorizontalSpacing = RowLength / iCount
			if (HorizontalSpacing > MAX_SPECIALIST_BUTTON_SPACING):
				HorizontalSpacing = MAX_SPECIALIST_BUTTON_SPACING

			for k in range (iCount):
				if (k >= pHeadSelectedCity.getSpecialistCount(i)):
					szName = "IncresseCitizenBanner" + str((i * 100) + k)
					screen.addCheckBoxGFC(szName, gc.getSpecialistInfo(i).getTexture(), "",
							xResolution - (SPECIALIST_AREA_MARGIN + iXShiftVal) - (HorizontalSpacing * k),
							(yResolution - 282 - (SPECIALIST_ROW_HEIGHT * iYShiftVal)),
							30, 30,
							WidgetTypes.WIDGET_CHANGE_SPECIALIST, i, 1,
							ButtonStyles.BUTTON_STYLE_LABEL)
					screen.enable(szName, False)
					screen.show(szName)

					szName = "IncresseCitizenButton" + str((i * 100) + k)
					screen.addCheckBoxGFC(szName, "", "",
							xResolution - (SPECIALIST_AREA_MARGIN + iXShiftVal) - (HorizontalSpacing * k),
							(yResolution - 282 - (SPECIALIST_ROW_HEIGHT * iYShiftVal)),
							30, 30,
							WidgetTypes.WIDGET_CHANGE_SPECIALIST, i, 1,
							ButtonStyles.BUTTON_STYLE_LABEL)
					screen.show(szName)

				else:
					szName = "DecresseCitizenButton" + str((i * 100) + k)
					screen.addCheckBoxGFC(szName, gc.getSpecialistInfo(i).getTexture(), "",
							xResolution - (SPECIALIST_AREA_MARGIN + iXShiftVal) - (HorizontalSpacing * k),
							(yResolution - 282 - (SPECIALIST_ROW_HEIGHT * iYShiftVal)),
							30, 30,
							WidgetTypes.WIDGET_CHANGE_SPECIALIST, i, -1,
							ButtonStyles.BUTTON_STYLE_LABEL)
					screen.show(szName)
		#screen.show("SpecialistBackground")
		#screen.show("SpecialistLabel")
		# advc.004: Signal to the caller that the label should be shown
		return True
# BUG - city specialist - end

# BUG - city specialist - start
	def updateCitizenButtons_Chevron(self):
		if not CyInterface().isCityScreenUp():
			return False
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		if not (pHeadSelectedCity and
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			return False
		global MAX_CITIZEN_BUTTONS
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		iCount = pHeadSelectedCity.angryPopulation(0)
		bHandled = False
		j = 0
		while (iCount > 0):
			bHandled = True
			szName = "AngryCitizen" + str(j)
			screen.show(szName)
			xCoord = xResolution - 74 - (26 * j)
			yCoord = yResolution - 238
			szName = "AngryCitizenChevron" + str(j)
			if iCount >= 20:
				szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON20").getPath()
				iCount -= 20
			elif iCount >= 10:
				szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON10").getPath()
				iCount -= 10
			elif iCount >= 5:
				szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON5").getPath()
				iCount -= 5
			else:
				szFileName = ""
				iCount -= 1
			if (szFileName != ""):
				screen.addDDSGFC(szName ,
						szFileName,
						xCoord, yCoord, 10, 10,
						WidgetTypes.WIDGET_CITIZEN, j, False)
				screen.show(szName)
			j += 1

		iFreeSpecialistCount = 0
		for i in range(gc.getNumSpecialistInfos()):
			iFreeSpecialistCount += pHeadSelectedCity.getFreeSpecialistCount(i)

		iCount = 0
		bHandled = False
		if (iFreeSpecialistCount > MAX_CITIZEN_BUTTONS):
			for i in range(gc.getNumSpecialistInfos()):
				if (pHeadSelectedCity.getFreeSpecialistCount(i) > 0):
					if (iCount < MAX_CITIZEN_BUTTONS):
						szName = "FreeSpecialist" + str(iCount)
						screen.setImageButton(szName,
								gc.getSpecialistInfo(i).getTexture(),
								xResolution - 74 - (26 * iCount),
								yResolution - 214,
								24, 24,
								WidgetTypes.WIDGET_FREE_CITIZEN, i, 1)
						screen.show(szName)
						bHandled = True
					iCount += 1
		else:
			for i in range(gc.getNumSpecialistInfos()):
				for j in range(pHeadSelectedCity.getFreeSpecialistCount(i)):
					if (iCount < MAX_CITIZEN_BUTTONS):
						szName = "FreeSpecialist" + str(iCount)
						screen.setImageButton(szName,
								gc.getSpecialistInfo(i).getTexture(),
								xResolution - 74 - (26 * iCount),
								yResolution - 214,
								24, 24,
								WidgetTypes.WIDGET_FREE_CITIZEN, i, -1)
						screen.show(szName)
						bHandled = True
					iCount = iCount + 1

		for i in range(gc.getNumSpecialistInfos()):
			bHandled = False
			if (pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer() or
					gc.getGame().isDebugMode()):
				if (pHeadSelectedCity.isCitizensAutomated()):
					iSpecialistCount = max(pHeadSelectedCity.getSpecialistCount(i),
							pHeadSelectedCity.getForceSpecialistCount(i))
				else:
					iSpecialistCount = pHeadSelectedCity.getSpecialistCount(i)
				if (pHeadSelectedCity.isSpecialistValid(i, 1) and
						(pHeadSelectedCity.isCitizensAutomated() or
						iSpecialistCount < (pHeadSelectedCity.getPopulation() +
						pHeadSelectedCity.totalFreeSpecialists()))):
					szName = "IncreaseSpecialist" + str(i)
					screen.show(szName)
					szName = "CitizenDisabledButton" + str(i)
					screen.show(szName)

				if iSpecialistCount > 0:
					szName = "CitizenDisabledButton" + str(i)
					screen.hide(szName)
					szName = "DecreaseSpecialist" + str(i)
					screen.show(szName)

			iCount = pHeadSelectedCity.getSpecialistCount(i)
			j = 0
			while (iCount > 0):
				bHandled = True

				xCoord = xResolution - 74 - (26 * j)
				yCoord = yResolution - 272 - (26 * i)

				szName = "CitizenButton" + str((i * 100) + j)
				screen.addCheckBoxGFC(szName, gc.getSpecialistInfo(i).getTexture(), "",
						xCoord, yCoord, 24, 24,
						WidgetTypes.WIDGET_CITIZEN, i, j,
						ButtonStyles.BUTTON_STYLE_LABEL)
				screen.show(szName)

				szName = "CitizenChevron" + str((i * 100) + j)
				if iCount >= 20:
					szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON20").getPath()
					iCount -= 20
				elif iCount >= 10:
					szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON10").getPath()
					iCount -= 10
				elif iCount >= 5:
					szFileName = ArtFileMgr.getInterfaceArtInfo("OVERLAY_CHEVRON5").getPath()
					iCount -= 5
				else:
					szFileName = ""
					iCount -= 1

				if (szFileName != ""):
					screen.addDDSGFC(szName,
							szFileName,
							xCoord, yCoord, 10, 10,
							WidgetTypes.WIDGET_CITIZEN, i, False)
					screen.show(szName)
				j += 1

			if (not bHandled):
				szName = "CitizenDisabledButton" + str(i)
				screen.show(szName)

		return True # advc.004: Signal success
# BUG - city specialist - end

	# Will update the game data strings
	def updateGameDataStrings(self):

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)

		screen.hide("ResearchText")
		screen.hide("GoldText")
		screen.hide("TimeText")
		screen.hide("TwoLineResearchBar")

# BUG - NJAGC - start
		screen.hide("EraText")
# BUG - NJAGC - end

# BUG - Great Person Bar - start
		screen.hide("TwoLineGPBar")
		screen.hide("GreatPersonBarText")
# BUG - Great Person Bar - end

# BUG - Great General Bar - start
		screen.hide("TwoLineGGBar")
		screen.hide("GreatGeneralBarText")
# BUG - Great General Bar - end

# BUG - Bars on single line for higher resolution screens - start
		screen.hide("OneLineGGBar")
		screen.hide("OneLineResearchBar")
		screen.hide("OneLineGPBar")
# BUG - Bars on single line for higher resolution screens - end

# BUG - Progress Bar - Tick Marks - start
		self.pTwoLineResearchBar.hide(screen)
		self.pOneLineResearchBar.hide(screen)
# BUG - Progress Bar - Tick Marks - end

		bShift = CyInterface().shiftKey()

		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		pHeadSelectedCity = CyInterface().getHeadSelectedCity()

		if (pHeadSelectedCity):
			ePlayer = pHeadSelectedCity.getOwner()
		else:
			ePlayer = gc.getGame().getActivePlayer()

		if (ePlayer < 0 or ePlayer >= gc.getMAX_PLAYERS()):
			return 0

		for iI in range(CommerceTypes.NUM_COMMERCE_TYPES):
			szString = "PercentText" + str(iI)
			screen.hide(szString)
			szString = "RateText" + str(iI)
			screen.hide(szString)

		if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE_ALL or
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_MINIMAP_ONLY or
				CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_ADVANCED_START):
			return 0 # advc: Reduce indentation

		# Percent of commerce
		if gc.getPlayer(ePlayer).isAlive():
			iCount = 0
			for iI in range(CommerceTypes.NUM_COMMERCE_TYPES):
				eCommerce = (iI + 1) % CommerceTypes.NUM_COMMERCE_TYPES
				#if (gc.getPlayer(ePlayer).isCommerceFlexible(eCommerce) or (CyInterface().isCityScreenUp() and (eCommerce == CommerceTypes.COMMERCE_GOLD))):
				if self.showCommercePercent(eCommerce, ePlayer): # K-Mod
					szOutText = u"<font=2>%c:%d%%</font>" %(
							gc.getCommerceInfo(eCommerce).getChar(),
							gc.getPlayer(ePlayer).getCommercePercent(eCommerce))
					szString = "PercentText" + str(iI)
					screen.setLabel(szString, "Background",
							szOutText, CvUtil.FONT_LEFT_JUSTIFY,
							14, 50 + (iCount * 19), -0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_GENERAL, -1, -1)
					screen.show(szString)

					if not CyInterface().isCityScreenUp():
						szOutText = u"<font=2>" + localText.getText(
								"TXT_KEY_MISC_POS_GOLD_PER_TURN",
								(gc.getPlayer(ePlayer).getCommerceRate(CommerceTypes(eCommerce)),))
						szOutText += u"</font>"
						# <advc.004p>
						if (eCommerce == CommerceTypes.COMMERCE_CULTURE and
								not MainOpt.isShowTotalCultureRate()):
							szOutText = u""
						# </advc.004p>
						szString = "RateText" + str(iI)
# BUG - Min/Max Sliders - start
						if MainOpt.isShowMinMaxCommerceButtons():
							iMinMaxAdjustX = 40
						else:
							iMinMaxAdjustX = 0
						screen.setLabel(szString, "Background",
								szOutText, CvUtil.FONT_LEFT_JUSTIFY,
								112 + iMinMaxAdjustX, 50 + (iCount * 19), -0.1,
								FontTypes.SMALL_FONT,
								WidgetTypes.WIDGET_GENERAL, -1, -1)
# BUG - Min/Max Sliders - end
						screen.show(szString)

					iCount = iCount + 1;
		self.updateTimeText()
		screen.setLabel("TimeText", "Background",
				g_szTimeText, CvUtil.FONT_RIGHT_JUSTIFY,
				xResolution - 56, 6, -0.3, FontTypes.GAME_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.show("TimeText")
		# advc.103: Don't show gold rate and current research when investigating
		if (not gc.getPlayer(ePlayer).isAlive() or
				(ePlayer != gc.getGame().getActivePlayer() and
				not gc.getGame().isDebugMode())):
			return 0
# BUG - Gold Rate Warning - start
		if True:#MainOpt.isGoldRateWarning(): # advc.070
			pPlayer = gc.getPlayer(ePlayer)
			iGold = pPlayer.getGold()
			iGoldRate = pPlayer.calculateGoldRate()
			if iGold < 0: # advc.070 (comment): Only relevant for mod-mods I think, so I'm not changing anything here.
				szText = BugUtil.getText("TXT_KEY_MISC_NEG_GOLD", iGold)
				if iGoldRate != 0:
					if iGold + iGoldRate >= 0:
						szText += BugUtil.getText(
								"TXT_KEY_MISC_POS_GOLD_PER_TURN", iGoldRate)
					elif iGoldRate >= 0:
						szText += BugUtil.getText(
								"TXT_KEY_MISC_POS_WARNING_GOLD_PER_TURN", iGoldRate)
					else:
						szText += BugUtil.getText(
								"TXT_KEY_MISC_NEG_GOLD_PER_TURN", iGoldRate)
			else:
				szText = BugUtil.getText("TXT_KEY_MISC_POS_GOLD", iGold)
				if iGoldRate != 0:
					# <advc.070>
					szRateText = " ("
					szRateText += BugUtil.getText("TXT_KEY_MISC_PER_TURN", iGoldRate)
					szRateText += ")"
					# (I've removed the broke color option again in order to make room on the BUG menu)
					#iRateColor = MainOpt.getGoldRateBrokeColor()
					if iGoldRate >= 0:
						iRateColor = MainOpt.getPositiveGoldRateColor()
						#szText += BugUtil.getText("TXT_KEY_MISC_POS_GOLD_PER_TURN", iGoldRate)
					#elif iGold + iGoldRate >= 0:
					else:
						iRateColor = MainOpt.getNegativeGoldRateColor()
						#szText += BugUtil.getText("TXT_KEY_MISC_NEG_WARNING_GOLD_PER_TURN", iGoldRate)
					#else:
						#szText += BugUtil.getText("TXT_KEY_MISC_NEG_GOLD_PER_TURN", iGoldRate)
					szText += localText.changeTextColor(szRateText, iRateColor)
					# </advc.070>

			if pPlayer.isStrike():
				szText += BugUtil.getPlainText("TXT_KEY_MISC_STRIKE")
		else:
			szText = CyGameTextMgr().getGoldStr(ePlayer)
# BUG - Gold Rate Warning - end
		screen.setLabel("GoldText", "Background",
				szText, CvUtil.FONT_LEFT_JUSTIFY,
				12, 6, -0.3, FontTypes.GAME_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.show("GoldText")

		if (((gc.getPlayer(ePlayer).calculateGoldRate() != 0) and
				not (gc.getPlayer(ePlayer).isAnarchy())) or
				(gc.getPlayer(ePlayer).getGold() != 0)):
			screen.show("GoldText")
# BUG - NJAGC - start
		#if (ClockOpt.isEnabled() and ClockOpt.isShowEra()):
		# advc.067: Replacing the above
		if ClockOpt.isShowEra():
			# <advc.067>
			if ClockOpt.isShowGameEra():
				iEra = gc.getGame().getCurrentEra()
			else: # </advc.067>
				iEra = gc.getPlayer(ePlayer).getCurrentEra()
			szText = localText.getText("TXT_KEY_BUG_ERA",
					(gc.getEraInfo(iEra).getDescription(),))
			if(ClockOpt.isUseEraColor()):
				iEraColor = ClockOpt.getEraColor(gc.getEraInfo(iEra).getType())
				if (iEraColor >= 0):
					szText = localText.changeTextColor(szText, iEraColor)
			screen.setLabel("EraText", "Background",
					szText, CvUtil.FONT_RIGHT_JUSTIFY,
					250, 6, -0.3, FontTypes.GAME_FONT,
					WidgetTypes.WIDGET_GENERAL, -1, -1)
			screen.show("EraText")
# BUG - NJAGC - end
# BUG - Bars on single line for higher resolution screens - start
		if self.isShowTopBarsOnSingleLine():
			szResearchBar = "OneLineResearchBar"
		else:
			szResearchBar = "TwoLineResearchBar"
		gOffSetPoint("ResearchText", szResearchBar,
				RectLayout.CENTER,
				# Ruff: this used to be 3 but I changed it so it lines up with the Great Person Bar
				# advc: Should be OK now that it's an offset from the research bar
				VLEN(3))
		bAnarchy = gc.getPlayer(ePlayer).isAnarchy()
		szText = None
		if bAnarchy:
			szText = localText.getText("INTERFACE_ANARCHY",
					(gc.getPlayer(ePlayer).getAnarchyTurns(),))
		elif gc.getPlayer(ePlayer).getCurrentResearch() != -1:
			szText = CyGameTextMgr().getResearchStr(ePlayer)
		if szText:
			self.setText("ResearchText", "Background", szText,
					CvUtil.FONT_CENTER_JUSTIFY, FontTypes.GAME_FONT, -0.4,
					WidgetTypes.WIDGET_RESEARCH)
			# advc.004x: Always show ResearchText (i.e. anarchy turns)
			#if not bAnarchy:
			screen.show("ResearchText")
			#else:
			#	screen.hide("ResearchText")
		if szText and not bAnarchy:
# BUG - Bars on single line for higher resolution screens - end
			researchProgress = gc.getTeam(gc.getPlayer(ePlayer).getTeam()).getResearchProgress(
					gc.getPlayer(ePlayer).getCurrentResearch())
			overflowResearch = (gc.getPlayer(ePlayer).getOverflowResearch() *
					gc.getPlayer(ePlayer).calculateResearchModifier(
					gc.getPlayer(ePlayer).getCurrentResearch())) / 100
			researchCost = gc.getTeam(gc.getPlayer(ePlayer).getTeam()).getResearchCost(
					gc.getPlayer(ePlayer).getCurrentResearch())
			bTickMarks = MainOpt.isShowBarTickMarks() # advc.078
			researchRate = gc.getPlayer(ePlayer).calculateResearchRate(-1)
			# <advc.078>
			# Meaning that overflow is shown as part of the current progress
			overflowProgress = overflowResearch
			overflowRate = 0
			if bTickMarks:
				# Meaning overflow is shown as part of the next turn's research rate
				overflowRate = overflowResearch
				overflowProgress = 0
			# Mostly BtS code from here
			progressPortion = float(researchProgress + overflowProgress) / researchCost
			screen.setBarPercentage(szResearchBar, InfoBarTypes.INFOBAR_STORED, progressPortion)
			if (researchCost > researchProgress + overflowProgress):
				ratePortion = float(researchRate + overflowRate) / researchCost
				# I don't understand why, but setBarPercentage seems to multiply its argument
				# by the the remaining portion of the bar. Cancel that out:
				ratePortion /= (1 - progressPortion)
				screen.setBarPercentage(szResearchBar, InfoBarTypes.INFOBAR_RATE, ratePortion)
			# </advc.078>
			else:
				screen.setBarPercentage(szResearchBar, InfoBarTypes.INFOBAR_RATE, 0.0)
			screen.show(szResearchBar)
# BUG - Progress Bar - Tick Marks - start
			# advc.004x: researchRate condition added
			if bTickMarks and researchRate > 0:
				if szResearchBar == "TwoLineResearchBar":
					self.pTwoLineResearchBar.drawTickMarks(screen, researchProgress + overflowResearch,
							researchCost, researchRate, researchRate, False)
				else:
					self.pOneLineResearchBar.drawTickMarks(screen, researchProgress + overflowResearch,
							researchCost, researchRate, researchRate, False)
# BUG - Progress Bar - Tick Marks - end
		self.updateGreatPersonBar(screen) # BUG - Great Person Bar
		self.updateGreatGeneralBar(screen) # BUG - Great General Bar
		return 0

# BUG - Great Person Bar - start
	def updateGreatPersonBar(self, screen):
		if not self.isShowGPProgressBar() or CyInterface().isCityScreenUp():
			return
		if self.isShowTopBarsOnSingleLine():
			szGPBar = "OneLineGPBar"
		else:
			szGPBar = "TwoLineGPBar"
		gOffSetPoint("GreatPersonBarText", szGPBar,
				RectLayout.CENTER, VLEN(3))
		pGPCity, iGPTurns = GPUtil.getDisplayCity()
		szText = GPUtil.getGreatPeopleText(pGPCity, iGPTurns,
				gRect(szGPBar).width(),
				MainOpt.isGPBarTypesNone(), MainOpt.isGPBarTypesOne(), True)
		szText = u"<font=2>%s</font>" % (szText)
		if pGPCity:
			iCityID = pGPCity.getID()
		else:
			iCityID = -1
# BUG - Bars on single line for higher resolution screens - start
		self.setText("GreatPersonBarText", "Background", szText,
				CvUtil.FONT_CENTER_JUSTIFY, FontTypes.GAME_FONT, -0.4,
				WidgetTypes.WIDGET_GP_PROGRESS_BAR)
		if not pGPCity:
			screen.setHitTest("GreatPersonBarText", HitTestTypes.HITTEST_NOHIT)
		screen.show("GreatPersonBarText")
# BUG - Bars on single line for higher resolution screens - end
		if pGPCity:
			fThreshold = float(gc.getPlayer(pGPCity.getOwner()).greatPeopleThreshold(False))
			fRate = float(pGPCity.getGreatPeopleRate())
			fFirst = float(pGPCity.getGreatPeopleProgress()) / fThreshold
			screen.setBarPercentage(szGPBar, InfoBarTypes.INFOBAR_STORED, fFirst)
			if (fFirst == 1):
				screen.setBarPercentage(szGPBar, InfoBarTypes.INFOBAR_RATE,
						fRate / fThreshold)
			else:
				screen.setBarPercentage(szGPBar, InfoBarTypes.INFOBAR_RATE,
						fRate / fThreshold / (1 - fFirst))
		else:
			screen.setBarPercentage(szGPBar, InfoBarTypes.INFOBAR_STORED, 0)
			screen.setBarPercentage(szGPBar, InfoBarTypes.INFOBAR_RATE, 0)
		screen.show(szGPBar)
# BUG - Great Person Bar - end

# BUG - Great General Bar - start
	def updateGreatGeneralBar(self, screen):
		if not self.isShowGGProgressBar() or CyInterface().isCityScreenUp():
			return
		if self.isShowTopBarsOnSingleLine():
			szGGBar = "OneLineGGBar"
		else:
			szGGBar = "TwoLineGGBar"
		gOffSetPoint("GreatGeneralBarText", szGGBar,
				RectLayout.CENTER, VLEN(3))
		pPlayer = gc.getActivePlayer()
		iCombatExp = pPlayer.getCombatExperience()
		iThresholdExp = pPlayer.greatPeopleThreshold(True)
		iNeededExp = iThresholdExp - iCombatExp
		szText = u"<font=2>%s</font>" %(GGUtil.getGreatGeneralText(iNeededExp))
# BUG - Bars on single line for higher resolution screens - start
		self.setLabel("GreatGeneralBarText", "Background", szText,
				CvUtil.FONT_CENTER_JUSTIFY, FontTypes.GAME_FONT, -0.4,
				WidgetTypes.WIDGET_HELP_GREAT_GENERAL)
		screen.show("GreatGeneralBarText")
# BUG - Bars on single line for higher resolution screens - end
		fProgress = float(iCombatExp) / float(iThresholdExp)
		screen.setBarPercentage(szGGBar, InfoBarTypes.INFOBAR_STORED, fProgress)
		screen.show(szGGBar)
# BUG - Great General Bar - end

	# <advc.078> I've replaced all calls to MainOpt.isShowGGProgressBar and MainOpt.isShowGPProgressBar with these functions
	def isShowGGProgressBar(self):
		if not MainOpt.isShowGGProgressBar():
			return False
		if not MainOpt.isShowOnlyOnceProgress():
			return True
		iActivePlayer = gc.getGame().getActivePlayer()
		if iActivePlayer < 0:
			return False
		activePlayer = gc.getPlayer(iActivePlayer)
		return (activePlayer.getCombatExperience() > 0 or
				activePlayer.getGreatGeneralsCreated() > 0)

	def isShowGPProgressBar(self):
		if not MainOpt.isShowGPProgressBar():
			return False
		if not MainOpt.isShowOnlyOnceProgress():
			return True
		iActivePlayer = gc.getGame().getActivePlayer()
		if iActivePlayer < 0:
			return False
		activePlayer = gc.getPlayer(iActivePlayer)
		# Don't want to check all cities here over and over. Let the DLL keep track of this (new function: isAnyGPPEver). The second condition is only for old savegames.
		return (activePlayer.isAnyGPPEver() or
				activePlayer.getGreatPeopleCreated() > 0)
	# </advc.078>
	# advc.092:
	def isShowTopBarsOnSingleLine(self):
		return (gRect("TopBarsMaxSpace").encloses(gRect("TopBarsOneLineContainer")) and
				(self.isShowGGProgressBar() or self.isShowGPProgressBar()) and
				# Show the potentially longer non-single-line research bar on the city screen
				not CyInterface().isCityScreenUp())

	# advc.092: Don't show that frame when the bars take up two lines
	def isShowTopBarsFrame(self):
		return (self.isShowTopBarsOnSingleLine() or
				(not self.isShowGGProgressBar() and not self.isShowGPProgressBar()))

	def updateTimeText(self):

		global g_szTimeText

		ePlayer = gc.getGame().getActivePlayer()

# BUG - NJAGC - start
		# <advc.067> Moved out of the isEnabled block
		iEraColor = -1
		if(ClockOpt.isUseEraColor()):
			if ClockOpt.isShowGameEra():
				iEra = gc.getGame().getCurrentEra()
			else: # </advc.067>
				iEra = gc.getPlayer(ePlayer).getCurrentEra()
				iEraColor = ClockOpt.getEraColor(gc.getEraInfo(iEra).getType())
		# advc.067: End of moved code
		if (ClockOpt.isEnabled()):
			"""
			Format: Time - GameTurn/Total Percent - GA (TurnsLeft) Date

			Ex: 10:37 - 220/660 33% - GA (3) 1925
			"""
			if (g_bShowTimeTextAlt):
				bShowTime = ClockOpt.isShowAltTime()
				bShowGameTurn = ClockOpt.isShowAltGameTurn()
				bShowTotalTurns = ClockOpt.isShowAltTotalTurns()
				# advc.067: Option removed
				bShowPercentComplete = False #ClockOpt.isShowAltPercentComplete()
				bShowDateGA = ClockOpt.isShowAltDateGA()
			else:
				bShowTime = ClockOpt.isShowTime()
				bShowGameTurn = ClockOpt.isShowGameTurn()
				bShowTotalTurns = ClockOpt.isShowTotalTurns()
				# advc.067: Option removed
				bShowPercentComplete = False#ClockOpt.isShowPercentComplete()
				bShowDateGA = ClockOpt.isShowDateGA()

			if (not gc.getGame().getMaxTurns() > 0):
				bShowTotalTurns = False
				bShowPercentComplete = False

			bFirst = True
			g_szTimeText = ""

			if (bShowTime):
				bFirst = False
				g_szTimeText += getClockText()

			if (bShowGameTurn):
				if (bFirst):
					bFirst = False
				else:
					g_szTimeText += u" - "
				g_szTimeText += u"%d" %(gc.getGame().getElapsedGameTurns())
				if (bShowTotalTurns):
					g_szTimeText += u"/%d" %(gc.getGame().getMaxTurns())

			if (bShowPercentComplete):
				if (bFirst):
					bFirst = False
				else:
					if (not bShowGameTurn):
						g_szTimeText += u" - "
					else:
						g_szTimeText += u" "
				g_szTimeText += u"%2.2f%%" %(100 *(float(gc.getGame().getElapsedGameTurns()) /
						float(gc.getGame().getMaxTurns())))

			if (bShowDateGA):
				if (bFirst):
					bFirst = False
				else:
					g_szTimeText += u" - "
				szDateGA = unicode(CyGameTextMgr().getInterfaceTimeStr(ePlayer))
				if iEraColor >= 0: # advc.067: Replacing code that has moved up
					szDateGA = localText.changeTextColor(szDateGA, iEraColor)
				g_szTimeText += szDateGA
		else:
			"""
			Original Clock
			Format: Time - 'Turn' GameTurn - GA (TurnsLeft) Date

			Ex: 10:37 - Turn 220 - GA (3) 1925
			"""
			g_szTimeText = localText.getText("TXT_KEY_TIME_TURN",
					(CyGame().getGameTurn(),)) + u" - "
			# <advc.067> Based on NJAGC code above
			szDate = unicode(CyGameTextMgr().getInterfaceTimeStr(ePlayer))
			if iEraColor >= 0:
				szDate = localText.changeTextColor(szDate, iEraColor)
			g_szTimeText += szDate
			# </advc.067>
			if (CyUserProfile().isClockOn()):
				g_szTimeText = getClockText() + u" - " + g_szTimeText
# BUG - NJAGC - end

	# Will update the selection Data Strings
	def updateCityScreen(self):
		# advc: unused
		#global MAX_DISPLAYABLE_BUILDINGS
		#global MAX_DISPLAYABLE_TRADE_ROUTES
		#global MAX_BONUS_ROWS
		#global g_iNumTradeRoutes
		#global g_iNumBuildings
		global g_iNumLeftBonus
		global g_iNumCenterBonus
		global g_iNumRightBonus

		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		bShift = CyInterface().shiftKey()

		screen.hide("PopulationBar")
		screen.hide("ProductionBar")
		screen.hide("GreatPeopleBar")
		screen.hide("CultureBar")
		screen.hide("MaintenanceText")
		screen.hide("MaintenanceAmountText")
# BUG - Progress Bar - Tick Marks - start
		self.pBarPopulationBar.hide(screen)
		self.pBarProductionBar.hide(screen)
		self.pBarProductionBar_Whip.hide(screen)
# BUG - Progress Bar - Tick Marks - end
# BUG - Raw Commerce - start
		screen.hide("RawYieldsTrade0")
		screen.hide("RawYieldsFood1")
		screen.hide("RawYieldsProduction2")
		screen.hide("RawYieldsCommerce3")
		screen.hide("RawYieldsWorkedTiles4")
		screen.hide("RawYieldsCityTiles5")
		screen.hide("RawYieldsOwnedTiles6")
# BUG - Raw Commerce - end
		screen.hide("NationalityText")
		screen.hide("NationalityBar")
		screen.hide("DefenseText")
		screen.hide("CityScrollMinus")
		screen.hide("CityScrollPlus")
		screen.hide("CityNameText")
		screen.hide("PopulationText")
		screen.hide("PopulationInputText")
		screen.hide("HealthText")
		screen.hide("ProductionText")
		screen.hide("ProductionInputText")
		screen.hide("HappinessText")
		screen.hide("CultureText")
		screen.hide("GreatPeopleText")
		for i in range(gc.getNumReligionInfos()):
			szName = "ReligionHolyCityDDS" + str(i)
			screen.hide(szName)
			szName = "ReligionDDS" + str(i)
			screen.hide(szName)
		for i in range(gc.getNumCorporationInfos()):
			szName = "CorporationHeadquarterDDS" + str(i)
			screen.hide(szName)
			szName = "CorporationDDS" + str(i)
			screen.hide(szName)
		for i in range(CommerceTypes.NUM_COMMERCE_TYPES):
			szName = "CityPercentText" + str(i)
			screen.hide(szName)

		screen.addPanel("BonusPane0", u"", u"", True, False,
				xResolution - 244, 94, 57, yResolution - 520,
				PanelStyles.PANEL_STYLE_CITY_COLUMNL)
		screen.hide("BonusPane0")
		screen.addScrollPanel("BonusBack0", u"",
				xResolution - 242, 94, 157, yResolution - 536,
				PanelStyles.PANEL_STYLE_EXTERNAL)
		screen.hide("BonusBack0")

		screen.addPanel("BonusPane1", u"", u"", True, False,
				xResolution - 187, 94, 68, yResolution - 520,
				PanelStyles.PANEL_STYLE_CITY_COLUMNC)
		screen.hide("BonusPane1")
		screen.addScrollPanel("BonusBack1", u"",
				xResolution - 191, 94, 184, yResolution - 536,
				PanelStyles.PANEL_STYLE_EXTERNAL)
		screen.hide("BonusBack1")

		screen.addPanel("BonusPane2", u"", u"", True, False,
				xResolution - 119, 94, 107, yResolution - 520,
				PanelStyles.PANEL_STYLE_CITY_COLUMNR)
		screen.hide("BonusPane2")
		screen.addScrollPanel("BonusBack2", u"",
				xResolution - 125, 94, 205, yResolution - 536,
				PanelStyles.PANEL_STYLE_EXTERNAL)
		screen.hide("BonusBack2")

		screen.hide("TradeRouteTable")
		screen.hide("BuildingListTable")
		screen.hide("BuildingListBackground")
		screen.hide("TradeRouteListBackground")
		screen.hide("BuildingListLabel")
		screen.hide("TradeRouteListLabel")
		for i in range(g_iNumLeftBonus):
			szName = "LeftBonusItem" + str(i)
			screen.hide(szName)
		for i in range(g_iNumCenterBonus):
			szName = "CenterBonusItemLeft" + str(i)
			screen.hide(szName)
			szName = "CenterBonusItemRight" + str(i)
			screen.hide(szName)
		for i in range(g_iNumRightBonus):
			szName = "RightBonusItemLeft" + str(i)
			screen.hide(szName)
			szName = "RightBonusItemRight" + str(i)
			screen.hide(szName)
		for i in range(3):
			szName = "BonusPane" + str(i)
			screen.hide(szName)
			szName = "BonusBack" + str(i)
			screen.hide(szName)

		# advc: Deal with the non-city branch first (to reduce indentation)
		if not CyInterface().isCityScreenUp():
			self.setDefaultHelpTextArea(
					CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_SHOW)

			screen.hide("TopCityPanelCenter")
			# advc: Doesn't exist
			#screen.hide("InterfaceTopRightBackgroundWidget")
			screen.hide("CityLeftPanel")
			screen.hide("CityScreenTopWidget")
			screen.hide("CityNameBackground")
			screen.hide("TopCityPanelLeft")
			screen.hide("TopCityPanelRight")
			screen.hide("CityAdjustPanel")
			screen.hide("CityRightPanel")

			if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
				self.setMinimapButtonVisibility(True)
			return 0
		if not pHeadSelectedCity:
			return 0

		screen.show("TopCityPanelCenter")
		#screen.show("InterfaceTopRightBackgroundWidget")
		screen.show("CityLeftPanel")
		screen.show("CityScreenTopWidget")
		screen.show("CityNameBackground")
		screen.show("TopCityPanelLeft")
		screen.show("TopCityPanelRight")
		screen.show("CityAdjustPanel")
		screen.show("CityRightPanel")

		if (pHeadSelectedCity.getTeam() == gc.getGame().getActiveTeam()):
			if (gc.getActivePlayer().getNumCities() > 1):
				screen.show("CityScrollMinus")
				screen.show("CityScrollPlus")

		screen.setHelpTextArea(390, FontTypes.SMALL_FONT,
				0, 0, -2.2, True,
				ArtFileMgr.getInterfaceArtInfo("POPUPS_BACKGROUND_TRANSPARENT").getPath(),
				True, True,
				CvUtil.FONT_LEFT_JUSTIFY, 0)

		iFoodDifference = pHeadSelectedCity.foodDifference(True)
		iProductionDiffNoFood = pHeadSelectedCity.getCurrentProductionDifference(True, True)
		iProductionDiffJustFood = (pHeadSelectedCity.getCurrentProductionDifference(False, True)
				- iProductionDiffNoFood)

		szBuffer = u"<font=4>"

		if (pHeadSelectedCity.isCapital()):
			szBuffer += u"%c" %(CyGame().getSymbolID(FontSymbols.STAR_CHAR))
		elif (pHeadSelectedCity.isGovernmentCenter()):
			szBuffer += u"%c" %(CyGame().getSymbolID(FontSymbols.SILVER_STAR_CHAR))

		if (pHeadSelectedCity.isPower()):
			szBuffer += u"%c" %(CyGame().getSymbolID(FontSymbols.POWER_CHAR))

		szBuffer += u"%s: %d" %(pHeadSelectedCity.getName(), pHeadSelectedCity.getPopulation())

		if (pHeadSelectedCity.isOccupation()):
			szBuffer += u" (%c:%d)" %(CyGame().getSymbolID(FontSymbols.OCCUPATION_CHAR),
					pHeadSelectedCity.getOccupationTimer())

		szBuffer += u"</font>"

		screen.setText("CityNameText", "Background",
				szBuffer, CvUtil.FONT_CENTER_JUSTIFY,
				screen.centerX(512), 32, -0.3, FontTypes.GAME_FONT,
				WidgetTypes.WIDGET_CITY_NAME, -1, -1)
		screen.setStyle("CityNameText", "Button_Stone_Style")
		screen.show("CityNameText")

# BUG - Food Assist - start
		if (CityUtil.willGrowThisTurn(pHeadSelectedCity) or
				(iFoodDifference != 0) or
				not (pHeadSelectedCity.isFoodProduction())):
			# K-Mod disabled this. I think 'Growth!' sounds lame.
#			if (CityUtil.willGrowThisTurn(pHeadSelectedCity)):
				#was elif on next line
#				szBuffer = localText.getText("INTERFACE_CITY_GROWTH", ())
			if (iFoodDifference > 0):
				# <advc.002f>
				if CityUtil.avoidingGrowth(pHeadSelectedCity):
					szBuffer = localText.getText("INTERFACE_CITY_AVOIDING_GROWTH",
							(pHeadSelectedCity.getFoodTurnsLeft(),))
				else: # </advc.002f>
					szBuffer = localText.getText("INTERFACE_CITY_GROWING",
							(pHeadSelectedCity.getFoodTurnsLeft(),))
			elif (iFoodDifference < 0):
				if (CityScreenOpt.isShowFoodAssist()):
					#iTurnsToStarve = pHeadSelectedCity.getFood() / -iFoodDifference + 1
					# advc.189: The DLL can compute this now
					iTurnsToStarve = -pHeadSelectedCity.getFoodTurnsLeft()
					if iTurnsToStarve > 1:
						szBuffer = localText.getText("INTERFACE_CITY_SHRINKING",
								(iTurnsToStarve,))
					else:
						szBuffer = localText.getText("INTERFACE_CITY_STARVING", ())
				else:
					szBuffer = localText.getText("INTERFACE_CITY_STARVING", ())
# BUG - Food Assist - end
			else:
				szBuffer = localText.getText("INTERFACE_CITY_STAGNANT", ())

			self.setLabel("PopulationText", "Background", szBuffer,
					CvUtil.FONT_CENTER_JUSTIFY, FontTypes.GAME_FONT, -1.3)
			screen.setHitTest("PopulationText", HitTestTypes.HITTEST_NOHIT)
			screen.show("PopulationText")

		if (not pHeadSelectedCity.isDisorder() and
				not pHeadSelectedCity.isFoodProduction()):
# BUG - Food Assist - start
			if (CityScreenOpt.isShowFoodAssist()):
				iFoodYield = pHeadSelectedCity.getYieldRate(YieldTypes.YIELD_FOOD)
				iFoodEaten = pHeadSelectedCity.foodConsumption(False, 0)
				if iFoodYield == iFoodEaten:
					szBuffer = localText.getText("INTERFACE_CITY_FOOD_STAGNATE",
							(iFoodYield, iFoodEaten))
				elif iFoodYield > iFoodEaten:
					szBuffer = localText.getText("INTERFACE_CITY_FOOD_GROW",
							(iFoodYield, iFoodEaten, iFoodYield - iFoodEaten))
				else:
					szBuffer = localText.getText("INTERFACE_CITY_FOOD_SHRINK",
							(iFoodYield, iFoodEaten, iFoodYield - iFoodEaten))
			else:
				szBuffer = u"%d%c - %d%c" %(
						pHeadSelectedCity.getYieldRate(YieldTypes.YIELD_FOOD),
						gc.getYieldInfo(YieldTypes.YIELD_FOOD).getChar(),
						pHeadSelectedCity.foodConsumption(False, 0),
						CyGame().getSymbolID(FontSymbols.EATEN_FOOD_CHAR))
# BUG - Food Assist - end
# BUG - Food Rate Hover - start
			# draw label below
		else:
			szBuffer = u"%d%c" %(iFoodDifference,
					gc.getYieldInfo(YieldTypes.YIELD_FOOD).getChar())
			# draw label below
		# advc.004: BULL widget help enabled
		self.setLabel("PopulationInputText", "Background", szBuffer,
				CvUtil.FONT_RIGHT_JUSTIFY, FontTypes.GAME_FONT, -0.3,
				WidgetTypes.WIDGET_FOOD_MOD_HELP)
		screen.show("PopulationInputText")
# BUG - Food Rate Hover - end
		if (pHeadSelectedCity.badHealth(False) > 0 or
				pHeadSelectedCity.goodHealth() >= 0):
			if (pHeadSelectedCity.healthRate(False, 0) < 0):
				szBuffer = localText.getText(
						"INTERFACE_CITY_HEALTH_BAD",
						(pHeadSelectedCity.goodHealth(),
						pHeadSelectedCity.badHealth(False),
						pHeadSelectedCity.healthRate(False, 0)))
			elif (pHeadSelectedCity.badHealth(False) > 0):
				szBuffer = localText.getText(
						"INTERFACE_CITY_HEALTH_GOOD",
						(pHeadSelectedCity.goodHealth(),
						pHeadSelectedCity.badHealth(False)))
			else:
				szBuffer = localText.getText(
						"INTERFACE_CITY_HEALTH_GOOD_NO_BAD",
						(pHeadSelectedCity.goodHealth(),))
			self.setLabel("HealthText", "Background", szBuffer,
					CvUtil.FONT_LEFT_JUSTIFY, FontTypes.GAME_FONT, -0.3,
					WidgetTypes.WIDGET_HELP_HEALTH)
			screen.show("HealthText")
		if (iFoodDifference < 0):
			if (pHeadSelectedCity.getFood() + iFoodDifference > 0):
				iDeltaFood = pHeadSelectedCity.getFood() + iFoodDifference
			else:
				iDeltaFood = 0
			if (-iFoodDifference < pHeadSelectedCity.getFood()):
				iExtraFood = -iFoodDifference
			else:
				iExtraFood = pHeadSelectedCity.getFood()
			screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_STORED,
					float(iDeltaFood) / pHeadSelectedCity.growthThreshold())
			screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE, 0.0)
			if (pHeadSelectedCity.growthThreshold() > iDeltaFood):
				screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
						float(iExtraFood) / (pHeadSelectedCity.growthThreshold() - iDeltaFood))
			else:
				screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE_EXTRA, 0.0)
		else:
			screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_STORED,
					float(pHeadSelectedCity.getFood()) / pHeadSelectedCity.growthThreshold())
			if (pHeadSelectedCity.growthThreshold() > pHeadSelectedCity.getFood()):
				screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE,
						(float(iFoodDifference) /
						(pHeadSelectedCity.growthThreshold() - pHeadSelectedCity.getFood())))
			else:
				screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE, 0.0)
			screen.setBarPercentage("PopulationBar", InfoBarTypes.INFOBAR_RATE_EXTRA, 0.0)
		screen.show("PopulationBar")
# BUG - Progress Bar - Tick Marks - start
		if MainOpt.isShowBarTickMarks():
			self.pBarPopulationBar.drawTickMarks(screen,
					pHeadSelectedCity.getFood(), pHeadSelectedCity.growthThreshold(),
					iFoodDifference, iFoodDifference, False)
# BUG - Progress Bar - Tick Marks - end
		if (pHeadSelectedCity.getOrderQueueLength() > 0):
			if (pHeadSelectedCity.isProductionProcess()):
				szBuffer = pHeadSelectedCity.getProductionName()
# BUG - Whip Assist - start
			else:
				iProductionTurns = pHeadSelectedCity.getProductionTurnsLeft() # advc.004x
				HURRY_WHIP = gc.getInfoTypeForString("HURRY_POPULATION")
				HURRY_BUY = gc.getInfoTypeForString("HURRY_GOLD")
				if (CityScreenOpt.isShowWhipAssist() and
						pHeadSelectedCity.canHurry(HURRY_WHIP, False)):
					iHurryPop = pHeadSelectedCity.hurryPopulation(HURRY_WHIP)
					'''
					iOverflow = pHeadSelectedCity.hurryProduction(HURRY_WHIP) - pHeadSelectedCity.productionLeft()
					if CityScreenOpt.isWhipAssistOverflowCountCurrentProduction():
						iOverflow += pHeadSelectedCity.getCurrentProductionDifference(False, True)
					iMaxOverflow = max(pHeadSelectedCity.getProductionNeeded(),
							pHeadSelectedCity.getCurrentProductionDifference(False, False))
					iLost = max(0, iOverflow - iMaxOverflow)
					iOverflow = min(iOverflow, iMaxOverflow)
					iItemModifier = pHeadSelectedCity.getProductionModifier()
					iBaseModifier = pHeadSelectedCity.getBaseYieldRateModifier(YieldTypes.YIELD_PRODUCTION, 0)
					iTotalModifier = pHeadSelectedCity.getBaseYieldRateModifier(YieldTypes.YIELD_PRODUCTION, iItemModifier)
					iLost *= iBaseModifier
					iLost /= max(1, iTotalModifier)
					iOverflow = (iBaseModifier * iOverflow) / max(1, iTotalModifier)
					if iLost > 0:
						if pHeadSelectedCity.isProductionUnit():
							iGoldPercent = gc.getDefineINT("MAXED_UNIT_GOLD_PERCENT")
						elif pHeadSelectedCity.isProductionBuilding():
							iGoldPercent = gc.getDefineINT("MAXED_BUILDING_GOLD_PERCENT")
						elif pHeadSelectedCity.isProductionProject():
							iGoldPercent = gc.getDefineINT("MAXED_PROJECT_GOLD_PERCENT")
						else:
							iGoldPercent = 0
						iOverflowGold = iLost * iGoldPercent / 100
					'''
					# <advc.064> Replacing the above by calling C++ code that does almost the same thing
					bCountCurrentOverflow = CityScreenOpt.isWhipAssistOverflowCountCurrentProduction()
					iOverflow = pHeadSelectedCity.getHurryOverflow(
							HURRY_WHIP, True, bCountCurrentOverflow)
					iOverflowGold = pHeadSelectedCity.getHurryOverflow(
							HURRY_WHIP, False, bCountCurrentOverflow)
					if iOverflowGold > 0: # </advc.064>
						# <advc.004x>
						if iProductionTurns <= 0:
							szBuffer = localText.getText("INTERFACE_CITY_NO_PRODUCTION_WHIP_PLUS_GOLD",
									(pHeadSelectedCity.getProductionNameKey(),
									iHurryPop, iOverflow, iOverflowGold))
						else: # </advc.004x>
							szBuffer = localText.getText(
									"INTERFACE_CITY_PRODUCTION_WHIP_PLUS_GOLD",
									(pHeadSelectedCity.getProductionNameKey(), iProductionTurns,
									iHurryPop, iOverflow, iOverflowGold))
					else:
						# <advc.004x>
						if iProductionTurns <= 0:
							szBuffer = localText.getText(
									"INTERFACE_CITY_NO_PRODUCTION_WHIP",
									(pHeadSelectedCity.getProductionNameKey(),
									iHurryPop, iOverflow))
						else: # </advc.004x>
							szBuffer = localText.getText(
									"INTERFACE_CITY_PRODUCTION_WHIP",
									(pHeadSelectedCity.getProductionNameKey(), iProductionTurns,
									iHurryPop, iOverflow))
				elif (CityScreenOpt.isShowWhipAssist() and
						pHeadSelectedCity.canHurry(HURRY_BUY, False)):
					iHurryCost = pHeadSelectedCity.hurryGold(HURRY_BUY)
					# <advc.004x>
					if iProductionTurns <= 0:
						szBuffer = localText.getText(
								"INTERFACE_CITY_NO_PRODUCTION_BUY",
								(pHeadSelectedCity.getProductionNameKey(),
								iHurryCost))
					else: # </advc.004x>
						szBuffer = localText.getText(
								"INTERFACE_CITY_PRODUCTION_BUY",
							(pHeadSelectedCity.getProductionNameKey(), iProductionTurns,
							iHurryCost))
				else:
					# <advc.004x>
					if iProductionTurns <= 0:
						szBuffer = pHeadSelectedCity.getProductionName()
					else: # </advc.004x>
						szBuffer = localText.getText(
								"INTERFACE_CITY_PRODUCTION",
								(pHeadSelectedCity.getProductionNameKey(), iProductionTurns))
# BUG - Whip Assist - end
			self.setLabel("ProductionText", "Background", szBuffer,
					CvUtil.FONT_CENTER_JUSTIFY, FontTypes.GAME_FONT, -1.3,
					WidgetTypes.WIDGET_GENERAL)
			screen.setHitTest("ProductionText", HitTestTypes.HITTEST_NOHIT)
			screen.show("ProductionText")
		if (pHeadSelectedCity.isProductionProcess()):
			szBuffer = u"%d%c" %(pHeadSelectedCity.getYieldRate(
					YieldTypes.YIELD_PRODUCTION),
					gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getChar())
		elif (pHeadSelectedCity.isFoodProduction() and
				iProductionDiffJustFood > 0):
			szBuffer = u"%d%c + %d%c" %(iProductionDiffJustFood,
					gc.getYieldInfo(YieldTypes.YIELD_FOOD).getChar(),
					iProductionDiffNoFood,
					gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getChar())
		else:
			szBuffer = u"%d%c" %(iProductionDiffNoFood,
					gc.getYieldInfo(YieldTypes.YIELD_PRODUCTION).getChar())
		self.setLabel("ProductionInputText", "Background", szBuffer,
				CvUtil.FONT_RIGHT_JUSTIFY, FontTypes.GAME_FONT, -0.3,
				WidgetTypes.WIDGET_PRODUCTION_MOD_HELP)
		screen.show("ProductionInputText")
		if (pHeadSelectedCity.happyLevel() >= 0 or
				pHeadSelectedCity.unhappyLevel(0) > 0):
			if (pHeadSelectedCity.isDisorder()):
				szBuffer = u"%d%c" %(pHeadSelectedCity.angryPopulation(0),
						CyGame().getSymbolID(FontSymbols.ANGRY_POP_CHAR))
			elif (pHeadSelectedCity.angryPopulation(0) > 0):
				szBuffer = localText.getText(
						"INTERFACE_CITY_UNHAPPY",
						(pHeadSelectedCity.happyLevel(),
						pHeadSelectedCity.unhappyLevel(0),
						pHeadSelectedCity.angryPopulation(0)))
			elif (pHeadSelectedCity.unhappyLevel(0) > 0):
				szBuffer = localText.getText(
						"INTERFACE_CITY_HAPPY",
						(pHeadSelectedCity.happyLevel(),
						pHeadSelectedCity.unhappyLevel(0)))
			else:
				szBuffer = localText.getText(
						"INTERFACE_CITY_HAPPY_NO_UNHAPPY",
						(pHeadSelectedCity.happyLevel(),))
# BUG - Anger Display - start
			if (CityScreenOpt.isShowAngerCounter() and
					(pHeadSelectedCity.getTeam() == gc.getGame().getActiveTeam()
					or gc.getGame().isDebugMode())): # K-Mod
				iAngerTimer = max(pHeadSelectedCity.getHurryAngerTimer(),
						pHeadSelectedCity.getConscriptAngerTimer())
				# <advc.188> Cover all temporary unhappiness (but not getHappinessTimer)
				iAngerTimer = max(iAngerTimer,
						pHeadSelectedCity.getDefyResolutionAngerTimer()) # </advc.188>
				if iAngerTimer > 0:
					szBuffer += u" (%i)" % iAngerTimer
# BUG - Anger Display - end
			self.setLabel("HappinessText", "Background", szBuffer,
					CvUtil.FONT_LEFT_JUSTIFY, FontTypes.GAME_FONT, -0.3,
					WidgetTypes.WIDGET_HELP_HAPPINESS)
			screen.show("HappinessText")
		if (not pHeadSelectedCity.isProductionProcess()):
			# advc.064: Moved up
			HURRY_WHIP = gc.getInfoTypeForString("HURRY_POPULATION")
			iNeeded = pHeadSelectedCity.getProductionNeeded()
			iStored = pHeadSelectedCity.getProduction()
			screen.setBarPercentage("ProductionBar",
					InfoBarTypes.INFOBAR_STORED, float(iStored) / iNeeded)
			if iNeeded > iStored:
				screen.setBarPercentage("ProductionBar", InfoBarTypes.INFOBAR_RATE,
						float(iProductionDiffNoFood) / (iNeeded - iStored))
			else:
				screen.setBarPercentage("ProductionBar", InfoBarTypes.INFOBAR_RATE, 0.0)
			if iNeeded > iStored + iProductionDiffNoFood:
				screen.setBarPercentage("ProductionBar", InfoBarTypes.INFOBAR_RATE_EXTRA,
						float(iProductionDiffJustFood) /
						(iNeeded - iStored - iProductionDiffNoFood))
			else:
				screen.setBarPercentage("ProductionBar", InfoBarTypes.INFOBAR_RATE_EXTRA, 0.0)
			screen.show("ProductionBar")
# BUG - Progress Bar - Tick Marks - start
			# advc.064: Check moved down so that HurryTickMarks can be enabled independently
			if True:#MainOpt.isShowBarTickMarks():
				if (pHeadSelectedCity.isProductionProcess()):
					iFirst = 0
					iRate = 0
				elif (pHeadSelectedCity.isFoodProduction() and
						iProductionDiffJustFood > 0):
					iFirst = pHeadSelectedCity.getCurrentProductionDifference(False, True)
					iRate = pHeadSelectedCity.getCurrentProductionDifference(False, False)
				else:
					iFirst = pHeadSelectedCity.getCurrentProductionDifference(True, True)
					iRate = pHeadSelectedCity.getCurrentProductionDifference(True, False)
			if MainOpt.isShowBarTickMarks():
				self.pBarProductionBar.drawTickMarks(screen,
						pHeadSelectedCity.getProduction(),
						pHeadSelectedCity.getProductionNeeded(),
						iFirst, iRate, False)
			# advc.064: Now optional and independent from ShowBarTick
			if (CityScreenOpt.isShowHurryTickMarks() and
					# K-Mod, changed from False to True
					pHeadSelectedCity.canHurry(HURRY_WHIP, True)):
				iRate = (pHeadSelectedCity.hurryProduction(HURRY_WHIP) /
						pHeadSelectedCity.hurryPopulation(HURRY_WHIP))
				# <advc.064b> Subtract guaranteed production
				iMinProduction = (pHeadSelectedCity.minPlotProduction() +
						pHeadSelectedCity.getFeatureProduction()) # </advc.064b>
				self.pBarProductionBar_Whip.drawTickMarks(screen,
						pHeadSelectedCity.getProduction(),
						pHeadSelectedCity.getProductionNeeded()
						- iMinProduction, iFirst, iRate, True)
# BUG - Progress Bar - Tick Marks - end
		iCount = 0
		for i in range(CommerceTypes.NUM_COMMERCE_TYPES):
			eCommerce = (i + 1) % CommerceTypes.NUM_COMMERCE_TYPES
			#if ((gc.getPlayer(pHeadSelectedCity.getOwner()).isCommerceFlexible(eCommerce)) or (eCommerce == CommerceTypes.COMMERCE_GOLD)):
			if self.showCommercePercent(eCommerce, pHeadSelectedCity.getOwner()): # K-Mod
				szBuffer = u"%d.%02d %c" %(pHeadSelectedCity.getCommerceRate(eCommerce),
						pHeadSelectedCity.getCommerceRateTimes100(eCommerce)%100,
						gc.getCommerceInfo(eCommerce).getChar())
				iHappiness = pHeadSelectedCity.getCommerceHappinessByType(eCommerce)
				if (iHappiness != 0):
					if (iHappiness > 0):
						szTempBuffer = u", %d%c" %(iHappiness,
								CyGame().getSymbolID(FontSymbols.HAPPY_CHAR))
					else:
						szTempBuffer = u", %d%c" %(-iHappiness,
								CyGame().getSymbolID(FontSymbols.UNHAPPY_CHAR))
					szBuffer = szBuffer + szTempBuffer
				szName = "CityPercentText" + str(iCount)
				screen.setLabel(szName, "Background",
						szBuffer, CvUtil.FONT_RIGHT_JUSTIFY,
						220, 45 + (19 * iCount) + 4, -0.3,
						FontTypes.SMALL_FONT,
						WidgetTypes.WIDGET_COMMERCE_MOD_HELP, eCommerce, -1)
				screen.show(szName)
				iCount = iCount + 1
		screen.addTableControlGFC("BuildingListTable", 3,
				10, 317, 238, yResolution - 541,
				False, False, 32, 32,
				TableStyles.TABLE_STYLE_STANDARD)
		screen.setStyle("BuildingListTable", "Table_City_Style")
# BUG - Raw Yields - start
		bShowRawYields = g_bYieldView and CityScreenOpt.isShowRawYields()
		if (bShowRawYields):
			screen.addTableControlGFC("TradeRouteTable", 4,
					10, 187, 238, 98,
					False, False, 32, 32,
					TableStyles.TABLE_STYLE_STANDARD)
			screen.setStyle("TradeRouteTable", "Table_City_Style")
			# <advc.002b> Last param was 110 - too narrow
			screen.setTableColumnHeader("TradeRouteTable", 0, u"", 125)
			# Last param was 60
			screen.setTableColumnHeader("TradeRouteTable", 1, u"", 55)
			# Last param was 55
			screen.setTableColumnHeader("TradeRouteTable", 2, u"", 50)
			# Last param was 10
			screen.setTableColumnHeader("TradeRouteTable", 3, u"", 5)
			# </advc.002b>
			screen.setTableColumnRightJustify("TradeRouteTable", 1)
			screen.setTableColumnRightJustify("TradeRouteTable", 2)
		else:
			screen.addTableControlGFC("TradeRouteTable", 3,
					10, 187, 238, 98,
					False, False, 32, 32,
					TableStyles.TABLE_STYLE_STANDARD)
			screen.setStyle("TradeRouteTable", "Table_City_Style")
# K-Mod: Trade culture
			screen.setTableColumnHeader("TradeRouteTable", 0, u"", 128)
			screen.setTableColumnHeader("TradeRouteTable", 1, u"", 98)
# K-Mod: Trade culture end
			screen.setTableColumnHeader("TradeRouteTable", 2, u"", 10)
			screen.setTableColumnRightJustify("TradeRouteTable", 1)
# BUG - Raw Yields - end
		screen.setTableColumnHeader("BuildingListTable", 0, u"", 108)
		screen.setTableColumnHeader("BuildingListTable", 1, u"", 118)
		screen.setTableColumnHeader("BuildingListTable", 2, u"", 10)
		screen.setTableColumnRightJustify("BuildingListTable", 1)

		screen.show("BuildingListBackground")
		screen.show("TradeRouteListBackground")
		screen.show("BuildingListLabel")
# BUG - Raw Yields - start
		if (CityScreenOpt.isShowRawYields()):
			screen.setState("RawYieldsTrade0", not g_bYieldView)
			screen.show("RawYieldsTrade0")

			screen.setState("RawYieldsFood1",
					g_bYieldView and g_iYieldType == YieldTypes.YIELD_FOOD)
			screen.show("RawYieldsFood1")
			screen.setState("RawYieldsProduction2",
					g_bYieldView and g_iYieldType == YieldTypes.YIELD_PRODUCTION)
			screen.show("RawYieldsProduction2")
			screen.setState("RawYieldsCommerce3",
					g_bYieldView and g_iYieldType == YieldTypes.YIELD_COMMERCE)
			screen.show("RawYieldsCommerce3")

			screen.setState("RawYieldsWorkedTiles4",
					g_iYieldTiles == RawYields.WORKED_TILES)
			screen.show("RawYieldsWorkedTiles4")
			screen.setState("RawYieldsCityTiles5",
					g_iYieldTiles == RawYields.CITY_TILES)
			screen.show("RawYieldsCityTiles5")
			screen.setState("RawYieldsOwnedTiles6",
					g_iYieldTiles == RawYields.OWNED_TILES)
			screen.show("RawYieldsOwnedTiles6")
		else:
			screen.show("TradeRouteListLabel")
# BUG - Raw Yields - end
		for i in range(3):
			szName = "BonusPane" + str(i)
			screen.show(szName)
			szName = "BonusBack" + str(i)
			screen.show(szName)
		iNumBuildings = 0
# BUG - Raw Yields - start
		self.yields = RawYields.Tracker()
# BUG - Raw Yields - end
		for i in range(gc.getNumBuildingInfos()):
			if (pHeadSelectedCity.getNumBuilding(i) > 0):
				for k in range(pHeadSelectedCity.getNumBuilding(i)):
					szLeftBuffer = gc.getBuildingInfo(i).getDescription()
					szRightBuffer = u""
					bFirst = True
					if (pHeadSelectedCity.getNumActiveBuilding(i) > 0):
					# K-Mod. I've just swapped the order of health / happiness,
					# to match the DLL hover-text.
						iHappiness = pHeadSelectedCity.getBuildingHappiness(i)
						if (iHappiness != 0):
							if (bFirst == False):
								szRightBuffer = szRightBuffer + ", "
							else:
								bFirst = False
							if (iHappiness > 0):
								szTempBuffer = u"+%d%c" %(iHappiness,
										CyGame().getSymbolID(FontSymbols.HAPPY_CHAR))
								szRightBuffer = szRightBuffer + szTempBuffer
							else:
								szTempBuffer = u"+%d%c" %(-iHappiness,
										CyGame().getSymbolID(FontSymbols.UNHAPPY_CHAR))
								szRightBuffer = szRightBuffer + szTempBuffer
						iHealth = pHeadSelectedCity.getBuildingHealth(i)
						if (iHealth != 0):
							if (bFirst == False):
								szRightBuffer = szRightBuffer + ", "
							else:
								bFirst = False
							if (iHealth > 0):
								szTempBuffer = u"+%d%c" %(iHealth,
										CyGame().getSymbolID(FontSymbols.HEALTHY_CHAR))
								szRightBuffer = szRightBuffer + szTempBuffer
							else:
								szTempBuffer = u"+%d%c" %(-iHealth,
										CyGame().getSymbolID(FontSymbols.UNHEALTHY_CHAR))
								szRightBuffer = szRightBuffer + szTempBuffer
					# K-Mod end
						for j in range(YieldTypes.NUM_YIELD_TYPES):
							iYield = gc.getBuildingInfo(i).getYieldChange(j)
							iYield += (pHeadSelectedCity.getNumBuilding(i) *
									pHeadSelectedCity.getBuildingYieldChange(
									gc.getBuildingInfo(i).getBuildingClassType(), j))
							if (iYield != 0):
								if (bFirst == False):
									szRightBuffer = szRightBuffer + ", "
								else:
									bFirst = False
								if (iYield > 0):
									szTempBuffer = u"%s%d%c" %("+", iYield,
											gc.getYieldInfo(j).getChar())
									szRightBuffer = szRightBuffer + szTempBuffer
								else:
									szTempBuffer = u"%s%d%c" %("", iYield,
											gc.getYieldInfo(j).getChar())
									szRightBuffer = szRightBuffer + szTempBuffer
# BUG - Raw Yields - start
								self.yields.addBuilding(j, iYield)
# BUG - Raw Yields - end
					for j in range(CommerceTypes.NUM_COMMERCE_TYPES):
						iCommerce = pHeadSelectedCity.getBuildingCommerceByBuilding(j, i)
						iCommerce /= pHeadSelectedCity.getNumBuilding(i)
						if (iCommerce != 0):
							if (bFirst == False):
								szRightBuffer = szRightBuffer + ", "
							else:
								bFirst = False
							if (iCommerce > 0):
								szTempBuffer = u"%s%d%c" %("+", iCommerce,
										gc.getCommerceInfo(j).getChar())
								szRightBuffer = szRightBuffer + szTempBuffer
							else:
								szTempBuffer = u"%s%d%c" %("", iCommerce,
										gc.getCommerceInfo(j).getChar())
								szRightBuffer = szRightBuffer + szTempBuffer
					szBuffer = szLeftBuffer + "  " + szRightBuffer
					screen.appendTableRow("BuildingListTable")
					screen.setTableText("BuildingListTable", 0, iNumBuildings,
							"<font=1>" + szLeftBuffer + "</font>", "",
							WidgetTypes.WIDGET_HELP_BUILDING, i, -1,
							CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("BuildingListTable", 1, iNumBuildings,
							"<font=1>" + szRightBuffer + "</font>", "",
							WidgetTypes.WIDGET_HELP_BUILDING, i, -1,
							CvUtil.FONT_RIGHT_JUSTIFY)
					iNumBuildings = iNumBuildings + 1
		# advc: unused
		#if (iNumBuildings > g_iNumBuildings):
		#	g_iNumBuildings = iNumBuildings
		iNumTradeRoutes = 0
		for i in range(gc.getDefineINT("MAX_TRADE_ROUTES")):
			pLoopCity = pHeadSelectedCity.getTradeCity(i)
			if (pLoopCity and pLoopCity.getOwner() >= 0):
				player = gc.getPlayer(pLoopCity.getOwner())
				szLeftBuffer = u"<color=%d,%d,%d,%d>%s</color>" %(
						player.getPlayerTextColorR(), player.getPlayerTextColorG(),
						player.getPlayerTextColorB(), player.getPlayerTextColorA(),
						pLoopCity.getName())
				szRightBuffer = u""
				for j in range(YieldTypes.NUM_YIELD_TYPES):
# BUG - Fractional Trade - start
					iTradeProfit = TradeUtil.calculateTradeRouteYield(
							pHeadSelectedCity, i, j)
					if (iTradeProfit != 0):
						if (iTradeProfit > 0):
							if TradeUtil.isFractionalTrade():
								szTempBuffer = u"%s%d.%02d%c" %(
										"+", iTradeProfit // 100,
										iTradeProfit % 100,
										gc.getYieldInfo(j).getChar())
							else:
								szTempBuffer = u"%s%d%c" %(
										"+", iTradeProfit,
										gc.getYieldInfo(j).getChar())
							szRightBuffer = szRightBuffer + szTempBuffer
						else:
							if TradeUtil.isFractionalTrade():
								szTempBuffer = u"%s%d.%02d%c" %(
										"", iTradeProfit // 100,
										iTradeProfit % 100,
										gc.getYieldInfo(j).getChar())
							else:
								szTempBuffer = u"%s%d%c" %(
										"", iTradeProfit,
										gc.getYieldInfo(j).getChar())
							szRightBuffer = szRightBuffer + szTempBuffer
# BUG - Fractional Trade - end
# BUG - Raw Yields - start
						if (j == YieldTypes.YIELD_COMMERCE):
							if pHeadSelectedCity.getTeam() == pLoopCity.getTeam():
								self.yields.addDomesticTrade(iTradeProfit)
							else:
								self.yields.addForeignTrade(iTradeProfit)
# K-Mod: Trade culture
				iTradeCultureTimes100 = pLoopCity.getTradeCultureRateTimes100(
						pHeadSelectedCity.getCultureLevel())
				# advc.125:
				if (iTradeCultureTimes100 >= 20 and
						gc.getDefineINT("USE_KMOD_TRADE_CULTURE") != 0):
					szTradeCultureBuffer = u"%s%.1f%c" %(
							"+", iTradeCultureTimes100/100.0,
							gc.getCommerceInfo(CommerceTypes.COMMERCE_CULTURE).getChar())
					szRightBuffer = szRightBuffer + szTradeCultureBuffer
# K-Mod: Trade culture end
				if (not bShowRawYields):
					screen.appendTableRow("TradeRouteTable")
					screen.setTableText("TradeRouteTable", 0, iNumTradeRoutes,
							"<font=1>" + szLeftBuffer + "</font>", "",
							WidgetTypes.WIDGET_HELP_TRADE_ROUTE_CITY, i, -1,
							CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("TradeRouteTable", 1, iNumTradeRoutes,
							"<font=1>" + szRightBuffer + "</font>", "",
							WidgetTypes.WIDGET_HELP_TRADE_ROUTE_CITY, i, -1,
							CvUtil.FONT_RIGHT_JUSTIFY)
# BUG - Raw Yields - end
				iNumTradeRoutes = iNumTradeRoutes + 1
		# advc: unused
		#if (iNumTradeRoutes > g_iNumTradeRoutes):
		#	g_iNumTradeRoutes = iNumTradeRoutes
		iLeftCount = 0
		iCenterCount = 0
		iRightCount = 0
		for i in range(gc.getNumBonusInfos()):
			bHandled = False
			if (pHeadSelectedCity.hasBonus(i)):
				iHealth = pHeadSelectedCity.getBonusHealth(i)
				iHappiness = pHeadSelectedCity.getBonusHappiness(i)
				szBuffer = u""
				szLeadBuffer = u""
				szTempBuffer = u"<font=1>%c" %(gc.getBonusInfo(i).getChar())
				szLeadBuffer = szLeadBuffer + szTempBuffer
				if (pHeadSelectedCity.getNumBonuses(i) > 1):
					szTempBuffer = u"(%d)" %(pHeadSelectedCity.getNumBonuses(i))
					szLeadBuffer = szLeadBuffer + szTempBuffer
				szLeadBuffer = szLeadBuffer + "</font>"
				if (iHappiness != 0):
					if (iHappiness > 0):
						szTempBuffer = u"<font=1>+%d%c</font>" %(iHappiness,
								CyGame().getSymbolID(FontSymbols.HAPPY_CHAR))
					else:
						szTempBuffer = u"<font=1>+%d%c</font>" %(-iHappiness,
								CyGame().getSymbolID(FontSymbols.UNHAPPY_CHAR))
					if (iHealth > 0):
						szTempBuffer += u"<font=1>, +%d%c</font>" %(iHealth,
								CyGame().getSymbolID(FontSymbols.HEALTHY_CHAR))
					szName = "RightBonusItemLeft" + str(iRightCount)
					screen.setLabelAt(szName, "BonusBack2", szLeadBuffer,
							CvUtil.FONT_LEFT_JUSTIFY, 0, (iRightCount * 20) + 4,
							-0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_PEDIA_JUMP_TO_BONUS, i, -1)
					szName = "RightBonusItemRight" + str(iRightCount)
					screen.setLabelAt(szName, "BonusBack2", szTempBuffer,
							CvUtil.FONT_RIGHT_JUSTIFY, 102, (iRightCount * 20) + 4,
							-0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_PEDIA_JUMP_TO_BONUS, i, -1)
					iRightCount = iRightCount + 1
					bHandled = True
				if (iHealth != 0 and bHandled == False):
					if (iHealth > 0):
						szTempBuffer = u"<font=1>+%d%c</font>" %(iHealth,
								CyGame().getSymbolID(FontSymbols.HEALTHY_CHAR))
					else:
						szTempBuffer = u"<font=1>+%d%c</font>" %(-iHealth,
								CyGame().getSymbolID(FontSymbols.UNHEALTHY_CHAR))
					szName = "CenterBonusItemLeft" + str(iCenterCount)
					screen.setLabelAt(szName, "BonusBack1", szLeadBuffer,
							CvUtil.FONT_LEFT_JUSTIFY, 0, (iCenterCount * 20) + 4,
							-0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_PEDIA_JUMP_TO_BONUS, i, -1)
					szName = "CenterBonusItemRight" + str(iCenterCount)
					screen.setLabelAt(szName, "BonusBack1", szTempBuffer,
							CvUtil.FONT_RIGHT_JUSTIFY, 62, (iCenterCount * 20) + 4,
							-0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_PEDIA_JUMP_TO_BONUS, i, -1)
					iCenterCount = iCenterCount + 1
					bHandled = True
				szBuffer = u""
				if (not bHandled):
					szName = "LeftBonusItem" + str(iLeftCount)
					screen.setLabelAt(szName, "BonusBack0", szLeadBuffer,
							CvUtil.FONT_LEFT_JUSTIFY, 0, (iLeftCount * 20) + 4,
							-0.1, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_PEDIA_JUMP_TO_BONUS, i, -1)
					iLeftCount = iLeftCount + 1
					bHandled = True
		g_iNumLeftBonus = iLeftCount
		g_iNumCenterBonus = iCenterCount
		g_iNumRightBonus = iRightCount
		iMaintenance = pHeadSelectedCity.getMaintenanceTimes100()
		# <K-Mod>
		iMaintenance *= 100 + gc.getPlayer(
				pHeadSelectedCity.getOwner()).calculateInflationRate()
		iMaintenance /= 100 # </K-Mod>
		szBuffer = localText.getText("INTERFACE_CITY_MAINTENANCE", ())
		screen.setLabel("MaintenanceText", "Background", szBuffer,
				CvUtil.FONT_LEFT_JUSTIFY, 15, 126,
				-0.3, FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_HELP_MAINTENANCE, -1, -1)
		screen.show("MaintenanceText")
		szBuffer = u"-%d.%02d %c" %(iMaintenance/100, iMaintenance%100,
				gc.getCommerceInfo(CommerceTypes.COMMERCE_GOLD).getChar())
		screen.setLabel("MaintenanceAmountText", "Background", szBuffer,
				CvUtil.FONT_RIGHT_JUSTIFY, 220, 125,
				-0.3, FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_HELP_MAINTENANCE, -1, -1)
		screen.show("MaintenanceAmountText")
# BUG - Raw Yields - start
		if (bShowRawYields):
			self.yields.processCity(pHeadSelectedCity)
			self.yields.fillTable(screen, "TradeRouteTable", g_iYieldType, g_iYieldTiles)
# BUG - Raw Yields - end
		szBuffer = u""
# BUG - Limit/Extra Religions - start
		if CityScreenOpt.isShowOnlyPresentReligions():
			lReligions = ReligionUtil.getCityReligions(pHeadSelectedCity)
			iCountReligions = len(lReligions)
			iMaxWidth = 250#228
			iMaxButtons = iCountReligions
			# advc: Clutter moved into function
			(iButtonSize, iButtonSpace, iMaxButtons) = self.orgButtonLayout(
					iCountReligions, iMaxWidth, iMaxButtons)
			for ii in range(iCountReligions):
				i = lReligions[ii]
				xCoord = xResolution - 242 + ((ii % iMaxButtons) *
						(iButtonSize + iButtonSpace))
				#xCoord = xResolution - 242 + (i * 34) # Origional Civ4 Code
				yCoord = 42 + iButtonSize * (ii // iMaxButtons)
				#yCoord = 42 # Origional Civ4 Code

				bEnable = True
				# <advc> Commented out all code that only adds to szBuffer
				# b/c that string is never used. (Already unused in Vanilla Civ 4.)
				'''
				if (pHeadSelectedCity.isHolyCityByType(i)):
					szTempBuffer = u"%c" %(gc.getReligionInfo(i).getHolyCityChar())
					# < 47 Religions Mod Start >
					# This is now done below since the Holy City Overlay has to be added
					# after the Religion Icon and can not be shown before its added
					#szName = "ReligionHolyCityDDS" + str(i)
					#screen.show(szName)
					# < 47 Religions Mod Start >
				else:
					szTempBuffer = u"%c" %(gc.getReligionInfo(i).getChar())
				szBuffer = szBuffer + szTempBuffer
				for j in range(CommerceTypes.NUM_COMMERCE_TYPES):
					iCommerce = pHeadSelectedCity.getReligionCommerceByReligion(j, i)
					if (iCommerce != 0):
						if (iCommerce > 0):
							szTempBuffer = u",%s%d%c" %("+", iCommerce, gc.getCommerceInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
						else:
							szTempBuffer = u",%s%d%c" %("", iCommerce, gc.getCommerceInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
				iHappiness = pHeadSelectedCity.getReligionHappiness(i)
				if (iHappiness != 0):
					if (iHappiness > 0):
						szTempBuffer = u",+%d%c" %(iHappiness, CyGame().getSymbolID(FontSymbols.HAPPY_CHAR))
						szBuffer = szBuffer + szTempBuffer
					else:
						szTempBuffer = u",+%d%c" %(-(iHappiness), CyGame().getSymbolID(FontSymbols.UNHAPPY_CHAR))
						szBuffer = szBuffer + szTempBuffer
				szBuffer = szBuffer + " "
				'''
				szButton = gc.getReligionInfo(i).getButton()
				szName = "ReligionDDS" + str(i)
				screen.setImageButton(szName, szButton,
						xCoord, yCoord, iButtonSize, iButtonSize,
						WidgetTypes.WIDGET_HELP_RELIGION_CITY, i, -1)
				screen.enable(szName, bEnable)
				screen.show(szName)
				# Holy City Overlay
				if (pHeadSelectedCity.isHolyCityByType(i)):
					szName = "ReligionHolyCityDDS" + str(i)
					screen.addDDSGFC(szName,
							ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(),
							xCoord, yCoord, iButtonSize, iButtonSize,
							WidgetTypes.WIDGET_HELP_RELIGION_CITY, i, -1)
					screen.show(szName)
		else: # (show all religions)
			for i in range(gc.getNumReligionInfos()):
				xCoord = xResolution - 242 + (i * 34)
				yCoord = 42
				bEnable = True
				if (pHeadSelectedCity.isHasReligion(i)):
					# <advc>
					if (pHeadSelectedCity.isHolyCityByType(i)):
						#szTempBuffer = u"%c" %(gc.getReligionInfo(i).getHolyCityChar())
						szName = "ReligionHolyCityDDS" + str(i)
						screen.show(szName)
					# </advc> szBuffer code commented out (see advc comment above)
					'''
					else:
						szTempBuffer = u"%c" %(gc.getReligionInfo(i).getChar())
					szBuffer = szBuffer + szTempBuffer
					for j in range(CommerceTypes.NUM_COMMERCE_TYPES):
						iCommerce = pHeadSelectedCity.getReligionCommerceByReligion(j, i)
						if (iCommerce != 0):
							if (iCommerce > 0):
								szTempBuffer = u",%s%d%c" %("+", iCommerce, gc.getCommerceInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
							else:
								szTempBuffer = u",%s%d%c" %("", iCommerce, gc.getCommerceInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
					iHappiness = pHeadSelectedCity.getReligionHappiness(i)
					if (iHappiness != 0):
						if (iHappiness > 0):
							szTempBuffer = u",+%d%c" %(iHappiness, CyGame().getSymbolID(FontSymbols.HAPPY_CHAR))
							szBuffer = szBuffer + szTempBuffer
						else:
							szTempBuffer = u",+%d%c" %(-(iHappiness), CyGame().getSymbolID(FontSymbols.UNHAPPY_CHAR))
							szBuffer = szBuffer + szTempBuffer
					szBuffer = szBuffer + " "
					'''
					szButton = gc.getReligionInfo(i).getButton()
				else:
					bEnable = False
					szButton = gc.getReligionInfo(i).getButton()
				szName = "ReligionDDS" + str(i)
				screen.setImageButton(szName, szButton,
						xCoord, yCoord, 24, 24,
						WidgetTypes.WIDGET_HELP_RELIGION_CITY, i, -1)
				screen.enable(szName, bEnable)
				screen.show(szName)
				if (pHeadSelectedCity.isHolyCityByType(i)):
					szName = "ReligionHolyCityDDS" + str(i)
					screen.addDDSGFC(szName,
							ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(),
							xCoord, yCoord, 24, 24,
							WidgetTypes.WIDGET_HELP_RELIGION_CITY, i, -1)
					screen.show(szName)
# BUG - Limit/Extra Religions - end
# BUG - Limit/Extra Corporations - start
		if CityScreenOpt.isShowOnlyPresentCorporations():
			lCorporations = []
			for i in range(gc.getNumCorporationInfos()):
				if (not pHeadSelectedCity.isHasCorporation(i)):
					continue
				lCorporations += [i]
			iCountCorporations = len(lCorporations)
			iMaxWidth = 250#228
			iMaxButtons = iCountCorporations
			# advc: Duplicated clutter moved into function
			(iButtonSize, iButtonSpace, iMaxButtons) = self.orgButtonLayout(
					iCountCorporations, iMaxWidth, iMaxButtons)
			for ii in range(iCountCorporations):
				i = lCorporations[ii]
				xCoord = xResolution - 242 + ((ii % iMaxButtons) *
						(iButtonSize + iButtonSpace))
				#xCoord = xResolution - 242 + (i * 34) # Origional Civ4 Code
				yCoord = 66 + iButtonSize * (ii // iMaxButtons)
				#yCoord = 66 # Origional Civ4 Code
				bEnable = True
				# advc: szBuffer code commented out (see advc comment above)
				'''
				if (pHeadSelectedCity.isHeadquartersByType(i)):
					szTempBuffer = u"%c" %(gc.getCorporationInfo(i).getHeadquarterChar())
					szName = "CorporationHeadquarterDDS" + str(i)
					screen.show(szName)
				else:
					szTempBuffer = u"%c" %(gc.getCorporationInfo(i).getChar())
				szBuffer = szBuffer + szTempBuffer
				for j in range(YieldTypes.NUM_YIELD_TYPES):
					iYield = pHeadSelectedCity.getCorporationYieldByCorporation(j, i)
					if (iYield != 0):
						if (iYield > 0):
							szTempBuffer = u",%s%d%c" %("+", iYield, gc.getYieldInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
						else:
							szTempBuffer = u",%s%d%c" %("", iYield, gc.getYieldInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
				for j in range(CommerceTypes.NUM_COMMERCE_TYPES):
					iCommerce = pHeadSelectedCity.getCorporationCommerceByCorporation(j, i)
					if (iCommerce != 0):
						if (iCommerce > 0):
							szTempBuffer = u",%s%d%c" %("+", iCommerce, gc.getCommerceInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
						else:
							szTempBuffer = u",%s%d%c" %("", iCommerce, gc.getCommerceInfo(j).getChar())
							szBuffer = szBuffer + szTempBuffer
				szBuffer += " "
				'''
				szButton = gc.getCorporationInfo(i).getButton()
				szName = "CorporationDDS" + str(i)
				screen.setImageButton(szName, szButton,
						xCoord, yCoord, iButtonSize, iButtonSize,
						WidgetTypes.WIDGET_HELP_CORPORATION_CITY, i, -1)
				screen.enable(szName, bEnable)
				screen.show(szName)
				# Holy City Overlay
				if (pHeadSelectedCity.isHeadquartersByType(i)):
					szName = "CorporationHeadquarterDDS" + str(i)
					screen.addDDSGFC(szName,
							ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(),
							xCoord, yCoord, iButtonSize, iButtonSize,
							WidgetTypes.WIDGET_HELP_CORPORATION_CITY, i, -1)
					screen.show(szName)
		else: # (show all corps)
			for i in range(gc.getNumCorporationInfos()):
				xCoord = xResolution - 242 + (i * 34)
				yCoord = 66
				bEnable = True
				if (pHeadSelectedCity.isHasCorporation(i)):
					# <advc>
					if (pHeadSelectedCity.isHeadquartersByType(i)):
						#szTempBuffer = u"%c" %(gc.getCorporationInfo(i).getHeadquarterChar())
						szName = "CorporationHeadquarterDDS" + str(i)
						screen.show(szName)
					# </advc> szBuffer code commented out (see advc comment above)
					'''
					else:
						szTempBuffer = u"%c" %(gc.getCorporationInfo(i).getChar())
					szBuffer = szBuffer + szTempBuffer
					for j in range(YieldTypes.NUM_YIELD_TYPES):
						iYield = pHeadSelectedCity.getCorporationYieldByCorporation(j, i)
						if (iYield != 0):
							if (iYield > 0):
								szTempBuffer = u",%s%d%c" %("+", iYield, gc.getYieldInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
							else:
								szTempBuffer = u",%s%d%c" %("", iYield, gc.getYieldInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
					for j in range(CommerceTypes.NUM_COMMERCE_TYPES):
						iCommerce = pHeadSelectedCity.getCorporationCommerceByCorporation(j, i)
						if (iCommerce != 0):
							if (iCommerce > 0):
								szTempBuffer = u",%s%d%c" %("+", iCommerce, gc.getCommerceInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
							else:
								szTempBuffer = u",%s%d%c" %("", iCommerce, gc.getCommerceInfo(j).getChar())
								szBuffer = szBuffer + szTempBuffer
					szBuffer += " "
					'''
					szButton = gc.getCorporationInfo(i).getButton()
				else:
					bEnable = False
					szButton = gc.getCorporationInfo(i).getButton()
				szName = "CorporationDDS" + str(i)
				screen.setImageButton(szName, szButton,
						xCoord, yCoord, 24, 24,
						WidgetTypes.WIDGET_HELP_CORPORATION_CITY, i, -1)
				screen.enable(szName, bEnable)
				screen.show(szName)
				if (pHeadSelectedCity.isHeadquartersByType(i)):
					szName = "CorporationHeadquarterDDS" + str(i)
					screen.addDDSGFC(szName,
							ArtFileMgr.getInterfaceArtInfo("INTERFACE_HOLYCITY_OVERLAY").getPath(),
							xCoord, yCoord, 24, 24,
							WidgetTypes.WIDGET_HELP_CORPORATION_CITY, i, -1)
					screen.show(szName)
# BUG - Limit/Extra Corporations - end
		szBuffer = u"%d%% %s" %(
				pHeadSelectedCity.plot().calculateCulturePercent(pHeadSelectedCity.getOwner()),
				gc.getPlayer(pHeadSelectedCity.getOwner()).getCivilizationAdjective(0))
		screen.setLabel("NationalityText", "Background", szBuffer,
				CvUtil.FONT_CENTER_JUSTIFY, 125, yResolution - 210,
				-0.3, FontTypes.SMALL_FONT,
				WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.setHitTest("NationalityText", HitTestTypes.HITTEST_NOHIT)
		screen.show("NationalityText")
		iRemainder = 100
		iWhichBar = 0
		players = list()
		# <advc.099> Replaced "Alive" with "EverAlive"
		# Moreover, it turns out that setStackedBarColorsRGB will
		# stack at most 4 bars, and that happens outside the SDK.
		# The best one can do is to start with the longest bars.
		for h in range(gc.getMAX_PLAYERS()):
			if not gc.getPlayer(h).isEverAlive():
				continue
			iPercent = pHeadSelectedCity.plot().calculateCulturePercent(h)
			if iPercent <= 0:
				continue
			players.append((h, iPercent))
		players = sorted(players, key=lambda x: x[1], reverse=True)
		for (h, iPercent) in players: # </advc.099>
			screen.setStackedBarColorsRGB("NationalityBar", iWhichBar,
					gc.getPlayer(h).getPlayerTextColorR(),
					gc.getPlayer(h).getPlayerTextColorG(),
					gc.getPlayer(h).getPlayerTextColorB(),
					gc.getPlayer(h).getPlayerTextColorA())
			if (iRemainder <= 0):
				screen.setBarPercentage("NationalityBar", iWhichBar, 0.0)
			else:
				screen.setBarPercentage("NationalityBar", iWhichBar,
						float(iPercent) / iRemainder)
			iRemainder -= iPercent
			iWhichBar += 1
		screen.show("NationalityBar")
		iDefenseModifier = pHeadSelectedCity.getDefenseModifier(False)
		if (iDefenseModifier != 0):
			szBuffer = localText.getText("TXT_KEY_MAIN_CITY_DEFENSE",
					(CyGame().getSymbolID(FontSymbols.DEFENSE_CHAR), iDefenseModifier))
			if (pHeadSelectedCity.getDefenseDamage() > 0):
				szTempBuffer = u" (%d%%)" %(
						((gc.getMAX_CITY_DEFENSE_DAMAGE() - pHeadSelectedCity.getDefenseDamage()) * 100) /
						gc.getMAX_CITY_DEFENSE_DAMAGE())
				szBuffer = szBuffer + szTempBuffer
			szNewBuffer = "<font=4>"
			szNewBuffer = szNewBuffer + szBuffer
			szNewBuffer = szNewBuffer + "</font>"
			screen.setLabel("DefenseText", "Background", szBuffer,
					CvUtil.FONT_RIGHT_JUSTIFY, xResolution - 270, 40,
					-0.3, FontTypes.SMALL_FONT,
					WidgetTypes.WIDGET_HELP_DEFENSE, -1, -1)
			screen.show("DefenseText")
		# advc.001: Left side was missing empty parentheses
		if (pHeadSelectedCity.getCultureLevel() != CultureLevelTypes.NO_CULTURELEVEL):
			iRate = pHeadSelectedCity.getCommerceRateTimes100(CommerceTypes.COMMERCE_CULTURE)
			if (iRate%100 == 0):
				szBuffer = localText.getText(
						"INTERFACE_CITY_COMMERCE_RATE",
						(gc.getCommerceInfo(CommerceTypes.COMMERCE_CULTURE).getChar(),
						gc.getCultureLevelInfo(pHeadSelectedCity.getCultureLevel()).getTextKey(),
						iRate/100))
			else:
				szRate = u"+%d.%02d" % (iRate/100, iRate%100)
				szBuffer = localText.getText(
						"INTERFACE_CITY_COMMERCE_RATE_FLOAT",
						(gc.getCommerceInfo(CommerceTypes.COMMERCE_CULTURE).getChar(),
						gc.getCultureLevelInfo(pHeadSelectedCity.getCultureLevel()).getTextKey(),
						szRate))
# BUG - Culture Turns - start
			#if CityScreenOpt.isShowCultureTurns() and iRate > 0:
			if iRate > 0: # advc.065: No longer optional
				iCultureTimes100 = pHeadSelectedCity.getCultureTimes100(
						pHeadSelectedCity.getOwner())
				iCultureLeftTimes100 = 100 * pHeadSelectedCity.getCultureThreshold() - iCultureTimes100
				# K-Mod: (don't display a negative countdown when we pass legendary culture)
				if iCultureLeftTimes100 > 0:
					szBuffer += u" " + localText.getText(
							"INTERFACE_CITY_TURNS",
							(((iCultureLeftTimes100 + iRate - 1) / iRate),))
# BUG - Culture Turns - end
			screen.setLabel("CultureText", "Background", szBuffer,
					CvUtil.FONT_CENTER_JUSTIFY, 125, yResolution - 184,
					-1.3, FontTypes.GAME_FONT,
					WidgetTypes.WIDGET_GENERAL, -1, -1)
			screen.setHitTest("CultureText", HitTestTypes.HITTEST_NOHIT)
			screen.show("CultureText")
		if (pHeadSelectedCity.getGreatPeopleProgress() > 0 or
				pHeadSelectedCity.getGreatPeopleRate() > 0):
# BUG - Great Person Turns - start
			iRate = pHeadSelectedCity.getGreatPeopleRate()
			if CityScreenOpt.isShowCityGreatPersonInfo():
				iGPTurns = GPUtil.getCityTurns(pHeadSelectedCity)
				szBuffer = GPUtil.getGreatPeopleText(pHeadSelectedCity, iGPTurns,
						230, MainOpt.isGPBarTypesNone(), MainOpt.isGPBarTypesOne(), False)
			else:
				szBuffer = localText.getText("INTERFACE_CITY_GREATPEOPLE_RATE",
						(CyGame().getSymbolID(FontSymbols.GREAT_PEOPLE_CHAR),
						pHeadSelectedCity.getGreatPeopleRate()))
				if CityScreenOpt.isShowGreatPersonTurns() and iRate > 0:
					iGPTurns = GPUtil.getCityTurns(pHeadSelectedCity)
					szBuffer += u" " + localText.getText(
							"INTERFACE_CITY_TURNS", (iGPTurns,))
# BUG - Great Person Turns - end
			screen.setLabel("GreatPeopleText", "Background", szBuffer,
					CvUtil.FONT_CENTER_JUSTIFY, xResolution - 126, yResolution - 182,
					-1.3, FontTypes.GAME_FONT,
					WidgetTypes.WIDGET_GENERAL, -1, -1)
			screen.setHitTest("GreatPeopleText", HitTestTypes.HITTEST_NOHIT)
			screen.show("GreatPeopleText")
			# <advc> Refactored a bit
			fFirst = float(pHeadSelectedCity.getGreatPeopleProgress())
			fFirst /= gc.getPlayer(pHeadSelectedCity.getOwner()).greatPeopleThreshold(False)
			screen.setBarPercentage("GreatPeopleBar",
					InfoBarTypes.INFOBAR_STORED, fFirst)
			fProgress = float(pHeadSelectedCity.getGreatPeopleRate())
			fProgress /= gc.getPlayer(pHeadSelectedCity.getOwner()).greatPeopleThreshold(False)
			if fFirst < 1:
				fProgress /= (1 - fFirst)
			screen.setBarPercentage("GreatPeopleBar", InfoBarTypes.INFOBAR_RATE, fProgress)
			screen.show("GreatPeopleBar")
		fFirst = float(pHeadSelectedCity.getCultureTimes100(pHeadSelectedCity.getOwner()))
		fFirst /= 100 * pHeadSelectedCity.getCultureThreshold()
		screen.setBarPercentage("CultureBar", InfoBarTypes.INFOBAR_STORED, fFirst)
		fProgress = float(pHeadSelectedCity.getCommerceRate(CommerceTypes.COMMERCE_CULTURE))
		fProgress /= pHeadSelectedCity.getCultureThreshold()
		if fFirst < 1:
			fProgress /= (1 - fFirst) # </advc>
		screen.setBarPercentage("CultureBar", InfoBarTypes.INFOBAR_RATE, fProgress)
		screen.show("CultureBar")

		return 0

	# Will update the info pane strings
	def updateInfoPaneStrings(self):
		iRow = 0
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		pHeadSelectedCity = CyInterface().getHeadSelectedCity()
		pHeadSelectedUnit = CyInterface().getHeadSelectedUnit()
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		bShift = CyInterface().shiftKey()

		screen.addPanel("SelectedUnitPanel", u"", u"", True, False,
				8, yResolution - 140, 280, 130,
				PanelStyles.PANEL_STYLE_STANDARD)
		screen.setStyle("SelectedUnitPanel", "Panel_Game_HudStat_Style")
		screen.hide("SelectedUnitPanel")

		screen.addTableControlGFC("SelectedUnitText", 3,
				10, yResolution - 109, 183, 102,
				False, False, 32, 32,
				TableStyles.TABLE_STYLE_STANDARD)
		screen.setStyle("SelectedUnitText", "Table_EmptyScroll_Style")
		screen.hide("SelectedUnitText")
		screen.hide("SelectedUnitLabel")

		screen.addTableControlGFC("SelectedCityText", 3,
				10, yResolution - 139, 183, 128,
				False, False, 32, 32,
				TableStyles.TABLE_STYLE_STANDARD)
		screen.setStyle("SelectedCityText", "Table_EmptyScroll_Style")
		screen.hide("SelectedCityText")

		for i in range(gc.getNumPromotionInfos()):
			szName = "PromotionButton" + str(i)
			screen.hide(szName)
# BUG - Stack Promotions - start
			szName = "PromotionButtonCircle" + str(i)
			screen.hide(szName)
			szName = "PromotionButtonCount" + str(i)
			screen.hide(szName)
# BUG - Stack Promotions - end

		if CyEngine().isGlobeviewUp():
			return 0

		if (pHeadSelectedCity):
			iOrders = CyInterface().getNumOrdersQueued()
			screen.setTableColumnHeader("SelectedCityText", 0, u"", 121)
			screen.setTableColumnHeader("SelectedCityText", 1, u"", 54)
			screen.setTableColumnHeader("SelectedCityText", 2, u"", 10)
			screen.setTableColumnRightJustify("SelectedCityText", 1)
			for i in range(iOrders):
				szLeftBuffer = u""
				szRightBuffer = u""
				if (CyInterface().getOrderNodeType(i) == OrderTypes.ORDER_TRAIN):
					szLeftBuffer = gc.getUnitInfo(
							CyInterface().getOrderNodeData1(i)).getDescription()
					iProductionTurns = pHeadSelectedCity.getUnitProductionTurnsLeft(
							CyInterface().getOrderNodeData1(i), i)
					if iProductionTurns > 0: # advc.004x
						szRightBuffer = "(" + str(iProductionTurns) + ")"
					if (CyInterface().getOrderNodeSave(i)):
						szLeftBuffer = u"*" + szLeftBuffer
# BUG - Production Started - start
					if CityScreenOpt.isShowProductionStarted():
						eUnit = CyInterface().getOrderNodeData1(i)
						if pHeadSelectedCity.getUnitProduction(eUnit) > 0:
							szRightBuffer = BugUtil.colorText(szRightBuffer, "COLOR_CYAN")
# BUG - Production Started - end
# BUG - Production Decay - start
					# advc.094: BugDll.isPresent check removed; active player check added
					# (replacing a is-human check in the DLL).
					if (CityScreenOpt.isShowProductionDecayQueue() and
							pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer()):
						eUnit = CyInterface().getOrderNodeData1(i)
						if pHeadSelectedCity.getUnitProduction(eUnit) > 0:
							if pHeadSelectedCity.isUnitProductionDecay(eUnit):
								szLeftBuffer = BugUtil.getText(
										"TXT_KEY_BUG_PRODUCTION_DECAY_THIS_TURN",
										(szLeftBuffer,))
							elif pHeadSelectedCity.getUnitProductionTime(eUnit) > 0:
								iDecayTurns = pHeadSelectedCity.getUnitProductionDecayTurns(eUnit)
								if iDecayTurns <= CityScreenOpt.getProductionDecayQueueUnitThreshold():
									szLeftBuffer = BugUtil.getText(
											"TXT_KEY_BUG_PRODUCTION_DECAY_WARNING",
											(szLeftBuffer,))
# BUG - Production Decay - end
				elif (CyInterface().getOrderNodeType(i) == OrderTypes.ORDER_CONSTRUCT):
					szLeftBuffer = gc.getBuildingInfo(CyInterface().getOrderNodeData1(i)).getDescription()
					iProductionTurns = pHeadSelectedCity.getBuildingProductionTurnsLeft(
							CyInterface().getOrderNodeData1(i), i)
					if iProductionTurns > 0: # advc.004x
						szRightBuffer = "(" + str(iProductionTurns) + ")"
# BUG - Production Started - start
					if CityScreenOpt.isShowProductionStarted():
						eBuilding = CyInterface().getOrderNodeData1(i)
						if pHeadSelectedCity.getBuildingProduction(eBuilding) > 0:
							szRightBuffer = BugUtil.colorText(szRightBuffer, "COLOR_CYAN")
# BUG - Production Started - end
# BUG - Production Decay - start
					# advc.094: BugDll.isPresent check removed; active player check added.
					if (CityScreenOpt.isShowProductionDecayQueue() and
							pHeadSelectedCity.getOwner() == gc.getGame().getActivePlayer()):
						eBuilding = CyInterface().getOrderNodeData1(i)
						if pHeadSelectedCity.getBuildingProduction(eBuilding) > 0:
							if pHeadSelectedCity.isBuildingProductionDecay(eBuilding):
								szLeftBuffer = BugUtil.getText(
										"TXT_KEY_BUG_PRODUCTION_DECAY_THIS_TURN", (szLeftBuffer,))
							elif pHeadSelectedCity.getBuildingProductionTime(eBuilding) > 0:
								iDecayTurns = pHeadSelectedCity.getBuildingProductionDecayTurns(eBuilding)
								if iDecayTurns <= CityScreenOpt.getProductionDecayQueueBuildingThreshold():
									szLeftBuffer = BugUtil.getText(
											"TXT_KEY_BUG_PRODUCTION_DECAY_WARNING", (szLeftBuffer,))
# BUG - Production Decay - end
				elif (CyInterface().getOrderNodeType(i) == OrderTypes.ORDER_CREATE):
					szLeftBuffer = gc.getProjectInfo(CyInterface().getOrderNodeData1(i)).getDescription()
					iProductionTurns = pHeadSelectedCity.getProjectProductionTurnsLeft(
							CyInterface().getOrderNodeData1(i), i)
					if iProductionTurns > 0: # advc.004x
						szRightBuffer = "(" + str(iProductionTurns) + ")"
# BUG - Production Started - start
					if BugDll.isVersion(3) and CityScreenOpt.isShowProductionStarted():
						eProject = CyInterface().getOrderNodeData1(i)
						if pHeadSelectedCity.getProjectProduction(eProject) > 0:
							szRightBuffer = BugUtil.colorText(szRightBuffer, "COLOR_CYAN")
# BUG - Production Started - end
				elif (CyInterface().getOrderNodeType(i) == OrderTypes.ORDER_MAINTAIN):
					szLeftBuffer = gc.getProcessInfo(CyInterface().getOrderNodeData1(i)).getDescription()
				screen.appendTableRow("SelectedCityText")
				screen.setTableText("SelectedCityText", 0, iRow, szLeftBuffer, "",
						WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_LEFT_JUSTIFY)
				screen.setTableText("SelectedCityText", 1, iRow, szRightBuffer, "",
						WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_RIGHT_JUSTIFY)
				screen.show("SelectedCityText")
				screen.show("SelectedUnitPanel")
				iRow += 1
			# <advc> Reduce indentation
			return 0
		if (not pHeadSelectedUnit or
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_SHOW):
			return 0 # </advc>
		screen.setTableColumnHeader("SelectedUnitText", 0, u"", 100)
		screen.setTableColumnHeader("SelectedUnitText", 1, u"", 75)
		screen.setTableColumnHeader("SelectedUnitText", 2, u"", 10)
		screen.setTableColumnRightJustify("SelectedUnitText", 1)
		if (CyInterface().mirrorsSelectionGroup()):
			pSelectedGroup = pHeadSelectedUnit.getGroup()
		else:
			pSelectedGroup = 0
		if (CyInterface().getLengthSelectionList() > 1):
# BUG - Stack Movement Display - start
			szBuffer = localText.getText("TXT_KEY_UNIT_STACK",
					(CyInterface().getLengthSelectionList(),))
			if MainOpt.isShowStackMovementPoints():
				iMinMoves = 100000
				iMaxMoves = 0
				for i in range(CyInterface().getLengthSelectionList()):
					pUnit = CyInterface().getSelectionUnit(i)
					if (pUnit is not None):
						iLoopMoves = pUnit.movesLeft()
						if (iLoopMoves > iMaxMoves):
							iMaxMoves = iLoopMoves
						if (iLoopMoves < iMinMoves):
							iMinMoves = iLoopMoves
				if (iMinMoves == iMaxMoves):
					fMinMoves = float(iMinMoves) / gc.getMOVE_DENOMINATOR()
					szBuffer += u" %.1f%c" % (fMinMoves,
							CyGame().getSymbolID(FontSymbols.MOVES_CHAR))
				else:
					fMinMoves = float(iMinMoves) / gc.getMOVE_DENOMINATOR()
					fMaxMoves = float(iMaxMoves) / gc.getMOVE_DENOMINATOR()
					szBuffer += u" %.1f - %.1f%c" % (fMinMoves, fMaxMoves,
							CyGame().getSymbolID(FontSymbols.MOVES_CHAR))
			screen.setText("SelectedUnitLabel", "Background",
					szBuffer, CvUtil.FONT_LEFT_JUSTIFY,
					18, yResolution - 137, -0.1, FontTypes.SMALL_FONT,
					WidgetTypes.WIDGET_UNIT_NAME, -1, -1)
# BUG - Stack Movement Display - end
# BUG - Stack Promotions - start
			if MainOpt.isShowStackPromotions():
				iNumPromotions = gc.getNumPromotionInfos()
				lPromotionCounts = [0] * iNumPromotions
				iNumUnits = CyInterface().getLengthSelectionList()
				for i in range(iNumUnits):
					pUnit = CyInterface().getSelectionUnit(i)
					if (pUnit is not None):
						for j in range(iNumPromotions):
							if (pUnit.isHasPromotion(j)):
								lPromotionCounts[j] += 1
				iSPColor = MainOpt.getStackPromotionColor()
				iSPColorAll = MainOpt.getStackPromotionColorAll()
				iPromotionCount = 0
				bShowCount = MainOpt.isShowStackPromotionCounts()
				for i, iCount in enumerate(lPromotionCounts):
					if (iCount > 0):
						szName = "PromotionButton" + str(i)
						x, y = self.setPromotionButtonPosition(szName, iPromotionCount)
						screen.moveToFront(szName)
						screen.show(szName)
						if (bShowCount and iCount > 1):
							szName = "PromotionButtonCircle" + str(i)
							screen.moveItem(szName, x + 10, y + 10, -0.3)
							screen.moveToFront(szName)
							screen.show(szName)
							szName = "PromotionButtonCount" + str(iPromotionCount)
							szText = u"<font=2>%d</font>" % iCount
							if iCount == iNumUnits:
								szText = BugUtil.colorText(szText, iSPColorAll)
							else:
								szText = BugUtil.colorText(szText, iSPColor)
							screen.setText(szName, "Background",
									szText, CvUtil.FONT_CENTER_JUSTIFY,
									x + 17, y + 7, -0.2, FontTypes.SMALL_FONT,
									WidgetTypes.WIDGET_PEDIA_JUMP_TO_PROMOTION, i, -1)
							screen.setHitTest(szName, HitTestTypes.HITTEST_NOHIT)
							screen.moveToFront(szName)
							screen.show(szName)
						iPromotionCount += 1
# BUG - Stack Promotions - end
			if (pSelectedGroup == 0 or pSelectedGroup.getLengthMissionQueue() <= 1):
				if (pHeadSelectedUnit):
					for i in range(gc.getNumUnitInfos()):
						iCount = CyInterface().countEntities(i)
						if (iCount > 0):
							szRightBuffer = u""
							szLeftBuffer = gc.getUnitInfo(i).getDescription()
							if (iCount > 1):
								szRightBuffer = u"(" + str(iCount) + u")"
							szBuffer = szLeftBuffer + u"  " + szRightBuffer
							screen.appendTableRow("SelectedUnitText")
							screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
									WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_LEFT_JUSTIFY)
							screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
									WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_RIGHT_JUSTIFY)
							screen.show("SelectedUnitText")
							screen.show("SelectedUnitPanel")
							iRow += 1
		else: # (selection list length less than 1)
			if (pHeadSelectedUnit.getHotKeyNumber() == -1):
				szBuffer = localText.getText("INTERFACE_PANE_UNIT_NAME",
						(pHeadSelectedUnit.getName(),))
			else:
				szBuffer = localText.getText("INTERFACE_PANE_UNIT_NAME_HOT_KEY",
						(pHeadSelectedUnit.getHotKeyNumber(), pHeadSelectedUnit.getName()))
			if (len(szBuffer) > 60):
				szBuffer = "<font=2>" + szBuffer + "</font>"
			screen.setText("SelectedUnitLabel", "Background",
					szBuffer, CvUtil.FONT_LEFT_JUSTIFY,
					18, yResolution - 137, -0.1, FontTypes.SMALL_FONT,
					WidgetTypes.WIDGET_UNIT_NAME, -1, -1)
			if ((pSelectedGroup == 0) or (pSelectedGroup.getLengthMissionQueue() <= 1)):
				screen.show("SelectedUnitText")
				screen.show("SelectedUnitPanel")
				szBuffer = u""
				szLeftBuffer = u""
				szRightBuffer = u""
				if (pHeadSelectedUnit.getDomainType() == DomainTypes.DOMAIN_AIR):
					if (pHeadSelectedUnit.airBaseCombatStr() > 0):
						szLeftBuffer = localText.getText("INTERFACE_PANE_AIR_STRENGTH", ())
						if (pHeadSelectedUnit.isFighting()):
							szRightBuffer = u"?/%d%c" %(pHeadSelectedUnit.airBaseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
						elif (pHeadSelectedUnit.isHurt()):
							szRightBuffer = u"%.1f/%d%c" %(
									((float(pHeadSelectedUnit.airBaseCombatStr() *
									pHeadSelectedUnit.currHitPoints())) /
									(float(pHeadSelectedUnit.maxHitPoints()))),
									pHeadSelectedUnit.airBaseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
						else:
							szRightBuffer = u"%d%c" %(pHeadSelectedUnit.airBaseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
				else:
					if (pHeadSelectedUnit.canFight()):
						szLeftBuffer = localText.getText("INTERFACE_PANE_STRENGTH", ())
						if (pHeadSelectedUnit.isFighting()):
							szRightBuffer = u"?/%d%c" %(pHeadSelectedUnit.baseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
						elif (pHeadSelectedUnit.isHurt()):
							# <advc.004> Same as in CvGameTextMgr::setUnitHelp
							fCurrStrength = float(pHeadSelectedUnit.baseCombatStr())
							fCurrStrength *= pHeadSelectedUnit.currHitPoints()
							fCurrStrength /= pHeadSelectedUnit.maxHitPoints()
							iCurrStrengthTimes100 = 100 * pHeadSelectedUnit.baseCombatStr()
							iCurrStrengthTimes100 *= pHeadSelectedUnit.currHitPoints()
							iCurrStrengthTimes100 /= pHeadSelectedUnit.maxHitPoints()
							if (pHeadSelectedUnit.baseCombatStr() *
									pHeadSelectedUnit.maxHitPoints() - iCurrStrengthTimes100 <= 5):
								fCurrStrength = pHeadSelectedUnit.baseCombatStr() - 0.1
							if (pHeadSelectedUnit.baseCombatStr() *
									pHeadSelectedUnit.maxHitPoints() < 5):
								fCurrStrength = 0.1
							# </advc.004>
							szRightBuffer = u"%.1f/%d%c" %(fCurrStrength,
									pHeadSelectedUnit.baseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
						else:
							szRightBuffer = u"%d%c" %(pHeadSelectedUnit.baseCombatStr(),
									CyGame().getSymbolID(FontSymbols.STRENGTH_CHAR))
				szBuffer = szLeftBuffer + szRightBuffer
				if (szBuffer):
					screen.appendTableRow("SelectedUnitText")
					screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_RIGHT_JUSTIFY)
					screen.show("SelectedUnitText")
					screen.show("SelectedUnitPanel")
					iRow += 1
				szLeftBuffer = u""
				szRightBuffer = u""
				# <advc.004w> Don't show "Movement" row if it can't move
				eDomain = pHeadSelectedUnit.getDomainType()
				if eDomain == DomainTypes.DOMAIN_AIR: # Show range instead for air units
					szLeftBuffer = localText.getText("INTERFACE_PANE_RANGE", ())
					szRightBuffer = u"%d" %(pHeadSelectedUnit.airRange(),)
				elif pHeadSelectedUnit.getDomainType() != DomainTypes.DOMAIN_IMMOBILE:
				# </advc.004w>
# BUG - Unit Movement Fraction - start
					szLeftBuffer = localText.getText("INTERFACE_PANE_MOVEMENT", ())
					if MainOpt.isShowUnitMovementPointsFraction():
						szRightBuffer = u"%d%c" %(pHeadSelectedUnit.baseMoves(),
								CyGame().getSymbolID(FontSymbols.MOVES_CHAR))
						if (pHeadSelectedUnit.movesLeft() == 0):
							szRightBuffer = u"0/" + szRightBuffer
						elif (pHeadSelectedUnit.movesLeft() == pHeadSelectedUnit.baseMoves() *
								gc.getMOVE_DENOMINATOR()):
							pass
						else:
							fCurrMoves = float(pHeadSelectedUnit.movesLeft())
							fCurrMoves /= gc.getMOVE_DENOMINATOR()
							szRightBuffer = (u"%.1f/" % fCurrMoves) + szRightBuffer
					else:
						if ((pHeadSelectedUnit.movesLeft() % gc.getMOVE_DENOMINATOR()) > 0):
							iDenom = 1
						else:
							iDenom = 0
						iCurrMoves = ((pHeadSelectedUnit.movesLeft() /
							gc.getMOVE_DENOMINATOR()) + iDenom)
						if (pHeadSelectedUnit.baseMoves() == iCurrMoves or
								eDomain == DomainTypes.DOMAIN_AIR):
							szRightBuffer = u"%d%c" %(pHeadSelectedUnit.baseMoves(),
									CyGame().getSymbolID(FontSymbols.MOVES_CHAR))
						else:
							szRightBuffer = u"%d/%d%c" %(iCurrMoves,
									pHeadSelectedUnit.baseMoves(),
									CyGame().getSymbolID(FontSymbols.MOVES_CHAR))
# BUG - Unit Movement Fraction - end
				szBuffer = szLeftBuffer + "  " + szRightBuffer
				screen.appendTableRow("SelectedUnitText")
				screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
						WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_LEFT_JUSTIFY)
				screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
						WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_RIGHT_JUSTIFY)
				screen.show("SelectedUnitText")
				screen.show("SelectedUnitPanel")
				iRow += 1
				if (pHeadSelectedUnit.getLevel() > 0 and
						pHeadSelectedUnit.getExperience() > 0): # advc.004w
					szLeftBuffer = localText.getText("INTERFACE_PANE_LEVEL", ())
					szRightBuffer = u"%d" %(pHeadSelectedUnit.getLevel())
					szBuffer = szLeftBuffer + "  " + szRightBuffer
					screen.appendTableRow("SelectedUnitText")
					screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_RIGHT_JUSTIFY)
					screen.show("SelectedUnitText")
					screen.show("SelectedUnitPanel")
					iRow += 1
				if ((pHeadSelectedUnit.getExperience() > 0) and
						not pHeadSelectedUnit.isFighting()):
					szLeftBuffer = localText.getText("INTERFACE_PANE_EXPERIENCE", ())
					szRightBuffer = u"(%d/%d)" %(pHeadSelectedUnit.getExperience(),
							pHeadSelectedUnit.experienceNeeded())
					szBuffer = szLeftBuffer + "  " + szRightBuffer
					screen.appendTableRow("SelectedUnitText")
					screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, -1, -1, CvUtil.FONT_RIGHT_JUSTIFY)
					screen.show("SelectedUnitText")
					screen.show("SelectedUnitPanel")
					iRow += 1
				iPromotionCount = 0
				for i in range(gc.getNumPromotionInfos()):
					if (pHeadSelectedUnit.isHasPromotion(i)):
						szName = "PromotionButton" + str(i)
						self.setPromotionButtonPosition(szName, iPromotionCount)
						screen.moveToFront(szName)
						screen.show(szName)
						iPromotionCount = iPromotionCount + 1
		if (pSelectedGroup):
			iNodeCount = pSelectedGroup.getLengthMissionQueue()
			if (iNodeCount > 1):
				for i in range(iNodeCount):
					szLeftBuffer = u""
					szRightBuffer = u""
					if (gc.getMissionInfo(pSelectedGroup.getMissionType(i)).isBuild()):
						if (i == 0):
							szLeftBuffer = gc.getBuildInfo(
									pSelectedGroup.getMissionData1(i)).getDescription()
							# advc.251: Pass group owner as param
							szRightBuffer = localText.getText("INTERFACE_CITY_TURNS",
									(pSelectedGroup.plot().getBuildTurnsLeft(
									pSelectedGroup.getMissionData1(i),
									pSelectedGroup.getOwner(), 0, 0),))
						else:
							szLeftBuffer = u"%s..." %(
									gc.getBuildInfo(pSelectedGroup.getMissionData1(i)).getDescription())
					else:
						szLeftBuffer = u"%s..." %(
								gc.getMissionInfo(pSelectedGroup.getMissionType(i)).getDescription())
					szBuffer = szLeftBuffer + "  " + szRightBuffer
					screen.appendTableRow("SelectedUnitText")
					screen.setTableText("SelectedUnitText", 0, iRow, szLeftBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_LEFT_JUSTIFY)
					screen.setTableText("SelectedUnitText", 1, iRow, szRightBuffer, "",
							WidgetTypes.WIDGET_HELP_SELECTED, i, -1, CvUtil.FONT_RIGHT_JUSTIFY)
					screen.show("SelectedUnitText")
					screen.show("SelectedUnitPanel")
					iRow += 1
		return 0

	# Will update the scores
	def updateScoreStrings(self):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		screen.hide("ScoreBackground")
# BUG - Align Icons - start
		for i in range(gc.getMAX_CIV_PLAYERS()): # advc: Was MAX_PLAYERS
			szName = "ScoreText" + str(i)
			screen.hide(szName)
			szName = "ScoreTech" + str(i)
			screen.hide(szName)
			# <kekm.30>
			szName = "ScoreLeader" + str(i)
			screen.hide(szName)
			szName = "ScoreCiv" + str(i)
			screen.hide(szName) # </kekm.30>
			for j in range(Scoreboard.NUM_PARTS):
				szName = "ScoreText%d-%d" %(i, j)
				screen.hide(szName)
# BUG - Align Icons - end

		iWidth = 0
		iCount = 0
		iBtnHeight = 22
		yCoord = 0 # advc: Make sure this is defined when needed

		if ((CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_MINIMAP_ONLY)):
			# <advc.004z>
			kGLM = CyGlobeLayerManager()
			iCurrentLayerID = kGLM.getCurrentLayerID()
			# Copy-pasted from updateGlobeviewButtons
			bGlobeViewOptions = (iCurrentLayerID != -1 and
					kGLM.getLayer(iCurrentLayerID).getNumOptions() != 0 and
					(MainOpt.isResourceIconOptions() or
					kGLM.getLayer(iCurrentLayerID).getName() != "RESOURCES") and
					(gc.getDefineINT("SHOW_UNIT_LAYER_OPTIONS") > 0 or
					kGLM.getLayer(iCurrentLayerID).getName() != "UNITS"))
			# </advc.004z>
			if (CyInterface().isScoresVisible() and
					not CyInterface().isCityScreenUp() and
					(not CyEngine().isGlobeviewUp() or
					# <advc.004z>
					(not bGlobeViewOptions and MainOpt.isScoresInGlobeView() and
					CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE))):
					# </advc.004z>
# BUG - Align Icons - start
				bAlignIcons = ScoreOpt.isAlignIcons()
				if (bAlignIcons):
					scores = Scoreboard.Scoreboard()
				# <advc> Need to assign a value
				else:
					scores = None # </advc>
# BUG - Align Icons - end
				# (BUG - Power Rating)  advc: Moved into the loop
				i = gc.getMAX_CIV_TEAMS() - 1
				while (i > -1):
					eTeam = gc.getGame().getRankTeam(i)
					# advc.004v: Show members of unmet dead teams
					if (gc.getTeam(gc.getGame().getActiveTeam()).isHasMet(eTeam) or
							gc.getTeam(eTeam).isHuman() or
							gc.getGame().isDebugMode() or
							(not gc.getTeam(eTeam).isAlive() and
							gc.getTeam(eTeam).isEverAlive() and
							ScoreOpt.isShowDeadCivs())):
# BUG - Align Icons - start
						if (bAlignIcons):
							scores.addTeam(gc.getTeam(eTeam), i)
# BUG - Align Icons - end
						j = gc.getMAX_CIV_PLAYERS() - 1
						while (j > -1):
							ePlayer = gc.getGame().getRankPlayer(j)
							if (not CyInterface().isScoresMinimized() or
									gc.getGame().getActivePlayer() == ePlayer):
# BUG - Dead Civs - start
								if (gc.getPlayer(ePlayer).isEverAlive() and
										not gc.getPlayer(ePlayer).isBarbarian()
										and (gc.getPlayer(ePlayer).isAlive() or
										ScoreOpt.isShowDeadCivs())):
# BUG - Dead Civs - end
# BUG - Minor Civs - start
									if (not gc.getPlayer(ePlayer).isMinorCiv() or
											ScoreOpt.isShowMinorCivs()):
# BUG - Minor Civs - end
										if (gc.getPlayer(ePlayer).getTeam() == eTeam):
											szBuffer = u"<font=2>"
# BUG - Align Icons - start
											if (bAlignIcons):
												scores.addPlayer(gc.getPlayer(ePlayer), j)
# BUG - Align Icons - end
											# advc: Code moved into auxiliary function
											szBuffer += self.playerScoreString(ePlayer, scores, bAlignIcons)
											szBuffer = szBuffer + "</font>"
# BUG - Align Icons - start
											if not bAlignIcons:
												if CyInterface().determineWidth(szBuffer) > iWidth:
													iWidth = CyInterface().determineWidth(szBuffer)
												szName = "ScoreText" + str(ePlayer)
												if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW
														or CyInterface().isInAdvancedStart()):
													yCoord = yResolution - 206
												else:
													yCoord = yResolution - 88
# BUG - Dead Civs - start
												# Don't try to contact dead civs
												if gc.getPlayer(ePlayer).isAlive():
													iWidgetType = WidgetTypes.WIDGET_CONTACT_CIV
													eContactPlayer = ePlayer
												else:
													iWidgetType = WidgetTypes.WIDGET_GENERAL
													eContactPlayer = -1
												screen.setText(szName, "Background",
														szBuffer, CvUtil.FONT_RIGHT_JUSTIFY,
														xResolution - 12, yCoord - (iCount * iBtnHeight),
														-0.3, FontTypes.SMALL_FONT,
														iWidgetType, eContactPlayer, -1)
# BUG - Dead Civs - end
												screen.show(szName)
												CyInterface().checkFlashReset(ePlayer)
												iCount = iCount + 1
# BUG - Align Icons - end
							j = j - 1
					i = i - 1

# BUG - Align Icons - start
				if (bAlignIcons):
					scores.draw(screen)
				else:
					if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW or
							CyInterface().isInAdvancedStart()):
						# advc.106d: Was yResolution-168. That position is actually just fine,
						# but I can't figure out how to move the contents of the Scoreboard there.
						yCoord = yResolution - 184
					else:
						yCoord = yResolution - 68
					screen.setPanelSize("ScoreBackground",
							xResolution - 21 - iWidth,
							yCoord - (iBtnHeight * iCount) - 4,
							iWidth + 12,
							(iBtnHeight * iCount) + 8)
					screen.show("ScoreBackground")
# BUG - Align Icons - end

	# <advc> Body cut from updateScoreStrings in order to reduce indentation
	def playerScoreString(self, ePlayer, scores, bAlignIcons):
		pPlayer = gc.getPlayer(ePlayer)
		eTeam = pPlayer.getTeam()
		pTeam = gc.getTeam(eTeam)
		g = gc.getGame()
		eActivePlayer = g.getActivePlayer()
		eActiveTeam = g.getActiveTeam()
		pActivePlayer = gc.getPlayer(eActivePlayer)
		pActiveTeam = gc.getTeam(eActiveTeam)
		szBuffer = "" # </advc>
# BUG: Align Icons throughout -- if (bAlignIcons): scores.setFoo(foo)
		if g.isGameMultiPlayer():
			if not pPlayer.isTurnActive():
				szBuffer = szBuffer + "*"
				if bAlignIcons:
					scores.setWaiting()
# BUG - Dead Civs - start
		# <advc.190d>
		bConcealCiv = False
		bConcealLeader = False
		# Note: Not much of a point in concealing anything in HotSeat mode
		if (not pActiveTeam.isHasMet(eTeam) and
				not g.isDebugMode() and pPlayer.isAlive() and
				g.isNetworkMultiPlayer()):
			# (not all uses of these variables are tagged with comments)
			bConcealCiv = pPlayer.wasCivRandomlyChosen()
			bConcealLeader = pPlayer.wasLeaderRandomlyChosen()
			if bConcealCiv:
				kGPColor = gc.getColorInfo(gc.getInfoTypeForString("COLOR_GREAT_PEOPLE_STORED"))
				rgba = kGPColor.getColor()
				iUnmetR = int(255 * rgba.r)
				iUnmetG = int(255 * rgba.g)
				iUnmetB = int(255 * rgba.b)
				iUnmetA = int(255 * rgba.a)
		# </advc.190d>
		if ScoreOpt.isUsePlayerName():
			szPlayerName = pPlayer.getName()
		else:
			szPlayerName = gc.getLeaderHeadInfo(pPlayer.getLeaderType()).getDescription()
		if not bConcealCiv:
			if ScoreOpt.isShowBothNames():
				szCivName = pPlayer.getCivilizationShortDescription(0)
				szPlayerName = szPlayerName + "/" + szCivName
			elif ScoreOpt.isShowBothNamesShort():
				szCivName = pPlayer.getCivilizationDescription(0)
				szPlayerName = szPlayerName + "/" + szCivName
			elif ScoreOpt.isShowLeaderName():
				pass
			elif ScoreOpt.isShowCivName():
				szCivName = pPlayer.getCivilizationShortDescription(0)
				szPlayerName = szCivName
			else:
				szCivName = pPlayer.getCivilizationDescription(0)
				szPlayerName = szCivName
		if not pPlayer.isAlive() and ScoreOpt.isShowDeadTag():
			szPlayerScore = localText.getText("TXT_KEY_BUG_DEAD_CIV", ())
			if bAlignIcons:
				scores.setScore(szPlayerScore)
		else:
			iScore = g.getPlayerScore(ePlayer)
			szPlayerScore = u"%d" % iScore
			# <advc.155>
			# (To allow this option without the Advanced/Tabular layout option, simply remove the bAlignIcons check.)
			if (bAlignIcons and
					gc.getTeam(eTeam).getAliveCount() > 1 and
					ScoreOpt.isColorCodeTeamScore() and
					not bConcealCiv):
				pTeamLeader = gc.getPlayer(gc.getTeam(eTeam).getLeaderID())
				szPlayerScore = u"<color=%d,%d,%d,%d>%s</color>" %(
						pTeamLeader.getPlayerTextColorR(),
						pTeamLeader.getPlayerTextColorG(),
						pTeamLeader.getPlayerTextColorB(),
						pTeamLeader.getPlayerTextColorA(),
						szPlayerScore)
			# </advc.155>
			if bAlignIcons:
				scores.setScore(szPlayerScore)
# BUG - Score Delta - start
			if ScoreOpt.isShowScoreDelta():
				iGameTurn = g.getGameTurn()
				if ePlayer >= eActivePlayer:
					iGameTurn -= 1
				if ScoreOpt.isScoreDeltaIncludeCurrentTurn():
					iScoreDelta = iScore
				elif iGameTurn >= 0:
					iScoreDelta = pPlayer.getScoreHistory(iGameTurn)
				else:
					iScoreDelta = 0
				iPrevGameTurn = iGameTurn - 1
				if iPrevGameTurn >= 0:
					iScoreDelta -= pPlayer.getScoreHistory(iPrevGameTurn)
				if iScoreDelta != 0:
					if iScoreDelta > 0:
						# advc.085: To match the color I (might) use for tech progress. Was just GREEN.
						iColorType = gc.getInfoTypeForString("COLOR_ALT_HIGHLIGHT_TEXT")
					elif iScoreDelta < 0:
						iColorType = gc.getInfoTypeForString("COLOR_RED")
					szScoreDelta = "%+d" % iScoreDelta
					if iColorType >= 0:
						szScoreDelta = localText.changeTextColor(szScoreDelta, iColorType)
					szPlayerScore += szScoreDelta + u" "
					if bAlignIcons:
						scores.setScoreDelta(szScoreDelta)
# BUG - Score Delta - end
		if (not CyInterface().isFlashingPlayer(ePlayer) or
				CyInterface().shouldFlash(ePlayer)):
			if ePlayer == eActivePlayer:
				szPlayerName = u"[<color=%d,%d,%d,%d>%s</color>]" %(
						pPlayer.getPlayerTextColorR(),
						pPlayer.getPlayerTextColorG(),
						pPlayer.getPlayerTextColorB(),
						pPlayer.getPlayerTextColorA(),
						szPlayerName)
			else:
				if not pPlayer.isAlive() and ScoreOpt.isGreyOutDeadCivs():
					szPlayerName = u"<color=%d,%d,%d,%d>%s</color>" %(
							175, 175, 175, pPlayer.getPlayerTextColorA(),
							szPlayerName)
				# <advc.190d>
				elif bConcealCiv:
					szPlayerName = u"<color=%d,%d,%d,%d>%s</color>" %(
							iUnmetR, iUnmetG, iUnmetB, iUnmetA,
							szPlayerName)
				# </ advc.190d>
				else:
					szPlayerName = u"<color=%d,%d,%d,%d>%s</color>" %(
							pPlayer.getPlayerTextColorR(),
							pPlayer.getPlayerTextColorG(),
							pPlayer.getPlayerTextColorB(),
							pPlayer.getPlayerTextColorA(),
							szPlayerName)
		szTempBuffer = u"%s: %s" %(szPlayerScore, szPlayerName)
		szBuffer = szBuffer + szTempBuffer
		if bAlignIcons:
			scores.setName(szPlayerName)
			# <advc.190d>
			if bConcealCiv:
				scores.setID(u"<color=%d,%d,%d,%d>%d</color>" %(
						iUnmetR, iUnmetG, iUnmetB, iUnmetA,
						ePlayer))
			else: # </advc.190d>
				scores.setID(u"<color=%d,%d,%d,%d>%d</color>" %(
						pPlayer.getPlayerTextColorR(),
						pPlayer.getPlayerTextColorG(),
						pPlayer.getPlayerTextColorB(),
						pPlayer.getPlayerTextColorA(),
						ePlayer))
		if pPlayer.isAlive():
			if bAlignIcons:
				scores.setAlive()
			# BUG: Rest of Dead Civs change is merely indentation by 1 level ...
			#if pTeam.isAlive():
				# if not pActiveTeam.isHasMet(eTeam):
					# szBuffer = szBuffer + (" ?")
					# if bAlignIcons:
						# scores.setNotMet()
			# K-Mod
			if pTeam.isAlive() and not pActiveTeam.isHasMet(eTeam):
				szBuffer = szBuffer + (" ?")
				if bAlignIcons:
					scores.setNotMet()
			# K-Mod end
			# <kekm.30>
			if bAlignIcons:
				scores.setLeaderIcon(pPlayer.getLeaderType())
				scores.setCivIcon(pPlayer.getCivilizationType())
			# </kekm.30>
			# K-Mod
			if (pTeam.isAlive() and
					(pActiveTeam.isHasMet(eTeam) or g.isDebugMode())):
			# K-Mod end
				if pTeam.isAtWar(eActiveTeam):
					szBuffer += "("
					szBuffer += localText.getColorText("TXT_KEY_CONCEPT_WAR",
							(), gc.getInfoTypeForString("COLOR_RED")).upper()
					szBuffer += ")"
					if bAlignIcons:
						scores.setWar()
				elif pActiveTeam.isForcePeace(eTeam):
					if bAlignIcons:
						scores.setPeace()
				elif pTeam.isAVassal():
					for eMasterTeam in range(gc.getMAX_TEAMS()):
						if (pTeam.isVassal(eMasterTeam) and
								pActiveTeam.isForcePeace(eMasterTeam)):
							if bAlignIcons:
								scores.setPeace()
							break
				if (pPlayer.canTradeNetworkWith(eActivePlayer) and
						ePlayer != eActivePlayer):
					szTempBuffer = u"%c" %(g.getSymbolID(FontSymbols.TRADE_CHAR))
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setTrade()
				if pTeam.isOpenBorders(eActiveTeam):
					szTempBuffer = u"%c" %(g.getSymbolID(FontSymbols.OPEN_BORDERS_CHAR))
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setBorders()
				if pTeam.isDefensivePact(eActiveTeam):
					szTempBuffer = u"%c" %(g.getSymbolID(FontSymbols.DEFENSIVE_PACT_CHAR))
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setPact()
				eStateReligion = pPlayer.getStateReligion()
				if eStateReligion != -1:
					if pPlayer.hasHolyCity(eStateReligion):
						szTempBuffer = u"%c" %(
								gc.getReligionInfo(eStateReligion).getHolyCityChar())
					else:
						szTempBuffer = u"%c" %(
								gc.getReligionInfo(eStateReligion).getChar())
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setReligion(szTempBuffer)
				# BUG - 3.17: isEspionage check
				# advc.120h: Second condition was pTeam.getEspionagePointsAgainstTeam(eActiveTeam) < pActiveTeam.getEspionagePointsAgainstTeam(eTeam)
				if (GameUtil.isEspionage() and
						pActivePlayer.getEspionageSpendingWeightAgainstTeam(eTeam) > 0):
					szTempBuffer = u"%c" %(
							gc.getCommerceInfo(CommerceTypes.COMMERCE_ESPIONAGE).getChar())
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setEspionage()
				# <advc.085>
				if (ePlayer != eActivePlayer and
						(pPlayer.isGoldenAge() or pPlayer.isAnarchy())):
					# szBuffer += # Perhaps tbd. (non-tabular layout)
					if bAlignIcons:
						scores.setGoldenAge(pPlayer.isAnarchy())
				# </advc.085>
			# K-Mod (original code deleted)
			if (g.isDebugMode() or
					(pActivePlayer.canSeeResearch(ePlayer) and
					(eTeam != eActiveTeam or pActiveTeam.getNumMembers() > 1))):
			# K-Mod end
				eCurrentResearch = pPlayer.getCurrentResearch() # advc
				iProgressPercent = 0 # advc.085: Show that even when no current research
				if eCurrentResearch != -1:
					szTempBuffer = u"-%s" %gc.getTechInfo(eCurrentResearch).getDescription()
					# <advc.004x>
					#iTurnsLeft = pPlayer.getResearchTurnsLeft(eCurrentResearch, True)
					#if iTurnsLeft >= 0:
					# </advc.004x>
						#szTempBuffer = u"-%s (%d)" %(gc.getTechInfo(eCurrentResearch).getDescription(), iTurnsLeft)
					# <advc.085> Replacing the above
					iCurrentCost = pTeam.getResearchCost(eCurrentResearch)
					if iCurrentCost > 0:
						iProgressPercent = pTeam.getResearchProgress(eCurrentResearch) * 100
						iProgressPercent /= iCurrentCost
						iProgressPercent = min(iProgressPercent, 99)
						iProgressPercent = max(iProgressPercent, 0)
				szTempBuffer += u" %d%%" % iProgressPercent
				# Don't req. eCurrentResearch!=-1 unless in Debug mode
				if eCurrentResearch != -1 or not gc.getGame().isDebugMode():
					szBuffer += szTempBuffer
					if bAlignIcons:
						# Pass along iProgressPercent instead of iTurnsLeft
						scores.setResearch(eCurrentResearch, iProgressPercent)
					# </advc.085>
			# BUG (Dead Civs): ...end of indentation
# BUG - Dead Civs - end
# BUG - Power Rating - start
			# if on, show according to espionage "see demographics" mission
			if (ScoreOpt.isShowPower() and
					# K-Mod (original BUG condition deleted)
					eActivePlayer != ePlayer and
					(g.isDebugMode() or
					pActivePlayer.canSeeDemographics(ePlayer))):
				iPlayerPower = pActivePlayer.getPower()
				iPowerColor = ScoreOpt.getPowerColor()
				iHighPowerColor = ScoreOpt.getHighPowerColor()
				iLowPowerColor = ScoreOpt.getLowPowerColor()
				iPower = pPlayer.getPower()
				if iPower > 0: # avoid divide by zero
					fPowerRatio = float(iPlayerPower) / float(iPower)
					if ScoreOpt.isPowerThemVersusYou():
						if fPowerRatio > 0:
							fPowerRatio = 1.0 / fPowerRatio
						else:
							fPowerRatio = 999.0
					cPower = g.getSymbolID(FontSymbols.STRENGTH_CHAR)
					szTempBuffer = BugUtil.formatFloat(fPowerRatio, ScoreOpt.getPowerDecimals())
					szTempBuffer += u"%c" % (cPower)
					# <advc.085> Don't color the power ratios of teammates
					bAlly = (eTeam == eActiveTeam)
					iColor = 0 # Want to pass that to widget help </advc.085>
					if (iHighPowerColor >= 0 and
							not bAlly and fPowerRatio >= ScoreOpt.getHighPowerRatio()):
						iColor = iHighPowerColor
					elif (iLowPowerColor >= 0 and
							not bAlly and fPowerRatio <= ScoreOpt.getLowPowerRatio()):
						iColor = iLowPowerColor
					elif (iPowerColor >= 0):
						iColor = iPowerColor
					szTempBuffer = localText.changeTextColor(szTempBuffer, iColor)
					szBuffer = szBuffer + u" " + szTempBuffer
					if bAlignIcons:
						scores.setPower(szTempBuffer, iColor)
# BUG - Power Rating - end
# BUG - Attitude Icons - start
			if ScoreOpt.isShowAttitude():
				if not pPlayer.isHuman() and eActivePlayer != ePlayer:
					iAtt = pPlayer.AI_getAttitude(eActivePlayer)
					#cAtt = unichr(ord(unichr(g.getSymbolID(FontSymbols.POWER_CHAR) + 4)) + iAtt)
					# advc.187: I've added the airport icon as a GameFont_75 symbol and that breaks the offset used above. No cells are left for further insertions, so, I guess, at this point, the offset from POWER_CHAR can't break again - but let's do it a bit more cleanly anyway by exposing the leftmost attitude char to Python.
					cAtt = unichr(ord(unichr(g.getSymbolID(FontSymbols.WORST_ATTITUDE_CHAR) + iAtt)))
					szBuffer += cAtt
					if bAlignIcons:
						scores.setAttitude(cAtt)
# BUG - Attitude Icons - end
# BUG - Refuses to Talk - start
			if not DiplomacyUtil.isWillingToTalk(ePlayer, eActivePlayer):
				cRefusesToTalk = u"!"
				szBuffer += cRefusesToTalk
				if bAlignIcons:
					scores.setWontTalk()
# BUG - Refuses to Talk - end
# BUG - Worst Enemy - start
			if ScoreOpt.isShowWorstEnemy():
				if AttitudeUtil.isWorstEnemy(ePlayer, eActivePlayer):
					cWorstEnemy = u"%c" %(g.getSymbolID(FontSymbols.ANGRY_POP_CHAR))
					szBuffer += cWorstEnemy
					if bAlignIcons:
						scores.setWorstEnemy()
# BUG - Worst Enemy - end
# BUG - WHEOOH - start
			#if ScoreOpt.isShowWHEOOH():
			# advc.104: Enable iff UWAI is disabled. But the icon still won't show up unless it gets added to the scoreboard string.
			if CyGame().useKModAI():
				if PlayerUtil.isWHEOOH(ePlayer, PlayerUtil.getActivePlayerID()):
					szTempBuffer = u"%c" %(g.getSymbolID(FontSymbols.OCCUPATION_CHAR))
					szBuffer = szBuffer + szTempBuffer
					if bAlignIcons:
						scores.setWHEOOH()
# BUG - WHEOOH - end
# BUG - Num Cities - start
			if ScoreOpt.isShowCountCities():
				# if PlayerUtil.canSeeCityList(ePlayer):
					# szTempBuffer = u"%d" % PlayerUtil.getNumCities(ePlayer)
				# else:
					# szTempBuffer = BugUtil.colorText(u"%d" % PlayerUtil.getNumRevealedCities(ePlayer), "COLOR_CYAN")
				# K-Mod. count revealed cities only.
				if g.isDebugMode():
					szTempBuffer = u"%d" % pPlayer.getNumCities()
				else:
					szTempBuffer = u"%d" % PlayerUtil.getNumRevealedCities(ePlayer)
				# K-Mod end
				# advc.085: Make city counts gray
				szTempBuffer = localText.changeTextColor(szTempBuffer,
						gc.getInfoTypeForString("COLOR_BUILDING_TEXT"))
				szBuffer = szBuffer + " " + szTempBuffer
				if bAlignIcons:
					scores.setNumCities(szTempBuffer)
# BUG - Num Cities - end
		if g.isNetworkMultiPlayer():
			szTempBuffer = CyGameTextMgr().getNetStats(ePlayer)
			szBuffer = szBuffer + szTempBuffer
			if bAlignIcons:
				scores.setNetStats(szTempBuffer)
		if pPlayer.isHuman() and CyInterface().isOOSVisible():
			szTempBuffer = u" <color=255,0,0>* %s *</color> (%d)" %(
					CyGameTextMgr().getOOSSeeds(ePlayer), g.getTurnSlice()%8) # K-Mod, added TurnSlice
			szBuffer = szBuffer + szTempBuffer
			if bAlignIcons:
				scores.setNetStats(szTempBuffer)
		return szBuffer

	# Will update the help Strings
	def updateHelpStrings(self):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE_ALL):
			screen.setHelpTextString("")
		else:
			screen.setHelpTextString(CyInterface().getHelpString())
		return 0

	# Will set the promotion button position
	def setPromotionButtonPosition(self, szName, iPromotionCount):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
# BUG - Stack Promotions - start
		x, y = self.calculatePromotionButtonPosition(screen, iPromotionCount)
		screen.moveItem(szName, x, y, -0.3)
		return x, y
# BUG - Stack Promotions - end

	def calculatePromotionButtonPosition(self, screen, iPromotionCount):
		yResolution = screen.getYResolution()
		return (266 - (24 * (iPromotionCount / 6)),
				yResolution - 144 + (24 * (iPromotionCount % 6)))

	# Will set the selection button position
	def setResearchButtonPosition(self, szButtonID, iCount):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
# BUG - Bars on single line for higher resolution screens - start
		if (xResolution >= 1440 and
			(self.isShowGGProgressBar() or self.isShowGPProgressBar())):
			xCoord = 268 + (xResolution - 1440) / 2
			xCoord += 6 + 84
			screen.moveItem(szButtonID,
					264 + ((xResolution - 1024) / 2) + (34 * (iCount % 15)),
					0 + (34 * (iCount / 15)),
					-0.3)
		else:
			xCoord = 264 + ((xResolution - 1024) / 2)

		screen.moveItem(szButtonID,
				xCoord + (34 * (iCount % 15)),
				0 + (34 * (iCount / 15)),
				-0.3)
# BUG - Bars on single line for higher resolution screens - end

	# Will set the selection button position
	def setScoreTextPosition(self, szButtonID, iWhichLine):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		yResolution = screen.getYResolution()
		if (CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_SHOW):
			yCoord = yResolution - 180
		else:
			yCoord = yResolution - 88
		screen.moveItem(szButtonID,
				996, yCoord - (iWhichLine * 18), -0.3)

	# Will build the globeview UI
	def updateGlobeviewButtons(self):
		kInterface = CyInterface()
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		kEngine = CyEngine()
		kGLM = CyGlobeLayerManager()
		#iNumLayers = kGLM.getNumLayers() # advc: unused
		iCurrentLayerID = kGLM.getCurrentLayerID()
		# <advc.004m>
		# The layer id is meaningless to the DLL. Translate to enum type.
		eCurrentLayerType = GlobeLayerTypes.NO_GLOBE_LAYER
		if iCurrentLayerID >= 0:
			szLayerName = kGLM.getLayer(iCurrentLayerID).getName()[:3]
			if szLayerName == "STR":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_STRATEGY
			elif szLayerName == "TRA":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_TRADE
			elif szLayerName == "UNI":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_UNIT
			elif szLayerName == "RES":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_RESOURCE
			elif szLayerName == "REL":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_RELIGION
			elif szLayerName == "CUL":
				eCurrentLayerType = GlobeLayerTypes.GLOBE_LAYER_CULTURE
		gc.getGame().reportCurrentLayer(eCurrentLayerType)
		# </advc.004m>

		# Positioning things based on the visibility of the globe

		self.setDefaultHelpTextArea(kEngine.isGlobeviewUp() or
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_SHOW)

		# Set base Y position for the LayerOptions, if we find them
		if CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE:
			iGlobeLayerOptionsY_Minimal = 38 # distance from bottom edge
			iY = yResolution - iGlobeLayerOptionsY_Minimal
		else:
			iGlobeLayerOptionsY_Regular = 170# distance from bottom edge
			iY = yResolution - iGlobeLayerOptionsY_Regular

		# Hide the layer options ... all of them
		for i in range (20):
			szName = "GlobeLayerOption" + str(i)
			screen.hide(szName)

		# Setup the GlobeLayer panel
		#iNumLayers = kGLM.getNumLayers() # advc: unused
		if (kEngine.isGlobeviewUp() and
				CyInterface().getShowInterface() != InterfaceVisibility.INTERFACE_HIDE_ALL):
			# set up panel
			# <advc.004z>
			bUnitLayer = (eCurrentLayerType == GlobeLayerTypes.GLOBE_LAYER_UNIT)
			bResourceLayer = (eCurrentLayerType == GlobeLayerTypes.GLOBE_LAYER_RESOURCE)
			if (iCurrentLayerID >= 0 and
					kGLM.getLayer(iCurrentLayerID).getNumOptions() > 0 and
					# Could instead set NumOptions to 0 in CvGame::getGlobeLayers
					# but then the resource layer wouldn't update properly
					# when ResourceIconOptions is toggled in the BUG menu.
					(not bResourceLayer or MainOpt.isResourceIconOptions())):
				# </advc.004z>
				bHasOptions = True
			else:
				bHasOptions = False
				screen.hide("ScoreBackground")

			# set up toggle button
			screen.setState("GlobeToggle", True)

			# Set GlobeLayer indicators correctly
			for i in range(kGLM.getNumLayers()):
				screen.setState("GlobeLayer" + str(i), iCurrentLayerID == i)

			# Set up options pane
			if bHasOptions:
				kLayer = kGLM.getLayer(iCurrentLayerID)

				iCurY = iY
				iNumOptions = kLayer.getNumOptions()
				iCurOption = kLayer.getCurrentOption()
				iMaxTextWidth = -1
				for iTmp in range(iNumOptions):
					iOption = iTmp # iNumOptions - iTmp - 1
					# <advc.004z> Skip dummy option (see CvEnums.h)
					if bUnitLayer and iOption == 2:
						continue # </advc.004z>
					szName = "GlobeLayerOption" + str(iOption)
					szCaption = kLayer.getOptionName(iOption)
					# advc.004z: Highlight "All Units" option when the default (2) is selected.
					# This is the case when none of the options has been clicked yet.
					if (iOption == iCurOption or
							(bUnitLayer and iCurOption == 2 and iOption == 0)):
						szBuffer = "  <color=0,255,0>%s</color>  " % (szCaption)
					else:
						szBuffer = "  %s  " % (szCaption)
					iTextWidth = CyInterface().determineWidth(szBuffer)

					screen.setText(szName, "Background",
							szBuffer, CvUtil.FONT_LEFT_JUSTIFY,
							xResolution - 9 - iTextWidth, iCurY - iGlobeLayerOptionHeight - 10,
							-0.3, FontTypes.SMALL_FONT,
							WidgetTypes.WIDGET_GLOBELAYER_OPTION, iOption, -1)
					screen.show(szName)

					iCurY -= iGlobeLayerOptionHeight

					if iTextWidth > iMaxTextWidth:
						iMaxTextWidth = iTextWidth

				#make extra space
				iCurY -= iGlobeLayerOptionHeight;
				iPanelWidth = iMaxTextWidth + 32
				iPanelHeight = iY - iCurY
				iPanelX = xResolution - 14 - iPanelWidth
				iPanelY = iCurY
				screen.setPanelSize("ScoreBackground",
						iPanelX, iPanelY, iPanelWidth, iPanelHeight)
				screen.show("ScoreBackground")

		else:
			if iCurrentLayerID != -1:
				kLayer = kGLM.getLayer(iCurrentLayerID)
				if kLayer.getName() == "RESOURCES":
					screen.setState("ResourceIcons", True)
				else:
					screen.setState("ResourceIcons", False)
				if kLayer.getName() == "UNITS":
					screen.setState("UnitIcons", True)
				else:
					screen.setState("UnitIcons", False)
			else:
				screen.setState("ResourceIcons", False)
				screen.setState("UnitIcons", False)

			screen.setState("Grid", CyUserProfile().getGrid())
			screen.setState("BareMap", CyUserProfile().getMap())
			screen.setState("Yields", CyUserProfile().getYields())
			screen.setState("ScoresVisible", CyUserProfile().getScores())

			screen.hide("InterfaceGlobeLayerPanel")
			screen.setState("GlobeToggle", False)

	# Update minimap buttons
	def setMinimapButtonVisibility(self, bVisible):
		screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		kInterface = CyInterface()
		kGLM = CyGlobeLayerManager()
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		if (CyInterface().isCityScreenUp()):
			bVisible = False
		# advc.004z: Moved ResourceIcons from last position to second and swappend BareMap and Yields
		kMainButtons = ["UnitIcons", "ResourceIcons", "Grid", "Yields", "BareMap", "ScoresVisible"]
		kGlobeButtons = []
		for i in range(kGLM.getNumLayers()):
			kGlobeButtons.append("GlobeLayer" + str(i))

		if bVisible:
			if CyEngine().isGlobeviewUp():
				kHide = kMainButtons
				kShow = kGlobeButtons
			else:
				kHide = kGlobeButtons
				kShow = kMainButtons
			screen.show("GlobeToggle")

		else:
			kHide = kMainButtons + kGlobeButtons
			kShow = []
			screen.hide("GlobeToggle")

		for szButton in kHide:
			screen.hide(szButton)

		if CyInterface().getShowInterface() == InterfaceVisibility.INTERFACE_HIDE:
			iMinimapButtonsY_Minimal = 32
			iY = yResolution - iMinimapButtonsY_Minimal
			iGlobeButtonY_Minimal = 40
			iGlobeY = yResolution - iGlobeButtonY_Minimal
		else:
			iMinimapButtonsY_Regular = 160
			iY = yResolution - iMinimapButtonsY_Regular
			iGlobeButtonY_Regular = 168
			iGlobeY = yResolution - iGlobeButtonY_Regular

		iBtnX = xResolution - 39
		screen.moveItem("GlobeToggle", iBtnX, iGlobeY, 0.0)

		iBtnAdvance = 28
		iBtnX = iBtnX - len(kShow)*iBtnAdvance - 10
		if len(kShow) > 0:
			i = 0
			for szButton in kShow:
				screen.moveItem(szButton, iBtnX, iY, 0.0)
				screen.moveToFront(szButton)
				screen.show(szButton)
				iBtnX += iBtnAdvance
				i += 1


	def createGlobeviewButtons(self):
		screen = self.screen
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()
		kGLM = CyGlobeLayerManager()
		for i in range(kGLM.getNumLayers()):
			szButtonID = "GlobeLayer" + str(i)
			kLayer = kGLM.getLayer(i)
			szStyle = kLayer.getButtonStyle()
			if szStyle == 0 or szStyle == "":
				szStyle = "Button_HUDSmall_Style"
			lRect = gRect("GlobeButton")
			screen.addCheckBoxGFC(szButtonID, "", "",
					lRect.x(), lRect.y(), lRect.size(), lRect.size(),
					WidgetTypes.WIDGET_GLOBELAYER, i, -1,
					ButtonStyles.BUTTON_STYLE_LABEL)
			screen.setStyle(szButtonID, szStyle)
			screen.hide(szButtonID)


	def createMinimapButtons(self):
		screen = self.screen
		xResolution = screen.getXResolution()
		yResolution = screen.getYResolution()

		screen.addCheckBoxGFC("UnitIcons", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_UNIT_ICONS).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("UnitIcons", "Button_HUDGlobeUnit_Style")
		screen.setState("UnitIcons", False)
		screen.hide("UnitIcons")

		screen.addCheckBoxGFC("Grid", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_GRID).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("Grid", "Button_HUDBtnGrid_Style")
		screen.setState("Grid", False)
		screen.hide("Grid")

		screen.addCheckBoxGFC("BareMap", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_BARE_MAP).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("BareMap", "Button_HUDBtnClearMap_Style")
		screen.setState("BareMap", False)
		screen.hide("BareMap")

		screen.addCheckBoxGFC("Yields", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_YIELDS).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("Yields", "Button_HUDBtnTileAssets_Style")
		screen.setState("Yields", False)
		screen.hide("Yields")

		screen.addCheckBoxGFC("ScoresVisible", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_SCORES).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("ScoresVisible", "Button_HUDBtnRank_Style")
		screen.setState("ScoresVisible", True)
		screen.hide("ScoresVisible")

		screen.addCheckBoxGFC("ResourceIcons", "", "",
				0, 0, 28, 28,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_RESOURCE_ALL).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("ResourceIcons", "Button_HUDBtnResources_Style")
		screen.setState("ResourceIcons", False)
		screen.hide("ResourceIcons")

		screen.addCheckBoxGFC("GlobeToggle", "", "",
				-1, -1, 36, 36,
				WidgetTypes.WIDGET_ACTION,
				gc.getControlInfo(ControlTypes.CONTROL_GLOBELAYER).getActionInfoIndex(),
				-1,
				ButtonStyles.BUTTON_STYLE_LABEL)
		screen.setStyle("GlobeToggle", "Button_HUDZoom_Style")
		screen.setState("GlobeToggle", False)
		screen.hide("GlobeToggle")

	# advc: Cut from updateCityScreen
	def orgButtonLayout(self, iOrgs, iMaxWidth, iMaxButtons):
		if (iOrgs < 8):
			iButtonSize = 24
			iButtonSpace = 10
		#elif (iOrgs >= iMaxButtons):
			#iButtonSize = iMaxWidth / iMaxButtons
			#iButtonSpace = 0
		elif (iOrgs == 8):
			iButtonSize = 24
			iButtonSpace = 5
		elif (iOrgs == 9):
			iButtonSize = 24
			iButtonSpace = 2
		elif (iOrgs == 10):
			iButtonSize = 21
			iButtonSpace = 2
		elif (iOrgs == 11):
			iButtonSize = 20
			iButtonSpace = 1
		elif (iOrgs == 12):
			iButtonSize = 18
			iButtonSpace = 1
		elif (iOrgs == 13):
			iButtonSize = 18
			iButtonSpace = 0
		elif (iOrgs == 14):
			iButtonSize = 16
			iButtonSpace = 0
		elif (iOrgs == 15):
			iButtonSize = 15
			iButtonSpace = 0
		elif (iOrgs == 16):
			iButtonSize = 14
			iButtonSpace = 0
		elif (iOrgs == 17):
			iButtonSize = 13
			iButtonSpace = 0
		elif (iOrgs == 18):
			iButtonSize = 13
			iButtonSpace = 0
		# (advc.001: The original code had a copy-paste error here)
		elif (37 > iOrgs > 18):
			iMaxButtons = 18
			iButtonSize = 13
			iButtonSpace = 0
		elif iOrgs == 37 or iOrgs == 38:
			iMaxWidth = 240
			iMaxButtons = iround(iOrgs / 2.0, 0)
			iButtonSize = iMaxWidth / iMaxButtons
			iButtonSpace = (iMaxWidth - (iButtonSize * iMaxButtons)) // (iMaxButtons - 1)
		else:
			iMaxButtons = iround(iOrgs / 2.0, 0)
			iButtonSize = iMaxWidth / iMaxButtons
			iButtonSpace = (iMaxWidth - (iButtonSize * iMaxButtons)) // (iMaxButtons - 1)
		return (iButtonSize, iButtonSpace, iMaxButtons)

	def update(self, fDelta):
		return

	def forward(self):
		if (not CyInterface().isFocused() or CyInterface().isCityScreenUp()):
			if (CyInterface().isCitySelection()):
				CyGame().doControl(ControlTypes.CONTROL_NEXTCITY)
			else:
				CyGame().doControl(ControlTypes.CONTROL_NEXTUNIT)

	def back(self):
		if (not CyInterface().isFocused() or CyInterface().isCityScreenUp()):
			if (CyInterface().isCitySelection()):
				CyGame().doControl(ControlTypes.CONTROL_PREVCITY)
			else:
				CyGame().doControl(ControlTypes.CONTROL_PREVUNIT)

# BUG - Raw Yields - start
	def handleRawYieldsButtons(self, inputClass):
		iButton = inputClass.getID()
		if (inputClass.getNotifyCode() == NotifyCode.NOTIFY_CURSOR_MOVE_ON):
			self.PLE.displayHelpHover(RAW_YIELD_HELP[iButton])
		elif (inputClass.getNotifyCode() == NotifyCode.NOTIFY_CURSOR_MOVE_OFF):
			self.PLE.hideInfoPane()
		elif (inputClass.getNotifyCode() == NotifyCode.NOTIFY_CLICKED):
			global g_bYieldView
			global g_iYieldType
			global g_iYieldTiles
			if iButton == 0:
				g_bYieldView = False
			elif iButton in (1, 2, 3):
				g_bYieldView = True
				g_iYieldType = RawYields.YIELDS[iButton - 1]
			elif iButton in (4, 5, 6):
				g_bYieldView = True
				g_iYieldTiles = RawYields.TILES[iButton - 4]
			else:
				return 0
			CyInterface().setDirty(InterfaceDirtyBits.CityScreen_DIRTY_BIT, True)
			return 1
		return 0
# BUG - Raw Yields - end

	# Will handle the input for this screen...
	def handleInput (self, inputClass):
#		BugUtil.debugInput(inputClass)
# BUG - PLE - start
		if (inputClass.getNotifyCode() == NotifyCode.NOTIFY_CURSOR_MOVE_ON or
				inputClass.getNotifyCode() == NotifyCode.NOTIFY_CURSOR_MOVE_OFF or
				inputClass.getNotifyCode() == NotifyCode.NOTIFY_CLICKED):
			if (self.MainInterfaceInputMap.has_key(inputClass.getFunctionName())):
				return self.MainInterfaceInputMap.get(inputClass.getFunctionName())(inputClass)
			if (self.MainInterfaceInputMap.has_key(inputClass.getFunctionName() + "1")):
				return self.MainInterfaceInputMap.get(inputClass.getFunctionName() + "1")(inputClass)
# BUG - PLE - end

# BUG - BUG Option Button - Start
			if inputClass.getNotifyCode() == NotifyCode.NOTIFY_CLICKED:
				if inputClass.getFunctionName() == "BUGOptionsScreenWidget":
					BugOptionsScreen.showOptionsScreen()
					return 1
# BUG - BUG Option Button - End


# BUG - Raw Yields - start
		if (inputClass.getFunctionName().startswith("RawYields")):
			return self.handleRawYieldsButtons(inputClass)
# BUG - Raw Yields - end

# BUG - Great Person Bar - start
		if (inputClass.getNotifyCode() == NotifyCode.NOTIFY_CLICKED and
				inputClass.getFunctionName().startswith("TwoLineGPBar")):
			# Zoom to next GP city
			iCity = inputClass.getData1()
			if (iCity == -1):
				pCity, _ = GPUtil.findNextCity()
			else:
				pCity = gc.getActivePlayer().getCity(iCity)
			if pCity and not pCity.isNone():
				CyInterface().selectCity(pCity, False)
			return 1
# BUG - Great Person Bar - end

# BUG - field of view slider - start
		if inputClass.getNotifyCode() == NotifyCode.NOTIFY_SLIDER_NEWSTOP:
			if inputClass.getFunctionName() == "FoVSlider":
				screen = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
				#self.iField_View = inputClass.getData() + 1
				# <advc.090>
				# SLIDER_NEWSTOP triggers both on moving the slider and on hovering over the slider.
				# I don't think the two cases can be told apart.
				#BugUtil.debugInput(inputClass, True)
				iPos = inputClass.getData()
				iPrevPos = self.iFoVPos_Prev
				self.iFoVPos_Prev = iPos
				#print "slider new stop: pos=" + str(iPos) + ", prevPos=" + str(iPrevPos)
				# For some reason, the position jumps a bit upon releasing the slider.
				# I've tried to compensate, and it works somewhat, but can also make the
				# slider move back and forth when hovering. Not usable.
				#if iPrevPos > 0:
				#	if iPrevPos < iPos:
				#		iPos += 1
				#	elif iPrevPos > iPos:
				#		iPos -= 1
				self.iField_View = self.sliderPosToFoV(iPos)
				#print "iField_View=" + str(self.iField_View)
				# </advc.090>
				self.setFieldofView(screen, False)
				self.setFieldofView_Text(screen)
				MainOpt.setFieldOfView(self.iField_View)
		return 0

	# <advc.090>
	def sliderPosToFoVPercent(self, iPos): # iPos is between 0 and iW - 1
		fInterval = float(self.iFoVLabelUpper - self.iFoVLabelLower)
		return floor((iPos * fInterval) / gRect("FoVSlider").width() + self.iFoVLabelLower)
	# Inverse of the above
	def FoVPercentToSliderPos(self, iPercent):
		r = (iPercent - self.iFoVLabelLower) * gRect("FoVSlider").width()
		fInterval = float(self.iFoVLabelUpper - self.iFoVLabelLower)
		return ceil(r / fInterval)

	def PercentToFoV(self, iPercent):
		r = iPercent
		if r <= 75:
			return r
		return 2 * r - 75

	def FoVToPercent(self, iFoV):
		r = iFoV
		if r <= 75:
			return r
		return floor((75 + r) / 2)

	def sliderPosToFoV(self, iPos):
		return self.PercentToFoV(self.sliderPosToFoVPercent(iPos))

	def FoVToSliderPos(self, iFoV):
		return self.FoVPercentToSliderPos(self.FoVToPercent(iFoV))
	# </advc.090>

	def setFieldofView(self, screen, bDefault):
		try: # advc.009b
			# K-Mod
			#if bDefault or not MainOpt.isShowFieldOfView():
			if (bDefault or
					(not MainOpt.isShowFieldOfView() and
					not MainOpt.isRememberFieldOfView()) or
					# advc.004m: Only remember sensible values
					int(MainOpt.getFieldOfView()) < 10):
				self._setFieldofView(screen, self.DEFAULT_FIELD_OF_VIEW)
			else:
				self._setFieldofView(screen, self.iField_View)
		# <advc.009b>
		except AttributeError:
			pass # </advc.009b>

	def _setFieldofView(self, screen, iFoV):
		if self.iField_View_Prev != iFoV:
			gc.setDefineFLOAT("FIELD_OF_VIEW", float(iFoV))
			self.iField_View_Prev = iFoV

	def setFieldofView_Text(self, screen):
		zsFieldOfView_Text = "%s [%i]" % (
				self.sFieldOfView_Text,
				self.FoVToPercent(self.iField_View)) # advc.090: was self.iField_View
		self.setLabel("FoVSliderText", "", zsFieldOfView_Text,
				CvUtil.FONT_RIGHT_JUSTIFY, FontTypes.GAME_FONT)
# BUG - field of view slider - end
