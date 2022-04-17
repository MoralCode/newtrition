from __future__ import annotations

from bs4 import BeautifulSoup
from helpers import grab_id_from_parens, html_from_json_panel, extract_nutrition_info, clean_value, ingredient_split
from dataclasses import dataclass
from constants import NN_BASE_URL, JSON_HEADERS
import requests
import datetime
from dateutil.parser import parse


from dataclasses import field
from typing import List
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String, Date
from sqlalchemy import Table, UniqueConstraint
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship

mapper_registry = registry()


@mapper_registry.mapped
@dataclass
class DiningLocation:
	__table__ = Table(
        "dining_location",
        mapper_registry.metadata,
        Column("location_id", Integer, primary_key=True),
        # Column("name", Integer, ForeignKey("user.id")),
        Column("name", String(256)),
    )
	name:str
	location_id: int

	def get_menus(self, session=requests):
		if self._menus is not None:
			return self._menus
		
		menu_response = session.post(
			NN_BASE_URL + "/Unit/SelectUnitFromUnitsList",
			data="unitOid=" + str(self.location_id),
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
		self.location_id = identifier
		self._menus = None

	__mapper_args__ = {   # type: ignore
        "properties" : {
            "menus": relationship("DiningMenu", back_populates="location")
        }
    }


@mapper_registry.mapped
@dataclass
class DiningMenu:
	__table__ = Table(
        "dining_menu",
        mapper_registry.metadata,
        Column("menu_id", Integer, primary_key=True),
        Column("location_id", Integer, ForeignKey("dining_location.location_id")),
        Column("date", Date()),
    )
	date:datetime.datetime
	menu_id:int
	location_id: int

	def __init__(self, date, identifier):
		self.date = parse(date)
		self.menu_id = identifier
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
			data="menuOid=" + str(self.menu_id),
			headers=JSON_HEADERS)
		menuitem_html = html_from_json_panel(menuitem_response.json(), "itemPanel")
		menuitem_list_html = BeautifulSoup(menuitem_html, 'html.parser') 
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
			ins.location_id = for_location.location_id
		return ins
	
	__mapper_args__ = {   # type: ignore
        "properties" : {
			"location": relationship("DiningLocation", back_populates="menus"),
            "items": relationship("DiningMenuItem")#, back_populates="menu"
        }
    }


item_labels = Table('item_labels', mapper_registry.metadata,
    Column('item_id', ForeignKey('dining_menu_item.item_id'), primary_key=True),
    Column('label_id', ForeignKey('labels.label_id'), primary_key=True),
)


@mapper_registry.mapped
@dataclass
class DiningMenuItem:
	__table__ = Table(
        "dining_menu_item",
        mapper_registry.metadata,
        Column("item_id", Integer, primary_key=True),
        Column("menu_id", Integer, ForeignKey("dining_menu.menu_id")),
        Column("name", String(256)),
    )
	name:str
	item_id:int
	menu_id:int

	def __init__(self, name, identifier):
		self.name = name
		self.item_id = identifier
		self._menu = None
		self._nutrition = None
		self.label_names = []

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
			data="detailOid=" + str(self.item_id),
			headers=JSON_HEADERS)
		nutrition_html = BeautifulSoup(nutrition_response.content, 'html.parser') 
		data = list(nutrition_html.find("table").children)
		
		#ignore the forst two rows: name and "nutrition information" heading
		currentrow = 2
		servinginfo = None
		try:
			#servings per container
			serv = data[currentrow].find(class_="cbo_nn_LabelBottomBorderLabel")
			spc = list(serv.children)[0].string.split("\xa0")[0]
			servsize = serv.find(class_="inline-div-right").string

			# cals per serving
			currentrow += 1
			cals = int(data[currentrow].find(class_="inline-div-right").string)

			servinginfo = Serving(int(spc), clean_value(servsize), cals)
		except Exception as e:
			print("an error occurred while looking for serving info for menuitem {}: ".format(self.item_id) + str(e))

		# % dv heading, skip this
		currentrow += 1
		nutritionfacts = None
		try:
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
		except Exception as e:
			print("an error occurred while looking for nutrition facts for menuitem {}: ".format(self.item_id) + str(e))

		# ingredients
		currentrow += 1
		ingredients = None
		try:
			ingredients = data[currentrow].find(class_="cbo_nn_LabelIngredients").string
			ingredients = clean_value(ingredients)
			# ingredients = ingredient_split(ingredients, ",")
		except Exception as e:
			print("an error occurred while looking for ingredients for menuitem {}: ".format(self.item_id) + str(e))
		

		# allergens
		currentrow += 1
		allergens = None
		try:
			allergens = data[currentrow].find(class_="cbo_nn_LabelAllergens").string#.split(",")
			allergens = clean_value(allergens)
			# allergens = [clean_value(a) for a in allergens]
		except Exception as e:
			print("an error occurred while looking for allergens for menuitem {}: ".format(self.item_id) + str(e))

		self._nutrition = NutritionLabel(servinginfo, nutritionfacts, ingredients, allergens,for_item=self.item_id)
		return self._nutrition

	@classmethod
	def from_html(cls, html, for_menu=None):
		item = html.find(class_="cbo_nn_itemHover")
		name = next(item.children)
		identifier = grab_id_from_parens(item["onclick"])
		ins = cls(name, identifier)
		ins.label_names = [l.get("title") for l in item.find_all("img")]
		if for_menu is not None:
			ins.menu_id = for_menu.menu_id
		return ins

	__mapper_args__ = {   # type: ignore
        "properties" : {
			# "location": relationship("DiningLocation", back_populates="menus"),
            "nutrition_label": relationship("NutritionLabel", uselist=False),
			"labels": relationship("ItemLabel", secondary=item_labels)

        }
    }


@dataclass
class Serving:
	"""a convenience class to make it easier to create a nutrition label
	"""
	servingspercontainer:int
	servingsize:str
	calsperserving:int

@dataclass
class NutritionFacts:
	"""a convenience class to make it easier to create a nutrition label
	"""
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
	
	
# label_ingredients = Table('label_ingredients', mapper_registry.metadata,
#     Column('label_id', ForeignKey('nutrition_label.nutrition_label_id'), primary_key=True),
#     Column('ingredient_id', ForeignKey('ingredients.ingredient_id'), primary_key=True)
# )

# label_allergens = Table('label_allergens', mapper_registry.metadata,
#     Column('label_id', ForeignKey('nutrition_label.nutrition_label_id'), primary_key=True),
#     Column('allergen_id', ForeignKey('allergens.allergen_id'), primary_key=True)
# )

		
@mapper_registry.mapped
@dataclass
class NutritionLabel:
	__table__ = Table(
        "nutrition_label",
        mapper_registry.metadata,
        Column("nutrition_label_id", Integer, primary_key=True),
        Column("item_id", Integer, ForeignKey("dining_menu_item.item_id")),
		Column("servings_per_container", Integer),
        Column("cals_per_serving", Integer),
        Column("serving_size", String(32)),

        Column("total_fat_amt", String(32)),
		Column("total_fat_dv", String(32)),
		Column("saturated_fat_amt", String(32)),
		Column("saturated_fat_dv", String(32)),
		Column("trans_fat_amt", String(32)),
		Column("trans_fat_dv", String(32)),
		Column("cholesterol_amt", String(32)),
		Column("cholesterol_dv", String(32)),
		Column("sodium_amt", String(32)),
		Column("sodium_dv", String(32)),
		Column("total_carbohydrate_amt", String(32)),
		Column("total_carbohydrate_dv", String(32)),
		Column("fiber_amt", String(32)),
		Column("fiber_dv", String(32)),
		Column("total_sugars_amt", String(32)),
		Column("protein_amt", String(32)),

		Column("ingredients", String(2000)),
		Column("allergens", String(500)),
    )
	nutrition_label_id:int
	item_id:int

	servings_per_container:int
	serving_size:str
	cals_per_serving:int

	total_fat_amt: str
	total_fat_dv: str
	saturated_fat_amt: str
	saturated_fat_dv: str
	trans_fat_amt: str
	trans_fat_dv: str
	cholesterol_amt: str
	cholesterol_dv: str
	sodium_amt: str
	sodium_dv: str
	total_carbohydrate_amt: str
	total_carbohydrate_dv: str
	fiber_amt: str
	fiber_dv: str
	total_sugars_amt: str
	protein_amt: str
	#temporary vars used while processing the lists and deduping them
	ingredients:str
	allergens:str

	def __init__(self, serving: Serving, nutritionfacts:NutritionFacts, ingredients:list, allergens:list, for_item=None):
		if nutritionfacts:
			self.total_fat_amt = nutritionfacts.total_fat[0]
			self.total_fat_dv = nutritionfacts.total_fat[1]
			self.saturated_fat_amt = nutritionfacts.saturated_fat[0]
			self.saturated_fat_dv = nutritionfacts.saturated_fat[1]
			self.trans_fat_amt = nutritionfacts.trans_fat[0]
			self.trans_fat_dv = nutritionfacts.trans_fat[1]
			self.cholesterol_amt = nutritionfacts.cholesterol[0]
			self.cholesterol_dv = nutritionfacts.cholesterol[1]
			self.sodium_amt = nutritionfacts.sodium[0]
			self.sodium_dv = nutritionfacts.sodium[1]
			self.total_carbohydrate_amt = nutritionfacts.total_carbohydrate[0]
			self.total_carbohydrate_dv = nutritionfacts.total_carbohydrate[1]
			self.fiber_amt = nutritionfacts.fiber[0]
			self.fiber_dv = nutritionfacts.fiber[1]
			self.total_sugars_amt = nutritionfacts.total_sugars[0]
			self.protein_amt = nutritionfacts.protein[0]

		if serving:
			self.servings_per_container = serving.servingspercontainer
			self.serving_size = serving.servingsize
			self.cals_per_serving = serving.calsperserving
		if for_item:
			self.item_id = for_item
		self.ingredients = ingredients
		self.allergens = allergens 

	# __mapper_args__ = {   # type: ignore
    #     "properties" : {
    #         "ingredients": relationship("Ingredient", secondary=label_ingredients, nullable=True),
	# 		"allergens": relationship("Allergen", secondary=label_allergens),
			
    #     }
    # }

@mapper_registry.mapped
@dataclass
class Ingredient:
	__table__ = Table(
        "ingredients",
        mapper_registry.metadata,
        Column("ingredient_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(256)),
		UniqueConstraint("name")
    )
	ingredient_id:int
	name:str



@mapper_registry.mapped
@dataclass
class Allergen:
	__table__ = Table(
        "allergens",
        mapper_registry.metadata,
        Column("allergen_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(256)),
		UniqueConstraint("name")
    )
	allergen_id:int
	name:str


@mapper_registry.mapped
@dataclass
class ItemLabel:
	__table__ = Table(
        "labels",
        mapper_registry.metadata,
        Column("label_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(256)),
		UniqueConstraint("name")
    )
	label_id:int
	name:str