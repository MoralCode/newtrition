import requests 
from constants import NN_BASE_URL, JSON_HEADERS
def grab_id_from_parens(text:str) -> int:

	start = text.find("(")
	end = text.rfind(");")
	number = text[start + 1:end]
	return int(number)

def html_from_json_panel(json, panelid):
	return next((x for x in json.get("panels") if x.get("id") == panelid), None).get("html")


def extract_nutrition_info(row):
	amt = list(row.find(class_="inline-div-left").children)[1].string
	dv = row.find(class_="inline-div-right").string
	return (clean_value(amt), clean_value(dv))

def clean_value(val):
	if val is None:
		return val
	return val.replace("\xa0", " ").strip()

def ingredient_split(string, delimiter):
	"""essentially the same as python string.split, but does not traverse into parenthesis
	"""
	items = []
	last_cut = 0
	current_paren_level = 0
	for i in range(len(string)):
		if string[i] in ["(", "[", "<", "{"]:
			current_paren_level += 1
		elif string[i] in [")", "]", ">", "}"]:
			current_paren_level -= 1
		if (string[i] == delimiter) and current_paren_level <= 0:
			items.append(clean_value(string[last_cut:i]))
			# update the cut position and exclude the parens
			last_cut = i + 1
		# make sure the last item in the list gets included
		if i == len(string)-1:
			items.append(clean_value(string[last_cut:]))
	return items

def goback(session = requests):
	"""Send a request to the server to reset the state so another menu selection is allowed
	"""
	return session.post(
		NN_BASE_URL + "Menu/GoBackFromMenuList",
		headers=JSON_HEADERS)