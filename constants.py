COOKIES_FILE = "cookies.txt"
NN_BASE_URL = "https://www.rit.edu/fa/diningservices/netnutrition/1"
# https://www.rit.edu/fa/diningservices/netnutrition/1/NutritionDetail/ShowItemNutritionLabel

ARCHIVE_DB_CONNECTION_STR = "sqlite:///archive.db"

JSON_HEADERS = {
	"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
	"Referer": NN_BASE_URL
}