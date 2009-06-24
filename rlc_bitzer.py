#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This file is a plugin for anki flashcard application http://ichi2.net/anki/
# ---------------------------------------------------------------------------
# File:        rlc_bitzer.py
# Description: 
#
# Author:      Richard Colley (richard.colley@rcolley.com)
# Version:     0.06 (2008-03-30)
# License:     GPL
# ---------------------------------------------------------------------------
# Changelog:
# ---- 0.06 -- 2008-03-27 -- Richard Colley ----
#   finalised scribble pad
# ---- 0.05 -- 2008-03-27 -- Richard Colley ----
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


############ Debug stuff

import traceback
class RlcDebug(object):
	disabled = 0
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

class ExtendAnkiPrefs():
	def __init__( self ):
		self.tabItems = {}
		self.origSetupAdvanced = Preferences.setupAdvanced
		self.origPrefsAccept = Preferences.accept
		self.origPrefsReject = Preferences.reject
		Preferences.setupAdvanced = lambda prefs: self.__interceptSetupAdvanced( prefs )
		Preferences.accept = lambda prefs: self.__interceptPrefsAccept( prefs )
		Preferences.reject = lambda prefs: self.__interceptPrefsReject( prefs )

	# probably shouldn't touch these
	def __interceptSetupAdvanced( self, prefs ):
		self.config = prefs.config
		self.origSetupAdvanced( prefs )
		self.prefsSetup( prefs )
	def __interceptPrefsAccept( self, prefs ):
		self.config = prefs.config
		self.prefsAccept( prefs )
		self.origPrefsAccept( prefs )
	def __interceptPrefsReject( self, prefs ):
		self.config = prefs.config
		self.prefsReject( prefs )
		self.origPrefsReject( prefs )
		
	# over-ride these
	def prefsSetup( self, prefs ):
		pass
		
	def prefsAccept( self, prefs ):
		pass
	
	def prefsReject( self, prefs ):
		pass

	def prefsGetConfig( self, itemName, defaultValue=None ):
		if self.config.has_key( itemName ):
			return self.config[itemName]
		else:
			return defaultValue

	def prefsSetConfig( self, itemName, value ):
		self.config[itemName] = value

	def prefsGetItem( self, itemName ):
		return self.tabItems[itemName]

	def prefsCommitCheckBox( self, itemName ):
		checkBox = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, checkBox.isChecked() )

	def prefsCommitSlider( self, itemName ):
		slider = self.prefsGetItem( itemName )
		self.prefsSetConfig( itemName, slider.value() )


	# UI stuff
	def prefsAddTab( self, prefs, tabTitle ):
		self.tabTitle = tabTitle
		self.rlcPrefsTab = QtGui.QWidget()
		self.rlcPrefsTab.setObjectName( "rlcPrefsTab" )
		self.rlcPrefsTabVboxLayout = QtGui.QVBoxLayout(self.rlcPrefsTab)
		self.rlcPrefsTabVboxLayout.setObjectName("rlcPrefsTabVboxLayout")

		self.rlcPrefsGridLayout = QtGui.QGridLayout()
		self.rlcPrefsGridLayout.setObjectName("rlcPrefsGridLayout")

		self.rlcPrefsTabVboxLayout.addLayout(self.rlcPrefsGridLayout)
		spacerItem1 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
		self.rlcPrefsTabVboxLayout.addItem(spacerItem1)

		prefs.dialog.tabWidget.addTab(self.rlcPrefsTab,self.tabTitle)

	def prefsTabAddLabel( self, labelText ):
		label = QtGui.QLabel(self.rlcPrefsTab)
		label.setText( labelText )
		self.rlcPrefsGridLayout.addWidget(label,self.rlcPrefsGridLayout.rowCount(),0,1,1)

	def prefsTabAddCheckBox( self, label, itemName, defaultValue ):
		checkBox = QtGui.QCheckBox(self.rlcPrefsTab)
		checkBox.setObjectName( itemName )
		checkBox.setText( label )

		checkBox.setChecked( self.prefsGetConfig( itemName, defaultValue ) )
		self.tabItems[itemName] = checkBox
		self.rlcPrefsGridLayout.addWidget(checkBox,self.rlcPrefsGridLayout.rowCount(),0,1,1)

	def prefsTabAddSlider( self, label, itemName, defaultValue, min, max, step ):
		slider = QtGui.QSlider( self.rlcPrefsTab )
		slider.setOrientation( Qt.Horizontal )
		slider.setTickPosition(QtGui.QSlider.TicksBelow)
		slider.setMinimum( min )
		slider.setMaximum( max )
		slider.setTickInterval( step )
		slider.setSingleStep(step)
		slider.setPageStep(step)
		slider.setSliderPosition( self.prefsGetConfig( itemName, defaultValue ) / step )
		self.tabItems[itemName] = slider
		self.rlcPrefsGridLayout.addWidget(slider,self.rlcPrefsGridLayout.rowCount(),0,1,1)

class ExtendAnkiMain():
	def __init__( self ):
		self.origShowEaseButtons = AnkiQt.showEaseButtons
		AnkiQt.showEaseButtons = lambda main: self.interceptShowEaseButtons( main )
		self.origSetupAutoUpdate = AnkiQt.setupAutoUpdate
		AnkiQt.setupAutoUpdate = lambda main: self.interceptSetupAutoUpdate( main )
		self.origNewVerAvail = AnkiQt.newVerAvail
		AnkiQt.newVerAvail = lambda main, version: self.interceptNewVerAvail( main, version )

	def interceptShowEaseButtons( self, main ):
		self.origShowEaseButtons( main )

	def interceptSetupAutoUpdate( self, main ):
		self.origSetupAutoUpdate( main )

	def interceptNewVerAvail( self, main, version ):
		self.origNewVerAvail( main, version )

class ExtendAnkiEdit():
	def __init__( self ):
		self.origSelectLastCard = EditDeck.selectLastCard
		EditDeck.selectLastCard = lambda edit: self.interceptSelectLastCard( edit )
		DeckModel.findCard = lambda model, card: self.findCardInDeckModel( model, card )

	def interceptSelectLastCard( self, edit ):
		self.origSelectLastCard( edit )
		
	def findCardInDeckModel( self, model, card ):
		for i, thisCard in enumerate( model.cards ):
			if thisCard.id == card.id:
				return i
		return -1

######################

import time
from heapq import heappush, heappop
from anki.deck import Deck
import anki

class CardSchedulingPolicy():
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
		RlcDebug.debug( "Default returning card: ", card.question )
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
		    if not deck.failedCardsDueSoon():
			# stop
			return
		    # otherwise, go into final review mode.
		    item = deck.getOldestModifiedFailedCard()
		    if item.due - time.time() > deck.collapseTime:
			return
		# if it's not failed, check if it's spaced
		if item.successive or item.reps == 0:
		    space = deck.itemSpacing(item)
		    if space > now:
			# update due time and put it back in future queue
			item.due = max(item.due, space)
			heappush(deck.futureQueue, item)
			return deck.getCard()
		card = deck.s.query(anki.cards.Card).get(item.id)
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
		return card

class ExtendAnkiScheduling():
	def __init__( self ):
		self.oldDeckGetCard = Deck.getCard
		Deck.getCard = lambda deck : self.interceptDeckGetCard( deck )
		self.schedulingPolicy = AnkiDefaultSchedulingPolicy( self.oldDeckGetCard )

	def setSchedulingPolicy( self, schedulingPolicy ):
		self.schedulingPolicy = schedulingPolicy

	def interceptDeckGetCard( self, deck ):
		RlcDebug.debug( "deck get card" )
		return self.schedulingPolicy.getCard( deck )


class ExtendAnkiHelp():
	def __init__( self, mw ):
		self.mw = mw
		self.scribbleActive = False
		self.scribble = None

	def createScribble( self ):
		mwui = self.mw.mainWin
		self.scribble = Painting( mwui.innerHelpFrame, 300, 300 )
		self.scribble.setEnabled( True )
		self.scribble.setMinimumSize(QtCore.QSize(200,0))
		self.scribble.setMaximumSize(QtCore.QSize(300,300))

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

class RlcBitzer( ExtendAnkiPrefs, ExtendAnkiMain, ExtendAnkiEdit, ExtendAnkiScheduling ):

	# set to 1 to allow update checks to be completely disabled by user
	permitUpdateDisable = 0

	PREFS_FOCUS_ON_ANSWER = 'rlc.bitzer.answer.focusOnButton'
	PREFS_CHECK_FOR_UPDATE = 'rlc.bitzer.update.check'
	PREFS_QUIETEN_UPDATE = 'rlc.bitzer.update.quieten'
	PREFS_EDIT_CURRENT = 'rlc.bitzer.edit.startupOnlyCurrent'
	PREFS_NEW_CARD_DISTRIBUTION  = 'rlc.bitzer.cards.new.distribution'
	PREFS_ENABLE_SCRIBBLE = 'rlc.bitzer.help.scribble'

	def __init__( self, ankiMain ):
		# do early init
		ExtendAnkiPrefs.__init__( self )
		ExtendAnkiMain.__init__( self )
		ExtendAnkiEdit.__init__( self )
		ExtendAnkiScheduling.__init__( self )

		self.mw = ankiMain

		self.schedulingPolicy = DistributeNewCardsSchedulingPolicy(
			self.getConfig(self.PREFS_NEW_CARD_DISTRIBUTION,0) * 25 )

		self.setSchedulingPolicy( self.schedulingPolicy )

	def getConfig( self, item, default=None ):
		if self.mw.config.has_key( item ):
			return self.mw.config[item]
		else:
			return default

	def setConfig( self, item, value ):
		self.mw.config[item] = value

	def pluginInit( self ):
		self.extHelp = ExtendAnkiHelp( self.mw )
		self.extHelp.setScribble( self.getConfig( self.PREFS_ENABLE_SCRIBBLE ) )

	########################################
	# Over-ride methods in ExtendAnkiPrefs
	########################################

	def prefsSetup( self, prefs ):
		self.prefsAddTab( prefs, _("RLC Bitzer Settings") )
		self.prefsTabAddLabel( _("<h1>Main Window Settings</h1>") )
		self.prefsTabAddCheckBox( _("Focus on answer"), self.PREFS_FOCUS_ON_ANSWER, 1 )
		if self.permitUpdateDisable:
			self.prefsTabAddCheckBox( _("Check for Anki updates"), self.PREFS_CHECK_FOR_UPDATE, 1 )
		self.prefsTabAddCheckBox( _("Suppress update dialog"), self.PREFS_QUIETEN_UPDATE, 0 )
		self.prefsTabAddCheckBox( _("Enable scribble pad"), self.PREFS_ENABLE_SCRIBBLE, 0 )
		self.prefsTabAddLabel( _("<h1>Edit Cards Window</h1>") )
		self.prefsTabAddCheckBox( _("Start Edit Deck with only the current card displayed"), self.PREFS_EDIT_CURRENT, 1 )
		self.prefsTabAddLabel( _(
"""<h1>Card Scheduling</h1>
This setting changes whether or not you see New cards while you are<br>
still reviewing Old cards.
<p>
By setting this to the far-left, you retain the original Anki behaviour<br>
of showing no New cards if there are Old cards due.
<p>
By setting this to the far-right, New cards will be shown <b>before</b><br>
Old cards are shown.
""") )
		self.prefsTabAddSlider( _("Frequency of new cards during review"), self.PREFS_NEW_CARD_DISTRIBUTION, 0, 0, 4, 1 )

	def prefsAccept( self, prefs ):
		RlcDebug.debug( "prefsAccept: called" )
		self.prefsCommitCheckBox( self.PREFS_FOCUS_ON_ANSWER )
		if self.permitUpdateDisable:
			self.prefsCommitCheckBox( self.PREFS_CHECK_FOR_UPDATE )
		self.prefsCommitCheckBox( self.PREFS_QUIETEN_UPDATE )
		self.prefsCommitCheckBox( self.PREFS_EDIT_CURRENT )
		self.prefsCommitSlider( self.PREFS_NEW_CARD_DISTRIBUTION )
		self.schedulingPolicy.setDistribution( self.prefsGetConfig( self.PREFS_NEW_CARD_DISTRIBUTION )*25 )
		self.prefsCommitCheckBox( self.PREFS_ENABLE_SCRIBBLE )
		self.extHelp.setScribble( self.prefsGetConfig( self.PREFS_ENABLE_SCRIBBLE ) )


	########################################
	# Over-ride methods in ExtendAnkiMain
	########################################

	def interceptShowEaseButtons( self, mw ):
		# call original method
		ExtendAnkiMain.interceptShowEaseButtons( self, mw )
		if not self.getConfig(self.PREFS_FOCUS_ON_ANSWER):
			# now remove focus from answer button
			mw.setFocus()

	def interceptSetupAutoUpdate( self, mw ):
		if self.getConfig(self.PREFS_CHECK_FOR_UPDATE):
			ExtendAnkiMain.interceptSetupAutoUpdate( self, mw )

	def interceptNewVerAvail( self, mw, version ):
		if self.getConfig(self.PREFS_QUIETEN_UPDATE):
			mw.statusView.statusbar.showMessage( _("Anki Update Available: ") + version, 5000 )
		else:
			ExtendAnkiMain.interceptNewVerAvail( self, mw, version )

	########################################
	# Over-ride methods in ExtendAnkiEdit
	########################################

	def interceptSelectLastCard( self, edit ):
		if self.getConfig(self.PREFS_EDIT_CURRENT):
			ExtendAnkiEdit.interceptSelectLastCard( self, edit )
		else:
			edit.updateSearch()
			if edit.parent.currentCard:
				currentCardIndex = self.findCardInDeckModel( edit.model, edit.parent.currentCard )
				if currentCardIndex >= 0:
					edit.dialog.tableView.selectRow( currentCardIndex )
					edit.dialog.tableView.scrollTo( edit.model.index(currentCardIndex,0), edit.dialog.tableView.PositionAtTop )
					

###################################



def hookPluginInit():
	r.pluginInit()


# Startup has been split into 2 stages ... early stuff that happens as soon as
# plugin is imported ... used for intercepting deck load
#
# Stage 2 happens off the "init" hook ... and is used to do any initialisation
# after the main anki stuff has loaded

# Stage 1
r = RlcBitzer( mw )
# Hook Stage 2
mw.addHook( "init", hookPluginInit )
