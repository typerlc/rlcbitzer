#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This file is a plugin for anki flashcard application http://ichi2.net/anki/
# ---------------------------------------------------------------------------
# File:        rlc_bitzer.py
# Description: 
#
# Author:      Richard Colley (richard.colley@rcolley.com)
# License:     GPL v3
# ---------------------------------------------------------------------------

plugin_version = "v0.18"

# Changelog:
# 
# ---- 0.18 -- 2008-05-26 -- Richard Colley ----
#   Fixed mouse-over character selection
#   Env var 'bitzer_debug' turns on debug output
#   Fixed bug on Windows that tray icon wasn't immediately removed on close
#   Possibly fixed bug on Windows where minimize to tray leaves item in taskbar.
# ---- 0.17 -- 2008-05-01 -- Richard Colley ----
#   Mouse-over character info.
#   Preferences tool tips.
#   Minimise to tray icon.
# ---- 0.16 -- 2008-04-29 -- Richard Colley ----
#   Try to detect if the main Anki install has implemented some of the
#    the features of this plugin.  If so, don't interfere.
# ---- 0.15 -- 2008-04-25 -- Richard Colley ----
#   Merged with latest Anki scheduling code.
#   New option to not display interval time with answer buttons
# ---- 0.14 -- 2008-04-24 -- Richard Colley ----
#   Added tray icon, and plugin version string to prefs
# ---- 0.13 -- 2008-04-19 -- Richard Colley ----
#   Finished first pass of personal trainer.
# ---- 0.12 -- 2008-04-19 -- Richard Colley ----
#   Added new scheduling policy ... speedround.
#   This just keeps showing cards until the users stops.
#   Implications for future scheduling are unknown, but it looks ok.
#   No warranties!! :)
# ---- 0.11 -- 2008-04-03 -- Richard Colley ----
#   Added personal trainer ... unfinished
# ---- 0.10 -- 2008-04-02 -- Richard Colley ----
#   Refactored extension classes
# ---- 0.09 -- 2008-03-31 -- Richard Colley ----
#   Changed all to new-style classes
# ---- 0.08 -- 2008-03-31 -- Richard Colley ----
#   added combo box to choose new card scheduling policy
# ---- 0.07 -- 2008-03-30 -- Richard Colley ----
#   added button on scribble pad to clear
#   fixed changelog date mistakes
# ---- 0.06 -- 2008-03-30 -- Richard Colley ----
#   finalised scribble pad
# ---- 0.05 -- 2008-03-29 -- Richard Colley ----
#   added new card distribution policy
# ---- 0.04 -- 2008-03-27 -- Richard Colley ----
#   another refactor ... but still not happy
#   update check notification can be relegated to status bar
#   change selection behaviour when edit card window is displayed
# ---- 0.03 -- 2008-03-27 -- Richard Colley ----
#   another refactor ... but still more to do
#   for instance, can only add 1 tab to preferences ... ideally allow multiple
# ---- 0.02 -- 2008-03-27 -- Richard Colley ----
#   bit of a restructure ... could still be better
# ---- 0.01 -- 2008-03-26 -- Richard Colley ----
#   initial release
# ---------------------------------------------------------------------------

from PyQt4 import QtGui, QtCore

from ankiqt import mw
from ankiqt.ui.main import AnkiQt
from ankiqt.ui.cardlist import EditDeck, DeckModel
from ankiqt.ui.preferences import Preferences
from ankiqt.ui.utils import askUser

############

class AnkiFunctionality(object):
	def __init__(self):
		pass

	def isSuppressUpdateImplemented( self ):
		try:
			if mw.newVerInStatusBar:
				pass
			return True
		except:
			return False
	isSuppressUpdateImplemented=classmethod(isSuppressUpdateImplemented)

	def isEditSelectionImplemented( self ):
		try:
			if EditDeck.findCardInDeckModel:
				pass
			return True
		except:
			return False
	isEditSelectionImplemented=classmethod(isEditSelectionImplemented)

	def isTrayIconImplemented( self ):
		try:
			import ankiqt.ui.tray
			return True
		except:
			return False
	isTrayIconImplemented=classmethod(isTrayIconImplemented)

############

# based on anki hook stuff
class Hooks(object):
	def __init__( self ):
		self.setupHooks()

	def setupHooks(self):
		self.hooks = {}

	def addHook(self, hookName, func):
		if not self.hooks.get(hookName, None):
			self.hooks[hookName] = []
		if func not in self.hooks[hookName]:
			self.hooks[hookName].append(func)

	def removeHook(self, hookName, func):
		hook = self.hooks.get(hookName, [])
		if func in hook:
			hook.remove(func)

	def runHook(self, hookName, *args):
		hook = self.hooks.get(hookName, None)
		if hook:
			for func in hook:
				func(*args)



############ Debug stuff

import os
import traceback
class RlcDebug(object):
	disabled = not os.environ.has_key('bitzer_debug')
	def debug( self, *args ):
		if self.disabled:
			return
		for a in args:
			print a,
		print
	debug=classmethod(debug)

	def breakpoint( self ):
		if self.disabled:
			return
	breakpoint=classmethod(breakpoint)

	def whereAmI( self, str = None ):
		if self.disabled:
			return
		if str:
			print str
		try:
			raise "dummy"
		except:
			traceback.print_stack()
	whereAmI=classmethod(whereAmI)


#####################

# Config stuff
def getConfig( dict, itemName, defaultValue=None ):
	if dict.has_key( itemName ):
		return dict[itemName]
	else:
		return defaultValue

def getConfigInt( dict, itemName, defaultValue=None ):
	if dict.has_key( itemName ):
		return int(dict[itemName])
	else:
		return int(defaultValue)

def setConfig( dict, itemName, value ):
	dict[itemName] = value


#####################

class ExtendAnkiPrefs(Hooks):
	def __init__( self, name ):
		Hooks.__init__( self )

                self.name = name

		self.tabItems = {}
		self.origSetupAdvanced = Preferences.setupAdvanced
		self.origPrefsAccept = Preferences.accept
		self.origPrefsReject = Preferences.reject
		Preferences.setupAdvanced = lambda prefs: self.interceptSetupAdvanced( prefs )
		Preferences.accept = lambda prefs: self.interceptPrefsAccept( prefs )
		Preferences.reject = lambda prefs: self.interceptPrefsReject( prefs )

	def hookSetup( self, func ):
		self.addHook( 'setup', func )
	def hookAccept( self, func ):
		self.addHook( 'accept', func )
	def hookReject( self, func ):
		self.addHook( 'reject', func )

	def interceptSetupAdvanced( self, prefs ):
		self.prefs = prefs
                self.prefsAddTab( self.name + " (" + plugin_version + ")" )
		self.origSetupAdvanced( prefs )
		self.runHook( 'setup', self )
	def interceptPrefsAccept( self, prefs ):
		self.runHook( 'accept', self )
		self.origPrefsAccept( prefs )
	def interceptPrefsReject( self, prefs ):
		self.runHook( 'reject', self )
		self.origPrefsReject( prefs )

	def prefsGetConfig( self, itemName, defaultValue=None ):
		if self.prefs.config.has_key( itemName ):
			return self.prefs.config[itemName]
		else:
			return defaultValue

	def prefsSetConfig( self, itemName, value ):
		self.prefs.config[itemName] = value

	def prefsGetItem( self, itemName ):
		return self.tabItems[itemName]

	def prefsCommitCheckBox( self, itemName ):
		checkBox = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, checkBox.isChecked() )

	def prefsCommitIntegerBox( self, itemName ):
		item = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, item.text() )

	def prefsCommitStringBox( self, itemName ):
		item = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, item.text() )

	def prefsCommitSlider( self, itemName ):
		slider = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, slider.value() )

	def prefsCommitComboBox( self, itemName ):
		combo = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, combo.currentIndex() )

	# UI stuff
	def prefsAddTab( self, tabTitle ):
		self.tabTitle = tabTitle
		self.rlcPrefsTab = QtGui.QWidget()
		self.rlcPrefsTab.setObjectName( "rlcPrefsTab" )
		vboxLayout = QtGui.QVBoxLayout(self.rlcPrefsTab)
		vboxLayout.setObjectName("rlcPrefsTabVboxLayout")

		self.layout = QtGui.QGridLayout()
		self.layout.setObjectName("rlcPrefsGridLayout")

		vboxLayout.addLayout(self.layout)
		spacerItem1 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
		vboxLayout.addItem(spacerItem1)

		self.prefs.dialog.tabWidget.addTab(self.rlcPrefsTab,self.tabTitle)
		return self.layout

	def prefsTabAddLabel( self, labelText, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		label = QtGui.QLabel()
		label.setText( labelText )
		if toolTip:
			print type(toolTip)
			label.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(label,row,col,rowSpan,colSpan)
		return label

	def prefsTabAddCheckBox( self, label, itemName, defaultValue, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		checkBox = QtGui.QCheckBox()
		checkBox.setObjectName( itemName )
		checkBox.setText( label )

		checkBox.setChecked( self.prefsGetConfig( itemName, defaultValue ) )
		self.tabItems[itemName] = checkBox

		if toolTip:
			checkBox.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(checkBox,row,col,rowSpan,colSpan)
		return checkBox

	def prefsTabAddIntegerBox( self, label, itemName, defaultValue, min, max, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		textLine = QtGui.QLineEdit()
		textLine.setObjectName( itemName )

		validator = QtGui.QIntValidator(None)
		if min != None:
			validator.setBottom( min )
		if max != None:
			validator.setTop( max )
		textLine.setValidator( validator )

		textLine.setText( QtCore.QString( str( self.prefsGetConfig(itemName, defaultValue) ) ) )
		self.tabItems[itemName] = textLine

		if toolTip:
			textLine.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(textLine,row,col,rowSpan,colSpan)
		return textLine

	def prefsTabAddStringBox( self, label, itemName, defaultValue, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		textLine = QtGui.QLineEdit()
		textLine.setObjectName( itemName )
		textLine.setText( QtCore.QString( self.prefsGetConfig(itemName, defaultValue) ) )
		self.tabItems[itemName] = textLine
		if toolTip:
			textLine.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(textLine,row,col,rowSpan,colSpan)
		return textLine

	def prefsTabAddSlider( self, label, itemName, defaultValue, min, max, step, legend, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		slider = QtGui.QSlider()
		slider.setOrientation( Qt.Horizontal )
		slider.setTickPosition(QtGui.QSlider.TicksBelow)
		slider.setMinimum( min )
		slider.setMaximum( max )
		slider.setTickInterval( step )
		slider.setSingleStep(step)
		slider.setPageStep(step)
		slider.setSliderPosition( self.prefsGetConfig( itemName, defaultValue ) / step )
		self.tabItems[itemName] = slider
		if legend:
			comp = QtGui.QWidget()
			gl = QtGui.QGridLayout(comp)
			gl.addWidget(slider,0,col,1,-1)
			legendLen = len( legend )
			for i in range(legendLen):
				midpoint = legendLen / 2
				if i < midpoint:
					align=Qt.AlignLeft
				elif i == midpoint:
					align=Qt.AlignHCenter
				else:
					align=Qt.AlignRight
				label = QtGui.QLabel()
				label.setText( legend[i] )
				label.setAlignment( align )
				gl.addWidget(label,1,col+i,1,1)
		else:
			comp=slider
		if toolTip:
			slider.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(comp,row,col,rowSpan,colSpan)
		return comp

	def prefsTabAddComboBox( self, label, itemName, defaultValue, optionList, toolTip=None, row=None, col=0, rowSpan=1, colSpan=-1 ):
		combo = QtGui.QComboBox()
		combo.addItems( optionList )
		combo.setCurrentIndex( self.prefsGetConfig( itemName, defaultValue ) )
		self.tabItems[itemName] = combo
		if toolTip:
			combo.setToolTip( toolTip )
		if row == None:
			row = self.layout.rowCount()
		self.layout.addWidget(combo,row,col,rowSpan,colSpan)
		return combo

class ExtendAnkiMain(object):
	# set to 1 to allow update checks to be completely disabled by user
	permitUpdateDisable = 0

	PREFS_FOCUS_ON_ANSWER = 'rlc.bitzer.answer.focusOnButton'
	DEFAULT_FOCUS_ON_ANSWER = True
	TIP_FOCUS_ON_ANSWER = """<p>If enabled, when choosing an answer, [space] will select
				the default answer.
				<p>Otherwise, there will be no default."""
	PREFS_CHECK_FOR_UPDATE = 'rlc.bitzer.update.check'
	DEFAULT_CHECK_FOR_UPDATE = True
	PREFS_QUIETEN_UPDATE = 'rlc.bitzer.update.quieten'
	DEFAULT_QUIETEN_UPDATE = False
	TIP_QUIETEN_UPDATE = """<p>If enabled, on startup Anki will display a dialog if there's
				a new version available.
				<p>If not enabled, a message will be shown in the status bar
				instead"""
	PREFS_EASE_SHOW_TIMES = 'rlc.bitzer.answer.showTimes'
	DEFAULT_EASE_SHOW_TIMES = True
	TIP_EASE_SHOW_TIMES = """<p>If enabled, time intervals will be shown with each
				answer button."""

	def __init__( self, extPrefs ):
		self.origShowEaseButtons = AnkiQt.showEaseButtons
		AnkiQt.showEaseButtons = lambda main: self.interceptShowEaseButtons( main )
		self.origShowStandardEaseButtons = AnkiQt.showStandardEaseButtons
		AnkiQt.showStandardEaseButtons = lambda main,grid,nextInts,text: self.interceptShowStandardEaseButtons( main, grid, nextInts, text )
		self.origShowCompactEaseButtons = AnkiQt.showCompactEaseButtons
		AnkiQt.showCompactEaseButtons = lambda main,grid,nextInts: self.interceptShowCompactEaseButtons( main, grid, nextInts )
		if not AnkiFunctionality.isSuppressUpdateImplemented():
			self.origSetupAutoUpdate = AnkiQt.setupAutoUpdate
			AnkiQt.setupAutoUpdate = lambda main: self.interceptSetupAutoUpdate( main )
			self.origNewVerAvail = AnkiQt.newVerAvail
			AnkiQt.newVerAvail = lambda main, version: self.interceptNewVerAvail( main, version )

		# add to preferences tab
		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )


	def addToPrefsTab( self, extPrefs ):
		extPrefs.prefsTabAddLabel( _("<h1>Main Window Settings</h1>") )
		extPrefs.prefsTabAddCheckBox( _("Focus on answer"),
			self.PREFS_FOCUS_ON_ANSWER,
			self.DEFAULT_FOCUS_ON_ANSWER,
			self.TIP_FOCUS_ON_ANSWER
			)
		if not AnkiFunctionality.isSuppressUpdateImplemented():
			if self.permitUpdateDisable:
				extPrefs.prefsTabAddCheckBox( _("Check for Anki updates"),
					self.PREFS_CHECK_FOR_UPDATE,
					self.DEFAULT_CHECK_FOR_UPDATE,
					)
			extPrefs.prefsTabAddCheckBox( _("Suppress update dialog"),
				self.PREFS_QUIETEN_UPDATE,
				self.DEFAULT_QUIETEN_UPDATE,
				self.TIP_QUIETEN_UPDATE,
				)
		extPrefs.prefsTabAddCheckBox( _("Show interval time with answer buttons"),
			self.PREFS_EASE_SHOW_TIMES,
			self.DEFAULT_EASE_SHOW_TIMES,
			self.TIP_EASE_SHOW_TIMES )

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_FOCUS_ON_ANSWER )
		if not AnkiFunctionality.isSuppressUpdateImplemented():
			if self.permitUpdateDisable:
				extPrefs.prefsCommitCheckBox( self.PREFS_CHECK_FOR_UPDATE )
			extPrefs.prefsCommitCheckBox( self.PREFS_QUIETEN_UPDATE )
		extPrefs.prefsCommitCheckBox( self.PREFS_EASE_SHOW_TIMES )

	def interceptShowEaseButtons( self, mw ):
		self.origShowEaseButtons( mw )
		if not getConfig(mw.config, self.PREFS_FOCUS_ON_ANSWER, self.DEFAULT_FOCUS_ON_ANSWER):
			# now remove focus from answer button
			mw.setFocus()

	def interceptShowStandardEaseButtons( self, mw, grid, nextInts, text ):
		if not getConfig(mw.config, self.PREFS_EASE_SHOW_TIMES, self.DEFAULT_EASE_SHOW_TIMES):
			text = (
			    (_("Completely forgot"), ""),
				(_("Made a mistake"), ""),
				(_("Difficult"), ""),
				(_("About right"), ""),
				(_("Easy"), "") )
		return self.origShowStandardEaseButtons( mw, grid, nextInts, text )

	def interceptShowCompactEaseButtons( self, mw, grid, nextInts ):
		if not getConfig(mw.config, self.PREFS_EASE_SHOW_TIMES, self.DEFAULT_EASE_SHOW_TIMES):
			nextInts = { "ease0": "", "ease1": "", "ease2": "", "ease3": "", "ease4": "" }
		return self.origShowCompactEaseButtons( mw, grid, nextInts )

	def interceptSetupAutoUpdate( self, mw ):
		if not getConfig(mw.config, self.PREFS_CHECK_FOR_UPDATE, self.DEFAULT_CHECK_FOR_UPDATE):
			RlcDebug.debug( "Checking for update!" )
			self.origSetupAutoUpdate( mw )

	def interceptNewVerAvail( self, mw, version ):
		if getConfig(mw.config, self.PREFS_QUIETEN_UPDATE, self.DEFAULT_QUIETEN_UPDATE):
			mw.statusView.statusbar.showMessage( _("Anki Update Available: ") + version, 5000 )
		else:
			self.origNewVerAvail( mw, version )

class ExtendAnkiEdit(object):
	PREFS_EDIT_CURRENT = 'rlc.bitzer.edit.startupOnlyCurrent'
	DEFAULT_EDIT_CURRENT = True
	TIP_EDIT_CURRENT = """<p>If enabled, the Edit Deck window will open with only the
				current card displayed.
				<p>Otherwise, all cards are shown, but the cursor is placed
				on the current card."""

	def __init__( self, extPrefs ):
		self.origSelectLastCard = EditDeck.selectLastCard
		EditDeck.selectLastCard = lambda edit: self.interceptSelectLastCard( edit )
		DeckModel.findCard = lambda model, card: self.findCardInDeckModel( model, card )
		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )

	def addToPrefsTab( self, extPrefs ):
		extPrefs.prefsTabAddLabel( _("<h1>Edit Cards Window</h1>") )
		extPrefs.prefsTabAddCheckBox( _("Start Edit Deck with only the current card displayed"),
			self.PREFS_EDIT_CURRENT,
			self.DEFAULT_EDIT_CURRENT,
			self.TIP_EDIT_CURRENT
			)

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_EDIT_CURRENT )

	def findCardInDeckModel( self, model, card ):
		for i, thisCard in enumerate( model.cards ):
			if thisCard.id == card.id:
				return i
		return -1
	
	def interceptSelectLastCard( self, edit ):
		if getConfig(edit.config, self.PREFS_EDIT_CURRENT, self.DEFAULT_EDIT_CURRENT):
			self.origSelectLastCard( edit )
		else:
			edit.updateSearch()
			if edit.parent.currentCard:
				currentCardIndex = self.findCardInDeckModel( edit.model, edit.parent.currentCard )
				if currentCardIndex >= 0:
					edit.dialog.tableView.selectRow( currentCardIndex )
					edit.dialog.tableView.scrollTo( edit.model.index(currentCardIndex,0), edit.dialog.tableView.PositionAtTop )
					

######################

import time
from heapq import heappush, heappop
from anki.deck import Deck, FutureItem
import anki

class CardSchedulingPolicy(object):
	def __init__( self ):
		pass
	def getCard( self ):
		raise "Must implement this! And return a card"
		
class AnkiDefaultSchedulingPolicy( CardSchedulingPolicy ):
	def __init__( self, default ):
		CardSchedulingPolicy.__init__( self )
		self.default = default
	def getCard( self, deck ):
		card = self.default( deck )
		if card: RlcDebug.debug( "Default returning card: ", card.question )
		return card

class DistributeNewCardsSchedulingPolicy( CardSchedulingPolicy ):
	def __init__( self, distribution ):
		CardSchedulingPolicy.__init__( self )
		self.distribution = distribution
		self.totalCardsScheduled = 0
		self.cardsSinceLastNew = 0

	def getDistribution( self, distribution ):
		return self.distribution
	def setDistribution( self, distribution ):
		self.distribution = distribution

	def _timeForForcedNew( self, deck ):
		RlcDebug.debug( "timeForForcedNew(): self.distribution=", self.distribution )
		RlcDebug.debug( "timeForForcedNew(): self.cardsSinceLastNew=", self.cardsSinceLastNew )

		# avoid division issues
		if self.distribution == 0:
			return False
		elif self.distribution == 100:
			return True
		else:
			numCardsInCycle = 100 / self.distribution
			if numCardsInCycle == 0:
				return False
			return ( (self.cardsSinceLastNew+1) % numCardsInCycle ) == 0

	def getCard( self, deck ):
		"Return the next due card, or None"

		isNew = False

		now = time.time()
		# any expired cards?
		while deck.futureQueue and deck.futureQueue[0].due <= now:
		    newItem = heappop(deck.futureQueue)
		    deck.addExpiredItem(newItem)

		# check if we should schedule a new card now
		if self._timeForForcedNew(deck) and deck.acqQueue:
		    RlcDebug.debug( "should show a new card" )
		    RlcDebug.debug( "new cards avail: ", len( deck.acqQueue ) )
		    item = heappop(deck.acqQueue)
		    RlcDebug.debug( "popped: ", item )
		    isNew = True
		# failed card due?
		elif (deck.failedQueue and deck.failedQueue[0].due <= now):
		    item = heappop(deck.failedQueue)
		# failed card queue too big?
		elif (deck.failedCardMax and
		    deck.failedCardsDueSoon() >= deck.failedCardMax):
		    item = deck.getOldestModifiedFailedCard()
		# failed card queue too big?
		# card due for revision
		elif deck.revQueue:
		    item = heappop(deck.revQueue)
		# failed card queue too big?
		# card due for acquisition
		elif deck.acqQueue:
		    item = heappop(deck.acqQueue)
		    isNew = True
		else:
		    if deck.collapsedFailedCards():
			# final review
			item = deck.getOldestModifiedFailedCard(collapse=True)
		    else:
			return
		# if it's not failed, check if it's spaced
		if item.successive or item.reps == 0:
		    space = deck.itemSpacing(item)
		    if space > now:
			# update due time and put it back in future queue
			item.due = max(item.due, space)
			item = deck.itemFromItem(FutureItem, item)
			heappush(deck.futureQueue, item)
			return deck.getCard()
		card = deck.s.query(anki.cards.Card).get(item.id)
		if card:
			RlcDebug.debug( "Got card: ", card.id )
			card.genFuzz()
			card.startTimer()
			self.totalCardsScheduled=self.totalCardsScheduled+1
			if isNew:
			    RlcDebug.debug( "returning NEW card" )
			    self.cardsSinceLastNew = 0
			else:
			    RlcDebug.debug( "returning OLD card" )
			    self.cardsSinceLastNew = self.cardsSinceLastNew + 1
		else:
			RlcDebug.debug( "Something screwy, found item without card! ", item.id )
		return card

class SpeedRoundSchedulingPolicy( CardSchedulingPolicy ):
	def __init__( self ):
		CardSchedulingPolicy.__init__( self )

	def getCard( self, deck ):
		"Return the next card, due or not"

		item = None

		while deck.futureQueue:
		    newItem = heappop(deck.futureQueue)
		    deck.addExpiredItem(newItem)

		# failed card due?
		if deck.failedQueue:
		    item = heappop(deck.failedQueue)
		# card due for revision
		elif deck.revQueue:
		    item = heappop(deck.revQueue)
		# card due for acquisition
		elif deck.acqQueue:
		    item = heappop(deck.acqQueue)

		if not item:
			return

		card = deck.s.query(anki.cards.Card).get(item.id)
		if card:
			card.genFuzz()
			card.startTimer()
		return card

class ExtendAnkiScheduling(object):
	# types of new card scheduling policy
	NC_POLICY_ORIGINAL = 0
	NC_POLICY_DISTRIBUTE = 1
	NC_POLICY_SPEEDROUND = 2

	PREFS_NEW_CARD_POLICY = 'rlc.bitzer.cards.new.policy'
	DEFAULT_NEW_CARD_POLICY = NC_POLICY_ORIGINAL
	TIP_NEW_CARD_POLICY = """<p>Select between different card scheduling policies.
				These policies affect the order and timing of cards.
				<ul>
				  <li>Anki default policy</li>
				  <li>New card distribution policy - this lets you mix in
				  new cards while answering old ones.  You will be able to
				  choose how frequently new cards will be shown.</li>
				  <li>Ignore timing policy - review all cards immediately.
				  Cards will be shown in the scheduled order, but the timing
				  will be ignored.  Possibly useful for a quick review.</li>
				</ul>"""
	PREFS_NEW_CARD_DISTRIBUTION  = 'rlc.bitzer.cards.new.distribution'
	DEFAULT_NEW_CARD_DISTRIBUTION  = 0

	def __init__( self, extPrefs, config ):
		self.oldDeckGetCard = Deck.getCard
		Deck.getCard = lambda deck : self.interceptDeckGetCard( deck )
		self.defaultPolicy = AnkiDefaultSchedulingPolicy( self.oldDeckGetCard )
		self.setSchedulingPolicyFromConfig( config )
		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )

	def addToPrefsTab( self, extPrefs ):
		extPrefs.prefsTabAddLabel( _( """<h1>Card Scheduling</h1>""" ) )
	        combo = extPrefs.prefsTabAddComboBox( _("Choose Policy"),
			self.PREFS_NEW_CARD_POLICY,
			self.DEFAULT_NEW_CARD_POLICY,
			[ 'Anki Default', 'New cards mixed in', 'Ignore card timing' ],
			self.TIP_NEW_CARD_POLICY
			)
		extPrefs.prefs.connect(combo, QtCore.SIGNAL("currentIndexChanged(int)"), lambda i: self.policySelected(i))
		
		self.slider = extPrefs.prefsTabAddSlider( _("Frequency of new cards during review"),
			self.PREFS_NEW_CARD_DISTRIBUTION,
			self.DEFAULT_NEW_CARD_DISTRIBUTION,
			0, 4, 1, 
			[ _("Old first"), _("1 in 4 new"), _("1 in 2 new"), _("3 in 4 new"), _("New first") ] )

		self.policySelected( getConfig( extPrefs.prefs.config, self.PREFS_NEW_CARD_POLICY, self.DEFAULT_NEW_CARD_POLICY ) )

	def policySelected( self, index ):
		if index == self.NC_POLICY_DISTRIBUTE:
			self.slider.show()
		else:
			self.slider.hide()
		

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitComboBox( self.PREFS_NEW_CARD_POLICY )
		extPrefs.prefsCommitSlider( self.PREFS_NEW_CARD_DISTRIBUTION )
		self.setSchedulingPolicyFromConfig( extPrefs.prefs.config )

	def setSchedulingPolicy( self, schedulingPolicy ):
		self.schedulingPolicy = schedulingPolicy

	def interceptDeckGetCard( self, deck ):
		RlcDebug.debug( "deck get card" )
		return self.schedulingPolicy.getCard( deck )

	def setSchedulingPolicyFromConfig( self, config ):
		policy = getConfig( config, self.PREFS_NEW_CARD_POLICY, self.DEFAULT_NEW_CARD_POLICY )
		if policy == self.NC_POLICY_DISTRIBUTE:
			self.schedulingPolicy = DistributeNewCardsSchedulingPolicy(
				getConfig( config, self.PREFS_NEW_CARD_DISTRIBUTION,
						self.DEFAULT_NEW_CARD_DISTRIBUTION) * 25 )
		elif policy == self.NC_POLICY_SPEEDROUND:
			self.schedulingPolicy = SpeedRoundSchedulingPolicy()
		else:
			self.schedulingPolicy = self.defaultPolicy

		self.setSchedulingPolicy( self.schedulingPolicy )

class ExtendAnkiHelp(object):
	PREFS_ENABLE_SCRIBBLE = 'rlc.bitzer.help.scribble'
	DEFAULT_ENABLE_SCRIBBLE = False
	TIP_ENABLE_SCRIBBLE = """<p>Choose whether or not to enable the scribble pad.  This
				area can be used for practising writing kanji or kana.
				<p>Draw with the left mouse-button held down.  Right mouse-button
				will clear the area."""

	def __init__( self, extPrefs, mw ):
		self.mw = mw
		self.scribbleActive = False
		self.scribble = None
		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )

	def addToPrefsTab( self, extPrefs ):
		extPrefs.prefsTabAddCheckBox( _("Enable scribble pad"),
			self.PREFS_ENABLE_SCRIBBLE,
			self.DEFAULT_ENABLE_SCRIBBLE,
			self.TIP_ENABLE_SCRIBBLE,
			)

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_ENABLE_SCRIBBLE )
		self.setScribble( extPrefs.prefsGetConfig( self.PREFS_ENABLE_SCRIBBLE ) )

	def createScribble( self ):
		mwui = self.mw.mainWin
		self.scribble = QtGui.QWidget()
		layout = QtGui.QVBoxLayout(self.scribble)
		layout.setSpacing(3)
		layout.setMargin(3)

		pad = Painting( mwui.innerHelpFrame, 300, 300 )
		pad.setEnabled( True )
		pad.setMinimumSize(QtCore.QSize(200,0))
		pad.setMaximumSize(QtCore.QSize(300,300))

		button = QtGui.QPushButton(_("Clear Drawing"))
		button.setDefault(True)
		button.setFixedHeight(self.mw.easeButtonHeight)
		self.mw.connect(button, QtCore.SIGNAL("clicked()"),
                     lambda: pad.clearScreen())

		layout.addWidget(button)
		layout.addWidget(pad,1)
	

	def setScribble( self, display=False ):
		mwui = self.mw.mainWin

		RlcDebug.debug( "setScribble(): display = ", display )

		if not display and self.scribbleActive:
			RlcDebug.debug( "setScribble(): hiding" )
			self.scribbleActive = False
			mwui.hboxlayout2.removeWidget( self.helpSplitter )
			mwui.hboxlayout2.addWidget( mwui.help )
			self.scribble.hide()
			self.mw.help.hide()

		elif display and not self.scribbleActive:
			RlcDebug.debug( "setScribble(): showing" )
			self.scribbleActive = True
			if not self.scribble:
				self.createScribble()

			mwui.hboxlayout2.removeWidget( mwui.help )
			self.helpSplitter = QtGui.QSplitter( mwui.innerHelpFrame )
			self.helpSplitter.setOrientation( Qt.Vertical )
			mwui.hboxlayout2.addWidget( self.helpSplitter )
			self.helpSplitter.addWidget( mwui.help )
			self.helpSplitter.addWidget( self.scribble )

			self.helpSplitter.setSizes( [100,150] )

			self.scribble.show()
			self.mw.help.showText( """
<h1>Scribble</h1>
This is the scribble pane.
<p>
The top portion is Anki's help text (where this text appears).
<p>
The bottom part is a drawing area.  Hold the left mouse button, and drag to draw.  Right mouse button clears the drawing.
<p>
Betwen the top & bottom sections is a grab handle so you can re-size the two parts.
<p>
You can disable the scribble functionality from Preferences->RLC Bitzer Settings
""")

##############################

from PyQt4.QtGui import QDialog, QPainter, QWidget, QBrush, QImage, QPen, qRgb, QItemSelectionModel
from PyQt4.QtCore import Qt, QPoint

class Painting(QWidget):

    def __init__(self, parent, width=300, height=200 ):
	QWidget.__init__(self, parent)
	self.image = QImage( width, height , QImage.Format_Mono )
	self.image.setColor( 0, qRgb(0,0,0) )
	self.image.setColor( 1, qRgb(255,255,255) )
	self.scribble = 0
	self.clearScreen()

    def paintEvent(self, ev):
	p = QPainter()
	p.begin(self)
	p.drawImage( QPoint(0,0), self.image )
	p.end()

    def mouseMoveEvent(self, ev):
	if self.scribble:
		self.drawLineTo( QPoint( ev.pos() ) )

    def mousePressEvent(self, ev):
	if bool(ev.buttons() & QtCore.Qt.RightButton):
		self.clearScreen()
	else:
		self.scribble = 1
		self.currentPos=QPoint(ev.pos())

    def mouseReleaseEvent(self, ev):
	self.scribble = 0

    def clearScreen( self ):
	p = QPainter( self.image )
	p.fillRect(self.image.rect(), QBrush(Qt.white))
	self.update()

    def drawLineTo( self, newPos ):
	p = QPainter( self.image )
	pen = QPen(QtCore.Qt.black, 4, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
	p.setPen(pen)
	p.drawLine( self.currentPos, newPos )
	self.currentPos = newPos
	self.update()

###############################################

class AnkiPersonalTrainer(object):
	"""
	Motivate the user to the point of exhaustion :)
	"""

	PREFS_TRAINER_ENABLE = 'rlc.bitzer.trainer.enable'
	DEFAULT_TRAINER_ENABLE = False
	TIP_TRAINER_ENABLE = """<p>The Anki Personal Trainer can be used to limit your Anki
				study sessions.  You can set time limits or card number limits
				on a session.  Pace yourself, and get a sense of accomplishment.
				<p>When the session ends, Anki will ask you if you want to
				extend ... push that little bit further! :)"""
	PREFS_TRAINER_CARD_LIMIT = 'rlc.bitzer.trainer.limit.card'
	DEFAULT_TRAINER_CARD_LIMIT = True
	TIP_TRAINER_CARD_LIMIT = """<p>Enable if you want to set a limit on the number of cards
				you study in a session."""
	PREFS_TRAINER_CARD_LIMIT_VALUE = 'rlc.bitzer.trainer.limit.card.value'
	DEFAULT_TRAINER_CARD_LIMIT_VALUE = 100
	PREFS_TRAINER_TIME_LIMIT = 'rlc.bitzer.trainer.limit.time'
	DEFAULT_TRAINER_TIME_LIMIT = False
	TIP_TRAINER_TIME_LIMIT = """<p>Enable if you want to set a limit on the time you study
				in a session.  Time is in minutes."""
	PREFS_TRAINER_TIME_LIMIT_VALUE = 'rlc.bitzer.trainer.limit.time.value'
	DEFAULT_TRAINER_TIME_LIMIT_VALUE = 60	# minutes

	def __init__( self, extPrefs, mw ):
		self.mw = mw
		self.enable = 0
		self.firstTime = True
		self.cardsThisSession = 0
		self.sessionStart = time.time()
		self.setLimitsFromConfig( mw.config )
		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )
		self.origMoveToState = AnkiQt.moveToState
		AnkiQt.moveToState = lambda main, state: self.interceptMoveToState( main, state )

	def addToPrefsTab( self, extPrefs ):
		extPrefs.prefsTabAddLabel( _("<h1>Personal Trainer</h1>") )
		self.ptCheck = extPrefs.prefsTabAddCheckBox( _("Enable personal trainer"),
			self.PREFS_TRAINER_ENABLE,
			self.DEFAULT_TRAINER_ENABLE,
			self.TIP_TRAINER_ENABLE,
			)
		row =  extPrefs.layout.rowCount()
		extPrefs.prefs.connect(self.ptCheck, QtCore.SIGNAL("stateChanged(int)"), lambda i: self.ptCheckChanged(i))
		self.ptCardCheck = extPrefs.prefsTabAddCheckBox( _("Card limit"),
			self.PREFS_TRAINER_CARD_LIMIT,
			self.DEFAULT_TRAINER_CARD_LIMIT,
			self.TIP_TRAINER_CARD_LIMIT,
			row, 0, 1, 1 )
		extPrefs.prefs.connect(self.ptCardCheck, QtCore.SIGNAL("stateChanged(int)"), lambda i: self.ptCardCheckChanged(i))
		self.ptCardValue = extPrefs.prefsTabAddIntegerBox( None,
			self.PREFS_TRAINER_CARD_LIMIT_VALUE,
			self.DEFAULT_TRAINER_CARD_LIMIT_VALUE,
			1, 1000,
			None,
			row, 1, 1, 1 )
		self.ptTimeCheck = extPrefs.prefsTabAddCheckBox( _("Time limit"),
			self.PREFS_TRAINER_TIME_LIMIT,
			self.DEFAULT_TRAINER_TIME_LIMIT,
			self.TIP_TRAINER_TIME_LIMIT,
			row, 2, 1, 1 )
		extPrefs.prefs.connect(self.ptTimeCheck, QtCore.SIGNAL("stateChanged(int)"), lambda i: self.ptTimeCheckChanged(i))
		self.ptTimeValue = extPrefs.prefsTabAddIntegerBox( None,
			self.PREFS_TRAINER_TIME_LIMIT_VALUE,
			self.DEFAULT_TRAINER_TIME_LIMIT_VALUE,
			10, 600,
			None,
			row, 3, 1, 1 )

		self.ptCheckChanged( self.ptCheck.isChecked() )

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_TRAINER_ENABLE )
		extPrefs.prefsCommitCheckBox( self.PREFS_TRAINER_CARD_LIMIT )
		extPrefs.prefsCommitIntegerBox( self.PREFS_TRAINER_CARD_LIMIT_VALUE )
		extPrefs.prefsCommitCheckBox( self.PREFS_TRAINER_TIME_LIMIT )
		extPrefs.prefsCommitIntegerBox( self.PREFS_TRAINER_TIME_LIMIT_VALUE )
		self.setLimitsFromConfig( extPrefs.prefs.config )

	def setLimitsFromConfig( self, config ):
		self.enable = getConfig( config, self.PREFS_TRAINER_ENABLE, self.DEFAULT_TRAINER_ENABLE )
		self.card_limit = getConfig( config, self.PREFS_TRAINER_CARD_LIMIT, self.DEFAULT_TRAINER_CARD_LIMIT )
		self.card_limit_value = getConfigInt( config, self.PREFS_TRAINER_CARD_LIMIT_VALUE, self.DEFAULT_TRAINER_CARD_LIMIT_VALUE )
		self.time_limit = getConfig( config, self.PREFS_TRAINER_TIME_LIMIT, self.DEFAULT_TRAINER_TIME_LIMIT )
		self.time_limit_value = getConfigInt( config, self.PREFS_TRAINER_TIME_LIMIT_VALUE, self.DEFAULT_TRAINER_TIME_LIMIT_VALUE )


	def ptCheckChanged( self, state ):
		self.ptCardCheck.setEnabled(state)
		self.ptTimeCheck.setEnabled(state)
		if state:
			self.ptCardCheckChanged( self.ptCardCheck.isChecked() )
			self.ptTimeCheckChanged( self.ptTimeCheck.isChecked() )
		else:	
			self.ptCardCheckChanged( False )
			self.ptTimeCheckChanged( False )

	def ptCardCheckChanged( self, state ):
		self.cardsThisSession = 0
		self.ptCardValue.setEnabled(state)

	def ptTimeCheckChanged( self, state ):
		self.sessionStartTime = time.time()
		self.ptTimeValue.setEnabled(state)

	def sessionTimeExpired( self ):
		if self.time_limit:
			now = time.time()
			if now - self.sessionStart > self.time_limit_value:
				return True
			else:
				return False
		else:
			return False
		
	def sessionCardLimitReached( self ):
		if self.card_limit:
			if self.cardsThisSession > self.card_limit_value:
				return True
			else:
				return False
		else:
			return False

	def interceptMoveToState( self, mw, state ):
		if getConfig(mw.config, self.PREFS_TRAINER_ENABLE, self.DEFAULT_TRAINER_ENABLE):
			if state == "showQuestion" and self.firstTime:
				self.firstTime = False
			elif state == "showQuestion":
				self.cardsThisSession = self.cardsThisSession + 1

				# check if session is over
				if self.sessionTimeExpired():
					ans = QtGui.QMessageBox.information( mw, "Anki - Personal Trainer",
						 _( """Time's up.  Good session!!<br>
						But I think you can do more.""" ),
						"5 mins more", "1 mins more", "Enough", 0, 2 )
					if ans == 0:
						self.sessionStart = self.sessionStart + 300
					elif ans == 1:
						self.sessionStart = self.sessionStart + 60
					else:
						state = "deckFinished"

				elif self.sessionCardLimitReached():
					ans = QtGui.QMessageBox.information( mw, "Anki - Personal Trainer",
						_( """Card limit up!  Good session!!<br>
						But I think you can do more.""" ),
						"5 more", "1 more", "Enough", 0, 2 )
					if ans == 0:
						self.cardsThisSession = self.card_limit_value - (5-1)
					elif ans == 1:
						self.cardsThisSession = self.card_limit_value - (1-1)
					else:
						state = "deckFinished"

		self.origMoveToState( mw, state )

###############################################

class AnkiTrayIcon( QtCore.QObject ):
	"""
	Enable minimize to tray
	"""

	PREFS_TRAY_ENABLE = 'rlc.bitzer.tray.enable'
	DEFAULT_TRAY_ENABLE = False
	TIP_TRAY_ENABLE = """<p>Enable support for minimising Anki to the icon tray.
			<p>If this is enabled, the Anki icon will be displayed in the system
			icon tray.  If you click on the icon, the Anki window will be hidden.
			Click again on the icon to re-display Anki.
			<p>When questions are due, a pop-up box will be displayed to remind
			you."""
	def __init__( self, extPrefs, mw ):
		QtCore.QObject.__init__( self, mw )
		self.mw = mw
		self.anki_visible = True
		if QtGui.QSystemTrayIcon.isSystemTrayAvailable():
			self.ti = QtGui.QSystemTrayIcon( mw )
			if self.ti:
				self.ti.setIcon( QtGui.QIcon(":/icons/anki.png") )
				self.ti.setToolTip( "Anki" )

				# hook signls, and Anki state changes
				mw.addView( self )
				mw.connect(self.ti, QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), lambda i: self.activated(i))
				mw.connect(self.ti, QtCore.SIGNAL("messageClicked()"), lambda : self.messageClicked())

				self.setFromConfig( self.mw.config )
				extPrefs.hookSetup( self.addToPrefsTab )
				extPrefs.hookAccept( self.acceptPrefs )

				# intercept events (to detect minimise event)
				mw.installEventFilter( self )

	def addToPrefsTab( self, extPrefs ):
		self.ptCheck = extPrefs.prefsTabAddCheckBox( _("Enable tray icon"),
			self.PREFS_TRAY_ENABLE,
			self.DEFAULT_TRAY_ENABLE,
			self.TIP_TRAY_ENABLE,
			)
		self.ptCheckChanged( self.ptCheck.isChecked() )

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_TRAY_ENABLE )
		self.setFromConfig( extPrefs.prefs.config )

	def setFromConfig( self, config ):
		enable = getConfig( config, self.PREFS_TRAY_ENABLE, self.DEFAULT_TRAY_ENABLE )
		self.ptCheckChanged( enable )

	def ptCheckChanged( self, state ):
		if state:
			if self.ti:
				self.ti.show()
		else:
			if self.ti:
				self.ti.hide()

	def showMain( self ):
		winState = ( self.mw.windowState() & ~Qt.WindowMinimized ) | Qt.WindowActive;
		self.mw.setWindowState( winState )
		self.mw.show()
		self.anki_visible = True

	def hideMain( self ):
		self.mw.hide()
		self.anki_visible = False

	def activated( self, reason ):
		if self.anki_visible:
			self.hideMain()
		else:
			self.showMain()

	def messageClicked( self ):
		if not self.anki_visible:
			self.showMain()

	def setToolTip( self, message ):
		self.ti.setToolTip( message )

	def showMessage( self, message ):
		if self.ti.supportsMessages():
			self.ti.showMessage( "Anki", message )

	def setState( self, state ):
		RlcDebug.debug( "AnkiTrayIcon::setState(): state=" + state )
		if state == "showQuestion":
			if not self.anki_visible:
				self.showMessage( "A new card is available for review, click this message to display Anki" )
			self.setToolTip( "Anki - displaying question" )
		elif state == "showAnswer":
			self.setToolTip( "Anki - displaying answer" )
		elif state == "noDeck":
			self.setToolTip( "Anki - no deck" )
		elif state == "deckFinished":
			if self.mw and self.mw.deck:
				self.setToolTip( "Anki - next card in " + self.mw.deck.earliestTimeStr() )
		else:
			self.setToolTip( "Anki" )

	def getEnabled( self, config ):
		return getConfig( config, self.PREFS_TRAY_ENABLE, self.DEFAULT_TRAY_ENABLE )

	def eventFilter( self, obj, event ):
		if self.getEnabled( self.mw.config ) and self.parent() == obj:
			if event.type() == QtCore.QEvent.WindowStateChange:
				if self.ti and obj.windowState() & Qt.WindowMinimized:
					self.hideMain()
			elif event.type() == QtCore.QEvent.Close:
				if self.ti:
					self.ti.hide()

		return QtCore.QObject.eventFilter(self, obj, event)


###############################################

class ExtendToolTips(QtCore.QObject):
	"""
	Show info on characters hovered over.
	"""

	PREFS_TIPS_ENABLE = 'rlc.bitzer.tips.enable'
	DEFAULT_TIPS_ENABLE = False
	TIP_TIPS_ENABLE = """<p>When enabled, Anki will attempt to display additional
			information about the character under the mouse pointer.  This is
			displayed in a new dockable window.
			<p>The additional information can include:
			<ul>
			  <li>an image file (animated GIFs ok)</li>
			  <li>a HTML page</li>
			</ul>
			The image filename and info URL can include special tags that will be
			replaced by:
			<ul>
			  <li>%(char)s - the character itself</li>
			  <li>%(utf8-hex)s - hex digits for the character in UTF-8. e.g. e5ad90</li>
			  <li>%(utf8-url)s - hex digits for the character in UTF-8, but suitable for adding to a URL. e.g. %e5%ad%90</li>
			</ul>
			"""
	PREFS_TIPS_MOVIE_VALUE = 'rlc.bitzer.tips.movie'
	DEFAULT_TIPS_MOVIE_VALUE = 'soda-utf8/%(char)s.gif'
	TIP_TIPS_MOVIE_VALUE = """<p>Filename for the image file.  Remember that
		special tags will be replaced in the filename.
		<p>e.g. /home/user/soda-utf8/%(char)s.gif
			"""
	PREFS_TIPS_HTML_VALUE = 'rlc.bitzer.tips.html'
	DEFAULT_TIPS_HTML_VALUE = 'soda-utf8/%(char)s.html'
	TIP_TIPS_HTML_VALUE = """<p>Info on the character will be loaded from this URL
		Remember that special tags will be replaced in the URL.
		<p>e.g. http://www.csse.monash.edu.au/~jwb/cgi-bin/wwwjdic.cgi?1MMJ%(utf8-url)s_3
			"""

	def __init__(self, extPrefs, mw):
		QtCore.QObject.__init__( self, mw )
		self.mw = mw
		self.w = QtGui.QDockWidget()
		self.w.setFeatures( QtGui.QDockWidget.DockWidgetMovable|QtGui.QDockWidget.DockWidgetFloatable )
		self.frame = QtGui.QFrame()
		self.w.setWidget( self.frame )
		self.movieLabel = QtGui.QLabel()
		vbox = QtGui.QVBoxLayout()
		self.tip = QtGui.QTextEdit()
		self.tip.setReadOnly( True )
		vbox.addWidget( self.movieLabel )
		vbox.addWidget( self.tip )
		self.frame.setLayout( vbox )
		mw.addDockWidget( Qt.RightDockWidgetArea, self.w )

		self.w.setVisible(self.getEnabled(mw.config))

		self.lastSelected = None

		extPrefs.hookSetup( self.addToPrefsTab )
		extPrefs.hookAccept( self.acceptPrefs )

	def addToPrefsTab( self, extPrefs ):
		self.ptCheck = extPrefs.prefsTabAddCheckBox( _("Enable character tips"),
			self.PREFS_TIPS_ENABLE,
			self.DEFAULT_TIPS_ENABLE,
			self.TIP_TIPS_ENABLE,
			)
		extPrefs.prefs.connect(self.ptCheck, QtCore.SIGNAL("stateChanged(int)"), lambda i: self.ptCheckChanged(i))
		row =  extPrefs.layout.rowCount()
		extPrefs.prefsTabAddLabel( _("Movie:"), None, row, 0, 1, 1 )
		self.ptMovieValue = extPrefs.prefsTabAddStringBox( None,
			self.PREFS_TIPS_MOVIE_VALUE,
			self.DEFAULT_TIPS_MOVIE_VALUE,
			self.TIP_TIPS_MOVIE_VALUE,
			row, 1 )
		row =  extPrefs.layout.rowCount()
		extPrefs.prefsTabAddLabel( _("Info URL:"), None, row, 0, 1, 1 )
		self.ptHtmlValue = extPrefs.prefsTabAddStringBox( None,
			self.PREFS_TIPS_HTML_VALUE,
			self.DEFAULT_TIPS_HTML_VALUE,
			self.TIP_TIPS_HTML_VALUE,
			row, 1 )
		self.ptCheckChanged( self.ptCheck.isChecked() )

	def acceptPrefs( self, extPrefs ):
		extPrefs.prefsCommitCheckBox( self.PREFS_TIPS_ENABLE )
		extPrefs.prefsCommitStringBox( self.PREFS_TIPS_MOVIE_VALUE )
		extPrefs.prefsCommitStringBox( self.PREFS_TIPS_HTML_VALUE )
		self.setFromConfig( extPrefs.prefs.config )

	def setFromConfig( self, config ):
		enable = self.getEnabled(config)
		self.ptMovieValue.setText( self.getMovieValue(config) )
		self.ptHtmlValue.setText( self.getHtmlValue(config) )
		self.ptCheckChanged( enable )

	def ptCheckChanged( self, state ):
		self.ptMovieValue.setEnabled(state)
		self.ptHtmlValue.setEnabled(state)
		self.w.setVisible(state)

	def getEnabled( self, config ):
		return getConfig(config, self.PREFS_TIPS_ENABLE, self.DEFAULT_TIPS_ENABLE)

	def getMovieValue( self, config ):
		return getConfig(config, self.PREFS_TIPS_MOVIE_VALUE, self.DEFAULT_TIPS_MOVIE_VALUE)
	def getHtmlValue( self, config ):
		return getConfig(config, self.PREFS_TIPS_HTML_VALUE, self.DEFAULT_TIPS_HTML_VALUE)

	def expandString( self, specStr, tc ):
		self.lastSelected = tc.selectedText()
		selText = { 'char': unicode(tc.selectedText()),
		  'utf8-hex': repr(unicode(tc.selectedText()).encode('utf8')).replace('\\x','').strip("u'"),
		  'utf8-url': repr(unicode(tc.selectedText()).encode('utf8')).replace('\\x','%').strip("u'"),
		}
		tc.select( tc.WordUnderCursor )
		selText['word'] = unicode(tc.selectedText())
		return unicode(specStr) % selText

	def hookQtEvents( self, parent ):
		self.setParent(parent)
		parent.installEventFilter( self )

	def eventFilter( self, obj, event ):
		if self.getEnabled( self.mw.config ) and self.parent() == obj and event.type() == QtCore.QEvent.ToolTip:
			gpos = event.globalPos()
			pos = self.parent().mapFromGlobal( gpos )
			tc = self.parent().cursorForPosition( pos )
			qr = self.parent().cursorRect(tc)
			# adjust if mouse is on right-half of char
			if pos.x() < qr.topLeft().x():
				tc.movePosition( tc.Left, tc.MoveAnchor )
			tc.movePosition( tc.NextCharacter, tc.KeepAnchor )
			if tc.hasSelection() and tc.selectedText() != self.lastSelected:
				try:
					movieSpecString = self.getMovieValue(self.mw.config)
					movieName = self.expandString( movieSpecString, tc )
					RlcDebug.debug( "Loading movie: ", movieName )
					self.movie = QtGui.QMovie( movieName )
					self.movieLabel.setMovie( self.movie )
					self.movie.start()
				except Exception, e:
					pass

				try:
					htmlSpecString = self.getHtmlValue(self.mw.config)
					htmlName = self.expandString( htmlSpecString, tc )
					RlcDebug.debug( "Loading URL: ", htmlName )
					import urllib
					html = urllib.urlopen( htmlName )
					self.tip.setHtml( unicode(html.read(), 'utf8') )
				except Exception, e:
					self.tip.setText( """Can't load: %s
Due to exception: %s
""" % ( htmlName, e ) )

			elif not tc.hasSelection():
				self.lastSelected = None
				if self.movie:
					self.movie.stop()
			return True
		return QtCore.QObject.eventFilter(self, obj, event)


###############################################

class RlcBitzer( object ):

	def __init__( self, ankiMain ):
		# do early init
		self.mw = ankiMain

		self.extPrefs = ExtendAnkiPrefs( _("RLC Bitzer Settings") )
		self.extMain = ExtendAnkiMain( self.extPrefs )
		self.extHelp = ExtendAnkiHelp( self.extPrefs, self.mw )
		self.extToolTips = ExtendToolTips( self.extPrefs, self.mw )
		if not AnkiFunctionality.isTrayIconImplemented():
			self.trayIcon = AnkiTrayIcon( self.extPrefs, self.mw )

		if not AnkiFunctionality.isEditSelectionImplemented():
			self.extEdit = ExtendAnkiEdit( self.extPrefs )
		self.extScheduler = ExtendAnkiScheduling( self.extPrefs, self.mw.config )
		self.personalTrainer = AnkiPersonalTrainer( self.extPrefs, self.mw )

	def pluginLateInit( self ):
		self.extHelp.setScribble( getConfig( mw.config, self.extHelp.PREFS_ENABLE_SCRIBBLE, self.extHelp.DEFAULT_ENABLE_SCRIBBLE ) )
		self.extToolTips.hookQtEvents( self.mw.mainWin.mainText )


###################################

def hookPluginInit():
	r.pluginLateInit()


# Startup has been split into 2 stages ... early stuff that happens as soon as
# plugin is imported ... used for intercepting deck load
#
# Stage 2 happens off the "init" hook ... and is used to do any initialisation
# after the main anki stuff has loaded

# Stage 1
r = RlcBitzer( mw )
# Hook Stage 2
mw.addHook( "init", hookPluginInit )
