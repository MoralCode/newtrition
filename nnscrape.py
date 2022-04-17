from bs4 import BeautifulSoup
import requests
import requests_cache
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu, DiningMenuItem, NutritionLabel, Ingredient, Allergen
from constants import NN_BASE_URL, COOKIES_FILE
from helpers import goback
import csv
import argparse

from database import engine
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from netnutrition import mapper_registry


# based on https://stackoverflow.com/a/6078058/
def get_or_create(dbsession, model, identifier, fetched_object, debug = False):
	instance = dbsession.query(model).get(identifier)
	if debug:
		print("i:" + str(instance))
	if instance is None:
		dbsession.add(fetched_object)
		dbsession.commit()
		if debug:
			print("added {} with id {} to db".format(model.__name__, identifier))
	elif debug:
		print("{} with id {} already present in db".format(model.__name__, identifier))


	
def find_or_create(dbsession, model, fetched_object, debug = False, **kwargs):
	instance = dbsession.query(model).filter_by(**kwargs).first()
	if debug:
		print("i:" + str(instance))
	if instance is None:
		dbsession.add(fetched_object)
		dbsession.commit()
		if debug:
			print("added {} to db".format(fetched_object))
		return fetched_object
	else:
		if debug:
			print("{} already present in db".format(instance))
		return instance	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Process some integers.')
	parser.add_argument('mode', choices=['test', 'csv', 'archive'],
						help='pick a mode')
	parser.add_argument('--cached', action='store_true',
						help='whether caching should be used')
	parser.add_argument('--show-cookies', action='store_true',
						help='whether to print the session id in the cookies')
	parser.add_argument('--createdb', action='store_true',
						help='whether to create a new DB')
	parser.add_argument('--debug', action='store_true',
						help='print debugging output')
	args = parser.parse_args()


	# this will need to be put back once this goes live as every POST request needs to hit NN to work
	session = None
	if args.cached:
		session=requests_cache.CachedSession('nn_pagecache')
	else:
		session = session = requests.Session() #, allowable_methods=['GET'])

	if Path(COOKIES_FILE).exists():
		with open(COOKIES_FILE, 'rb') as c:
			# contents = c.read()
			# if len(contents) > 0:
			session.cookies.update(pickle.load(c))

	homepage = session.get(NN_BASE_URL)

	with open(COOKIES_FILE, 'wb') as c:
		pickle.dump(session.cookies, c)

	home_html = BeautifulSoup(homepage.content, 'html.parser') 

	if args.show_cookies:
	# Get cookies
		print(session.cookies.get_dict())

	dining_locations_html = home_html.find(id="cbo_nn_unitDataList").find(class_="row").children
	dining_locations = [DiningLocation.from_html(loc) for loc in dining_locations_html]

	if args.mode == "csv":
		item_ids = set()


		with open('data.csv', 'w') as csvfile:
			spamwriter = csv.writer(csvfile)
			for location in dining_locations:
				menus = location.get_menus(session = session)
				for menu in menus:

					items = menu.get_items(session = session)
					for item in items:
						print("processing loc: {}, menu: {}, item: {}".format(location.identifier, menu.identifier, item.identifier))
						if len(set([item.identifier]).intersection(item_ids)) == 1:
							print("\trepeat item found")
						else:
							item_ids.add(item.identifier)
						nut = item.get_nutrition_info(session=session)
						try:
							spamwriter.writerow([item.name, location.name, nut.serving.calsperserving])
						except Exception as e:
							print("not enough data to write: " + str(e))
					# reset state for the next menu
					goback(session=session)
				# reset state for the next location
				goback(session=session)

	elif args.mode == "test":

		artesanos = dining_locations[1]
		a_menu = artesanos.get_menus(session = session)[0]
		an_item = a_menu.get_items(session = session)[0]
		print(an_item)
		print(an_item.get_nutrition_info(session=session))


	elif args.mode == "archive":
		if args.createdb:
			mapper_registry.metadata.create_all(engine)


		with Session(engine) as dbsession:
			for dining_location in dining_locations:
				menus = dining_location.get_menus(session = session)
				for menu in menus:
					# get_or_create(dbsession, DiningMenu, menu.menu_id, menu, debug=args.debug)
					items = menu.get_items(session=session)
					for item in items:
						print("processing loc: {}, menu: {}, item: {}".format(dining_location.location_id, menu.menu_id, item.item_id))

						nut = item.get_nutrition_info(session=session)
						get_or_create(dbsession, NutritionLabel, nut.nutrition_label_id, nut, debug=args.debug)
						# print(nut)
						# if nut.ingredients_list:
						# 	nut.ingredients = [find_or_create(dbsession, Ingredient, Ingredient(None, i), debug=args.debug, name=i) for i in nut.ingredients_list]
						# if nut.allergen_list:
						# 	nut.allergens = [find_or_create(dbsession, Allergen, Allergen(None, i), debug=args.debug, name=i) for i in nut.allergen_list]
 					# reset state for the next menu
					goback(session=session)
				# reset state for the next location
				goback(session=session)