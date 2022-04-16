from bs4 import BeautifulSoup
from helpers import grab_id_from_parens
from dataclasses import dataclass

class NetNutrition:
	"""A class representing the net nutrition API and keeping track of the current state?
	"""
	pass


@dataclass
class DiningLocation:
	name:str
	identifier: int

	@classmethod
	def from_html(cls, html):
		link = html.find(class_="cbo_nn_unitNameLink")
		name = link.string
		identifier = grab_id_from_parens(link["onclick"])
		return cls(name, identifier)

	# def __init__(self, name, identifier):
	# 	self.name = name
	# 	self.id = identifier
