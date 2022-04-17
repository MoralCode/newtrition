
def grab_id_from_parens(text:str) -> int:

	start = text.find("(")
	end = text.rfind(");")
	number = text[start + 1:end]
	return int(number)

def html_from_json_panel(json, panelid):
	return next((x for x in json.get("panels") if x.get("id") == panelid), None).get("html")