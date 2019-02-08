import os
import time
import urllib
import glob
import requests

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
from datetime import datetime, timedelta

ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_SPACE = 12
ACTION_ENTER = 7
ACTION_SELECT = 93

__addon__ = xbmcaddon.Addon()
api = __addon__.getSetting("api1")
host = __addon__.getSetting("url1")


data_path = xbmc.translatePath(__addon__.getAddonInfo('profile'))
black = os.path.join(__addon__.getAddonInfo('path'), 'resources', 'media', 'black.png')

coords = (0, 0, 1280, 720)
txtctl = 0


url = "http://" + host + ":8080/?action=snapshot"


def file_fmt():
    return os.path.join(data_path, "{0}.{{0}}.jpg".format(time.time()))


class CamView(xbmcgui.WindowDialog):
	def __init__(self):
		self.host = host
		self.s = requests.Session()
		headers = {
			'X-Api-Key': api,
			'Content-Type': 'application/json'
			}
		self.s.headers.update(headers)
		self.addControl(xbmcgui.ControlImage(0, 0, 1280, 720, black))
		self.image_controls = []
		self.txt_controls = []
		image_file_fmt = file_fmt()
		image_file = image_file_fmt.format(1)
		urllib.urlretrieve(url, image_file)
		self.cam = xbmcgui.ControlImage(*coords, filename=image_file, aspectRatio=2)
		self.addControl(self.cam)
		self.addControl(xbmcgui.ControlLabel(0, 0, 1280, 720, "Octoprint", alignment = 0x00000000, font="font34", textColor="0xFFFFFFFF"))
		self.closing = False
		temp = "nothing"
		self.status = xbmcgui.ControlLabel(0, 30, 1280, 720, temp, alignment = 0x00000000, font="font14", textColor="0xFFFFFFFF")
		self.jobname = xbmcgui.ControlLabel(0, 50, 1280, 720, temp, alignment = 0x00000000, font="font14", textColor="0xFFFFFFFF")
		self.tempstat = xbmcgui.ControlLabel(0, 70, 1280, 720, temp, alignment = 0x00000000, font="font14", textColor="0xFFFFFFFF")
		self.progress = xbmcgui.ControlLabel(0, 90, 1280, 720, temp, alignment = 0x00000000, font="font14", textColor="0xFFFFFFFF")
		self.addControl(self.status)
		self.addControl(self.jobname)
		self.addControl(self.tempstat)
		self.addControl(self.progress)
		
	def __enter__(self):
		return self

	def get_bed_temp(self):
		data = self.s.get('http://' + self.host + '/api/printer/bed').content.decode('utf-8').split('\n')
		for line in data:
			if 'actual' in line:
				return line[line.find(':')+1:line.find(',')]
		return 0
		
	def get_extruder_current_temp(self):
		data = self.s.get('http://' + self.host + '/api/printer/tool').content.decode('utf-8').split('\n')
		for line in data:
			if 'actual' in line:
				return line[line.find(':')+1:line.find(',')]
		return 0
		

	def get_file_printing(self):
		data = self.s.get('http://' + self.host + '/api/job').content.decode('utf-8').split('\n')
		for line in data:
			if 'name' in line:
			# check if null
				if 'null' in line:
					return 0
				else:
					return line[line.find(':')+1:line.find(',')].replace('"', '').strip()
		return 0
		
	def get_print_progress(self):
		data = self.s.get('http://' + self.host + '/api/job').content.decode('utf-8').split('\n')
		for line in data:
			if 'completion' in line:
			# check if null
				if 'null' in line:
					return 0
				else:
					return int(float(line[line.find(':')+1:line.find(',')].replace(',', '').strip()))
		return 0

	def get_estimatePrinttime(self):
		data = self.s.get('http://' + self.host + '/api/job').content.decode('utf-8').split('\n')
		for line in data:
			if 'estimatedPrintTime' in line:
			# check if null
				if 'null' in line:
					return 0
				else:
					return line[line.find(':')+1:line.find(',')].replace(',', '').strip()
		return 0
			
	def get_printTimeLeft(self):
		data = self.s.get('http://' + self.host + '/api/job').content.decode('utf-8').split('\n')
		for line in data:
			if 'printTimeLeft' in line:
			# check if null
				if 'null' in line:
					time66 = self.get_estimatePrinttime()
					return int(float(time66))
				else:
					return int(line[line.find(':')+1:line.find(',')].replace(',', '').strip())
		return 0
		
	def get_printerState(self):
		data = self.s.get('http://' + self.host + '/api/job').content.decode('utf-8').split('\n')
		for line in data:
			if 'state' in line:
			# check if null
				if 'null' in line:
					0
				else:
					return line[line.find(':')+1:line.find(',')].replace('"', '').strip()
		return "Detenido..."
		
	def pausePrint(self):
		r = self.s.post('http://' + self.host + '/api/job', json={'command': 'pause'})


		
	def onAction(self, action):
		print str(action)
		if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK, ACTION_STOP):
			self.stop()
		elif action in (ACTION_SPACE, ACTION_ENTER, ACTION_SELECT):
			self.pausePrint()


	def start(self):
		self.show()
		while(not self.closing):
			image_file_fmt = file_fmt()
			nozzeltemp = self.get_extruder_current_temp()
			heatbed = self.get_bed_temp()
			tempsline = "Ext1:" + str(nozzeltemp) + "c   bed:" + str(heatbed) + "c"
			jobline = "Filename: " + str(self.get_file_printing())
			sec = timedelta(seconds=self.get_printTimeLeft())
			d = datetime(1,1,1) + sec
			timeleft = str(self.get_print_progress()) + "% timeleft: " + str(d.day-1) + " days " + str(d.hour) + ":" + str(d.minute) + ":" + str(d.second)
			printerstate = "Status: " + str(self.get_printerState())
			image_file = image_file_fmt.format(1)
			urllib.urlretrieve(url, image_file)
			viewer.cam.setImage(image_file, useCache=False)
			viewer.status.setLabel(str(printerstate))
			viewer.jobname.setLabel(str(jobline))
			viewer.tempstat.setLabel(str(tempsline))
			viewer.progress.setLabel(str(timeleft))
			xbmc.sleep(200)


	def stop(self):
		self.closing = True
		self.close()
        
	def __exit__(self, exc_type, exc_value, traceback):
		for f in glob.glob(os.path.join(data_path, "*.jpg")):
			os.remove(f)


with CamView() as viewer:
    viewer.start()

del viewer
