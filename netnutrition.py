from bs4 import BeautifulSoup
from helpers import grab_id_from_parens, html_from_json_panel
from dataclasses import dataclass
from constants import NN_BASE_URL, JSON_HEADERS
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
		
		menu_response = session.post(
			NN_BASE_URL + "/Unit/SelectUnitFromUnitsList",
			data="unitOid=" + str(self.identifier),
			headers=JSON_HEADERS)
		menu_html = html_from_json_panel(menu_response.json(),"menuPanel")
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

	def __init__(self, name, identifier):
		self.name = name
		self.identifier = identifier
		self._menus = None


@dataclass
class DiningMenu:
	date:str
	identifier:int

	def __init__(self, date, identifier):
		self.date = date
		self.identifier = identifier
		self._location = None
		self._items = None

	@property
	def location(self):
		return self._location
	
	@location.setter
	def location(self, val):
		self._location = val

	def get_items(self, session=requests):
		if self._items is not None:
			return self.menus
		
		menuitem_response = session.post(
			NN_BASE_URL + "/Menu/SelectMenu",
			data="menuOid=" + str(self.identifier),
			headers=JSON_HEADERS)
		menuitem_html = html_from_json_panel(menuitem_response.json(), "itemPanel")
		menuitem_list_html = BeautifulSoup(menuitem_html, 'html.parser') 
		# print(menuitem_list_html)
		menuitem_list_items = menuitem_list_html.find("table").find_all(class_=["cbo_nn_itemPrimaryRow", "cbo_nn_itemAlternateRow"])
		self._items = [DiningMenuItem.from_html(html, for_menu=self) for html in menuitem_list_items]
		return self._items

	@classmethod
	def from_html(cls, html, for_location=None):
		title = html.find(class_="card-title")
		date = title.string
		identifier = grab_id_from_parens(html.find(class_="cbo_nn_menuLink")["onclick"])
		ins = cls(date, identifier)
		if for_location is not None:
			ins.location = for_location
		return ins



@dataclass
class DiningMenuItem:
	date:str
	identifier:int

	def __init__(self, date, identifier):
		self.date = date
		self.identifier = identifier
		self._menu = None

	@property
	def menu(self):
		return self._menu
	
	@menu.setter
	def menu(self, val):
		self._menu = val

	@classmethod
	def from_html(cls, html, for_menu=None):
		title = html.find(class_="card-title")
		date = title.string
		identifier = grab_id_from_parens(html.find(class_="cbo_nn_menuLink")["onclick"])
		ins = cls(date, identifier)
		if for_menu is not None:
			ins.menu = for_menu
		return ins