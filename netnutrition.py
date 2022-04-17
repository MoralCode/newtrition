from bs4 import BeautifulSoup
from helpers import grab_id_from_parens
from dataclasses import dataclass
from constants import NN_BASE_URL
import requests
class NetNutrition:
	"""A class representing the net nutrition API and keeping track of the current state?
	"""
	pass


@dataclass
class DiningLocation:
	name:str
	identifier: int

	def get_menus(self, session=requests):
		if self._menus is not None:
			return self.menus
		
		menus_url = NN_BASE_URL + "/Unit/SelectUnitFromUnitsList"
		menu_data = "unitOid=" + str(artesanos.identifier)
		menu_headers = {
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			# "Accept": "*/*",
			"Referer": NN_BASE_URL
		}

		menu_response = session.post(menus_url, data=menu_data, headers=menu_headers)
		menu_panels = menu_response.json().get("panels")
		menu_panel = next((x for x in menu_panels if x.get("id") == "menuPanel"), None)
		if not menu_panel:
			print("cannot find menu html")
		menu_html = menu_panel.get("html")
		menu_list_html = BeautifulSoup(menu_html, 'html.parser') 
		menu_list_items = menu_list_html.find(id="cbo_nn_menuDataList").find(class_="row").children
		self._menus = [DiningMenu.from_html(html, for_location=self) for html in menu_list_items]
		return self._menus

	@classmethod
	def from_html(cls, html):
		link = html.find(class_="cbo_nn_unitNameLink")
		name = link.string
		identifier = grab_id_from_parens(link["onclick"])
		return cls(name, identifier)

	# def __init__(self, name, identifier):
	# 	self.name = name
	# 	self.id = identifier

@dataclass
class DiningMenu:
	date:str
	identifier:int

	@property
	def location(self):
		return self._location
	
	@property.setter
	def location(self, location):
		self._location = location

	@classmethod
	def from_html(cls, html, for_location=None):
		title = html.find(class_="card-title")
		date = title.string
		identifier = grab_id_from_parens(html.find(class_="cbo_nn_menuLink")["onclick"])
		ins = cls(date, identifier)
		if for_location:
			ins.location = for_location
		return ins