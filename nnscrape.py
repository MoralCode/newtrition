from bs4 import BeautifulSoup
import requests
import requests_cache
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu, DiningMenuItem, NutritionLabel, Ingredient, Allergen, ItemLabel
from constants import NN_BASE_URL, COOKIES_FILE, PROCESSING_BATCH_SIZE
from helpers import goback, find_or_create, get_or_create
from scraper import Scraper
import csv, sys
import argparse

from database import engine
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from netnutrition import mapper_registry	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='scrape data from NetNutrition into a database')
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

	scraper = Scraper(session=session, cachedir=Path("./cache"))

	homepage = scraper.get(NN_BASE_URL)

	with open(COOKIES_FILE, 'wb') as c:
		pickle.dump(session.cookies, c)

	home_html = BeautifulSoup(homepage.content, 'html.parser') 

	if args.show_cookies:
	# Get cookies
		print(session.cookies.get_dict())

	dining_locations_html = None
	try:
		dining_locations_html = home_html.find(id="cbo_nn_unitDataList").find(class_="row").children
		dining_locations = [DiningLocation.from_html(loc) for loc in dining_locations_html]

	except AttributeError as e:
		print("Could not find data. Try deleting the cookies file")
		print(e)
		sys.exit(1)

	if args.createdb:
		mapper_registry.metadata.create_all(engine)

		# then, load the Alembic configuration and generate the
		# version table, "stamping" it with the most recent rev:
		from alembic.config import Config
		from alembic import command
		alembic_cfg = Config("./alembic.ini")
		command.stamp(alembic_cfg, "head")

	batched = PROCESSING_BATCH_SIZE > 0

	with Session(engine) as dbsession:
		items_processed = 0
		for dining_location in dining_locations:
			get_or_create(dbsession, DiningLocation, dining_location.location_id, dining_location, debug=args.debug, batched=batched)
			menus = dining_location.get_menus(session = session)
			for menu in menus:
				get_or_create(dbsession, DiningMenu, menu.menu_id, menu, debug=args.debug)
				items = menu.get_items(session=session)
				for item in items:
					print("checking loc: {}, menu: {}, item: {}".format(dining_location.location_id, menu.menu_id, item.item_id))
					db_item = get_or_create(dbsession, DiningMenuItem, item.item_id, item, debug=args.debug, batched=batched)
					if db_item != item:
						if items_processed >= PROCESSING_BATCH_SIZE and batched:
							dbsession.commit()
						
						# this is just a best effort check to put *something* in the database. since updating it later would require fetching everything from scratch, which is temporally expensive
						if db_item.nutrition_label is None:
							nut = item.get_nutrition_info(session=session)
							db_item.nutrition_label = nut

						if item.label_names != [i.name for i in db_item.labels]:
							db_item.labels = [find_or_create(dbsession, ItemLabel, ItemLabel(None, i), name=i) for i in item.label_names]
						
						# if nut.ingredients_list:
						# 	nut.ingredients = [find_or_create(dbsession, Ingredient, Ingredient(None, i), debug=args.debug, name=i) for i in nut.ingredients_list]
						# if nut.allergen_list:
						# 	nut.allergens = [find_or_create(dbsession, Allergen, Allergen(None, i), debug=args.debug, name=i) for i in nut.allergen_list]
					
						items_processed += 1
				if items_processed > 0:
					items_processed = 0
					dbsession.commit()
				# reset state for the next menu
				goback(session=session)
			# reset state for the next location
			goback(session=session)