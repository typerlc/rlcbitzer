#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This file is a plugin for anki flashcard application http://ichi2.net/anki/
# ---------------------------------------------------------------------------
# File:        rlc_bitzer.py
# Description: 

# Author:      Richard Colley (richard.colley@rcolley.com)
# 			These comments ripped off from yesno.py by Andreas Klauer (Andreas.Klauer@metamorpher.de)
# Version:     0.04 (2008-03-27)
# License:     GPL
# ---------------------------------------------------------------------------
# Changelog:
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
import time

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
		self.origSetupAdvanced( prefs )
		self.prefsSetup( prefs )
	def __interceptPrefsAccept( self, prefs ):
		self.prefsAccept( prefs )
		self.origPrefsAccept( prefs )
	def __interceptPrefsReject( self, prefs ):
		self.prefsReject( prefs )
		self.origPrefsReject( prefs )
		
	# over-ride these
	def prefsSetup( self, prefs ):
		pass
		
	def prefsAccept( self, prefs ):
		pass
	
	def prefsReject( self, prefs ):
		pass

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

	def prefsTabAddHeading( self, heading ):
		rlcPrefsHeading = QtGui.QLabel(self.rlcPrefsTab)
		rlcPrefsHeading.setObjectName("rlcPrefsHeading")
		rlcPrefsHeading.setText( heading )
		self.rlcPrefsGridLayout.addWidget(rlcPrefsHeading,self.rlcPrefsGridLayout.rowCount(),0,1,1)

	def prefsTabAddCheckBox( self, label, itemName, initialValue ):
		rlcPrefsCheckBox = QtGui.QCheckBox(self.rlcPrefsTab)
		rlcPrefsCheckBox.setObjectName( itemName )
		rlcPrefsCheckBox.setText( label )
		self.rlcPrefsGridLayout.addWidget(rlcPrefsCheckBox,self.rlcPrefsGridLayout.rowCount(),0,1,1)

		rlcPrefsCheckBox.setChecked( initialValue )
		self.tabItems[itemName] = rlcPrefsCheckBox

	def prefsGetItem( self, itemName ):
		return self.tabItems[itemName]


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

	def interceptSelectLastCard( self, main ):
		self.origSelectLastCard( main )
		
	def findCardInDeckModel( self, model, card ):
		for i, thisCard in enumerate( model.cards ):
			if thisCard.id == card.id:
				return i
		return -1

###############################################

class RlcPrefs( ExtendAnkiPrefs, ExtendAnkiMain, ExtendAnkiEdit ):
	def __init__( self, ankiMain ):
		self.mw = ankiMain
		ExtendAnkiPrefs.__init__( self )
		ExtendAnkiMain.__init__( self )
		ExtendAnkiEdit.__init__( self )
		self.initConfig( ankiMain )
		
	def initConfig( self, mw ):
		# set to 1 to allow update checks to be completely disabled by user
		self.permitUpdateDisable = 0
		if not self.permitUpdateDisable:
			mw.config['rlc.checkForUpdate'] = 1

		if not mw.config.has_key( 'rlc.focusOnAnswer' ):
			mw.config['rlc.focusOnAnswer'] = 1
		if not mw.config.has_key( 'rlc.checkForUpdate' ):
			mw.config['rlc.checkForUpdate'] = 1
		if not mw.config.has_key( 'rlc.quietenUpdate' ):
			mw.config['rlc.quietenUpdate'] = 0
		if not mw.config.has_key( 'rlc.edit.startupOnlyCurrent' ):
			mw.config['rlc.edit.startupOnlyCurrent'] = 0

	def prefsSetup( self, prefs ):
		focusOnAnswer = prefs.config['rlc.focusOnAnswer']
		checkForUpdate = prefs.config['rlc.checkForUpdate']
		quietenUpdate = prefs.config['rlc.quietenUpdate']
		editStartupOnlyCurrent = prefs.config['rlc.edit.startupOnlyCurrent']

		self.prefsAddTab( prefs, _("RLC Plugin Settings") )
		self.prefsTabAddHeading( _("<h1>Main Window Settings</h1>") )
		self.prefsTabAddCheckBox( _("Focus on answer"), "rlcPrefsFocusOnAnswer", focusOnAnswer )
		if self.permitUpdateDisable:
			self.prefsTabAddCheckBox( _("Check for Anki updates"), "rlcPrefsCheckForUpdate", checkForUpdate )
		self.prefsTabAddCheckBox( _("Suppress update dialog"), "rlcPrefsQuietenUpdate", quietenUpdate )
		self.prefsTabAddHeading( _("<h1>Edit Cards Window</h1>") )
		self.prefsTabAddCheckBox( _("Start Edit Deck with only the current card displayed"), "rlcPrefsEditStartupOnlyCurrent", editStartupOnlyCurrent )

	def prefsAccept( self, prefs ):
		prefs.config['rlc.focusOnAnswer'] = self.prefsGetItem("rlcPrefsFocusOnAnswer").isChecked()
		if self.permitUpdateDisable:
			prefs.config['rlc.checkForUpdate'] = self.prefsGetItem("rlcPrefsCheckForUpdate").isChecked()
		prefs.config['rlc.quietenUpdate'] = self.prefsGetItem("rlcPrefsQuietenUpdate").isChecked()
		prefs.config['rlc.edit.startupOnlyCurrent'] = self.prefsGetItem("rlcPrefsEditStartupOnlyCurrent").isChecked()

	def interceptShowEaseButtons( self, mw ):
		# call original method
		ExtendAnkiMain.interceptShowEaseButtons( self, mw )
		if not mw.config['rlc.focusOnAnswer']:
			# now remove focus from answer button by setting focus to the main window
			mw.setFocus()

	def interceptSetupAutoUpdate( self, mw ):
		if mw.config['rlc.checkForUpdate']:
			ExtendAnkiMain.interceptSetupAutoUpdate( self, mw )

	def interceptNewVerAvail( self, mw, version ):
		if mw.config['rlc.quietenUpdate']:
			mw.statusView.statusbar.showMessage( _("Anki Update Available: ") + version, 5000 )
		else:
			ExtendAnkiMain.interceptNewVerAvail( self, mw, version )

	def interceptSelectLastCard( self, edit ):
		if self.mw.config['rlc.edit.startupOnlyCurrent']:
			ExtendAnkiEdit.interceptSelectLastCard( self, edit )
		else:
			edit.updateSearch()
			if edit.parent.currentCard:
				currentCardIndex = self.findCardInDeckModel( edit.model, edit.parent.currentCard )
				if currentCardIndex >= 0:
					edit.dialog.tableView.selectRow( currentCardIndex )
					edit.dialog.tableView.scrollTo( edit.model.index(currentCardIndex,0), edit.dialog.tableView.PositionAtTop )
					

##############################

from PyQt4.QtGui import QDialog, QPainter, QWidget, QBrush, QImage, QPen, qRgb, QItemSelectionModel
from PyQt4.QtCore import Qt, QPoint

class Painting(QWidget):

    def __init__(self, *args):
	apply(QWidget.__init__,(self, ) + args)
	self.image = QImage( 300, 300 , QImage.Format_Mono )
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

class PaintingWindow( QDialog ):
    def __init__(self, *args):
	apply(QWidget.__init__,(self, ) + args)
	self.resize( 300,300 )
	self.painting = Painting(self)
	layout = QtGui.QVBoxLayout()	
	layout.addWidget( self.painting )
	self.setLayout( layout )
	self.show()

#pw = PaintingWindow()


def hookPluginInit():
	RlcPrefs( mw )

mw.addHook( "init", hookPluginInit )
