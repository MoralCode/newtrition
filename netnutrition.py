from bs4 import BeautifulSoup
from helpers import grab_id_from_parens, html_from_json_panel, extract_nutrition_info, clean_value, ingredient_split
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
			return self._menus
		
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
	name:str
	identifier:int

	def __init__(self, name, identifier):
		self.name = name
		self.identifier = identifier
		self._menu = None
		self._nutrition = None

	@property
	def nutrition(self):
		return self._nutrition
	
	@nutrition.setter
	def nutrition(self, val):
		self._nutrition = val

	def get_nutrition_info(self, session=requests):
		if self._nutrition is not None:
			return self._nutrition
		
		nutrition_response = session.post(
			NN_BASE_URL + "/NutritionDetail/ShowItemNutritionLabel",
			data="detailOid=" + str(self.identifier),
			headers=JSON_HEADERS)
		nutrition_html = BeautifulSoup(nutrition_response.content, 'html.parser') 
		data = list(nutrition_html.find("table").children)
		
		#ignore the forst two rows: name and "nutrition information" heading
		currentrow = 2
		
		#servings per container
		serv = data[currentrow].find(class_="cbo_nn_LabelBottomBorderLabel")
		spc = list(serv.children)[0].string.split("\xa0")[0]
		servsize = serv.find(class_="inline-div-right").string

		# cals per serving
		currentrow += 1
		cals = int(data[currentrow].find(class_="inline-div-right").string)

		servinginfo = Serving(int(spc), clean_value(servsize), cals)


		# % dv heading, skip this
		currentrow += 1

		# Total fat
		currentrow += 1
		total_fat = extract_nutrition_info(data[currentrow])
		# saturated fat
		currentrow += 1
		saturated_fat = extract_nutrition_info(data[currentrow])
		# trans fat
		currentrow += 1
		trans_fat = extract_nutrition_info(data[currentrow])
		#Cholesterol
		currentrow += 1
		cholesterol = extract_nutrition_info(data[currentrow])
		# Sodium
		currentrow += 1
		sodium = extract_nutrition_info(data[currentrow])
		# Total Carbohydrate
		currentrow += 1
		total_carbohydrate = extract_nutrition_info(data[currentrow])
		# Dietary Fiber
		currentrow += 1
		fiber = extract_nutrition_info(data[currentrow])
		# Total Sugars
		currentrow += 1
		total_sugars = extract_nutrition_info(data[currentrow])
		# Protein
		currentrow += 1
		protein = extract_nutrition_info(data[currentrow])

		nutritionfacts = NutritionFacts(total_fat, saturated_fat, trans_fat, cholesterol, sodium, total_carbohydrate, fiber, total_sugars, protein)
		# second table label/spacer
		currentrow += 1
		# label disclaimer
		currentrow += 1
		

		# ingredients
		currentrow += 1
		ingredients = data[currentrow].find(class_="cbo_nn_LabelIngredients").string
		ingredients = ingredient_split(ingredients, ",")

		# allergens
		currentrow += 1

		allergens = data[currentrow].find(class_="cbo_nn_LabelAllergens").string.split(",")
		allergens = [clean_value(a) for a in allergens]

		self._nutrition = NutritionLabel(servinginfo, nutritionfacts, ingredients, allergens)
		return self._nutrition

	@classmethod
	def from_html(cls, html, for_menu=None):
		item = html.find(class_="cbo_nn_itemHover")
		name = next(item.children)
		identifier = grab_id_from_parens(item["onclick"])
		ins = cls(name, identifier)
		if for_menu is not None:
			ins.menu = for_menu
		return ins


@dataclass
class Serving:
	servingspercontainer:int
	servingsize:str
	calsperserving:int

@dataclass
class NutritionFacts:
	# a series of tuples representing content and %dv
	total_fat: (str, str)
	saturated_fat: (str, str)
	trans_fat: (str, str)
	cholesterol: (str, str)
	sodium: (str, str)
	total_carbohydrate: (str, str)
	fiber: (str, str)
	total_sugars: (str, str)
	protein: (str, str)

@dataclass
class NutritionLabel:
	serving:Serving
	nutritionfacts:NutritionFacts
	ingredients:list
	allergens:list
