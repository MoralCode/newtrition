
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
