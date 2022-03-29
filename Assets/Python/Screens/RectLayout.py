# advc.092: New module to help specify positions of rectangular widgets
# relative to each other.

# Layout data of a rectangular widget or group of widgets:
# a pair of coordinates and a pair of side lengths.
# The constructor receives the coordinates as an offset from another
# ("parent") RectLayout - and converts them to absolute screen coordinates
# accessible through the x and y methods.
# For convenience, the constructors works with float values, but the accessors
# return integers because that's what most of the CyGInterfaceScreen functions
# in the EXE expect.
class RectLayout:
	_ALIGN_CENTER = 100000
	_ALIGN_OPPOSITE = _ALIGN_CENTER + 1

	LEFT = 0
	TOP = 0
	CENTER = _ALIGN_CENTER	
	RIGHT = _ALIGN_OPPOSITE
	BOTTOM = _ALIGN_OPPOSITE
	def __init__(self,
			# ('None' is allowed only for the RectLayout representing the screen itself.
			# In that case, fX and fY need to be absolute screen coordinates.)
			lParent,
			# Distance from the lParent's left edge if positive,
			# from the right edge if negative.
			# CENTER centers this widget horizontally.
			# LEFT is equivalent to 0.
			# RIGHT is equivalent to lParent.width().
			fX,
			# Distance from the lParent's top edge if positive,
			# from the bottom edge if negative.
			# CENTER centers this widget vertically.
			# TOP is equivalent to 0.
			# BOTTOM is equivalent to lParent.height().
			fY,
			# Our side lengths in pixels.
			# If negative, then the parent's width or height gets added.
			fWidth, fHeight):
		if fWidth < 0:
			fWidth += lParent.width()
		if fHeight < 0:
			fHeight += lParent.height()
		self.fWidth = fWidth
		self.fHeight = fHeight
		if not lParent:
			self.fX = fX
			self.fY = fY
		else:
			self.fX = self._calcCoord(lParent.x(), lParent.width(), fX, fWidth)
			self.fY = self._calcCoord(lParent.y(), lParent.height(), fY, fHeight)
		assert self.fWidth >= 0
		assert self.fHeight >= 0
		# (It's OK for widgets to be only partly on the screen, so
		# having negative fX or fY isn't necessarily wrong.)

	# Calculate absolute coordinate on screen
	def _calcCoord(self, iParentVal, iParentDim, iVal, iDim):
		iR = iParentVal
		if iVal == RectLayout.CENTER:
			iR += (iParentDim - iDim) / 2
			return iR
		if iVal == RectLayout._ALIGN_OPPOSITE:
			return iParentDim - iDim
		assert iVal < 100000, "High vals are reserved"
		iR += iVal
		if iVal < 0:
			iR += iParentDim - iDim
		return iR
	# Screen coordinates of our upper left corner
	def x(self):
		return int(round(self.fX))
	def y(self):
		return int(round(self.fY))
	# Our side lengths (pixels)
	def width(self):
		return int(round(self.fWidth))
	def height(self):
		return int(round(self.fHeight))

# Positional data for a group of widgets layed out in a single row or column.
# Intended as an abstract class.
# Tbd.: Wrap behavior, so that this class can be used for the "plot list" (unit icons).
class _SingleFileLayout(RectLayout):
	HORIZONTAL = True
	VERTICAL = False
	def __init__(self, lParent,
			# Whether the widgets are layed out horizontally (HORIZONTAL)
			# or vertically (VERTICAL)
			orientation,
			fX, fY, # See super class ctor
			iWidgets, # (Positive) number of widgets in the group
			# Space in between two adjacent widgets.
			# Negative space means that they overlap.
			iSpacing,
			# (Positive) widget size. By default, square dimensions are assumed.
			fWidth, fHeight = None):
		if not fHeight:
			fHeight = fWidth
		bHorizontal = orientation
		if bHorizontal:
			iExpandingDim = fWidth
			iTotalHeight = fHeight
		else:
			iExpandingDim = fHeight
			iTotalWidth = fWidth
		iTotalExpandingDim = iWidgets * iExpandingDim + (iWidgets - 1) * iSpacing
		if bHorizontal:
			iTotalWidth = iTotalExpandingDim
		else:
			iTotalHeight = iTotalExpandingDim
		super().__init__(lParent, fX, fY, iTotalWidth, iTotalHeight)
		assert iSpacing > -iExpandingDim, "widgets will appear out of sequence"
		self.iWidgets = iWidgets
		self.iNextWidget = 0
		self.seq = []
		# Coordinates of current widget as an offset to ours
		iBtnX = 0
		iBtnY = 0
		for i in range(iWidgets):
			lWidget = RectLayout(self, iBtnX, iBtnY, fWidth, fHeight)
			widgets.append(lWidget)
			if bHorizontal:
				iBtnX += iSpacing + fWidth
			else:
				iBtnY += iSpacing + fHeight
	def next(self):
		if iNextWidget > iWidgets:
			return None
		lNext = seq[iNextWidget]
		iNextWidget += 1
		return lNext

class ColumnLayout(_SingleFileLayout):
	def __init__(self, lParent, fX, fY, iWidgets, iSpacing, fWidth, fHeight = None):
		super().__init__(lParent, SingleFileLayout.VERTICAL, fX, fY, iWidgets, iSpacing, fWidth, fHeight)
class RowLayout(_SingleFileLayout):
	def __init__(self, lParent, fX, fY, iWidgets, iSpacing, fWidth, fHeight = None):
		super().__init__(lParent, SingleFileLayout.HORIZONTAL, fX, fY, iWidgets, iSpacing, fWidth, fHeight)

def offsetRectLayout(lRect, iDeltaX, iDeltaY = 0):
	lCopy = RectLayout(None, 0, 0, lRect.width(), lRect.height())
	lCopy.fX = lRect.fX + iDeltaX
	lCopy.fY = lRect.fY + iDeltaY
	return lCopy
