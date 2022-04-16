
def grab_id_from_parens(text:str) -> int:

	start = text.find("(")
	end = text.rfind(");")
	number = text[start + 1:end]
	return int(number)